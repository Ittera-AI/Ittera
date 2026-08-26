from datetime import datetime, timezone, timedelta
import json
import logging
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.content_draft import ContentDraft, ContentDraftMedia
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.schemas.content import GenerateRequest, RepurposeRequest, ScheduleRequest, SuggestRequest
from app.services import brand_profile_service, context_service, trend_service
from app.services.publisher_service import PublishError, publish_draft
from app.services.publishing_state import (
    DRAFT_STATUS_CANCELLED,
    DRAFT_STATUS_DRAFT,
    DRAFT_STATUS_FAILED,
    DRAFT_STATUS_PUBLISHED,
    DRAFT_STATUS_PUBLISHING,
    DRAFT_STATUS_SCHEDULED,
    IMMUTABLE_PUBLISH_STATUSES,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_DRAFT,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_REVIEW_DUE,
    TERMINAL_PUBLISH_STATUSES,
    PublishingValidationError,
    validate_platform_media,
)
from app.services.storage_queue import StorageOperationType, get_storage_queue
from app.services.storage_service import StorageError, StorageService
from app.services.social_service import get_calendar_connection
from app.services.google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)

LIMITS = {"linkedin": 3000, "instagram": 2200, "twitter": 280}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_DRAFT_IMAGES = 4
IMAGE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
}
IMAGE_EXTENSIONS = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
}


def _ensure_draft_mutable(draft: ContentDraft, action: str = "edited") -> None:
    """Reject content/media/schedule changes on an immutable draft (Requirement 8.2).

    A draft that is mid-publish (``publishing``) or already ``published`` is frozen:
    its content, media, and schedule can no longer change. Drafts in any other state
    (``draft``, ``scheduled``, ``failed``) remain editable. Raises HTTP 409 with a
    category-level message that never leaks internal detail.
    """
    if draft.status in IMMUTABLE_PUBLISH_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Published or publishing drafts cannot be {action}.",
        )


def suggest(db: Session, user: User, payload: SuggestRequest) -> dict:
    ctx = context_service.assemble(db, user, platform=payload.platform or user.primary_platform)
    trends = trend_service.get_trends_for_user(db, user)["trends"]

    # Prefer the report's top topics, fall back to trend feed, then niche
    if ctx.report.top_performing_topics:
        base_topic = payload.topic or ctx.report.top_performing_topics[0]
    else:
        base_topic = payload.topic or (trends[0]["topic"] if trends else user.niche or "content strategy")

    # Use persona pillars as format hints when available
    pillar_hint = f" (aligns with your pillar: {ctx.persona.content_pillars[0]})" if ctx.persona.content_pillars else ""

    suggestions = [
        {
            "hook": f"Most teams misunderstand {base_topic}.",
            "angle": f"Explain the practical shift behind {base_topic}.",
            "format": "hot-take",
            "trend_tie": base_topic,
            "why_it_works": f"Starts with tension and resolves into a useful principle{pillar_hint}.",
        },
        {
            "hook": f"A simple {base_topic} checklist:",
            "angle": "Turn the topic into a practical framework readers can save.",
            "format": "listicle",
            "trend_tie": base_topic,
            "why_it_works": f"Concrete, skimmable, and aligned with your analytical voice{pillar_hint}.",
        },
        {
            "hook": f"The quiet advantage of {base_topic} is not speed.",
            "angle": "Connect the trend to trust, review loops, and better decisions.",
            "format": "story",
            "trend_tie": base_topic,
            "why_it_works": f"Gives your audience a more thoughtful take than the obvious trend post{pillar_hint}.",
        },
    ]
    return {
        "suggestions": suggestions,
        "context_warnings": ctx.missing_layers,
    }


