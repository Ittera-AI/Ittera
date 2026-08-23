"""
Auth dependency — supports two JWT issuers:

1. Supabase JWT (preferred): issued by the Supabase project when the user signs in
   via the frontend. Verified using the project JWT secret (HS256). The `sub`
   claim is the Supabase user UUID.

2. Legacy Iterra JWT: issued by this backend's /auth/login and /auth/register
   endpoints. Used for email/password flows that bypass Supabase.

Both paths resolve to a local `User` row. If the user doesn't exist locally yet
(e.g. first Supabase OAuth login), we create a minimal profile on the fly.
"""

import logging

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies.db import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

_SUPABASE_AUDIENCE = "authenticated"

# Bounded timeout (seconds) for the Supabase REST fallback validation call so a
# slow or unresponsive Supabase Auth endpoint cannot hang request handling (R1.5).
_SUPABASE_FALLBACK_TIMEOUT_SECONDS = 5.0


def _decode_supabase_jwt(token: str) -> dict | None:
    """Try to decode a Supabase-issued JWT. Returns payload or None."""
    secret = settings.SUPABASE_JWT_SECRET
    if not secret:
        return None
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=_SUPABASE_AUDIENCE,
            options={"verify_aud": True},
        )
    except JWTError:
        return None


def _decode_legacy_jwt(token: str) -> dict | None:
    """Try to decode a legacy Iterra-issued JWT. Returns payload or None."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def _is_email_verified(payload: dict) -> bool:
    """Return whether server-controlled Supabase claims verify the email.

    ``user_metadata`` is intentionally excluded: Supabase users can update that
    object themselves, so it cannot authorize first-time provisioning or link a
    Supabase identity to an existing local account. An explicit top-level
    ``email_verified`` value is authoritative; otherwise the REST user object's
    top-level ``email_confirmed_at`` timestamp is accepted. Missing, malformed,
    or contradictory claims fail closed.
    """

    def _truthy(value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes"}
        return False

    if "email_verified" in payload:
        return _truthy(payload.get("email_verified"))

    confirmed_at = payload.get("email_confirmed_at")
    return isinstance(confirmed_at, str) and bool(confirmed_at.strip())


def _get_or_create_user_from_supabase(db: Session, payload: dict) -> User:
    """
    Resolve (or create) a local User row from a decoded Supabase JWT payload.

    Supabase stores the user's UUID in `sub`, email in `email`, and display
    name in `user_metadata.full_name` or `user_metadata.name`.
    """
    supabase_id = payload.get("sub")
    email = (payload.get("email") or "").strip().lower()

    if not supabase_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase token missing sub or email claim",
        )

    if not _is_email_verified(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email is not verified",
        )

    # Resolve the immutable Supabase subject before considering email-based
    # linking. A subject already associated with a different local email is an
    # identity inconsistency and must fail closed rather than causing a duplicate
    # primary-key insert or silently changing account ownership.
    subject_user = db.query(User).filter(User.id == supabase_id).first()
    if subject_user is not None:
        if subject_user.email.strip().lower() != email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase identity does not match the local account",
            )
        return subject_user

    # A verified email may link a pre-existing legacy account. The current data
    # model has no separate external-identity table, so this compatibility path
    # intentionally preserves the existing local user identifier.
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user

    # First time we're seeing this Supabase user — create a local profile
    meta = payload.get("user_metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    name = (
        meta.get("full_name")
        or meta.get("name")
        or email.split("@")[0].replace(".", " ").capitalize()
    )
    import secrets as _secrets
    user = User(
        id=supabase_id,  # reuse Supabase UUID so they stay in sync
        email=email,
        hashed_password=_secrets.token_hex(32),  # unusable random — Supabase owns auth
        name=name,
        full_name=name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def _fetch_supabase_user(token: str) -> dict | None:
    """
    Fallback: call the Supabase REST API to validate an opaque or mismatched token.

    Returns a dict with at least {'sub': <uuid>} on success, or None on any
    failure so the caller responds with HTTP 401 (R1.5). Hardening applied:

    - A bounded request timeout (``_SUPABASE_FALLBACK_TIMEOUT_SECONDS``) is
      applied so a slow/unresponsive Supabase endpoint cannot hang request
      handling.
    - The returned identity is re-checked: the audience claim must equal
      ``authenticated`` and the email must be verified. An identity that is not
      verified is never trusted.
    - Errors and non-2xx responses are not swallowed silently — they are logged
      at the category level (no token or secret values) and result in ``None``.

    Requires SUPABASE_URL, a public Supabase key, and a valid Supabase access token.
    """
    import httpx

    url = (settings.SUPABASE_URL or settings.NEXT_PUBLIC_SUPABASE_URL or "").rstrip("/")
    api_key = settings.SUPABASE_ANON_KEY or settings.NEXT_PUBLIC_SUPABASE_ANON_KEY
    if not url or not api_key or not token:
        return None

    try:
        async with httpx.AsyncClient(
            timeout=_SUPABASE_FALLBACK_TIMEOUT_SECONDS
        ) as client:
            resp = await client.get(
                f"{url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": api_key,
                },
            )
    except httpx.HTTPError as exc:
        # Do not swallow silently: log the error category (never the token) and
        # fail closed so the caller returns 401.
        logger.warning(
            "Supabase REST fallback validation failed: %s", type(exc).__name__
        )
        return None

    # Any non-2xx result is treated as an unresolved identity (R1.5).
    if resp.is_error:
        logger.warning(
            "Supabase REST fallback returned non-success status %s", resp.status_code
        )
        return None

    try:
        data = resp.json()
    except ValueError:
        logger.warning("Supabase REST fallback returned a non-JSON body")
        return None

    if not isinstance(data, dict):
        logger.warning("Supabase REST fallback returned an unexpected payload shape")
        return None

    # Re-check the audience claim on the returned identity. The Supabase user
    # object carries `aud` ("authenticated" for a normally signed-in user). The
    # value may be a string or a list of audiences.
    aud = data.get("aud")
    aud_ok = (
        aud == _SUPABASE_AUDIENCE
        or (isinstance(aud, (list, tuple)) and _SUPABASE_AUDIENCE in aud)
    )
    if not aud_ok:
        logger.warning("Supabase REST fallback identity has unexpected audience")
        return None

    # Re-check verified status — never trust an unverified identity (R1.5).
    if not _is_email_verified(data):
        logger.warning("Supabase REST fallback identity is not email-verified")
        return None

    # Supabase returns { id, email, ... } — normalise to { sub, email }
    if "id" in data:
        data["sub"] = data["id"]
    return data


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias="ittera_token"),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials if credentials else cookie_token
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    # --- Try Supabase JWT first (local signature/audience verification) ---
    supabase_payload = _decode_supabase_jwt(token)
    if supabase_payload is not None:
        # Supabase access tokens commonly keep verification-looking fields in
        # user_metadata, which is user-editable and therefore not authoritative.
        # When the signed token lacks a trusted top-level claim, resolve the
        # same identity through Auth's /user endpoint before provisioning or
        # linking by email.
        if not _is_email_verified(supabase_payload):
            verified_payload = await _fetch_supabase_user(token)
            if verified_payload is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email is not verified",
                )

            local_subject = supabase_payload.get("sub")
            remote_subject = verified_payload.get("sub")
            local_email = (supabase_payload.get("email") or "").strip().lower()
            remote_email = (verified_payload.get("email") or "").strip().lower()
            if (
                not local_subject
                or local_subject != remote_subject
                or not local_email
                or local_email != remote_email
            ):
                logger.warning(
                    "Supabase local and REST identity assertions do not match"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Supabase identity verification failed",
                )
            supabase_payload = verified_payload

        return _get_or_create_user_from_supabase(db, supabase_payload)

    # --- Then the legacy Iterra JWT (also local, no network) ---
    # Verify any locally-verifiable token before making a network round-trip.
    # A legacy-signed token never validates as a Supabase JWT (different secret),
    # so resolving it here avoids a pointless Supabase REST call on every
    # email/password request — and keeps the path deterministic and offline.
    legacy_payload = _decode_legacy_jwt(token)
    if legacy_payload is not None:
        user_id: str = legacy_payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user

    # --- Last resort: Supabase Auth REST validation (network call) ---
    # Used only when the token is neither a locally-verifiable Supabase JWT nor a
    # legacy Iterra JWT (e.g. an opaque token, or a project using signing keys
    # this service cannot verify locally).
    supabase_payload = await _fetch_supabase_user(token)
    if supabase_payload is not None:
        return _get_or_create_user_from_supabase(db, supabase_payload)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
    )
