from typing import Optional

from pydantic import BaseModel


class OAuthConnectResponse(BaseModel):
    authorization_url: str


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