def generate(db: Session, user: User, payload: GenerateRequest) -> dict:
    _require_brand_profile(db, user)

    # Assemble the 3-layer context for this generation call
    ctx = context_service.assemble(db, user, platform=payload.platform)

    from iterra_ai.content.engine import ContentGenerationEngine
    from iterra_ai.content.schemas import ContentGenerationInput
    from iterra_ai.content.platform_rules import get_rules
    from app.services.platform_limits import resolve_content_limit, split_into_thread

    # Resolve tier-aware character limit
    content_limit = resolve_content_limit(db, user.id, payload.platform)

    # Override platform_rules max_chars with the resolved limit
    rules = dict(get_rules(payload.platform))
    rules["max_chars"] = content_limit.max_chars

    engine_input = ContentGenerationInput(
        platform=payload.platform,
        prompt=payload.prompt,
        hook=payload.suggestion.hook if payload.suggestion else None,
        system_prompt=ctx.system_prompt,
        platform_rules=rules,
    )
    
    engine = ContentGenerationEngine()
    output = engine.generate(engine_input)
    fit_score, fit_notes = _persona_fit(output.content, ctx)
    if fit_score < 60:
        rewrite_input = ContentGenerationInput(
            platform=payload.platform,
            prompt=(
                f"{payload.prompt}\n\nRewrite once to fit the persona more tightly. "
                "Use the user's voice, audience, pillars, avoid-topic constraints, and prior performance facts."
            ),
            hook=payload.suggestion.hook if payload.suggestion else None,
            system_prompt=ctx.system_prompt,
            platform_rules=rules,
        )
        rewritten = engine.generate(rewrite_input)
        rewritten_score, rewritten_notes = _persona_fit(rewritten.content, ctx)
        if rewritten_score >= fit_score:
            output = rewritten
            fit_score = rewritten_score
            fit_notes = rewritten_notes

    # Validate output length against platform limit
    within_limit = output.char_count <= content_limit.max_chars

    # Auto-split into thread if free-tier Twitter and over limit
    thread_segments = None
    if not within_limit and content_limit.is_thread_eligible:
        split_result = split_into_thread(output.content, content_limit.max_chars)
        thread_segments = split_result.segments

    # Store draft as thread JSON if split, plain text otherwise
    draft_content = json.dumps(thread_segments) if thread_segments else output.content

    draft = ContentDraft(
        user_id=user.id,
        platform=payload.platform,
        content=draft_content,
        prompt_used=payload.prompt,
        trend_used=payload.trend_used,
        generation_model=output.model,
        persona_fit_score=fit_score,
        persona_fit_notes=fit_notes,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    # Save to Google Drive if user has Drive connected
    try:
        _save_draft_to_drive_if_connected(db, user, draft, draft_content)
    except Exception as e:
        # Don't fail the generation if Drive save fails
        logger.warning("Failed to save draft to Drive: %s", e)
    
    return {
        "draft_id": draft.id,
        "content": draft_content,
        "word_count": output.word_count,
        "within_platform_limit": within_limit,
        "thread_segments": thread_segments,
        "content_limit": {
            "platform": content_limit.platform,
            "max_chars": content_limit.max_chars,
            "tier": content_limit.tier,
        },
        "context_warnings": ctx.missing_layers,
        "context_summary": {
            "permanent_complete": ctx.permanent.is_complete(),
            "persona_confidence": ctx.persona.confidence_score,
            "report_posts": ctx.report.posts_analysed,
            "context_version": ctx.permanent.context_version,
            "persona_fit_score": fit_score,
            "persona_fit_notes": fit_notes,
        },
        "generation_mode": "mock" if output.is_mock else "live",
    }


def repurpose(db: Session, user: User, payload: RepurposeRequest) -> dict:
    draft = _draft(db, user, payload.draft_id)
    
    from iterra_ai.repurpose.engine import RepurposeEngine
    from iterra_ai.repurpose.schemas import RepurposeInput
    from app.services.platform_limits import resolve_content_limit, split_into_thread

    # Resolve tier-aware character limit for target platform (Req 6.1)
    content_limit = resolve_content_limit(db, user.id, payload.target_platform)

    # Assemble brand profile context for voice consistency (Req 6.3, 6.4)
    ctx = context_service.assemble(db, user, platform=payload.target_platform)
    
    engine_input = RepurposeInput(
        source_platform=draft.platform,
        target_platforms=[payload.target_platform],
        original_content=draft.content,
        max_chars=content_limit.max_chars,
        system_prompt=ctx.system_prompt,
    )
    
    engine = RepurposeEngine()
    output = engine.generate(engine_input)
    
    # Get repurposed content (engine output or fallback)
    content = output.repurposed[0].content if output.repurposed else _repurposed_content(draft.content, payload.target_platform)

    # Validate and enforce tier-aware limits (Req 6.1)
    within_limit = len(content) <= content_limit.max_chars
    thread_segments = None

    # Auto-split into thread if free-tier Twitter and over limit
    if not within_limit and content_limit.is_thread_eligible:
        split_result = split_into_thread(content, content_limit.max_chars)
        thread_segments = split_result.segments
        within_limit = split_result.all_within_limit
    elif not within_limit:
        # For non-thread-eligible platforms, truncate to limit
        content = content[:content_limit.max_chars]
        within_limit = True

    # Determine draft content: thread JSON or plain text
    draft_content = json.dumps(thread_segments) if thread_segments else content

    # Create an independent ContentDraft for the repurposed content (Req 6.2)
    new_draft = ContentDraft(
        user_id=user.id,
        platform=payload.target_platform,
        content=draft_content,
        prompt_used=f"Repurposed from {draft.platform} draft {draft.id}",
        status=DRAFT_STATUS_DRAFT,
    )
    # Allow independent scheduling if scheduled_for is provided
    if payload.scheduled_for is not None:
        new_draft.scheduled_for = _aware(payload.scheduled_for)
        new_draft.status = DRAFT_STATUS_SCHEDULED
    
    db.add(new_draft)

    # Also update repurposed_versions on source draft for backwards compatibility
    versions = dict(draft.repurposed_versions or {})
    versions[payload.target_platform] = content
    draft.repurposed_versions = versions
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(new_draft)

    return {
        "draft_id": draft.id,
        "content": content,
        "platform": payload.target_platform,
        "new_draft_id": new_draft.id,
        "thread_segments": thread_segments,
        "within_platform_limit": within_limit,
        "content_limit": {
            "platform": content_limit.platform,
            "max_chars": content_limit.max_chars,
            "tier": content_limit.tier,
        },
    }


def create_draft(db: Session, user: User, payload) -> ContentDraft:
    """Create a new content draft, supporting thread content (list of strings) for Twitter.

    When content is a list (thread for Twitter):
      - Validates each segment is within the platform character limit
      - Stores as a JSON-serialized array string in content_drafts.content
    When content is a plain string:
      - Stores as-is (existing behavior)
    """
    import json
    from app.services.platform_limits import resolve_content_limit

    content_limit = resolve_content_limit(db, user.id, payload.platform)

    if isinstance(payload.content, list):
        # Thread content — validate each segment
        segments = payload.content
        if len(segments) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Thread content must contain at least one segment.",
            )
        for i, segment in enumerate(segments):
            if not isinstance(segment, str) or not segment.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Thread segment {i + 1} must be a non-empty string.",
                )
            if len(segment) > content_limit.max_chars:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Thread segment {i + 1} exceeds the {content_limit.max_chars}-character "
                        f"limit for {payload.platform} ({len(segment)} characters)."
                    ),
                )
        # Store as JSON array string
        draft_content = json.dumps(segments)
    else:
        # Plain string content — store as-is
        draft_content = payload.content

    draft = ContentDraft(
        user_id=user.id,
        platform=payload.platform,
        content=draft_content,
        status=DRAFT_STATUS_DRAFT,
    )
    if payload.scheduled_for is not None:
        draft.scheduled_for = _aware(payload.scheduled_for)
        draft.status = DRAFT_STATUS_SCHEDULED

    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def list_drafts(db: Session, user: User, status_filter: str | None = None) -> list[ContentDraft]:
    query = db.query(ContentDraft).filter(ContentDraft.user_id == user.id)
    if status_filter:
        query = query.filter(ContentDraft.status == status_filter)
    return query.order_by(ContentDraft.created_at.desc()).all()


