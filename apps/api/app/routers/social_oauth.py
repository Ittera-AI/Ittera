"""
Social account OAuth connections — Twitter/X, LinkedIn, Instagram.

Flow:
  1. Frontend opens popup → backend /connect/{platform}/start
  2. Platform redirects to /connect/{platform}/callback
  3. Backend stores tokens in SocialConnection, returns HTML that
     postMessages back to the opener and closes the popup.
"""

import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from urllib.parse import urlencode, urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import redact_text
from app.core.security import encrypt_value
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.schemas.social import ConnectSessionResponseV1
from app.services.connect_state_store import (
    ConnectStateStoreError,
    bind_connect_state,
    take_connect_state,
)
from app.services.connect_token_store import (
    ConnectTokenStoreError,
    mint_connect_token,
    take_connect_token,
)
from app.services.pkce_store import VerifierStoreError, put_verifier, take_verifier
from app.services.publishing_state import (
    LINKEDIN_POSTING_SCOPES,
    LINKEDIN_READ_SCOPES,
    X_MEDIA_SCOPES,
    X_POSTING_SCOPES,
    missing_scopes,
)

router = APIRouter()

logger = logging.getLogger(__name__)


async def _resolve_start_user(ct: Optional[str]) -> Tuple[Optional[str], str]:
    """Resolve the connecting user for a ``/start`` request.

    The connecting identity is accepted only through the single-use ``ct`` token
    minted by ``POST /connect/session`` (a server-side exchange). This keeps the
    bearer JWT out of the OAuth start URL entirely; a raw bearer JWT supplied as
    a ``?token=`` query parameter is no longer accepted. (R4.2)

    The returned reason is always a category-level message — it never embeds a
    raw token value or an upstream payload. (R4.5)
    """
    if not ct:
        return None, "No connect token provided."
    try:
        user_id = take_connect_token(ct)
    except ConnectTokenStoreError:
        logger.warning("connect-token store unavailable during OAuth /start")
        return None, "Could not reach the connect-token store. Please try again."
    if user_id:
        return user_id, ""
    return None, "Connect token is missing, expired, or already used."

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _frontend_origin() -> str:
    """Scheme://host[:port] derived from settings.FRONTEND_URL.

    Used as the postMessage target origin so the OAuth popup posts its result
    only to the configured frontend, never to a wildcard ("*") origin.
    """
    parsed = urlparse(settings.FRONTEND_URL)
    return f"{parsed.scheme}://{parsed.netloc}"


def _popup_response(platform: str, status_str: str, username: str = "", error: str = "") -> HTMLResponse:
    """Returns an HTML page that postMessages to the opener and closes itself."""
    target_origin = _frontend_origin()
    payload = json.dumps({
        "type": "ittera_oauth",
        "platform": platform,
        "status": status_str,
        "username": username,
        "error": error,
    })
    html = f"""<!DOCTYPE html>
<html>
<head><title>Connecting...</title></head>
<body>
<script>
  try {{
    window.opener.postMessage({payload}, {json.dumps(target_origin)});
  }} catch(e) {{}}
  window.close();
</script>
<p style="font-family:sans-serif;text-align:center;margin-top:40px;color:#888">
  {"Connected! You can close this window." if status_str == "connected" else "Something went wrong. You can close this window."}
</p>
</body>
</html>"""
    return HTMLResponse(content=html)


