"""
Twitter sync task — syncs real tweets and chains to brand profile analysis
when enough posts are available.

Flow:
  sync_twitter_posts(user_id)
    → twitter_sync_service.sync_posts(db, user)
    → if result.ready_for_analysis:
        analyze_brand_profile.delay(user_id)   [fires in parallel, non-blocking]

Mirrors the scrape_linkedin_posts task pattern for consistency.
"""

from __future__ import annotations

import asyncio
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
    raise RuntimeError("Could not resolve apps/api from twitter_sync task path")


@celery_app.task(
    name="workers.celery.tasks.twitter_sync.sync_twitter_posts",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def sync_twitter_posts(self, user_id: str) -> dict:
    """
    Syncs Twitter posts for a user, then triggers brand profile analysis
    if the user has enough posts across all platforms.

    Args:
        user_id: The user's UUID string.

    Returns:
        dict with status, synced_posts, total_posts, sync_path, ready_for_analysis.
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.user import User
    from app.services.twitter_service import twitter_sync_service

    logger.info("sync_twitter_posts started user_id=%s", user_id)

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.error("sync_twitter_posts: user not found user_id=%s", user_id)
            return {
                "status": "error",
                "user_id": user_id,
                "message": "User not found",
            }

        # sync_posts is async — run it via asyncio.run()
        result = asyncio.run(twitter_sync_service.sync_posts(db, user))

        logger.info(
            "sync_twitter_posts: sync complete path=%s synced=%d total=%d user_id=%s",
            result.sync_path,
            result.synced_posts,
            result.total_posts,
            user_id,
        )

        # Chain brand profile analysis if we have enough posts
        if result.ready_for_analysis:
            from workers.celery.tasks.brand_profile import analyze_brand_profile

            analyze_brand_profile.delay(user_id)
            logger.info(
                "sync_twitter_posts: queued analyze_brand_profile user_id=%s", user_id
            )

        return {
            "status": "completed",
            "user_id": user_id,
            "synced_posts": result.synced_posts,
            "total_posts": result.total_posts,
            "last_synced_at": (
                result.last_synced_at.isoformat()
                if result.last_synced_at and hasattr(result.last_synced_at, "isoformat")
                else str(result.last_synced_at)
            ),
            "sync_path": result.sync_path,
            "ready_for_analysis": result.ready_for_analysis,
            "message": result.message,
        }

    except Exception as exc:
        logger.exception("sync_twitter_posts failed user_id=%s", user_id)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()


# ── Periodic fan-out: sync all active Twitter users ───────────────────────────


@celery_app.task(
    name="workers.celery.tasks.twitter_sync.sync_all_twitter_users",
    bind=True,
)
def sync_all_twitter_users(self) -> dict:
    """
    Beat-scheduled task that fans out a sync_twitter_posts task for every
    user with an active Twitter connection.

    Can be added to BEAT_SCHEDULE for periodic syncs.
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.social_connection import SocialConnection

    logger.info("sync_all_twitter_users: starting fan-out")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        connections = (
            db.query(SocialConnection)
            .filter(
                SocialConnection.platform == "twitter",
                SocialConnection.is_active == True,  # noqa: E712
            )
            .all()
        )
        user_ids = [c.user_id for c in connections]
        logger.info("sync_all_twitter_users: queuing %d users", len(user_ids))

        for uid in user_ids:
            sync_twitter_posts.delay(uid)

        return {"status": "queued", "users_queued": len(user_ids)}
    finally:
        db.close()
