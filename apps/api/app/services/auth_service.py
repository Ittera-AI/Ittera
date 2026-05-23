import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest, OnboardingRequest, RegisterRequest

_pwd = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def make_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def make_oauth_state(purpose: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload = {
        "purpose": purpose,
        "nonce": secrets.token_urlsafe(16),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def frontend_callback_url(**params: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback?{urlencode(params)}"


def fallback_name(email: str) -> str:
    raw = email.split("@")[0].replace(".", " ").replace("_", " ").replace("-", " ")
    return " ".join(part.capitalize() for part in raw.split()) or "Ittera User"


def is_valid_oauth_state(state: str, purpose: str) -> bool:
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("purpose") == purpose
    except Exception:
        return False


def register(db: Session, payload: RegisterRequest) -> User:
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    name = payload.name.strip()
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        name=name,
        full_name=name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, payload: LoginRequest) -> tuple[User, str]:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return user, make_token(user.id)


def complete_onboarding(db: Session, user: User, payload: OnboardingRequest) -> User:
    if payload.full_name:
        user.full_name = payload.full_name.strip()
        user.name = user.full_name
    if payload.niche:
        user.niche = payload.niche.strip()
    user.goals = payload.goals.strip() if payload.goals else None
    user.primary_platform = payload.primary_platform
    user.storage_preference = payload.storage_preference
    user.onboarding_complete = True
    db.commit()
    db.refresh(user)
    return user


async def exchange_google_code(db: Session, code: str, state: str) -> RedirectResponse:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth is not configured")

    if not is_valid_oauth_state(state, "google_oauth"):
        return RedirectResponse(url=frontend_callback_url(error="Invalid or expired Google OAuth state."), status_code=302)

    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        if token_response.is_error:
            return RedirectResponse(url=frontend_callback_url(error="Google token exchange failed."), status_code=302)

        access_token = token_response.json().get("access_token")
        if not access_token:
            return RedirectResponse(url=frontend_callback_url(error="Google did not return an access token."), status_code=302)

        profile_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        if profile_response.is_error:
            return RedirectResponse(url=frontend_callback_url(error="Unable to fetch your Google profile."), status_code=302)

    profile = profile_response.json()
    email = (profile.get("email") or "").strip().lower()
    name = (profile.get("name") or "").strip()
    if not email or not profile.get("email_verified"):
        return RedirectResponse(url=frontend_callback_url(error="Your Google account must have a verified email."), status_code=302)

    user = _get_or_create_oauth_user(db, email=email, name=name)
    return RedirectResponse(url=frontend_callback_url(token=make_token(user.id)), status_code=302)


async def exchange_linkedin_code(db: Session, code: str, state: str) -> RedirectResponse:
    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_CLIENT_SECRET or not settings.LINKEDIN_REDIRECT_URI:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LinkedIn OAuth is not configured")

    if not is_valid_oauth_state(state, "linkedin_oauth"):
        return RedirectResponse(url=frontend_callback_url(error="Invalid or expired LinkedIn OAuth state."), status_code=302)

    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        if token_response.is_error:
            return RedirectResponse(url=frontend_callback_url(error="LinkedIn token exchange failed."), status_code=302)

        access_token = token_response.json().get("access_token")
        if not access_token:
            return RedirectResponse(url=frontend_callback_url(error="LinkedIn did not return an access token."), status_code=302)

        profile_response = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        if profile_response.is_error:
            return RedirectResponse(url=frontend_callback_url(error="Unable to fetch your LinkedIn profile."), status_code=302)

    profile = profile_response.json()
    email = (profile.get("email") or "").strip().lower()
    name = (profile.get("name") or "").strip()
    if not email:
        return RedirectResponse(url=frontend_callback_url(error="LinkedIn did not provide an email address for this account."), status_code=302)

    user = _get_or_create_oauth_user(db, email=email, name=name)
    return RedirectResponse(url=frontend_callback_url(token=make_token(user.id)), status_code=302)


def _get_or_create_oauth_user(db: Session, email: str, name: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user

    display_name = name or fallback_name(email)
    user = User(
        email=email,
        hashed_password=hash_password(uuid.uuid4().hex),
        name=display_name,
        full_name=display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
