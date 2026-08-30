import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class OAuthConnectResponse(BaseModel):
    authorization_url: str


class ConnectSessionResponseV1(BaseModel):
    """Versioned one-time OAuth connect-token contract.

    Contract owner: Developer A. Primary consumer: Developer B web OAuth flow.
    """

    schema_version: Literal["connect-session.v1"] = "connect-session.v1"
    connect_token: str


class LinkedInCredentialsRequest(BaseModel):
    username: str  # LinkedIn email or username
    password: str


class SyncResponse(BaseModel):
    task_id: str
    message: str = "Sync enqueued"


class SyncStatusResponse(BaseModel):
    task_id: str
    status: str  # "PENDING" | "STARTED" | "SUCCESS" | "FAILURE"
    result: Optional[dict] = None
    error: Optional[str] = None


class PlatformStatus(BaseModel):
    platform: str
    connected: bool
    username: Optional[str] = None
    last_synced_at: Optional[str] = None
    metadata_summary: Optional[dict] = None


class SocialStatusResponse(BaseModel):
    connections: list[PlatformStatus]


class TwitterTierUpdateRequest(BaseModel):
    tier: Literal["free", "premium"]


class TwitterTierUpdateResponse(BaseModel):
    tier: str
    max_chars: int
    is_thread_eligible: bool = False
    message: str = "Twitter tier updated successfully"


# ── Auto-Post Toggle ─────────────────────────────────────────────────────────


class AutoPostUpdateRequest(BaseModel):
    """Request body for toggling auto-post on/off for a platform."""

    enabled: bool


class AutoPostUpdateResponse(BaseModel):
    """Response after updating auto-post preference."""

    platform: str
    auto_post_enabled: bool
    message: str = "Auto-post preference updated"


# ── Preferred Posting Times ──────────────────────────────────────────────────

# HH:MM format pattern
_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class PostingTimesUpdateRequest(BaseModel):
    """Request body for setting preferred posting times per platform.

    Times should be in HH:MM (24-hour) format, e.g. ["09:00", "14:00", "18:00"].
    """

    times: list[str]

    @field_validator("times")
    @classmethod
    def validate_time_format(cls, v: list[str]) -> list[str]:
        for t in v:
            if not _TIME_PATTERN.match(t):
                raise ValueError(
                    f"Invalid time format '{t}'. Expected HH:MM in 24-hour format (e.g. '09:00', '14:30')."
                )
        return v


class PostingTimesUpdateResponse(BaseModel):
    """Response after updating preferred posting times."""

    platform: str
    preferred_posting_times: list[str]
    message: str = "Posting times updated"


# ── Platform Preferences (combined GET response) ─────────────────────────────


class PlatformPreferencesResponse(BaseModel):
    """Combined response for a platform's publishing preferences."""

    platform: str
    auto_post_enabled: bool
    preferred_posting_times: list[str]


# ── Settings Platforms Endpoint Schemas (Requirement 5.1, 5.2, 5.3) ──────────

class SettingsPlatformStatus(BaseModel):
    """Rich per-platform status for the settings page.

    Includes connection info, sync state, readiness flags, and missing scopes.
    """

    platform: str
    connected: bool
    platform_username: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    posting_ready: bool = False
    read_sync_ready: bool = False
    missing_scopes: list[str] = []
    missing_posting_scopes: list[str] = []
    missing_read_scopes: list[str] = []
    sync_status: Optional[str] = None  # "initiated", "in_progress", "completed", "failed"
    sync_error: Optional[str] = None
    sync_in_progress: bool = False
    reconnect_required: bool = False
    # Actions available
    can_disconnect: bool = True
    can_reconnect: bool = True
    can_sync: bool = False


class SettingsPlatformsResponse(BaseModel):
    """Response for GET /platforms — all connected platform statuses."""

    platforms: list[SettingsPlatformStatus]
