from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from workers.celery.app import celery_app

logger = logging.getLogger(__name__)


def _resolve_api_root() -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "apps" / "api"
        if candidate.is_dir() and (candidate / "main.py").is_file():
            return candidate
    raise RuntimeError("Could not resolve apps/api from publisher task path")


def _session():
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))
    from app.config import settings

    engine = create_engine(settings.DATABASE_URL)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def _bridge_and_enqueue_learning_loop(db, user, draft, publish_result) -> None:
    """
    Bridge a freshly-published draft to a Post and enqueue the learning loop.

    Best-effort and isolated from the publish flow: any failure here is logged and
    swallowed so it can never break publishing (Requirement 1.8). The bridge commits
    its own Post/linkage, so if the enqueue ultimately fails the Post and
    ``draft.post_id`` linkage are retained.

    Imports are local to avoid import cycles and to keep publishing resilient if the
    bridge/orchestrator modules can't be imported in this context (Requirement 1.6).
    """
    try:
        from app.services.post_bridge_service import bridge_draft_to_post

        post = bridge_draft_to_post(db, user, draft, publish_result)
        if post is None:
            return

        try:
            from workers.celery.tasks.learning_loop import on_post_published
        except ImportError:
            logger.warning(
                "learning_loop task not importable; skipping enqueue for post_id=%s",
                post.id,
            )
            return

        if not _enqueue_with_retry(on_post_published, post.id):
            logger.error(
                "Failed to enqueue on_post_published for post_id=%s after retries; "
                "Post and draft linkage retained",
                post.id,
            )
    except Exception:
        logger.exception(
            "Learning-loop bridge/enqueue failed for draft_id=%s",
            getattr(draft, "id", None),
        )


def _lock_due_draft(db, draft_id):
    """Re-read a due draft under a row-level lock before transitioning to publishing.

    On Postgres this issues ``SELECT ... FOR UPDATE SKIP LOCKED`` so that concurrent
    queue runs can never select and publish the same draft: a row already locked by
    another run is skipped (returns ``None``) instead of blocking. On SQLite (the test
    environment, which does not support ``FOR UPDATE SKIP LOCKED``) the lock clause is
    omitted, mirroring the ``_lock_draft`` pattern in ``content_service`` (R8.1).

    Returns the locked draft, or ``None`` when the row is locked by another run or no
    longer exists.
    """
    from app.models.content_draft import ContentDraft

    query = db.query(ContentDraft).filter(ContentDraft.id == draft_id)
    try:
        if db.bind and db.bind.dialect.name != "sqlite":
            query = query.with_for_update(skip_locked=True)
    except Exception:
        pass
    return query.first()


def _already_published_platform_post_id(db, draft) -> str | None:
    """Return the platform post id when this draft was already published.

    Natural-key idempotency guard (R8.5): a retry after a partial success must not
    re-post to the platform. A publish is treated as already done when either

    * the draft itself already carries a ``platform_post_id`` (set on a prior
      attempt before the run was interrupted), or
    * a ``Post`` already exists for this draft under the natural key
      ``(user_id, platform, platform_post_id)`` — located via the draft's
      ``post_id`` linkage written by the publication bridge.

    Returns the existing platform post id, or ``None`` when no prior publish is
    found and the platform call should proceed.
    """
    from app.models.post import Post

    if draft.platform_post_id:
        return draft.platform_post_id

    if draft.post_id:
        existing = (
            db.query(Post)
            .filter(
                Post.id == draft.post_id,
                Post.user_id == draft.user_id,
                Post.platform == draft.platform,
            )
            .first()
        )
        if existing and existing.platform_post_id:
            return existing.platform_post_id
    return None


def _enqueue_with_retry(task, post_id: str, attempts: int = 3) -> bool:
    """
    Enqueue a Celery task by post id, retrying transient broker failures.

    Returns ``True`` on a successful enqueue, ``False`` if all attempts fail.
    """
    for attempt in range(1, attempts + 1):
        try:
            task.delay(post_id)
            return True
        except Exception:
            logger.warning(
                "Enqueue attempt %d/%d failed for post_id=%s", attempt, attempts, post_id
            )
    return False


