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
import httpx
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies.db import get_db
from app.models.user import User
from app.models.waitlist import WaitlistEntry

bearer_scheme = HTTPBearer(auto_error=False)

_SUPABASE_AUDIENCE = "authenticated"
_PLACEHOLDER_SUPABASE_SECRETS = {
    "",
    "your-supabase-jwt-secret",
    "placeholder",
    "placeholder-jwt-secret",
}


def _normalized_admin_emails() -> set[str]:
    return {email.strip().lower() for email in settings.ADMIN_EMAILS if email.strip()}


def is_admin_email(email: str) -> bool:
    return email.strip().lower() in _normalized_admin_emails()


def get_waitlist_access(db: Session, user: User) -> dict:
    email = user.email.strip().lower()
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.email == email).first()
    is_admin = is_admin_email(email)
    access_approved = bool(entry and entry.access_approved)
    has_access = is_admin or access_approved
    reason = None
    if not has_access:
        reason = "pending_approval" if entry else "not_waitlisted"

    return {
        "email": email,
        "has_access": has_access,
        "waitlisted": entry is not None,
        "access_approved": access_approved,
        "is_admin": is_admin,
        "approved_at": entry.approved_at.isoformat() if entry and entry.approved_at else None,
        "reason": reason,
    }


def _has_supabase_jwt_secret() -> bool:
    return settings.SUPABASE_JWT_SECRET.strip() not in _PLACEHOLDER_SUPABASE_SECRETS


def _decode_supabase_jwt(token: str) -> dict | None:
    """Try to decode a Supabase-issued JWT. Returns payload or None."""
    if not _has_supabase_jwt_secret():
        return None
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=_SUPABASE_AUDIENCE,
            options={"verify_aud": True},
        )
    except JWTError:
        return None


async def _fetch_supabase_user(token: str) -> dict | None:
    """
    Validate a Supabase access token via Supabase Auth when local JWT verification
    is unavailable. This keeps local/dev deployments working when only the public
    Supabase URL + anon key are configured.
    """
    if not settings.SUPABASE_URL or not settings.NEXT_PUBLIC_SUPABASE_ANON_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
                headers={
                    "apikey": settings.NEXT_PUBLIC_SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
    except httpx.HTTPError:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    return {
        "sub": data.get("id"),
        "email": data.get("email"),
        "user_metadata": data.get("user_metadata") or {},
    }


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
    import secrets as _secrets  # noqa: E401
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

    # --- Last resort: validate Supabase token via Auth API when JWT secret is unavailable ---
    supabase_payload = await _fetch_supabase_user(token)
    if supabase_payload is not None:
        return _get_or_create_user_from_supabase(db, supabase_payload)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
    )


async def get_current_workspace_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    access = get_waitlist_access(db, current_user)
    if not access["has_access"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is waiting for workspace access approval.",
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not is_admin_email(current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
