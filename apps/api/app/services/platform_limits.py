"""Platform-aware character limit resolution.

Sits between content_service.py and iterra_ai's platform_rules.py.
Resolves the effective max_chars for a user+platform combination
by reading subscription tier from connection_metadata.
"""

import json
import re
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.orm import Session

from app.models.social_connection import SocialConnection


class TwitterTier(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


# Hard limits per platform+tier (characters)
PLATFORM_CHAR_LIMITS: dict[str, int | dict[str, int]] = {
    "linkedin": 3_000,
    "instagram": 2_200,
    "twitter": {
        TwitterTier.FREE: 280,
        TwitterTier.PREMIUM: 25_000,
    },
}

# Default tier when unknown or missing
DEFAULT_TWITTER_TIER = TwitterTier.FREE


@dataclass
class ContentLimit:
    """Resolved character limit for a platform+user combination."""

    platform: str
    max_chars: int
    tier: str | None  # None for platforms without tiers
    is_thread_eligible: bool  # True if content can be auto-split into a thread


def resolve_content_limit(db: Session, user_id: str, platform: str) -> ContentLimit:
    """
    Resolve the effective character limit for a user on a platform.

    For Twitter: reads subscription_tier from connection_metadata.
    Falls back to FREE tier if tier is unknown/missing.
    For other platforms: returns the static limit.
    """
    if platform == "twitter":
        tier = _get_twitter_tier(db, user_id)
        limit = PLATFORM_CHAR_LIMITS["twitter"][tier]
        return ContentLimit(
            platform=platform,
            max_chars=limit,
            tier=tier,
            is_thread_eligible=(tier == TwitterTier.FREE),
        )

    max_chars = PLATFORM_CHAR_LIMITS.get(platform, 3_000)
    if isinstance(max_chars, dict):
        max_chars = 3_000  # safety fallback
    return ContentLimit(
        platform=platform,
        max_chars=max_chars,
        tier=None,
        is_thread_eligible=False,
    )


def _get_twitter_tier(db: Session, user_id: str) -> TwitterTier:
    """Read Twitter subscription tier from connection_metadata."""
    conn = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user_id,
            SocialConnection.platform == "twitter",
            SocialConnection.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not conn:
        return DEFAULT_TWITTER_TIER

    metadata = conn.connection_metadata or {}
    tier_value = metadata.get("subscription_tier")

    if tier_value == TwitterTier.PREMIUM:
        return TwitterTier.PREMIUM
    return DEFAULT_TWITTER_TIER


def update_twitter_tier(db: Session, user_id: str, tier: TwitterTier) -> None:
    """Update the stored Twitter subscription tier in connection_metadata."""
    conn = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user_id,
            SocialConnection.platform == "twitter",
            SocialConnection.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not conn:
        return

    metadata = dict(conn.connection_metadata or {})
    metadata["subscription_tier"] = tier
    conn.connection_metadata = metadata
    db.commit()


# --- Thread Splitting Algorithm ---

# Sentence boundary pattern: period, question mark, or exclamation followed by space or end
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")

# Thread segment numbering format
THREAD_NUMBERING = True  # e.g., "1/3", "2/3", "3/3"


@dataclass
class ThreadSplitResult:
    """Result of splitting content into a thread."""

    segments: list[str]
    segment_count: int
    original_length: int
    all_within_limit: bool


def split_into_thread(content: str, max_chars: int = 280) -> ThreadSplitResult:
    """
    Split content into thread segments respecting sentence boundaries.

    Algorithm:
    1. Split content into sentences
    2. Greedily pack sentences into segments up to max_chars
    3. If a single sentence exceeds max_chars, fall back to word-boundary split
    4. Optionally prepend thread numbering (e.g., "1/N")

    Returns ThreadSplitResult with all segments.
    """
    content = content.strip()
    if len(content) <= max_chars:
        return ThreadSplitResult(
            segments=[content],
            segment_count=1,
            original_length=len(content),
            all_within_limit=True,
        )

    sentences = SENTENCE_BOUNDARY_RE.split(content)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Reserve space for numbering if enabled (e.g., "XX/XX " worst case)
    numbering_reserve = 6 if THREAD_NUMBERING else 0
    effective_max = max_chars - numbering_reserve

    segments: list[str] = []
    current_segment = ""

    for sentence in sentences:
        if len(sentence) > effective_max:
            # Sentence too long — flush current segment, then word-split the long sentence
            if current_segment:
                segments.append(current_segment.strip())
                current_segment = ""
            segments.extend(_word_boundary_split(sentence, effective_max))
        elif len(current_segment) + len(sentence) + 1 <= effective_max:
            # Fits in current segment
            current_segment = f"{current_segment} {sentence}".strip()
        else:
            # Start new segment
            if current_segment:
                segments.append(current_segment.strip())
            current_segment = sentence

    if current_segment:
        segments.append(current_segment.strip())

    # Apply numbering
    if THREAD_NUMBERING and len(segments) > 1:
        total = len(segments)
        segments = [f"{i + 1}/{total} {seg}" for i, seg in enumerate(segments)]

    all_within = all(len(s) <= max_chars for s in segments)

    return ThreadSplitResult(
        segments=segments,
        segment_count=len(segments),
        original_length=len(content),
        all_within_limit=all_within,
    )


def _word_boundary_split(text: str, max_chars: int) -> list[str]:
    """Split a single long sentence at word boundaries."""
    words = text.split()
    segments: list[str] = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = f"{current} {word}".strip()
        else:
            if current:
                segments.append(current)
            current = word

    if current:
        segments.append(current)

    return segments


def is_thread(content: str) -> bool:
    """Detect if content represents a thread (stored as JSON array)."""
    try:
        parsed = json.loads(content)
        return isinstance(parsed, list) and len(parsed) > 1
    except (json.JSONDecodeError, TypeError):
        return False
