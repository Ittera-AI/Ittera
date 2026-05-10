"""Timezone-aware UTC for SQLAlchemy defaults and services."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