def _make_connect_state(user_id: str, platform: str, extra: dict = {}) -> str:
    """Encode user_id + platform in a signed JWT state param."""
    from datetime import timedelta
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload = {"sub": user_id, "platform": platform, "exp": expire, **extra}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_connect_state(state: str) -> Optional[dict]:
    try:
        return jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def _upsert_connection(
    db: Session,
    user_id: str,
    platform: str,
    platform_user_id: str,
    platform_username: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    scopes: list = [],
    metadata: dict = {},
    token_expires_at: datetime | None = None,
) -> SocialConnection:
    # Encrypt all OAuth tokens at rest (requirement 5.1/5.2). Read sites use
    # decrypt_token (X) or decrypt_token_lenient (LinkedIn/Instagram, which may
    # still hold legacy plaintext rows) so this is safe across the migration.
    stored_access_token = encrypt_value(access_token) if access_token else access_token
    stored_refresh_token = encrypt_value(refresh_token) if refresh_token else refresh_token

    conn = (
        db.query(SocialConnection)
        .filter_by(user_id=user_id, platform=platform)
        .first()
    )
    if conn:
        conn.platform_user_id = platform_user_id
        conn.platform_username = platform_username
        conn.access_token = stored_access_token
        conn.refresh_token = stored_refresh_token
        conn.token_expires_at = token_expires_at
        conn.scopes = scopes
        conn.connection_metadata = metadata
        conn.is_active = True
        # A fresh authorization clears any prior reconnect requirement (R4.3).
        conn.requires_reconnect = False
        conn.last_synced_at = datetime.now(timezone.utc)
    else:
        conn = SocialConnection(
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
            platform_username=platform_username,
            access_token=stored_access_token,
            refresh_token=stored_refresh_token,
            token_expires_at=token_expires_at,
            scopes=scopes,
            connection_metadata=metadata,
        )
        db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


# ─── Status & Disconnect ─────────────────────────────────────────────────────

