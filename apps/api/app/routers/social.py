"""
Social connections router.
Routes: /api/v1/social/*
All logic delegated to social_service. Routers are thin HTTP handlers only.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.config import settings
from app.dependencies.auth import get_current_workspace_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.social import (
    LinkedInCredentialsRequest,
    OAuthConnectResponse,
    SocialStatusResponse,
    SyncResponse,
    SyncStatusResponse,
)
from app.services import social_service

router = APIRouter()


# ── LinkedIn OAuth (connect for posting / publishing) ────────────────────────

@router.get("/connect/linkedin", response_model=OAuthConnectResponse)
async def connect_linkedin(current_user: User = Depends(get_current_workspace_user)):
    url = social_service.build_linkedin_oauth_url()
    return OAuthConnectResponse(authorization_url=url)


@router.get("/callback/linkedin")
async def linkedin_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    from app.services.auth_service import exchange_linkedin_code
    return await exchange_linkedin_code(db, code, state)


# ── Google Drive OAuth ───────────────────────────────────────────────────────

@router.get("/connect/google-drive", response_model=OAuthConnectResponse)
async def connect_google_drive(current_user: User = Depends(get_current_workspace_user)):
    url = social_service.build_google_drive_oauth_url(user_id=str(current_user.id))
    return OAuthConnectResponse(authorization_url=url)


@router.get("/callback/google-drive")
async def google_drive_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    await social_service.handle_google_drive_callback(db, code=code, state=state)
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/dashboard?drive=connected",
        status_code=302,
    )


# ── LinkedIn credentials (for scraper) ───────────────────────────────────────

@router.post("/credentials/linkedin")
async def store_linkedin_credentials(
    payload: LinkedInCredentialsRequest,
    current_user: User = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    await social_service.store_linkedin_credentials(
        db,
        user_id=str(current_user.id),
        username=payload.username,
        password=payload.password,
    )
    return {"message": "LinkedIn credentials stored successfully"}


# ── Status ───────────────────────────────────────────────────────────────────

@router.get("/status", response_model=SocialStatusResponse)
async def get_social_status(
    current_user: User = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    return social_service.get_connection_status(db, user_id=str(current_user.id))


# ── Sync (enqueue LinkedIn scrape) ───────────────────────────────────────────

@router.post("/sync", response_model=SyncResponse)
async def sync_linkedin(
    current_user: User = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    from workers.celery.tasks.scraper import scrape_linkedin_posts

    task = scrape_linkedin_posts.delay(str(current_user.id))
    return SyncResponse(task_id=task.id)


@router.get("/sync/status/{task_id}", response_model=SyncStatusResponse)
async def sync_status(
    task_id: str,
    current_user: User = Depends(get_current_workspace_user),
):
    from workers.celery.app import celery_app
    result = celery_app.AsyncResult(task_id)
    return SyncStatusResponse(
        task_id=task_id,
        status=result.status,
        result=result.result if result.successful() else None,
        error=str(result.result) if result.failed() else None,
    )
