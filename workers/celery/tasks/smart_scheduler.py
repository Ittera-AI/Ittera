"""Smart Scheduler - AI-powered optimal timing for content publishing.

Integrates the TimingPredictionEngine with the scheduling system to:
- Automatically suggest optimal times for scheduled content
- Reschedule content based on predicted performance
- Batch schedule multiple posts at optimal times
- Handle timezone and constraint preferences

Features:
- Uses historical performance + AI predictions
- Respects user constraints (business hours, days)
- Provides confidence scores for recommendations
- Batch optimization for content calendars
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from workers.celery.app import celery_app
from app.db.session import SessionLocal
from app.models.content_draft import ContentDraft
from app.models.user import User
from app.services import content_service

# Import timing prediction engine
from iterra_ai.predictions import TimingPredictionEngine, TimingInput

logger = logging.getLogger(__name__)


def get_optimal_publish_time(
    content: str,
    platform: str,
    user_id: str,
    timezone: str = "UTC",
    earliest: datetime | None = None,
    latest: datetime | None = None,
    allowed_days: list[str] | None = None,
    allowed_hours_start: int = 8,
    allowed_hours_end: int = 18,
) -> dict[str, Any]:
    """
    Get AI-predicted optimal publish time for content.
    
    Args:
        content: The content to schedule
        platform: Target platform (linkedin, twitter, etc.)
        user_id: User ID for historical context
        timezone: User's timezone
        earliest: Earliest allowed time
        latest: Latest allowed time
        allowed_days: Days of week allowed (mon, tue, etc.)
        allowed_hours_start: Start of allowed hours
        allowed_hours_end: End of allowed hours
        
    Returns:
        Dict with optimal_time, confidence, alternatives
    """
    db = SessionLocal()
    
    try:
        # Get user's historical posting data
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found for optimal timing")
            return _fallback_timing(platform, timezone, earliest, latest)
        
        # Build historical posts data for context
        historical_posts = _get_historical_timing_data(db, user_id, limit=100)
        
        # Create prediction input
        input_data = TimingInput(
            content=content,
            platform=platform,
            timezone=timezone,
            author_historical_posts=historical_posts,
            allowed_days=allowed_days or ["mon", "tue", "wed", "thu", "fri"],
            allowed_hours_start=allowed_hours_start,
            allowed_hours_end=allowed_hours_end,
        )
        
        # Get prediction from AI engine
        engine = TimingPredictionEngine()
        prediction = engine.predict(input_data)
        
        # Adjust optimal time if constraints provided
        optimal_time = prediction.optimal_time
        
        if earliest and optimal_time < earliest:
            # Find next best time after earliest
            for slot in prediction.alternative_slots:
                slot_time = _convert_slot_to_datetime(slot, timezone)
                if slot_time >= earliest:
                    optimal_time = slot_time
                    break
        
        if latest and optimal_time > latest:
            # Find best time before latest
            for slot in sorted(prediction.alternative_slots, 
                              key=lambda s: s.score, reverse=True):
                slot_time = _convert_slot_to_datetime(slot, timezone)
                if slot_time <= latest:
                    optimal_time = slot_time
                    break
        
        return {
            "optimal_time": optimal_time.isoformat(),
            "confidence_score": prediction.confidence_score,
            "alternative_slots": [
                {
                    "day": s.day,
                    "hour": s.hour,
                    "score": s.score,
                    "predicted_engagement_rate": s.predicted_engagement_rate,
                }
                for s in prediction.alternative_slots[:3]
            ],
            "best_days": prediction.best_days,
            "best_hours": prediction.best_hours,
            "reasoning": _generate_timing_reasoning(prediction),
        }
        
    except Exception as e:
        logger.error(f"Error getting optimal timing: {e}")
        return _fallback_timing(platform, timezone, earliest, latest)
    finally:
        db.close()


def _get_historical_timing_data(db: Session, user_id: str, limit: int = 100) -> list[dict]:
    """Get user's historical posts with timing and performance data."""
    from app.models.post import Post
    
    posts = (
        db.query(Post)
        .filter(
            Post.user_id == user_id,
            Post.published_at.isnot(None),
            Post.engagement_rate > 0,
        )
        .order_by(Post.published_at.desc())
        .limit(limit)
        .all()
    )
    
    DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    
    return [
        {
            "day": DAY_NAMES[p.published_at.weekday()],
            "hour": p.published_at.hour,
            "engagement_rate": p.engagement_rate,
            "platform": p.platform,
        }
        for p in posts
    ]


