"""
Generic sync router.
Routes: /api/v1/sync/{platform} and /api/v1/sync/{platform}/status

Provides platform-agnostic endpoints for triggering content sync and
querying platform status. Routes to the correct provider service via
a registry dict keyed by platform name.

Requirements: 5.4, 5.5, 7.1, 7.5
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.services.content_sync_provider import ContentSyncProvider, PlatformStatus
from app.services.linkedin_service import linkedin_sync_service, queue_scrape_task
from app.services.twitter_service import twitter_sync_service, queue_twitter_sync_task

router = APIRouter()


# ── Provider Registry ─────────────────────────────────────────────────────────
# Maps platform name to its ContentSyncProvider implementation and Celery task queuer.

_SYNC_PROVIDERS: dict[str, ContentSyncProvider] = {
    "linkedin": linkedin_sync_service,
    "twitter": twitter_sync_service,
}

# Maps platform name to a callable that queues the Celery sync task.
# Each callable accepts (user_id: str) and returns a Celery AsyncResult.
_SYNC_TASK_QUEUERS: dict[str, Any] = {
    "linkedin": queue_scrape_task,
    "twitter": queue_twitter_sync_task,
}


# ── Response Schemas ──────────────────────────────────────────────────────────


class SyncTriggerResponse(BaseModel):
    """Response after triggering a platform sync."""

    task_id: str
    platform: str
    message: str = "Sync enqueued"


class PlatformStatusResponse(BaseModel):
    """Full platform status response matching PlatformStatus dataclass."""

    platform: str
    connected: bool
    platform_username: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    synced_posts: int = 0
    scopes: list[str] = []
    posting_ready: bool = False
    read_sync_ready: bool = False
    missing_posting_scopes: list[str] = []
    missing_read_scopes: list[str] = []
    reconnect_required: bool = False
    message: Optional[str] = None
    sync_status: Optional[str] = None
    sync_error: Optional[str] = None
    sync_started_at: Optional[datetime] = None


# ── Helper ────────────────────────────────────────────────────────────────────


def _get_provider(platform: str) -> ContentSyncProvider:
    """Retrieve the provider for a given platform name, or raise 404."""
    provider = _SYNC_PROVIDERS.get(platform)
    if provider is None:
        supported = ", ".join(sorted(_SYNC_PROVIDERS.keys()))
        raise HTTPException(
            status_code=404,
            detail=f"Platform '{platform}' is not supported. Supported platforms: {supported}",
        )
    return provider


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/all", response_model=list[PlatformStatusResponse])
async def get_all_platforms_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the sync/connection status for ALL registered platforms in one call.

    Iterates over _SYNC_PROVIDERS registry and calls provider.get_status()
    for each platform. Returns a list of PlatformStatusResponse objects
    including per-platform: username, connection date, last sync time,
    posting readiness, sync readiness, missing scopes, sync-in-progress
    indicator, and error states.

    Requirements: 5.1, 5.2, 5.3
    """
    results: list[PlatformStatusResponse] = []

    for platform_name, provider in _SYNC_PROVIDERS.items():
        status: PlatformStatus = provider.get_status(db, current_user)
        results.append(
            PlatformStatusResponse(
                platform=platform_name,
                connected=status.connected,
                platform_username=status.platform_username,
                last_synced_at=status.last_synced_at,
                synced_posts=status.synced_posts,
                scopes=status.scopes,
                posting_ready=status.posting_ready,
                read_sync_ready=status.read_sync_ready,
                missing_posting_scopes=status.missing_posting_scopes,
                missing_read_scopes=status.missing_read_scopes,
                reconnect_required=status.reconnect_required,
                message=status.message,
                sync_status=status.sync_status,
                sync_error=status.sync_error,
                sync_started_at=status.sync_started_at,
            )
        )

    return results


@router.post("/{platform}", response_model=SyncTriggerResponse)
async def trigger_sync(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger a manual content sync for the specified platform.

    Validates the platform exists in the registry, then queues the
    appropriate Celery sync task. Returns the task ID for status polling.
    """
    # Validate platform exists
    _get_provider(platform)

    # Get the task queuer for this platform
    queuer = _SYNC_TASK_QUEUERS.get(platform)
    if queuer is None:
        raise HTTPException(
            status_code=501,
            detail=f"Sync task queuing is not configured for platform '{platform}'.",
        )

    task = queuer(str(current_user.id))
    return SyncTriggerResponse(
        task_id=task.id,
        platform=platform,
        message=f"{platform.capitalize()} sync enqueued",
    )


@router.get("/{platform}/status", response_model=PlatformStatusResponse)
async def get_platform_status(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the current sync/connection status for a platform.

    Retrieves the provider from the registry and calls get_status()
    to return comprehensive PlatformStatus information.
    """
    provider = _get_provider(platform)
    status: PlatformStatus = provider.get_status(db, current_user)

    return PlatformStatusResponse(
        platform=platform,
        connected=status.connected,
        platform_username=status.platform_username,
        last_synced_at=status.last_synced_at,
        synced_posts=status.synced_posts,
        scopes=status.scopes,
        posting_ready=status.posting_ready,
        read_sync_ready=status.read_sync_ready,
        missing_posting_scopes=status.missing_posting_scopes,
        missing_read_scopes=status.missing_read_scopes,
        reconnect_required=status.reconnect_required,
        message=status.message,
        sync_status=status.sync_status,
        sync_error=status.sync_error,
        sync_started_at=status.sync_started_at,
    )
