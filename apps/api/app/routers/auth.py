from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, OnboardingRequest, RegisterRequest, UserResponse
from app.services import auth_service

router = APIRouter()

AUTH_COOKIE = "ittera_token"


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        AUTH_COOKIE,
        token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register(db, payload)


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user, token = auth_service.login(db, payload)
    _set_auth_cookie(response, token)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return auth_service.complete_onboarding(db, current_user, payload)


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
            "state": auth_service.make_oauth_state("google_oauth"),
        }
    )
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}", status_code=status.HTTP_302_FOUND)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    return await auth_service.exchange_google_code(db, code, state)


@router.get("/linkedin/start")
async def linkedin_start():
    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_REDIRECT_URI:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LinkedIn OAuth is not configured")

    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "state": auth_service.make_oauth_state("linkedin_oauth"),
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
    return await auth_service.exchange_linkedin_code(db, code, state)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE, path="/")
    return {"message": "Logged out"}