@router.get("/status")
def connection_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all active social connections for the current user."""
    conns = db.query(SocialConnection).filter_by(user_id=current_user.id, is_active=True).all()
    return [_connection_status_payload(c) for c in conns]


@router.post("/session", response_model=ConnectSessionResponseV1)
def create_connect_session(
    current_user: User = Depends(get_current_user),
) -> ConnectSessionResponseV1:
    """Mint a single-use connect token for the authenticated user.

    The frontend calls this (Bearer auth) and passes the returned token to
    ``/connect/{platform}/start`` as ``?ct=...`` instead of the raw Supabase JWT,
    so no bearer credential ends up in the OAuth start URL.
    """
    try:
        connect_token = mint_connect_token(current_user.id)
    except ConnectTokenStoreError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the connect-token store. Please try again.",
        )
    return ConnectSessionResponseV1(connect_token=connect_token)


@router.delete("/{platform}")
def disconnect(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = db.query(SocialConnection).filter_by(user_id=current_user.id, platform=platform).first()
    if conn:
        conn.is_active = False
        db.commit()
    return {"disconnected": platform}


# ─── Twitter / X OAuth 2.0 (PKCE) ────────────────────────────────────────────

TWITTER_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
TWITTER_ME_URL = "https://api.twitter.com/2/users/me"
TWITTER_SCOPES = "tweet.read users.read tweet.write media.write offline.access"


def _x_token_auth() -> Optional[Tuple[str, str]]:
    """Return HTTP Basic credentials when a client secret is configured.

    When ``settings.TWITTER_CLIENT_SECRET`` is set, the X app is a confidential
    client and every token-endpoint request authenticates via HTTP Basic auth
    (``client_id:client_secret``). Returns ``None`` only when no secret is
    configured (public-client fallback). Both the connect and refresh flows
    obtain their client authentication from this single helper so they cannot
    drift apart.
    """
    if settings.TWITTER_CLIENT_SECRET:
        return (settings.TWITTER_CLIENT_ID, settings.TWITTER_CLIENT_SECRET)
    return None


def _pkce_pair():
    verifier = secrets.token_urlsafe(43)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


@router.get("/twitter/start")
async def twitter_start(
    ct: Optional[str] = Query(None, description="Single-use connect token from POST /connect/session"),
    db: Session = Depends(get_db),
):
    """Open this in a popup. Redirects to Twitter OAuth."""
    if not settings.TWITTER_CLIENT_ID:
        return _popup_response("twitter", "error", error="Twitter OAuth is not configured.")

    user_id, err_reason = await _resolve_start_user(ct)
    if not user_id:
        return _popup_response("twitter", "error", error=err_reason)

    verifier, challenge = _pkce_pair()
    state = _make_connect_state(user_id, "twitter")
    try:
        put_verifier(state, verifier)  # store verifier keyed by state (TTL 10m)
    except VerifierStoreError:
        return _popup_response(
            "twitter",
            "error",
            error="Could not reach the verifier store. Please try connecting again.",
        )

    params = urlencode({
        "response_type": "code",
        "client_id": settings.TWITTER_CLIENT_ID,
        "redirect_uri": settings.TWITTER_REDIRECT_URI,
        "scope": TWITTER_SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    from starlette.responses import RedirectResponse
    return RedirectResponse(url=f"{TWITTER_AUTH_URL}?{params}", status_code=302)


@router.get("/twitter/callback")
async def twitter_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    decoded = _decode_connect_state(state)
    if not decoded or decoded.get("platform") != "twitter":
        return _popup_response("twitter", "error", error="Invalid OAuth state.")

    user_id = decoded["sub"]
    try:
        verifier = take_verifier(state)
    except VerifierStoreError:
        return _popup_response(
            "twitter",
            "error",
            error="Could not reach the verifier store. Please try connecting again.",
        )
    if not verifier:
        return _popup_response(
            "twitter",
            "error",
            error="PKCE verifier is missing or expired. Please start the connection again.",
        )

    auth = _x_token_auth()
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.TWITTER_REDIRECT_URI,
        "code_verifier": verifier,
    }
    # When Basic auth is used the client is identified by the Authorization
    # header, so client_id must not also be sent in the form body.
    if auth is None:
        token_data["client_id"] = settings.TWITTER_CLIENT_ID

    async with httpx.AsyncClient(timeout=15) as client:
        token_res = await client.post(
            TWITTER_TOKEN_URL,
            data=token_data,
            auth=auth,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_res.is_error:
            # Never log the raw upstream response body or tokens — status only. (R4.4)
            logger.warning("twitter token exchange failed (status=%s)", token_res.status_code)
            return _popup_response("twitter", "error", error="Token exchange failed.")

        tokens = token_res.json()
        access_token = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token")
        token_expires_at = None
        if tokens.get("expires_in"):
            token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(tokens["expires_in"]))
        scopes = str(tokens.get("scope") or TWITTER_SCOPES).split()

        me_res = await client.get(
            f"{TWITTER_ME_URL}?user.fields=username,name,profile_image_url",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if me_res.is_error:
            logger.warning("twitter profile fetch failed (status=%s)", me_res.status_code)
            return _popup_response("twitter", "error", error="Could not fetch Twitter profile.")

        me = me_res.json().get("data", {})

    # Preserve existing subscription_tier on reconnect
    existing_conn = (
        db.query(SocialConnection)
        .filter_by(user_id=user_id, platform="twitter")
        .first()
    )
    existing_tier = "free"
    if existing_conn and existing_conn.connection_metadata:
        existing_tier = existing_conn.connection_metadata.get("subscription_tier", "free")

    _upsert_connection(
        db,
        user_id=user_id,
        platform="twitter",
        platform_user_id=me.get("id", ""),
        platform_username=me.get("username", ""),
        access_token=access_token,
        refresh_token=refresh_token,
        scopes=scopes,
        token_expires_at=token_expires_at,
        metadata={
            "name": me.get("name", ""),
            "profile_image": me.get("profile_image_url", ""),
            "subscription_tier": existing_tier,
        },
    )

    # ── Auto-trigger Twitter content sync immediately after OAuth completes ──
    # This fires in the background (Celery) — the user sees "Connected" right away.
    try:
        from app.services.twitter_service import queue_twitter_sync_task
        queue_twitter_sync_task(user_id)
    except Exception:
        logger.warning(
            "twitter_callback: could not enqueue sync task for user_id=%s — "
            "Celery may not be running. User can trigger sync manually.",
            user_id,
        )

    return _popup_response("twitter", "connected", username=me.get("username", ""))


# ─── LinkedIn OAuth 2.0 ───────────────────────────────────────────────────────

LINKEDIN_CONNECT_SCOPES = "openid profile email w_member_social"


@router.get("/linkedin/start")
async def linkedin_start(
    ct: Optional[str] = Query(None, description="Single-use connect token from POST /connect/session"),
    db: Session = Depends(get_db),
):
    if not settings.LINKEDIN_CLIENT_ID:
        return _popup_response("linkedin", "error", error="LinkedIn OAuth is not configured.")

    user_id, err_reason = await _resolve_start_user(ct)
    if not user_id:
        return _popup_response("linkedin", "error", error=err_reason)

    state = _make_connect_state(user_id, "linkedin")
    try:
        bind_connect_state(state, user_id)  # single-use, session-bound (TTL 10m)
    except ConnectStateStoreError:
        return _popup_response(
            "linkedin",
            "error",
            error="Could not reach the connection store. Please try connecting again.",
        )
    params = urlencode({
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": LINKEDIN_CONNECT_SCOPES,
    })
    from starlette.responses import RedirectResponse
    return RedirectResponse(url=f"https://www.linkedin.com/oauth/v2/authorization?{params}", status_code=302)


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    if error:
        # Do not echo the upstream ``error_description`` back to the browser or
        # logs — it may carry raw provider payload. Log a redacted, category-only
        # record and return a category-level message. (R4.4, R4.5)
        logger.warning(
            "linkedin oauth callback returned an error: %s",
            redact_text(str(error)),
        )
        return _popup_response(
            "linkedin",
            "error",
            error="LinkedIn authorization failed. Please try connecting again.",
        )
    if not code or not state:
        return _popup_response("linkedin", "error", error="LinkedIn did not return an authorization code.")

    decoded = _decode_connect_state(state)
    if not decoded or decoded.get("platform") != "linkedin":
        return _popup_response("linkedin", "error", error="Invalid OAuth state.")

    user_id = decoded["sub"]

    # Single-use/binding check: the state must have been recorded at /start, must
    # not be expired, and must not have been consumed already. Rejects missing,
    # expired, reused, and unbound states (mirrors the X PKCE verifier guarantee).
    try:
        bound_user_id = take_connect_state(state)
    except ConnectStateStoreError:
        return _popup_response(
            "linkedin",
            "error",
            error="Could not reach the connection store. Please try connecting again.",
        )
    if not bound_user_id or bound_user_id != user_id:
        return _popup_response(
            "linkedin",
            "error",
            error="OAuth state is missing, expired, or already used. Please start the connection again.",
        )

    async with httpx.AsyncClient(timeout=15) as client:
        token_res = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_res.is_error:
            logger.warning("linkedin token exchange failed (status=%s)", token_res.status_code)
            return _popup_response("linkedin", "error", error="Token exchange failed.")

        tokens = token_res.json()
        access_token = tokens.get("access_token", "")
        scopes = str(tokens.get("scope") or LINKEDIN_CONNECT_SCOPES).split()

        profile_res = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_res.is_error:
            logger.warning("linkedin profile fetch failed (status=%s)", profile_res.status_code)
            return _popup_response("linkedin", "error", error="Could not fetch LinkedIn profile.")

        profile = profile_res.json()

    username = profile.get("email", "").split("@")[0] or profile.get("name", "user")
    _upsert_connection(
        db,
        user_id=user_id,
        platform="linkedin",
        platform_user_id=profile.get("sub", ""),
        platform_username=username,
        access_token=access_token,
        scopes=scopes,
        metadata={"name": profile.get("name", ""), "picture": profile.get("picture", "")},
    )

    # ── Auto-trigger post sync immediately after OAuth completes ─────────────
    # This fires in the background (Celery) — the user sees "Connected" right away.
    try:
        from app.services import linkedin_service
        if "r_member_social" in scopes:
            linkedin_service.queue_scrape_task(user_id)
    except Exception:
        logger.warning(
            "linkedin_callback: could not enqueue scrape task for user_id=%s — "
            "Celery may not be running. User can trigger sync manually.",
            user_id,
        )

    return _popup_response("linkedin", "connected", username=username)


# ─── Instagram (Meta) OAuth ───────────────────────────────────────────────────

INSTAGRAM_AUTH_URL = "https://api.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
INSTAGRAM_ME_URL = "https://graph.instagram.com/me"
INSTAGRAM_SCOPES = "user_profile,user_media"


@router.get("/instagram/start")
async def instagram_start(
    ct: Optional[str] = Query(None, description="Single-use connect token from POST /connect/session"),
    db: Session = Depends(get_db),
):
    if not settings.INSTAGRAM_APP_ID:
        return _popup_response("instagram", "error", error="Instagram OAuth is not configured.")

    user_id, err_reason = await _resolve_start_user(ct)
    if not user_id:
        return _popup_response("instagram", "error", error=err_reason)

    state = _make_connect_state(user_id, "instagram")
    try:
        bind_connect_state(state, user_id)  # single-use, session-bound (TTL 10m)
    except ConnectStateStoreError:
        return _popup_response(
            "instagram",
            "error",
            error="Could not reach the connection store. Please try connecting again.",
        )
    params = urlencode({
        "client_id": settings.INSTAGRAM_APP_ID,
        "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
        "scope": INSTAGRAM_SCOPES,
        "response_type": "code",
        "state": state,
    })
    from starlette.responses import RedirectResponse
    return RedirectResponse(url=f"{INSTAGRAM_AUTH_URL}?{params}", status_code=302)


@router.get("/instagram/callback")
async def instagram_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    decoded = _decode_connect_state(state)
    if not decoded or decoded.get("platform") != "instagram":
        return _popup_response("instagram", "error", error="Invalid OAuth state.")

    user_id = decoded["sub"]

    # Single-use/binding check: the state must have been recorded at /start, must
    # not be expired, and must not have been consumed already. Rejects missing,
    # expired, reused, and unbound states (mirrors the X PKCE verifier guarantee).
    try:
        bound_user_id = take_connect_state(state)
    except ConnectStateStoreError:
        return _popup_response(
            "instagram",
            "error",
            error="Could not reach the connection store. Please try connecting again.",
        )
    if not bound_user_id or bound_user_id != user_id:
        return _popup_response(
            "instagram",
            "error",
            error="OAuth state is missing, expired, or already used. Please start the connection again.",
        )

    async with httpx.AsyncClient(timeout=15) as client:
        token_res = await client.post(
            INSTAGRAM_TOKEN_URL,
            data={
                "client_id": settings.INSTAGRAM_APP_ID,
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
                "code": code,
            },
        )
        if token_res.is_error:
            logger.warning("instagram token exchange failed (status=%s)", token_res.status_code)
            return _popup_response("instagram", "error", error="Token exchange failed.")

        tokens = token_res.json()
        access_token = tokens.get("access_token", "")
        ig_user_id = str(tokens.get("user_id", ""))

        me_res = await client.get(
            f"{INSTAGRAM_ME_URL}?fields=id,username&access_token={access_token}"
        )
        if me_res.is_error:
            logger.warning("instagram profile fetch failed (status=%s)", me_res.status_code)
            return _popup_response("instagram", "error", error="Could not fetch Instagram profile.")

        me = me_res.json()

    _upsert_connection(
        db,
        user_id=user_id,
        platform="instagram",
        platform_user_id=ig_user_id or me.get("id", ""),
        platform_username=me.get("username", ""),
        access_token=access_token,
        scopes=INSTAGRAM_SCOPES.split(","),
    )
    return _popup_response("instagram", "connected", username=me.get("username", ""))


def _connection_status_payload(conn: SocialConnection) -> dict:
    scopes = list(conn.scopes or [])
    if conn.platform == "linkedin":
        posting_missing = missing_scopes(scopes, LINKEDIN_POSTING_SCOPES)
        read_missing = missing_scopes(scopes, LINKEDIN_READ_SCOPES)
    elif conn.platform == "twitter":
        posting_missing = missing_scopes(scopes, X_POSTING_SCOPES | X_MEDIA_SCOPES)
        read_missing = []
    else:
        posting_missing = []
        read_missing = []
    return {
        "platform": conn.platform,
        # Canonical field names (aligned with PlatformStatusResponse). The legacy
        # aliases below are retained for backward compatibility with older clients.
        "platform_username": conn.platform_username,
        "connected_at": conn.created_at,
        "last_synced_at": conn.last_synced_at,
        "scopes": scopes,
        "missing_scopes": posting_missing,
        "missing_posting_scopes": posting_missing,
        "missing_read_scopes": read_missing,
        "posting_ready": not posting_missing,
        "read_sync_ready": not read_missing,
        # A persisted requires_reconnect (token could not be refreshed/decrypted)
        # forces reconnect regardless of scope state (R4.3).
        "reconnect_required": bool(posting_missing) or bool(conn.requires_reconnect),
        # ── Legacy aliases (deprecated) ──
        "username": conn.platform_username,
        "last_synced": conn.last_synced_at,
    }
