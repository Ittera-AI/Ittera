"""
Celery task: analyze_brand_profile

Triggered automatically after a successful LinkedIn post sync (from scraper.py task)
when the user has at least MIN_POSTS_FOR_ANALYSIS posts.

Runs BrandProfileEngine in the Celery worker process (not the API server),
then persists the result via brand_profile_service.generate_profile_from_data().

This keeps heavy AI inference out of the request/response cycle.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from workers.celery.app import celery_app

logger = logging.getLogger(__name__)


def _resolve_api_root() -> Path:
    """Locate apps/api whether the worker runs from repo root or /app in Docker."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "apps" / "api"
        if candidate.is_dir() and (candidate / "main.py").is_file():
            return candidate
    raise RuntimeError("Could not resolve apps/api from brand_profile task path")


@celery_app.task(
    name="workers.celery.tasks.brand_profile.analyze_brand_profile",
    bind=True,
    max_retries=2,
    default_retry_delay=60,  # 1 minute between retries (LLM calls can be slow)
)
def analyze_brand_profile(self, user_id: str) -> dict:
    """
    Run BrandProfileEngine for a user and persist the output.

    Args:
        user_id: The user's UUID string.

    Returns:
        dict with status, confidence_score, analysis_based_on_posts.
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.post import Post
    from app.models.user import User
    from app.services import brand_profile_service

    logger.info("analyze_brand_profile started user_id=%s", user_id)

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.error("analyze_brand_profile: user not found user_id=%s", user_id)
            return {"status": "error", "user_id": user_id, "message": "User not found"}

        posts = (
            db.query(Post)
            .filter(Post.user_id == user_id, Post.platform == "linkedin")
            .all()
        )

        if not posts:
            logger.warning(
                "analyze_brand_profile: no posts found — skipping user_id=%s", user_id
            )
            return {
                "status": "skipped",
                "user_id": user_id,
                "message": "No posts available for analysis.",
            }

        logger.info(
            "analyze_brand_profile: running engine on %d posts user_id=%s",
            len(posts),
            user_id,
        )

        # Run the engine (may be mock if ANTHROPIC_API_KEY not set)
        engine_output = brand_profile_service._run_engine(user, posts)

        # Persist result
        result = brand_profile_service.generate_profile_from_data(
            db, user, engine_output, posts=posts
        )

        logger.info(
            "analyze_brand_profile: complete confidence=%.2f posts=%d user_id=%s",
            result.get("ai_confidence_score", 0),
            result.get("analysis_based_on_posts", 0),
            user_id,
        )
        return {
            "status": "completed",
            "user_id": user_id,
            "ai_confidence_score": result.get("ai_confidence_score"),
            "analysis_based_on_posts": result.get("analysis_based_on_posts"),
            "profile_version": result.get("version"),
        }

    except Exception as exc:
        logger.exception("analyze_brand_profile failed user_id=%s", user_id)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