def get_draft(db: Session, user: User, draft_id: str) -> ContentDraft:
    """
    Get a draft by ID.

    If draft has drive_file_id and user's storage_preference is google_drive,
    content is loaded from Google Drive (with DB as fallback).
    """
    draft = _draft(db, user, draft_id)

    # Try to load from Drive if applicable
    if draft.drive_file_id and user.storage_preference == "google_drive":
        try:
            drive_content = _load_draft_from_drive(db, user, draft)
            if drive_content:
                # Update draft content from Drive (sync latest version)
                draft.content = drive_content
                logger.debug("Loaded draft %s content from Drive", draft_id)
        except Exception as e:
            logger.warning("Failed to load draft from Drive, using DB content: %s", e)

    return draft


def update_draft(db: Session, user: User, draft_id: str, payload) -> ContentDraft:
    draft = _draft(db, user, draft_id)
    _ensure_draft_mutable(draft, "edited")
        
    content_changed = False
    if getattr(payload, "content", None) is not None:
        draft.content = payload.content
        content_changed = True
    if getattr(payload, "scheduled_for", None) is not None:
        draft.scheduled_for = _aware(payload.scheduled_for)
    requested_status = getattr(payload, "status", None)
    if requested_status is not None:
        if requested_status not in {DRAFT_STATUS_DRAFT, DRAFT_STATUS_SCHEDULED}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported draft status update.")
        draft.status = requested_status
    if content_changed:
        _reset_review_after_edit(draft)
        draft.publish_error = None
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return draft


