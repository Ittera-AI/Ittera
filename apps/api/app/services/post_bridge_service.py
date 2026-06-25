"""
Publication Bridge Agent (Gap 1).

Creates or links the ``Post`` that represents an Iterra-published ``ContentDraft``
so the self-learning loop has something to analyze. The bridge is the missing link
between publishing (which today writes only to ``ContentDraft``) and the learning
loop (which learns from ``Post`` + ``PostAnalysis``).

Design reference: design.md section B.3.1.

Key guarantees:
  - Idempotent on the natural key ``(platform, platform_post_id)`` (case-sensitive
    exact match) and on ``draft.post_id`` (Requirements 1.1, 1.2, 1.7).
  - Reuses an existing ``Post`` when the draft is already bridged or when a scraper
    created the ``Post`` first, setting ``source="iterra_published"`` on link
    (Requirements 1.2, 1.3).
  - Sets ``draft.post_id`` before returning a success result (Requirement 1.4).
  - Emits a ``post_bridge_failed`` event and returns ``None`` (without rolling back
    the publish) when no ``platform_post_id`` is available (Requirement 1.5).
"""

import json

from sqlalchemy.orm import Session

from app.db.datetime_helpers import utc_now
from app.models.content_draft import ContentDraft
from app.models.post import Post
from app.models.user import User


def bridge_draft_to_post(
    db: Session,
    user: User,
    draft: ContentDraft,
    publish_result: dict,
) -> Post | None:
    """
    Create or link the Post that represents an Iterra-published draft.

    Idempotent on ``(platform, platform_post_id)`` and on ``draft.post_id``.
    Returns the linked Post, or ``None`` when the draft has no ``platform_post_id``
    (in which case a ``post_bridge_failed`` event is emitted and the publish is
    allowed to succeed without rollback).
    """
    platform_post_id = (publish_result or {}).get("platform_post_id") or draft.platform_post_id
    if not platform_post_id:
        # No way to identify the published item on the platform — the loop has
        # nothing to learn from. Record the failure but never break publishing.
        _emit_event(
            db,
            user.id,
            "post_bridge_failed",
            metrics={"draft_id": draft.id, "reason": "no_platform_post_id"},
        )
        return None

    # Already bridged — return the linked Post without creating another.
    if draft.post_id:
        return db.query(Post).filter(Post.id == draft.post_id).first()

    # A scraper/importer may have created the Post first; link to it (exact,
    # case-sensitive match on the natural key) and mark it as Iterra-published.
    existing = (
        db.query(Post)
        .filter(
            Post.platform == draft.platform,
            Post.platform_post_id == platform_post_id,
        )
        .first()
    )
    if existing:
        draft.post_id = existing.id
        existing.source = "iterra_published"
        db.commit()
        _emit_event(
            db,
            user.id,
            "post_bridged",
            post_id=existing.id,
            metrics={"draft_id": draft.id, "linked_existing": True},
        )
        return existing

    # First time we see this published item — create exactly one Post.
    post = Post(
        user_id=user.id,
        workspace_id=draft.workspace_id,
        platform=draft.platform,
        platform_post_id=platform_post_id,
        content=_draft_plaintext(draft),
        content_type="thread" if _is_thread(draft.content) else "post",
        published_at=draft.published_at or utc_now(),
        source="iterra_published",
        topics=[],
    )
    db.add(post)
    db.flush()  # assign post.id before linking the draft
    draft.post_id = post.id
    db.commit()
    _emit_event(
        db,
        user.id,
        "post_bridged",
        post_id=post.id,
        metrics={"draft_id": draft.id, "linked_existing": False},
    )
    return post


def _emit_event(
    db: Session,
    user_id: str,
    event_type: str,
    post_id: str | None = None,
    metrics: dict | None = None,
) -> None:
    """
    Record an ``AnalyticsEvent`` for bridge audit/idempotency.

    Imported locally to mirror ``analytics_service`` and avoid import cycles.
    """
    from app.models.analytics_snapshot import AnalyticsEvent

    event = AnalyticsEvent(
        user_id=user_id,
        event_type=event_type,
        post_id=post_id,
        metrics=metrics or {},
    )
    db.add(event)
    db.commit()


def _is_thread(content: str | None) -> bool:
    """
    A draft stores thread content as a JSON-serialized list of segments and plain
    posts as a raw string. Treat content as a thread only when it parses to a list.
    """
    if not content:
        return False
    try:
        parsed = json.loads(content)
    except (ValueError, TypeError):
        return False
    return isinstance(parsed, list)


def _draft_plaintext(draft: ContentDraft) -> str:
    """
    Produce the plain-text content for the Post. Thread drafts (JSON list of
    segments) are joined into a single newline-separated string; plain drafts are
    returned as-is. Never returns ``None`` because ``Post.content`` is NOT NULL.
    """
    content = draft.content
    if not content:
        return ""
    try:
        parsed = json.loads(content)
    except (ValueError, TypeError):
        return content
    if isinstance(parsed, list):
        return "\n\n".join(str(segment) for segment in parsed)
    return content
