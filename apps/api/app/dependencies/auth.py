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

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies.db import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_SUPABASE_AUDIENCE = "authenticated"


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

    # Look up by email first (handles edge case where user already exists via
    # the legacy email/password flow with the same address)
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user

    # First time we're seeing this Supabase user — create a local profile
    meta = payload.get("user_metadata") or {}
    name = (
        meta.get("full_name")
        or meta.get("name")
        or email.split("@")[0].replace(".", " ").capitalize()
    )
    import uuid, secrets as _secrets  # noqa: E401
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
    Returns a dict with at least {'sub': <uuid>} on success, or None on failure.
    Requires SUPABASE_URL and the token to be a valid Supabase access token.
    """
    import httpx

    url = settings.SUPABASE_URL
    if not url or not token:
        return None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.SUPABASE_JWT_SECRET,  # anon key not needed here; JWT validates
                },
            )
            if resp.is_error:
                return None
            data = resp.json()
            # Supabase returns { id, email, ... } — normalise to { sub, email }
            if "id" in data:
                data["sub"] = data["id"]
            return data
    except Exception:
        return None


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

    # --- Try Supabase JWT first ---
    supabase_payload = _decode_supabase_jwt(token)
    if supabase_payload is not None:
        return _get_or_create_user_from_supabase(db, supabase_payload)

    # --- Fall back to legacy Iterra JWT ---
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

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
    )