def _already_published_platform_post_id(db: Session, draft: ContentDraft) -> str | None:
    """Return the platform post id when this draft was already published.

    Natural-key idempotency guard (R8.5): a retry after a partial success must not
    re-post to the platform. A publish is treated as already done when either the
    draft itself already carries a ``platform_post_id``, or a ``Post`` already exists
    for this draft under the natural key ``(user_id, platform, platform_post_id)`` —
    located via the draft's ``post_id`` linkage written by the publication bridge.

    Returns the existing platform post id, or ``None`` when no prior publish is found
    and the platform call should proceed.
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


async def publish_now(db: Session, user: User, draft_id: str) -> dict:
    draft = _lock_draft(db, user, draft_id)
    now = datetime.now(timezone.utc)
    if draft.status == DRAFT_STATUS_PUBLISHED and draft.platform_post_id:
        return {"platform_post_id": draft.platform_post_id, "published_at": draft.published_at or now}
    if draft.status in TERMINAL_PUBLISH_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Draft is already {draft.status}.")
    if not (draft.content or "").strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Draft content is empty")
    try:
        validate_platform_media(draft.platform, len([item for item in draft.media if item.status != "deleted"]))
    except PublishingValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    draft.status = DRAFT_STATUS_PUBLISHING
    draft.publish_error = None
    draft.updated_at = now
    if not draft.publish_idempotency_key:
        draft.publish_idempotency_key = uuid.uuid4().hex
    db.commit()
    db.refresh(draft)

    # Natural-key idempotency guard (R8.5): if a prior attempt already posted to the
    # platform (the draft carries a platform_post_id, or a published Post exists for
    # this draft under the natural key (user_id, platform, platform_post_id)), do not
    # re-post on retry — finalize the draft as published instead.
    already_post_id = _already_published_platform_post_id(db, draft)
    if already_post_id:
        published_at = draft.published_at or datetime.now(timezone.utc)
        draft.status = DRAFT_STATUS_PUBLISHED
        draft.review_status = REVIEW_STATUS_APPROVED
        draft.platform_post_id = already_post_id
        draft.published_at = published_at
        draft.publish_error = None
        draft.updated_at = published_at
        db.commit()
        return {"platform_post_id": draft.platform_post_id, "published_at": published_at}

    try:
        result = await publish_draft(db, user, draft)
    except PublishError as exc:
        draft.status = DRAFT_STATUS_FAILED
        draft.publish_error = exc.detail
        draft.updated_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except HTTPException as exc:
        draft.status = DRAFT_STATUS_FAILED
        draft.publish_error = str(exc.detail)
        draft.updated_at = datetime.now(timezone.utc)
        db.commit()
        raise
    except Exception as exc:
        logger.exception("Publish failed draft_id=%s", draft.id)
        draft.status = DRAFT_STATUS_FAILED
        draft.publish_error = "Publishing failed. Try again after checking the connection."
        draft.updated_at = now
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=draft.publish_error) from exc

    published_at = datetime.now(timezone.utc)
    draft.status = DRAFT_STATUS_PUBLISHED
    draft.published_at = published_at
    draft.review_status = REVIEW_STATUS_APPROVED
    draft.platform_post_id = result.get("platform_post_id") or draft.platform_post_id
    draft.publish_error = None
    draft.updated_at = published_at
    db.commit()

    # Self-learning loop wiring: bridge the published draft to a learnable Post and
    # enqueue the orchestrator. Runs only after a successful publish + commit and
    # never raises out of here — publishing must succeed regardless of the outcome
    # (Requirements 1.6, 1.8).
    _bridge_and_enqueue_learning_loop(db, user, draft, result)

    return {"platform_post_id": draft.platform_post_id, "published_at": published_at}


def _bridge_and_enqueue_learning_loop(
    db: Session, user: User, draft: ContentDraft, publish_result: dict
) -> None:
    """
    Bridge a freshly-published draft to a Post and enqueue the learning loop.

    Best-effort and isolated from the publish flow: any failure here is logged and
    swallowed so it can never break publishing (Requirement 1.8). The bridge commits
    its own Post/linkage, so if the enqueue ultimately fails the Post and
    ``draft.post_id`` linkage are retained.

    Imports the bridge service and the Celery task locally to avoid import cycles and
    to keep the API importable when the worker/celery stack isn't available in this
    context (Requirement 1.6 guard).
    """
    try:
        from app.services.post_bridge_service import bridge_draft_to_post

        post = bridge_draft_to_post(db, user, draft, publish_result)
        if post is None:
            return

        try:
            from workers.celery.tasks.learning_loop import on_post_published
        except ImportError:
            # Celery/worker package not importable in this context — the Post and
            # linkage are already committed and the beat cadence will pick it up.
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
        # Never let bridge/enqueue failures break a successful publish.
        logger.exception(
            "Learning-loop bridge/enqueue failed for draft_id=%s", draft.id
        )


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


def schedule_post(db: Session, user: User, payload: ScheduleRequest) -> dict:
    scheduled_for = _aware(payload.scheduled_for)
    if scheduled_for <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Schedule time must be in the future")
    draft = _draft(db, user, payload.draft_id)
    _ensure_draft_mutable(draft, "rescheduled")
    if not (draft.content or "").strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Draft content is empty")
    try:
        validate_platform_media(draft.platform, len([item for item in draft.media if item.status != "deleted"]))
    except PublishingValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    draft.status = DRAFT_STATUS_SCHEDULED
    draft.scheduled_for = scheduled_for
    draft.auto_post_enabled_snapshot = bool(user.auto_post_enabled)
    if user.auto_post_enabled:
        draft.review_status = REVIEW_STATUS_APPROVED
    else:
        review_due_at = scheduled_for - timedelta(hours=24)
        draft.review_status = REVIEW_STATUS_REVIEW_DUE if review_due_at <= datetime.now(timezone.utc) else REVIEW_STATUS_DRAFT
    draft.review_email_sent_at = None
    draft.celery_task_id = "publishing-queue"
    draft.publish_error = None
    
    # Try to sync with Google Calendar
    calendar_conn = get_calendar_connection(db, user.id)
    if calendar_conn:
        try:
            calendar_service = GoogleCalendarService(
                access_token=calendar_conn.access_token,
                refresh_token=calendar_conn.refresh_token,
                encrypted=True,
            )
            event_id = calendar_service.create_event(
                title=f"Iterra Post: {draft.platform.capitalize()}",
                description=f"Link: {settings.FRONTEND_URL}/draft/{draft.id}\n\nContent Preview:\n{(draft.content or '')[:100]}...",
                start_time=scheduled_for,
            )
            # Store event id in platform_media JSON column since we don't have a dedicated column
            media_data = draft.platform_media or {}
            media_data["google_calendar_event_id"] = event_id
            draft.platform_media = media_data
        except Exception as exc:
            logger.warning("Failed to sync scheduled post to Google Calendar: %s", exc)

    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "celery_task_id": draft.celery_task_id,
        "scheduled_for": scheduled_for,
        "suggested_times": suggested_times(),
    }


def cancel_schedule(db: Session, user: User, draft_id: str) -> dict:
    draft = _draft(db, user, draft_id)
    _ensure_draft_mutable(draft, "cancelled")
    draft.status = DRAFT_STATUS_CANCELLED
    draft.review_status = REVIEW_STATUS_REJECTED
    draft.celery_task_id = None
    draft.publish_error = None
    
    # Delete from Google Calendar if synced
    if draft.platform_media and "google_calendar_event_id" in draft.platform_media:
        event_id = draft.platform_media.pop("google_calendar_event_id")
        calendar_conn = get_calendar_connection(db, user.id)
        if calendar_conn:
            try:
                calendar_service = GoogleCalendarService(
                    access_token=calendar_conn.access_token,
                    refresh_token=calendar_conn.refresh_token,
                    encrypted=True,
                )
                calendar_service.delete_event(event_id)
            except Exception as exc:
                logger.warning("Failed to delete scheduled post from Google Calendar: %s", exc)
                
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "cancelled"}


def approve_draft(db: Session, user: User, draft_id: str) -> ContentDraft:
    draft = _draft(db, user, draft_id)
    if draft.status in {DRAFT_STATUS_CANCELLED, DRAFT_STATUS_PUBLISHED, DRAFT_STATUS_PUBLISHING}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Draft is already {draft.status}.")
    draft.review_status = REVIEW_STATUS_APPROVED
    draft.publish_error = None
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return draft


def add_media_to_draft(
    db: Session,
    user: User,
    draft_id: str,
    filename: str,
    mime_type: str,
    content: bytes,
) -> ContentDraftMedia:
    draft = _draft(db, user, draft_id)
    _ensure_draft_mutable(draft, "given new media")
    if draft.status == DRAFT_STATUS_CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot change media while draft is {draft.status}.")
    canonical_mime = _validate_image_upload(filename, mime_type, content)
    existing = (
        db.query(ContentDraftMedia)
        .filter(ContentDraftMedia.draft_id == draft.id, ContentDraftMedia.status != "deleted")
        .count()
    )
    if existing >= MAX_DRAFT_IMAGES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A draft can have up to 4 images.")

    media_id = str(uuid.uuid4())
    clean_name = _safe_filename(filename)
    storage_dir = Path(settings.MEDIA_STORAGE_DIR) / user.id / draft.id
    storage_dir.mkdir(parents=True, exist_ok=True)
    local_path = storage_dir / f"{media_id}_{clean_name}"
    local_path.write_bytes(content)

    media = ContentDraftMedia(
        id=media_id,
        draft_id=draft.id,
        user_id=user.id,
        filename=clean_name,
        mime_type=canonical_mime,
        local_path=str(local_path),
        public_path=f"{settings.MEDIA_PUBLIC_URL_PREFIX.rstrip('/')}/{media_id}",
        position=existing,
        status="ready",
    )
    db.add(media)
    _reset_review_after_edit(draft)
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(media)

    try:
        drive_file_id = _mirror_media_to_drive_if_connected(db, user, media, content)
        if drive_file_id:
            media.drive_file_id = drive_file_id
            db.commit()
            db.refresh(media)
    except Exception as exc:
        logger.warning("Failed to mirror media %s to Drive: %s", media.id, exc)

    return media


def delete_media(db: Session, user: User, draft_id: str, media_id: str) -> dict:
    draft = _draft(db, user, draft_id)
    media = (
        db.query(ContentDraftMedia)
        .filter(
            ContentDraftMedia.id == media_id,
            ContentDraftMedia.draft_id == draft.id,
            ContentDraftMedia.user_id == user.id,
        )
        .first()
    )
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    _ensure_draft_mutable(draft, "stripped of media")
    if draft.status == DRAFT_STATUS_CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot change media while draft is {draft.status}.")
    path = Path(media.local_path)
    media.status = "deleted"
    media.drive_file_id = None
    _reset_review_after_edit(draft)
    db.commit()
    db.delete(media)
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    try:
        if path.is_file():
            path.unlink()
    except OSError as exc:
        logger.warning("Failed to remove media file %s: %s", path, exc)
    _compact_media_positions(db, draft.id)
    return {"deleted": media_id}


def get_media_file(db: Session, user: User, media_id: str) -> ContentDraftMedia:
    media = (
        db.query(ContentDraftMedia)
        .filter(ContentDraftMedia.id == media_id, ContentDraftMedia.user_id == user.id, ContentDraftMedia.status != "deleted")
        .first()
    )
    if media is None or not Path(media.local_path).is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    return media


def calendar_events(db: Session, user: User) -> list[dict]:
    events = []
    for draft in list_drafts(db, user):
        starts_at = draft.scheduled_for or draft.published_at
        if starts_at and draft.status in {
            DRAFT_STATUS_SCHEDULED,
            DRAFT_STATUS_PUBLISHING,
            DRAFT_STATUS_PUBLISHED,
            DRAFT_STATUS_FAILED,
            DRAFT_STATUS_CANCELLED,
        }:
            events.append(
                {
                    "id": draft.id,
                    "title": (draft.content.splitlines()[0][:80] if draft.content and draft.content.splitlines() else "Untitled Draft"),
                    "platform": draft.platform,
                    "status": draft.status,
                    "review_status": draft.review_status,
                    "starts_at": starts_at,
                    "content": draft.content,
                    "media": draft.media,
                }
            )
    return events


def suggested_times(db: Session | None = None, user: User | None = None, platform: str = "linkedin") -> list[datetime]:
    """
    Returns suggested posting times. When context is available, uses the user's
    platform-specific best_post_times fact (if approved). Falls back to generic slots.
    """
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    # Try to use the user's platform-specific approved best time
    if db is not None and user is not None:
        ctx = context_service.assemble(db, user, platform=platform)
        facts = ctx.permanent.platform_facts.get(platform)
        if facts and facts.best_post_times:
            try:
                hour = int(facts.best_post_times[0].split(":")[0])
                return [
                    (now + timedelta(days=1)).replace(hour=hour),
                    (now + timedelta(days=2)).replace(hour=hour),
                    (now + timedelta(days=3)).replace(hour=hour),
                ]
            except (ValueError, IndexError):
                pass

    return [now + timedelta(days=1, hours=9), now + timedelta(days=2, hours=12), now + timedelta(days=3, hours=9)]


def _persona_fit(content: str, ctx) -> tuple[int, list[str]]:
    score = 100
    notes: list[str] = []
    lowered = content.lower()

    persona = ctx.persona
    if persona.voice_tone and not _contains_any(lowered, _keywords(persona.voice_tone)):
        score -= 15
        notes.append(f"Voice tone may not fully reflect: {persona.voice_tone}.")
    target_audience = ctx.permanent.target_audience
    if target_audience and not _contains_any(lowered, _keywords(target_audience)):
        score -= 15
        notes.append(f"Audience fit is light: {target_audience}.")
    if persona.content_pillars and not any(_contains_any(lowered, _keywords(pillar)) for pillar in persona.content_pillars[:5]):
        score -= 20
        notes.append("Draft does not clearly touch the confirmed content pillars.")
    avoid_topics = getattr(persona, "avoid_topics", []) or []
    matched_avoid = [topic for topic in avoid_topics if _contains_any(lowered, _keywords(topic))]
    if matched_avoid:
        score -= 30
        notes.append(f"Draft touches avoid topics: {', '.join(matched_avoid[:3])}.")
    if ctx.report.top_performing_topics and not any(
        _contains_any(lowered, _keywords(topic)) for topic in ctx.report.top_performing_topics[:5]
    ):
        score -= 10
        notes.append("Could be tied more strongly to prior top-performing topics.")

    if not notes:
        notes.append("Strong persona fit.")
    return max(0, min(100, score)), notes


def _keywords(value: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", value.lower())
    return [word for word in words if len(word) >= 4]


def _contains_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _safe_filename(filename: str) -> str:
    name = Path(filename or "image").name
    name = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip(".-")
    return name or "image"


def _validate_image_upload(filename: str, declared_mime: str, content: bytes) -> str:
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Image file is empty.")
    if len(content) > settings.MEDIA_MAX_BYTES:
        limit_mb = max(1, settings.MEDIA_MAX_BYTES // (1024 * 1024))
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Image must be {limit_mb}MB or smaller.")
    if declared_mime not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, and WebP images are supported.",
        )

    suffix = Path(filename or "").suffix.lower()
    if suffix and suffix not in IMAGE_EXTENSIONS[declared_mime]:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Image extension does not match its content type.")
    if declared_mime == "image/webp":
        valid = content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP"
    else:
        valid = any(content.startswith(signature) for signature in IMAGE_SIGNATURES[declared_mime])
    if not valid:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Image file signature is invalid.")
    return declared_mime


def _reset_review_after_edit(draft: ContentDraft) -> None:
    if draft.status != DRAFT_STATUS_SCHEDULED:
        return
    if draft.auto_post_enabled_snapshot:
        return
    draft.review_status = REVIEW_STATUS_DRAFT
    draft.review_email_sent_at = None


def _lock_draft(db: Session, user: User, draft_id: str) -> ContentDraft:
    query = db.query(ContentDraft).filter(ContentDraft.id == draft_id, ContentDraft.user_id == user.id)
    try:
        if db.bind and db.bind.dialect.name != "sqlite":
            query = query.with_for_update()
    except Exception:
        pass
    draft = query.first()
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return draft


def _compact_media_positions(db: Session, draft_id: str) -> None:
    media_items = (
        db.query(ContentDraftMedia)
        .filter(ContentDraftMedia.draft_id == draft_id, ContentDraftMedia.status != "deleted")
        .order_by(ContentDraftMedia.position.asc(), ContentDraftMedia.created_at.asc())
        .all()
    )
    for idx, item in enumerate(media_items):
        item.position = idx
    db.commit()


def _mirror_media_to_drive_if_connected(db: Session, user: User, media: ContentDraftMedia, content: bytes) -> str | None:
    drive_connection = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user.id,
            SocialConnection.platform == "google_drive",
            SocialConnection.is_active.is_(True),
        )
        .first()
    )
    if not drive_connection:
        return None
    meta = drive_connection.connection_metadata or {}
    folder_id = meta.get("drafts_folder_id") or meta.get("iterra_folder_id")
    if not folder_id:
        return None

    storage = StorageService(
        access_token=drive_connection.access_token,
        refresh_token=drive_connection.refresh_token,
        encrypted=True,
        expires_at=drive_connection.token_expires_at,
    )
    return storage.save_media_file(
        folder_id=folder_id,
        filename=media.filename,
        content=content,
        mime_type=media.mime_type,
        user_id=user.id,
    )


def _require_brand_profile(db: Session, user: User) -> None:
    if brand_profile_service.ensure_confirmed_profile(db, user) is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Confirm your Brand Profile before creating content.")


def _draft(db: Session, user: User, draft_id: str) -> ContentDraft:
    draft = db.query(ContentDraft).filter(ContentDraft.id == draft_id, ContentDraft.user_id == user.id).first()
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return draft


def _repurposed_content(content: str, platform: str) -> str:
    if platform == "instagram":
        return f"{content}\n\nSave this for your next planning sprint.\n\n#ContentStrategy #CreatorSystems #AIWorkflow"
    return f"1/3 {content[:220]}\n\n2/3 The point: build the loop before chasing volume.\n\n3/3 Better systems create better taste."


def _get_storage_preference(user: User, content_type: str = "default") -> str:
    """
    Get the storage preference for a specific content type.

    Args:
        user: The user to get preferences for
        content_type: Type of content (drafts, analysis, etc.)

    Returns:
        Storage location (google_drive, local, or iterra)
    """
    # First check new granular preferences
    if user.storage_preferences:
        specific = user.storage_preferences.get(content_type)
        if specific:
            return specific
        default = user.storage_preferences.get("default", "google_drive")
        return default

    # Fall back to legacy storage_preference
    if user.storage_preference:
        return user.storage_preference

    # Default to google_drive for privacy-first default
    return "google_drive"


def _save_draft_to_drive_if_connected(
    db: Session, user: User, draft: ContentDraft, content: str
) -> None:
    """
    Save draft to Google Drive if user has Drive connected.
    Updates draft.drive_file_id with the Drive file ID.
    If Drive save fails, queues the operation for later retry.
    """
    # Check storage preference for drafts
    storage_pref = _get_storage_preference(user, "drafts")
    if storage_pref != "google_drive":
        logger.debug("User %s has drafts storage preference '%s', skipping Drive save", user.id, storage_pref)
        return

    # Get Google Drive connection
    drive_connection = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user.id,
            SocialConnection.platform == "google_drive",
            SocialConnection.is_active.is_(True),
        )
        .first()
    )

    if not drive_connection:
        logger.debug("User %s has no Google Drive connection, skipping Drive save", user.id)
        return

    # Get folder IDs from metadata
    meta = drive_connection.connection_metadata or {}
    drafts_folder_id = meta.get("drafts_folder_id")

    if not drafts_folder_id:
        logger.warning("User %s has Drive connection but no drafts folder ID", user.id)
        return

    # Prepare draft data for Drive
    draft_data = {
        "id": draft.id,
        "content": content,
        "platform": draft.platform,
        "prompt_used": draft.prompt_used,
        "trend_used": draft.trend_used,
        "generation_model": draft.generation_model,
        "status": draft.status,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }

    # Save to Drive
    storage = StorageService(
        access_token=drive_connection.access_token,
        refresh_token=drive_connection.refresh_token,
        encrypted=True,
        expires_at=drive_connection.token_expires_at,
    )

    try:
        file_id = storage.save_draft(
            drafts_folder_id=drafts_folder_id,
            draft_id=draft.id,
            draft_data=draft_data,
        )

        # Update draft with Drive file ID
        draft.drive_file_id = file_id
        db.commit()

        logger.info("Saved draft %s to Drive with file ID %s", draft.id, file_id)

    except StorageError as e:
        logger.warning("Failed to save draft %s to Drive: %s. Queuing for retry.", draft.id, e)

        # Queue the operation for later retry
        queue = get_storage_queue()
        if queue.is_available():
            job_id = queue.queue_operation(
                user_id=user.id,
                operation_type=StorageOperationType.SAVE_DRAFT,
                draft_id=draft.id,
                data=draft_data,
            )
            if job_id:
                logger.info("Queued draft save operation with job ID: %s", job_id)
            else:
                logger.error("Failed to queue draft save operation")
        else:
            logger.error("Storage queue not available - draft will not be saved to Drive")


def _load_draft_from_drive(db: Session, user: User, draft: ContentDraft) -> str | None:
    """
    Load draft content from Google Drive.

    Returns the content string, or None if Drive load fails.
    """
    if not draft.drive_file_id:
        return None

    # Get Google Drive connection
    drive_connection = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user.id,
            SocialConnection.platform == "google_drive",
            SocialConnection.is_active.is_(True),
        )
        .first()
    )

    if not drive_connection:
        logger.debug("User %s has no Drive connection for loading draft", user.id)
        return None

    # Load from Drive
    storage = StorageService(
        access_token=drive_connection.access_token,
        refresh_token=drive_connection.refresh_token,
        encrypted=True,
        expires_at=drive_connection.token_expires_at,
    )

    draft_data = storage.load_draft(file_id=draft.drive_file_id)

    if draft_data and "content" in draft_data:
        return draft_data["content"]

    return None