def _convert_slot_to_datetime(slot, timezone: str) -> datetime:
    """Convert a time slot to a datetime."""
    DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    
    now = datetime.now()
    target_day = DAYS.get(slot.day, 0)
    
    # Find next occurrence of this day
    days_ahead = target_day - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    
    target_date = now + timedelta(days=days_ahead)
    return target_date.replace(hour=slot.hour, minute=0, second=0, microsecond=0)


def _generate_timing_reasoning(prediction) -> str:
    """Generate human-readable reasoning for the optimal time."""
    patterns = prediction.detected_patterns
    
    reasons = []
    for pattern in patterns[:2]:
        reasons.append(pattern.description)
    
    if not reasons:
        return f"Based on {prediction.platform} best practices and your historical performance."
    
    return " ".join(reasons)


def _fallback_timing(
    platform: str,
    timezone: str,
    earliest: datetime | None,
    latest: datetime | None,
) -> dict[str, Any]:
    """Fallback timing when AI prediction fails."""
    
    # Platform defaults
    platform_defaults = {
        "linkedin": {"best_days": ["tue", "wed", "thu"], "best_hours": [9, 12, 17]},
        "twitter": {"best_days": ["tue", "wed", "thu"], "best_hours": [9, 12, 18]},
        "instagram": {"best_days": ["tue", "wed", "thu"], "best_hours": [11, 13, 19]},
        "facebook": {"best_days": ["wed", "thu", "fri"], "best_hours": [13, 15]},
    }
    
    defaults = platform_defaults.get(platform, platform_defaults["linkedin"])
    
    # Find next best time
    now = datetime.now()
    target_time = now + timedelta(days=1)
    target_time = target_time.replace(hour=defaults["best_hours"][0], minute=0)
    
    if earliest and target_time < earliest:
        target_time = earliest
    if latest and target_time > latest:
        target_time = latest
    
    return {
        "optimal_time": target_time.isoformat(),
        "confidence_score": 0.5,
        "alternative_slots": [],
        "best_days": defaults["best_days"],
        "best_hours": defaults["best_hours"],
        "reasoning": f"Based on {platform} general best practices (AI prediction unavailable).",
        "fallback": True,
    }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def suggest_optimal_schedule(self, draft_id: str) -> dict[str, Any]:
    """
    Celery task to suggest optimal schedule for a draft.
    
    Analyzes content and returns recommended publish time with confidence.
    """
    db = SessionLocal()
    
    try:
        draft = db.query(ContentDraft).filter(ContentDraft.id == draft_id).first()
        if not draft:
            logger.error(f"Draft {draft_id} not found")
            return {"error": "Draft not found"}
        
        result = get_optimal_publish_time(
            content=draft.content or "",
            platform=draft.platform,
            user_id=draft.user_id,
        )
        
        logger.info(f"Optimal timing for draft {draft_id}: {result['optimal_time']}")
        return result
        
    except Exception as exc:
        logger.error(f"Error suggesting schedule: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def auto_schedule_draft(self, draft_id: str, confidence_threshold: float = 0.7) -> dict[str, Any]:
    """
    Automatically schedule a draft at the optimal time if confidence is high.
    
    Only schedules if confidence >= threshold.
    """
    db = SessionLocal()
    
    try:
        draft = db.query(ContentDraft).filter(ContentDraft.id == draft_id).first()
        if not draft:
            return {"error": "Draft not found"}
        
        # Get optimal timing
        timing = get_optimal_publish_time(
            content=draft.content or "",
            platform=draft.platform,
            user_id=draft.user_id,
        )
        
        if timing.get("confidence_score", 0) < confidence_threshold:
            return {
                "draft_id": draft_id,
                "scheduled": False,
                "reason": "Confidence below threshold",
                "confidence": timing.get("confidence_score"),
                "suggested_time": timing.get("optimal_time"),
            }
        
        # Schedule the draft
        optimal_time = datetime.fromisoformat(timing["optimal_time"])
        
        content_service.schedule_draft(
            db=db,
            draft_id=draft_id,
            scheduled_for=optimal_time,
        )
        
        logger.info(f"Auto-scheduled draft {draft_id} for {optimal_time}")
        
        return {
            "draft_id": draft_id,
            "scheduled": True,
            "scheduled_for": timing["optimal_time"],
            "confidence": timing["confidence_score"],
            "reasoning": timing.get("reasoning"),
        }
        
    except Exception as exc:
        logger.error(f"Error auto-scheduling: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task
def batch_optimize_schedule(draft_ids: list[str]) -> dict[str, Any]:
    """
    Optimize scheduling for multiple drafts to spread them optimally.
    
    Ensures posts are spaced out and scheduled at best times.
    """
    results = {
        "optimized": [],
        "failed": [],
        "total": len(draft_ids),
    }
    
    scheduled_times = set()
    
    for draft_id in draft_ids:
        try:
            # Get optimal time
            timing = suggest_optimal_schedule(draft_id)
            
            if "error" in timing:
                results["failed"].append({"draft_id": draft_id, "error": timing["error"]})
                continue
            
            optimal_time = datetime.fromisoformat(timing["optimal_time"])
            
            # Check for conflicts (ensure 2 hour minimum spacing)
            while any(abs((optimal_time - st).total_seconds()) < 7200 for st in scheduled_times):
                optimal_time += timedelta(hours=2)
            
            scheduled_times.add(optimal_time)
            
            # Schedule it
            db = SessionLocal()
            try:
                content_service.schedule_draft(
                    db=db,
                    draft_id=draft_id,
                    scheduled_for=optimal_time,
                )
                results["optimized"].append({
                    "draft_id": draft_id,
                    "scheduled_for": optimal_time.isoformat(),
                    "confidence": timing.get("confidence_score"),
                })
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error optimizing draft {draft_id}: {e}")
            results["failed"].append({"draft_id": draft_id, "error": str(e)})
    
    return results


@celery_app.task
def daily_schedule_optimization() -> dict[str, Any]:
    """
    Daily task to review and optimize upcoming scheduled posts.
    
    Checks if there are better times available and reschedules if confidence
    improvement is significant.
    """
    db = SessionLocal()
    
    try:
        # Get drafts scheduled for next 48 hours
        upcoming = (
            db.query(ContentDraft)
            .filter(
                ContentDraft.status == "scheduled",
                ContentDraft.scheduled_for >= datetime.utcnow(),
                ContentDraft.scheduled_for <= datetime.utcnow() + timedelta(hours=48),
            )
            .all()
        )
        
        rescheduled = []
        kept = []
        
        for draft in upcoming:
            try:
                # Get new optimal timing
                new_timing = get_optimal_publish_time(
                    content=draft.content or "",
                    platform=draft.platform,
                    user_id=draft.user_id,
                    earliest=draft.scheduled_for - timedelta(hours=2),
                    latest=draft.scheduled_for + timedelta(hours=2),
                )
                
                new_time = datetime.fromisoformat(new_timing["optimal_time"])
                current_time = draft.scheduled_for
                
                # Only reschedule if significant improvement
                if new_timing["confidence_score"] > 0.8 and abs((new_time - current_time).total_seconds()) > 1800:
                    draft.scheduled_for = new_time
                    db.commit()
                    rescheduled.append({
                        "draft_id": draft.id,
                        "old_time": current_time.isoformat(),
                        "new_time": new_time.isoformat(),
                        "confidence": new_timing["confidence_score"],
                    })
                else:
                    kept.append({
                        "draft_id": draft.id,
                        "scheduled_for": current_time.isoformat(),
                    })
                    
            except Exception as e:
                logger.error(f"Error optimizing draft {draft.id}: {e}")
        
        return {
            "reviewed": len(upcoming),
            "rescheduled": rescheduled,
            "kept": kept,
        }
        
    finally:
        db.close()
