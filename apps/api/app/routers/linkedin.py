"""
LinkedIn API router.

Endpoints:
  GET  /status          — connection status + post count
  POST /connect/mock    — dev-only mock connection
  POST /sync            — legacy mock sync (dev/testing)
  POST /sync/real       — trigger real sync (OAuth API or cookie fallback)
  POST /sync/trigger    — enqueue real sync as a background Celery task
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.linkedin import LinkedInConnectResponse, LinkedInRealSyncResponse, LinkedInStatusResponse, LinkedInSyncResponse
from app.services import linkedin_service

router = APIRouter()


# ── Status ─────────────────────────────────────────────────────────────────────

@router.get("/status", response_model=LinkedInStatusResponse)
async def status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return connection status and current post count."""
    try:
        return linkedin_service.get_status(db, current_user)
    except (OperationalError, ProgrammingError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database schema is out of date. Run `alembic upgrade head` in apps/api.",
        ) from exc


# ── Dev mock connection ─────────────────────────────────────────────────────────

@router.post("/connect/mock", response_model=LinkedInConnectResponse)
async def connect_mock(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a mock LinkedIn connection (development only)."""
    return linkedin_service.connect_mock(db, current_user)


# ── Sync endpoints ─────────────────────────────────────────────────────────────

@router.post("/sync", response_model=LinkedInSyncResponse)
async def sync_mock(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Legacy mock sync — inserts deterministic fake posts.
    Kept for dev/testing. Use /sync/real for production.
    """
    from app.services.linkedin_service import _sync_mock_posts_fallback
    return _sync_mock_posts_fallback(db, current_user)


@router.post("/sync/real", response_model=LinkedInRealSyncResponse)
async def sync_real(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Synchronously fetches real LinkedIn posts (OAuth API or cookie fallback).
    Blocks until sync completes. Use /sync/trigger for non-blocking background sync.
    """
    try:
        result = await linkedin_service.sync_real_posts(db, current_user)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LinkedIn sync failed: {exc}",
        ) from exc


@router.post("/sync/trigger")
async def sync_trigger(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enqueues a background Celery task to sync real LinkedIn posts.
    Returns immediately. Check task status via Celery or /status.
    """
    try:
        from workers.celery.tasks.scraper import scrape_linkedin_posts
        task = scrape_linkedin_posts.delay(str(current_user.id))
        return {
            "queued": True,
            "task_id": task.id,
            "message": "LinkedIn sync queued. Posts will appear shortly.",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not enqueue sync task (Celery may not be running): {exc}",
        ) from exc
