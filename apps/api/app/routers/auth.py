import secrets
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse

router = APIRouter()

_pwd = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return _pwd.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def _make_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _make_google_state() -> str:
    return _make_oauth_state("google_oauth")


def _make_oauth_state(purpose: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=10)
    payload = {
        "purpose": purpose,
        "nonce": secrets.token_urlsafe(16),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _frontend_callback_url(**params: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback?{urlencode(params)}"


def _fallback_name(email: str) -> str:
    raw = email.split("@")[0].replace(".", " ").replace("_", " ").replace("-", " ")
    return " ".join(part.capitalize() for part in raw.split()) or "Ittera User"


def _is_valid_oauth_state(state: str, purpose: str) -> bool:
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("purpose") == purpose
    except Exception:
        return False


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=payload.email.lower(),
        hashed_password=_hash_password(payload.password),
        name=payload.name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not _verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return {"access_token": _make_token(user.id), "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/google/start")
async def google_start():
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth is not configured")

    query = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": _make_google_state(),
        }
    )
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}", status_code=status.HTTP_302_FOUND)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth is not configured")

    if not _is_valid_oauth_state(state, "google_oauth"):
        return RedirectResponse(
            url=_frontend_callback_url(error="Invalid or expired Google OAuth state."),
            status_code=status.HTTP_302_FOUND,
        )

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
            return RedirectResponse(
                url=_frontend_callback_url(error="Google token exchange failed."),
                status_code=status.HTTP_302_FOUND,
            )

        access_token = token_response.json().get("access_token")
        if not access_token:
            return RedirectResponse(
                url=_frontend_callback_url(error="Google did not return an access token."),
                status_code=status.HTTP_302_FOUND,
            )

        profile_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )

        if profile_response.is_error:
            return RedirectResponse(
                url=_frontend_callback_url(error="Unable to fetch your Google profile."),
                status_code=status.HTTP_302_FOUND,
            )

    profile = profile_response.json()
    email = (profile.get("email") or "").strip().lower()
    name = (profile.get("name") or "").strip()

    if not email or not profile.get("email_verified"):
        return RedirectResponse(
            url=_frontend_callback_url(error="Your Google account must have a verified email."),
            status_code=status.HTTP_302_FOUND,
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            hashed_password=_hash_password(uuid.uuid4().hex),
            name=name or _fallback_name(email),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    app_token = _make_token(user.id)
    return RedirectResponse(
        url=_frontend_callback_url(token=app_token),
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/linkedin/start")
async def linkedin_start():
    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_REDIRECT_URI:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LinkedIn OAuth is not configured")

    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "state": _make_oauth_state("linkedin_oauth"),
            "scope": "openid profile email",
        }
    )
    return RedirectResponse(
        url=f"https://www.linkedin.com/oauth/v2/authorization?{query}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_CLIENT_SECRET or not settings.LINKEDIN_REDIRECT_URI:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LinkedIn OAuth is not configured")

    if not _is_valid_oauth_state(state, "linkedin_oauth"):
        return RedirectResponse(
            url=_frontend_callback_url(error="Invalid or expired LinkedIn OAuth state."),
            status_code=status.HTTP_302_FOUND,
        )

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
            return RedirectResponse(
                url=_frontend_callback_url(error="LinkedIn token exchange failed."),
                status_code=status.HTTP_302_FOUND,
            )

        access_token = token_response.json().get("access_token")
        if not access_token:
            return RedirectResponse(
                url=_frontend_callback_url(error="LinkedIn did not return an access token."),
                status_code=status.HTTP_302_FOUND,
            )

        profile_response = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )

        if profile_response.is_error:
            return RedirectResponse(
                url=_frontend_callback_url(error="Unable to fetch your LinkedIn profile."),
                status_code=status.HTTP_302_FOUND,
            )

    profile = profile_response.json()
    email = (profile.get("email") or "").strip().lower()
    name = (profile.get("name") or "").strip()

    if not email:
        return RedirectResponse(
            url=_frontend_callback_url(error="LinkedIn did not provide an email address for this account."),
            status_code=status.HTTP_302_FOUND,
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            hashed_password=_hash_password(uuid.uuid4().hex),
            name=name or _fallback_name(email),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    app_token = _make_token(user.id)
    return RedirectResponse(
        url=_frontend_callback_url(token=app_token),
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/logout")
async def logout():
    return {"message": "Logged out"}
