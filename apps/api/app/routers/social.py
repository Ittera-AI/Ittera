"""
Social connections router.
Routes: /api/v1/social/*
All logic delegated to social_service. Routers are thin HTTP handlers only.
"""

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from starlette.responses import RedirectResponse

from app.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.social import (
    AutoPostUpdateRequest,
    AutoPostUpdateResponse,
    LinkedInCredentialsRequest,
    OAuthConnectResponse,
    PlatformPreferencesResponse,
    PostingTimesUpdateRequest,
    PostingTimesUpdateResponse,
    SettingsPlatformStatus,
    SettingsPlatformsResponse,
    SocialStatusResponse,
    SyncResponse,
    SyncStatusResponse,
    TwitterTierUpdateRequest,
    TwitterTierUpdateResponse,
)
from app.services import social_service

if TYPE_CHECKING:
    from app.models.social_connection import SocialConnection

router = APIRouter()


# ── LinkedIn OAuth (connect for posting / publishing) ────────────────────────

@router.get("/connect/linkedin", response_model=OAuthConnectResponse)
async def connect_linkedin(current_user: User = Depends(get_current_user)):
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
async def connect_google_drive(current_user: User = Depends(get_current_user)):
    url = social_service.build_google_drive_oauth_url(user_id=str(current_user.id))
    return OAuthConnectResponse(authorization_url=url)


@router.get("/callback/google-drive")
async def google_drive_callback(
    code: str = Query(...),
    state: str = Query(...),  # user_id passed as state
    db: Session = Depends(get_db),
):
    await social_service.handle_google_drive_callback(db, code=code, user_id=state)
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/dashboard?drive=connected",
        status_code=302,
    )


# ── LinkedIn credentials (for scraper) ───────────────────────────────────────

