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
import secrets
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies.auth import get_current_user, _decode_supabase_jwt, _decode_legacy_jwt, _fetch_supabase_user
from app.dependencies.db import get_db
from app.models.social_connection import SocialConnection
from app.models.user import User

router = APIRouter()

from typing import Optional, Tuple

async def _get_user_id_from_token(token: str) -> Tuple[Optional[str], str]:
    if not token:
        return None, "Token is empty"
    payload = _decode_supabase_jwt(token)
    if payload and "sub" in payload:
        return payload["sub"], ""
    payload = _decode_legacy_jwt(token)
    if payload and "sub" in payload:
        return payload["sub"], ""
    try:
        payload = await _fetch_supabase_user(token)
        if payload and "sub" in payload:
            return payload["sub"], ""
        return None, f"Supabase auth API returned: {payload}"
    except Exception as e:
        return None, f"Supabase auth API exception: {str(e)}"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _popup_response(platform: str, status_str: str, username: str = "", error: str = "") -> HTMLResponse:
    """Returns an HTML page that postMessages to the opener and closes itself."""
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
    window.opener.postMessage({payload}, "*");
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
) -> SocialConnection:
    conn = (
        db.query(SocialConnection)
        .filter_by(user_id=user_id, platform=platform)
        .first()
    )
    if conn:
        conn.platform_user_id = platform_user_id
        conn.platform_username = platform_username
        conn.access_token = access_token
        conn.refresh_token = refresh_token
        conn.scopes = scopes
        conn.connection_metadata = metadata
        conn.is_active = True
        conn.last_synced_at = datetime.now(timezone.utc)
    else:
        conn = SocialConnection(
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
            platform_username=platform_username,
            access_token=access_token,
            refresh_token=refresh_token,
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
    return [
        {
            "platform": c.platform,
            "username": c.platform_username,
            "connected_at": c.created_at,
            "last_synced": c.last_synced_at,
        }
        for c in conns
    ]


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
TWITTER_SCOPES = "tweet.read users.read offline.access"


def _pkce_pair():
    verifier = secrets.token_urlsafe(43)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


# In-memory PKCE verifier store (production: use Redis)
_pkce_store: dict[str, str] = {}


@router.get("/twitter/start")
async def twitter_start(
    token: str = Query(..., description="Ittera JWT — identifies the connecting user"),
    db: Session = Depends(get_db),
):
    """Open this in a popup. Redirects to Twitter OAuth."""
    if not settings.TWITTER_CLIENT_ID:
        return _popup_response("twitter", "error", error="Twitter OAuth is not configured.")

    user_id, err_reason = await _get_user_id_from_token(token)
    if not user_id:
        return _popup_response("twitter", "error", error=f"Invalid session token. Reason: {err_reason}")

    verifier, challenge = _pkce_pair()
    state = _make_connect_state(user_id, "twitter")
    _pkce_store[state] = verifier  # store verifier keyed by state

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
    verifier = _pkce_store.pop(state, None)
    if not verifier:
        return _popup_response("twitter", "error", error="PKCE verifier not found.")

    async with httpx.AsyncClient(timeout=15) as client:
        token_res = await client.post(
            TWITTER_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.TWITTER_REDIRECT_URI,
                "client_id": settings.TWITTER_CLIENT_ID,
                "code_verifier": verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_res.is_error:
            return _popup_response("twitter", "error", error="Token exchange failed.")

        tokens = token_res.json()
        access_token = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token")

        me_res = await client.get(
            f"{TWITTER_ME_URL}?user.fields=username,name,profile_image_url",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if me_res.is_error:
            return _popup_response("twitter", "error", error="Could not fetch Twitter profile.")

        me = me_res.json().get("data", {})

    _upsert_connection(
        db,
        user_id=user_id,
        platform="twitter",
        platform_user_id=me.get("id", ""),
        platform_username=me.get("username", ""),
        access_token=access_token,
        refresh_token=refresh_token,
        scopes=TWITTER_SCOPES.split(),
        metadata={"name": me.get("name", ""), "profile_image": me.get("profile_image_url", "")},
    )
    return _popup_response("twitter", "connected", username=me.get("username", ""))


# ─── LinkedIn OAuth 2.0 ───────────────────────────────────────────────────────

LINKEDIN_CONNECT_SCOPES = "openid profile email w_member_social"


@router.get("/linkedin/start")
async def linkedin_start(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    if not settings.LINKEDIN_CLIENT_ID:
        return _popup_response("linkedin", "error", error="LinkedIn OAuth is not configured.")

    user_id, err_reason = await _get_user_id_from_token(token)
    if not user_id:
        return _popup_response("linkedin", "error", error=f"Invalid session token. Reason: {err_reason}")

    state = _make_connect_state(user_id, "linkedin")
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
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    decoded = _decode_connect_state(state)
    if not decoded or decoded.get("platform") != "linkedin":
        return _popup_response("linkedin", "error", error="Invalid OAuth state.")

    user_id = decoded["sub"]

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
            return _popup_response("linkedin", "error", error="Token exchange failed.")

        tokens = token_res.json()
        access_token = tokens.get("access_token", "")

        profile_res = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_res.is_error:
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
        scopes=LINKEDIN_CONNECT_SCOPES.split(),
        metadata={"name": profile.get("name", ""), "picture": profile.get("picture", "")},
    )

    # ── Auto-trigger post sync immediately after OAuth completes ─────────────
    # This fires in the background (Celery) — the user sees "Connected" right away.
    try:
        from workers.celery.tasks.scraper import scrape_linkedin_posts
        scrape_linkedin_posts.delay(user_id)
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
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
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    if not settings.INSTAGRAM_APP_ID:
        return _popup_response("instagram", "error", error="Instagram OAuth is not configured.")

    user_id, err_reason = await _get_user_id_from_token(token)
    if not user_id:
        return _popup_response("instagram", "error", error=f"Invalid session token. Reason: {err_reason}")

    state = _make_connect_state(user_id, "instagram")
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
            return _popup_response("instagram", "error", error="Token exchange failed.")

        tokens = token_res.json()
        access_token = tokens.get("access_token", "")
        ig_user_id = str(tokens.get("user_id", ""))

        me_res = await client.get(
            f"{INSTAGRAM_ME_URL}?fields=id,username&access_token={access_token}"
        )
        if me_res.is_error:
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