@celery_app.task(name="workers.celery.tasks.publisher.process_publishing_queue", bind=True)
def process_publishing_queue(self) -> dict:
    from app.models.content_draft import ContentDraft
    from app.models.user import User
    from app.services.email import send_post_review_email
    from app.services.publisher_service import PublishError, publish_draft
    from app.services.publishing_state import (
        DRAFT_STATUS_FAILED,
        DRAFT_STATUS_PUBLISHED,
        DRAFT_STATUS_PUBLISHING,
        DRAFT_STATUS_SCHEDULED,
        REVIEW_STATUS_APPROVED,
        REVIEW_STATUS_REVIEW_DUE,
        PublishingValidationError,
        validate_platform_media,
    )

    db = _session()
    now = datetime.now(timezone.utc)
    result = {"review_emails": 0, "published": 0, "failed": 0, "waiting_for_approval": 0}

    try:
        review_due = (
            db.query(ContentDraft)
            .filter(
                ContentDraft.status == DRAFT_STATUS_SCHEDULED,
                ContentDraft.scheduled_for <= now + timedelta(hours=24),
                ContentDraft.scheduled_for > now,
                ContentDraft.review_email_sent_at.is_(None),
                ContentDraft.auto_post_enabled_snapshot == False,
            )
            .all()
        )
        for draft in review_due:
            user = db.query(User).filter(User.id == draft.user_id).first()
            if not user:
                continue
            draft.review_status = REVIEW_STATUS_REVIEW_DUE
            draft.review_email_sent_at = now
            title = (draft.content or "Scheduled post").splitlines()[0][:180]
            try:
                send_post_review_email(
                    email=user.email,
                    name=user.name,
                    draft_id=draft.id,
                    title=title,
                    scheduled_for=draft.scheduled_for.isoformat() if draft.scheduled_for else "",
                )
                result["review_emails"] += 1
            except Exception:
                logger.exception("Review email failed draft_id=%s", draft.id)

        due = (
            db.query(ContentDraft)
            .filter(
                ContentDraft.status == DRAFT_STATUS_SCHEDULED,
                ContentDraft.scheduled_for <= now,
            )
            .all()
        )
        for due_draft in due:
            # Acquire a row-level lock (FOR UPDATE SKIP LOCKED on Postgres) before
            # transitioning the draft so concurrent queue runs cannot select the same
            # draft and produce duplicate posts (R8.1). A draft already locked by another
            # run is skipped; the lock is held until the publishing-state commit below.
            draft = _lock_due_draft(db, due_draft.id)
            if draft is None:
                continue
            if draft.status != DRAFT_STATUS_SCHEDULED:
                continue
                
            user = db.query(User).filter(User.id == draft.user_id).first()
            if not user:
                continue
            if not draft.auto_post_enabled_snapshot and draft.review_status != REVIEW_STATUS_APPROVED:
                draft.review_status = REVIEW_STATUS_REVIEW_DUE
                draft.publish_error = "Waiting for review approval."
                result["waiting_for_approval"] += 1
                continue
            try:
                validate_platform_media(draft.platform, len([item for item in draft.media if item.status != "deleted"]))

                # Natural-key idempotency guard (R8.5): before calling the platform,
                # detect a prior (partially-successful) publish so a retry does not
                # create a duplicate post. A draft that already carries a
                # ``platform_post_id`` — or for which a ``published`` Post already
                # exists under the natural key (user_id, platform, platform_post_id) —
                # is finalized as published without re-posting.
                already_post_id = _already_published_platform_post_id(db, draft)
                if already_post_id:
                    draft.status = DRAFT_STATUS_PUBLISHED
                    draft.review_status = REVIEW_STATUS_APPROVED
                    draft.platform_post_id = already_post_id
                    draft.published_at = draft.published_at or now
                    draft.publish_error = None
                    result["published"] += 1
                    db.commit()
                    continue

                # Set a stable idempotency key before the platform call so the
                # publish can be correlated across retries after a partial success (R8.5).
                if not draft.publish_idempotency_key:
                    draft.publish_idempotency_key = uuid.uuid4().hex
                draft.status = DRAFT_STATUS_PUBLISHING
                draft.publish_error = None
                db.commit()
                published = asyncio.run(publish_draft(db, user, draft))
                draft.status = DRAFT_STATUS_PUBLISHED
                draft.review_status = REVIEW_STATUS_APPROVED
                draft.platform_post_id = published["platform_post_id"]
                draft.published_at = now
                draft.publish_error = None
                result["published"] += 1
                db.commit()

                # Self-learning loop wiring: bridge the published draft to a
                # learnable Post and enqueue the orchestrator. Runs only after a
                # successful publish + commit and never raises out of here so a
                # bridge/enqueue failure can't fail the publish (Requirements 1.6, 1.8).
                _bridge_and_enqueue_learning_loop(db, user, draft, published)
            except (PublishingValidationError, PublishError, Exception) as exc:
                # Bounded failure (R8.3): any publish error transitions the draft to a
                # terminal ``failed`` state with a category-level message. Failed drafts
                # are never re-selected (the due query above filters ``status ==
                # scheduled``), so a failed publish is not retried indefinitely.
                error_category = getattr(exc, "code", "unknown_error")
                error_detail = getattr(exc, "detail", "An unexpected error occurred during publishing.")
                if not isinstance(exc, (PublishingValidationError, PublishError)):
                    error_detail = "An unexpected error occurred during publishing."
                    
                logger.error(
                    "Publishing failed. draft_id=%s user_id=%s platform=%s error_category=%s",
                    str(draft.id),
                    str(draft.user_id),
                    draft.platform,
                    error_category,
                )
                draft.status = DRAFT_STATUS_FAILED
                draft.publish_error = error_detail
                result["failed"] += 1

        db.commit()
        return result
    finally:
        db.close()