@router.post("/credentials/linkedin")
async def store_linkedin_credentials(
    payload: LinkedInCredentialsRequest,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return social_service.get_connection_status(db, user_id=str(current_user.id))


# ── Sync (enqueue LinkedIn scrape) ───────────────────────────────────────────

@router.post("/sync", response_model=SyncResponse)
async def sync_linkedin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import linkedin_service

    task = linkedin_service.queue_scrape_task(str(current_user.id))
    return SyncResponse(task_id=task.id)


@router.get("/sync/status/{task_id}", response_model=SyncStatusResponse)
async def sync_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    from app.services import linkedin_service

    result = linkedin_service.get_scrape_task_result(task_id)
    return SyncStatusResponse(
        task_id=task_id,
        status=result.status,
        result=result.result if result.successful() else None,
        error=str(result.result) if result.failed() else None,
    )


# ── Twitter Sync (enqueue Twitter content sync) ──────────────────────────────

@router.post("/sync/twitter", response_model=SyncResponse)
async def sync_twitter(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger a manual Twitter content sync for the current user."""
    from app.services.twitter_service import queue_twitter_sync_task

    task = queue_twitter_sync_task(str(current_user.id))
    return SyncResponse(task_id=task.id)


@router.get("/sync/twitter/status/{task_id}", response_model=SyncStatusResponse)
async def twitter_sync_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Check the status of a Twitter sync task."""
    from app.services.twitter_service import get_twitter_sync_task_result

    result = get_twitter_sync_task_result(task_id)
    return SyncStatusResponse(
        task_id=task_id,
        status=result.status,
        result=result.result if result.successful() else None,
        error=str(result.result) if result.failed() else None,
    )


# ── Twitter Tier Management ──────────────────────────────────────────────────

@router.get("/platforms", response_model=SettingsPlatformsResponse)
async def get_all_platforms_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return detailed status for all connected platforms (settings page).

    Iterates through registered sync providers to get rich status (posting
    readiness, sync readiness, missing scopes, sync-in-progress indicator).
    Also includes platforms that have a connection but no sync provider
    (e.g., instagram, google_drive) with basic connection info.

    Requirements: 5.1, 5.2, 5.3
    """
    from app.models.social_connection import SocialConnection
    from app.routers.sync import _SYNC_PROVIDERS
    from app.services.content_sync_provider import PlatformStatus as ProviderStatus

    user_id = str(current_user.id)

    # Fetch all connections for the user (active and inactive)
    all_conns = (
        db.query(SocialConnection)
        .filter(SocialConnection.user_id == user_id)
        .all()
    )
    conn_by_platform: dict[str, SocialConnection] = {
        c.platform: c for c in all_conns
    }

    platforms: list[SettingsPlatformStatus] = []

    # 1. Platforms with sync providers get rich status via provider.get_status()
    for platform_name, provider in _SYNC_PROVIDERS.items():
        conn = conn_by_platform.pop(platform_name, None)

        if conn and conn.is_active:
            # Use the provider's get_status() for detailed info
            status: ProviderStatus = provider.get_status(db, current_user)
            sync_in_progress = status.sync_status in ("initiated", "in_progress")

            platforms.append(
                SettingsPlatformStatus(
                    platform=platform_name,
                    connected=status.connected,
                    platform_username=status.platform_username,
                    connected_at=conn.created_at,
                    last_synced_at=status.last_synced_at,
                    posting_ready=status.posting_ready,
                    read_sync_ready=status.read_sync_ready,
                    missing_scopes=status.missing_posting_scopes + status.missing_read_scopes,
                    missing_posting_scopes=status.missing_posting_scopes,
                    missing_read_scopes=status.missing_read_scopes,
                    sync_status=status.sync_status,
                    sync_error=status.sync_error,
                    sync_in_progress=sync_in_progress,
                    reconnect_required=status.reconnect_required,
                    can_disconnect=True,
                    can_reconnect=True,
                    can_sync=status.connected and not sync_in_progress,
                )
            )
        else:
            # Provider exists but user has no active connection
            platforms.append(
                SettingsPlatformStatus(
                    platform=platform_name,
                    connected=False,
                    platform_username=None,
                    connected_at=conn.created_at if conn else None,
                    can_disconnect=False,
                    can_reconnect=True,
                    can_sync=False,
                )
            )

    # 2. Remaining connections not in the provider registry (instagram, google_drive, etc.)
    for platform_name, conn in conn_by_platform.items():
        platforms.append(
            SettingsPlatformStatus(
                platform=platform_name,
                connected=conn.is_active,
                platform_username=conn.platform_username,
                connected_at=conn.created_at,
                last_synced_at=conn.last_synced_at,
                posting_ready=False,  # No provider = no posting support yet
                read_sync_ready=False,
                can_disconnect=True,
                can_reconnect=True,
                can_sync=False,  # No sync provider registered
            )
        )

    return SettingsPlatformsResponse(platforms=platforms)


@router.post("/platforms/{platform}/disconnect")
async def disconnect_platform(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect a platform (deactivate the connection).

    The connection record is retained but marked inactive.
    User can reconnect via the OAuth flow.
    Requirements: 5.3
    """
    from app.models.social_connection import SocialConnection

    conn = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == str(current_user.id),
            SocialConnection.platform == platform,
        )
        .first()
    )
    if not conn:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"No connection found for platform '{platform}'.")

    conn.is_active = False
    db.commit()
    return {"platform": platform, "disconnected": True, "message": f"{platform} disconnected successfully"}


@router.post("/platforms/{platform}/reconnect")
async def reconnect_platform(
    platform: str,
    current_user: User = Depends(get_current_user),
):
    """Return the OAuth URL to reconnect a platform.

    The frontend should open this URL in a popup to re-authorize.
    Requirements: 5.3
    """
    # Map platform to its OAuth start path
    oauth_paths = {
        "twitter": "/api/v1/connect/twitter/start",
        "linkedin": "/api/v1/connect/linkedin/start",
        "instagram": "/api/v1/connect/instagram/start",
    }
    path = oauth_paths.get(platform)
    if not path:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Reconnect not supported for platform '{platform}'.",
        )

    return {
        "platform": platform,
        "reconnect_url": path,
        "message": f"Open the reconnect_url in a popup to re-authorize {platform}",
    }


