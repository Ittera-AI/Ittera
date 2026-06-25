"""Timezone-aware UTC for SQLAlchemy defaults and services."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware(dt: datetime | None) -> datetime | None:
    """Normalize a datetime to timezone-aware UTC.

    Naive ``DateTime`` columns lose tzinfo when round-tripped through
    Postgres, so any Python-level arithmetic that mixes a stored value with a
    tz-aware ``utc_now()`` raises "can't subtract offset-naive and
    offset-aware datetimes". Call this on values read back from the DB before
    comparing/subtracting. ``None`` passes through unchanged.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
