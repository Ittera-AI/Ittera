from datetime import datetime

from pydantic import BaseModel


class LinkedInStatusResponse(BaseModel):
    connected: bool
    platform_username: str | None = None
    last_synced_at: datetime | None = None
    synced_posts: int = 0
    scopes: list[str] = []
    posting_ready: bool = False
    read_sync_ready: bool = False
    missing_posting_scopes: list[str] = []
    missing_read_scopes: list[str] = []
    reconnect_required: bool = False
    message: str | None = None


class LinkedInConnectResponse(BaseModel):
    connected: bool
    platform_username: str
    message: str


class LinkedInSyncResponse(BaseModel):
    """Legacy mock sync response — used by POST /sync."""
    synced_posts: int
    last_synced_at: datetime
    message: str


class LinkedInRealSyncResponse(BaseModel):
    """Response from POST /sync/real — includes path info and analysis readiness."""
    synced_posts: int
    total_posts: int
    last_synced_at: datetime
    message: str
    sync_path: str  # "oauth_api" | "cookie_auth" | "unavailable" | "mock"
    ready_for_analysis: bool