@router.put("/twitter/tier", response_model=TwitterTierUpdateResponse)
async def update_twitter_tier_endpoint(
    payload: TwitterTierUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the user's Twitter subscription tier (free or premium).

    This affects character limits applied to subsequent content generation:
    - free: 280 chars per tweet (thread splitting enabled)
    - premium: 25,000 chars per post
    """
    from app.services.platform_limits import (
        PLATFORM_CHAR_LIMITS,
        TwitterTier,
        update_twitter_tier,
    )

    tier = TwitterTier(payload.tier)
    update_twitter_tier(db, str(current_user.id), tier)

    max_chars = PLATFORM_CHAR_LIMITS["twitter"][tier]
    return TwitterTierUpdateResponse(
        tier=tier,
        max_chars=max_chars,
        is_thread_eligible=(tier == TwitterTier.FREE),
    )


@router.get("/twitter/tier")
async def get_twitter_tier_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the user's current Twitter subscription tier and associated limits."""
    from app.services.platform_limits import resolve_content_limit

    content_limit = resolve_content_limit(db, str(current_user.id), "twitter")
    return {
        "tier": content_limit.tier,
        "max_chars": content_limit.max_chars,
        "is_thread_eligible": content_limit.is_thread_eligible,
    }


# ── Auto-Post Toggle Per Platform ────────────────────────────────────────────


@router.put("/{platform}/auto-post", response_model=AutoPostUpdateResponse)
async def update_auto_post(
    platform: str,
    payload: AutoPostUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle auto-post on/off for a specific platform.

    Stores the preference in connection_metadata on the SocialConnection row.
    Uses flag_modified to ensure SQLAlchemy detects JSON column mutation.
    Requirements: 5.6
    """
    conn = _get_platform_connection(db, str(current_user.id), platform)
    metadata = dict(conn.connection_metadata or {})
    metadata["auto_post_enabled"] = payload.enabled
    conn.connection_metadata = metadata
    flag_modified(conn, "connection_metadata")
    db.commit()
    db.refresh(conn)

    return AutoPostUpdateResponse(
        platform=platform,
        auto_post_enabled=payload.enabled,
    )


@router.get("/{platform}/auto-post", response_model=AutoPostUpdateResponse)
async def get_auto_post(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current auto-post preference for a platform."""
    conn = _get_platform_connection(db, str(current_user.id), platform)
    metadata = conn.connection_metadata or {}
    enabled = metadata.get("auto_post_enabled", False)

    return AutoPostUpdateResponse(
        platform=platform,
        auto_post_enabled=enabled,
        message="Current auto-post preference",
    )


# ── Preferred Posting Times Per Platform ─────────────────────────────────────


@router.put("/{platform}/posting-times", response_model=PostingTimesUpdateResponse)
async def update_posting_times(
    platform: str,
    payload: PostingTimesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set preferred posting times for a specific platform.

    Times should be in HH:MM (24-hour) format.
    Stores the preference in connection_metadata on the SocialConnection row.
    Uses flag_modified to ensure SQLAlchemy detects JSON column mutation.
    Requirements: 5.7
    """
    conn = _get_platform_connection(db, str(current_user.id), platform)
    metadata = dict(conn.connection_metadata or {})
    metadata["preferred_posting_times"] = payload.times
    conn.connection_metadata = metadata
    flag_modified(conn, "connection_metadata")
    db.commit()
    db.refresh(conn)

    return PostingTimesUpdateResponse(
        platform=platform,
        preferred_posting_times=payload.times,
    )


@router.get("/{platform}/posting-times", response_model=PostingTimesUpdateResponse)
async def get_posting_times(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current preferred posting times for a platform."""
    conn = _get_platform_connection(db, str(current_user.id), platform)
    metadata = conn.connection_metadata or {}
    times = metadata.get("preferred_posting_times", [])

    return PostingTimesUpdateResponse(
        platform=platform,
        preferred_posting_times=times,
        message="Current posting times",
    )


# ── Combined Platform Preferences ────────────────────────────────────────────


@router.get("/{platform}/preferences", response_model=PlatformPreferencesResponse)
async def get_platform_preferences(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all publishing preferences for a platform (auto-post + posting times)."""
    conn = _get_platform_connection(db, str(current_user.id), platform)
    metadata = conn.connection_metadata or {}

    return PlatformPreferencesResponse(
        platform=platform,
        auto_post_enabled=metadata.get("auto_post_enabled", False),
        preferred_posting_times=metadata.get("preferred_posting_times", []),
    )


# ── Internal helpers ─────────────────────────────────────────────────────────


def _get_platform_connection(
    db: Session, user_id: str, platform: str
) -> "SocialConnection":
    """Retrieve the active SocialConnection for a user+platform, or raise 404."""
    from app.models.social_connection import SocialConnection

    conn = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user_id,
            SocialConnection.platform == platform,
            SocialConnection.is_active.is_(True),
        )
        .first()
    )
    if conn is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active connection found for platform '{platform}'. Please connect your {platform} account first.",
        )
    return conn
