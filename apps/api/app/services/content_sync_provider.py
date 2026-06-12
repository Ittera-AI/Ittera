"""
ContentSyncProvider — Protocol defining the common interface for all platform content sync services.

This module formalizes the provider pattern used by LinkedIn and Twitter sync services.
Each platform implements this Protocol to enable consistent sync operations, status reporting,
and post mapping across the system.

Design principle: Python Protocol (structural typing) keeps services decoupled and testable
without requiring inheritance from an abstract base class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from sqlalchemy.orm import Session

from app.models.user import User


@dataclass
class SyncResult:
    """Metadata returned by all provider sync operations."""

    synced_posts: int
    total_posts: int
    last_synced_at: datetime
    message: str
    ready_for_analysis: bool
    sync_path: str  # "oauth_api", "cookie_auth", "mock", "unavailable"


@dataclass
class PlatformStatus:
    """Connection and sync status returned by get_status()."""

    connected: bool
    platform_username: str | None
    last_synced_at: datetime | None
    synced_posts: int
    scopes: list[str] = field(default_factory=list)
    posting_ready: bool = False
    read_sync_ready: bool = False
    missing_posting_scopes: list[str] = field(default_factory=list)
    missing_read_scopes: list[str] = field(default_factory=list)
    reconnect_required: bool = False
    message: str | None = None
    # Sync progress tracking (requirement 1.8)
    sync_status: str | None = None  # "initiated", "in_progress", "completed", "failed"
    sync_error: str | None = None  # Error message when sync_status == "failed"
    sync_started_at: datetime | None = None


@runtime_checkable
class ContentSyncProvider(Protocol):
    """Common interface for all platform content sync services."""

    platform: str  # "linkedin", "twitter", "instagram"

    async def sync_posts(self, db: Session, user: User) -> SyncResult:
        """Fetch and upsert posts. Returns sync metadata."""
        ...

    def get_status(self, db: Session, user: User) -> PlatformStatus:
        """Return connection status, scope info, readiness flags."""
        ...

    def map_post(self, raw: dict) -> dict | None:
        """Map platform-specific API response to Post model fields."""
        ...
