from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.content_draft import ContentDraft
from app.models.user import User
from app.schemas.content import GenerateRequest, RepurposeRequest, ScheduleRequest, SuggestRequest
from app.services import brand_profile_service, trend_service

LIMITS = {"linkedin": 3000, "instagram": 2200, "twitter": 280}


def suggest(db: Session, user: User, payload: SuggestRequest) -> dict:
    trends = trend_service.get_trends_for_user(db, user)["trends"]
    base_topic = payload.topic or (trends[0]["topic"] if trends else user.niche or "content strategy")
    suggestions = [
        {
            "hook": f"Most teams misunderstand {base_topic}.",
            "angle": f"Explain the practical shift behind {base_topic}.",
            "format": "hot-take",
            "trend_tie": base_topic,
            "why_it_works": "It starts with tension and resolves into a useful operating principle.",
        },
        {
            "hook": f"A simple {base_topic} checklist:",
            "angle": "Turn the topic into a practical framework readers can save.",
            "format": "listicle",
            "trend_tie": base_topic,
            "why_it_works": "It is concrete, skimmable, and aligned with your analytical voice.",
        },
        {
            "hook": f"The quiet advantage of {base_topic} is not speed.",
            "angle": "Connect the trend to trust, review loops, and better decisions.",
            "format": "story",
            "trend_tie": base_topic,
            "why_it_works": "It gives your audience a more thoughtful take than the obvious trend post.",
        },
    ]
    return {"suggestions": suggestions}


def generate(db: Session, user: User, payload: GenerateRequest) -> dict:
    _require_brand_profile(db, user)
    seed = payload.suggestion.hook if payload.suggestion else payload.prompt
    content = (
        f"{seed}\n\n"
        f"Here is the practical version: {payload.prompt.strip()}\n\n"
        "The best content systems do three things well:\n"
        "1. Notice the signal before it becomes noisy.\n"
        "2. Shape the idea through a clear point of view.\n"
        "3. Review performance without losing the voice that made it work.\n\n"
        "That is how a content loop compounds."
    )
    draft = ContentDraft(
        user_id=user.id,
        platform=payload.platform,
        content=content,
        prompt_used=payload.prompt,
        trend_used=payload.trend_used,
        generation_model="mock-local",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return {
        "draft_id": draft.id,
        "content": draft.content,
        "word_count": len(draft.content.split()),
        "within_platform_limit": len(draft.content) <= LIMITS[payload.platform],
    }


def repurpose(db: Session, user: User, payload: RepurposeRequest) -> dict:
    draft = _draft(db, user, payload.draft_id)
    content = _repurposed_content(draft.content, payload.target_platform)
    versions = dict(draft.repurposed_versions or {})
    versions[payload.target_platform] = content
    draft.repurposed_versions = versions
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"draft_id": draft.id, "content": content, "platform": payload.target_platform}


def list_drafts(db: Session, user: User, status_filter: str | None = None) -> list[ContentDraft]:
    query = db.query(ContentDraft).filter(ContentDraft.user_id == user.id)
    if status_filter:
        query = query.filter(ContentDraft.status == status_filter)
    return query.order_by(ContentDraft.created_at.desc()).all()


def get_draft(db: Session, user: User, draft_id: str) -> ContentDraft:
    return _draft(db, user, draft_id)


def update_draft(db: Session, user: User, draft_id: str, payload) -> ContentDraft:
    draft = _draft(db, user, draft_id)
    for field in ("content", "status", "scheduled_for"):
        value = getattr(payload, field, None)
        if value is not None:
            setattr(draft, field, value)
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return draft


def publish_now(db: Session, user: User, draft_id: str) -> dict:
    draft = _draft(db, user, draft_id)
    now = datetime.now(timezone.utc)
    draft.status = "published"
    draft.published_at = now
    draft.platform_post_id = f"mock-published-{draft.id[:8]}"
    draft.publish_error = None
    db.commit()
    return {"platform_post_id": draft.platform_post_id, "published_at": now}


def schedule_post(db: Session, user: User, payload: ScheduleRequest) -> dict:
    if payload.scheduled_for <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Schedule time must be in the future")
    draft = _draft(db, user, payload.draft_id)
    draft.status = "scheduled"
    draft.scheduled_for = payload.scheduled_for
    draft.celery_task_id = f"mock-task-{draft.id[:8]}"
    db.commit()
    return {
        "celery_task_id": draft.celery_task_id,
        "scheduled_for": payload.scheduled_for,
        "suggested_times": suggested_times(),
    }


def cancel_schedule(db: Session, user: User, draft_id: str) -> dict:
    draft = _draft(db, user, draft_id)
    draft.status = "draft"
    draft.scheduled_for = None
    draft.celery_task_id = None
    db.commit()
    return {"status": "cancelled"}


def calendar_events(db: Session, user: User) -> list[dict]:
    events = []
    for draft in list_drafts(db, user):
        starts_at = draft.scheduled_for or draft.published_at
        if starts_at and draft.status in {"scheduled", "published"}:
            events.append(
                {
                    "id": draft.id,
                    "title": draft.content.splitlines()[0][:80],
                    "platform": draft.platform,
                    "status": draft.status,
                    "starts_at": starts_at,
                    "content": draft.content,
                }
            )
    return events


def suggested_times() -> list[datetime]:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return [now + timedelta(days=1, hours=9), now + timedelta(days=2, hours=12), now + timedelta(days=3, hours=9)]


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
