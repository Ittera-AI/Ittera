from datetime import datetime

from pydantic import BaseModel


class LinkedInStatusResponse(BaseModel):
    connected: bool
    platform_username: str | None = None
    last_synced_at: datetime | None = None
    synced_posts: int = 0


class LinkedInConnectResponse(BaseModel):
    connected: bool
    platform_username: str
    message: str


class LinkedInSyncResponse(BaseModel):
    synced_posts: int
    last_synced_at: datetime
    message: str
