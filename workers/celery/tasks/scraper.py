"""
LinkedIn scrape task — syncs real posts (with mock fallback) and chains to
brand profile analysis when enough posts are available.

Flow:
  scrape_linkedin_posts(user_id)
    → linkedin_service.sync_real_posts(db, user)        [PATH A/B/MOCK auto-selected]
    → if result["ready_for_analysis"]:
        analyze_brand_profile.delay(user_id)            [fires in parallel, non-blocking]
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
    raise RuntimeError("Could not resolve apps/api from scraper task path")


@celery_app.task(
    name="workers.celery.tasks.scraper.scrape_linkedin_posts",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def scrape_linkedin_posts(self, user_id: str) -> dict:
    """
    Syncs LinkedIn posts for a user, then triggers brand profile analysis
    if the user has enough posts.

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
    from app.services import linkedin_service

    logger.info("scrape_linkedin_posts started user_id=%s", user_id)

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.error("scrape_linkedin_posts: user not found user_id=%s", user_id)
            return {
                "status": "error",
                "user_id": user_id,
                "message": "User not found",
            }

        # sync_real_posts is async — run it via asyncio.run() (Python 3.10+ safe)
        result = asyncio.run(
            linkedin_service.sync_real_posts(db, user)
        )

        logger.info(
            "scrape_linkedin_posts: sync complete path=%s synced=%d total=%d user_id=%s",
            result.get("sync_path"),
            result.get("synced_posts", 0),
            result.get("total_posts", 0),
            user_id,
        )

        # Chain brand profile analysis if we have enough posts
        if result.get("ready_for_analysis"):
            from workers.celery.tasks.brand_profile import analyze_brand_profile
            analyze_brand_profile.delay(user_id)
            logger.info(
                "scrape_linkedin_posts: queued analyze_brand_profile user_id=%s", user_id
            )

        return {
            "status": "completed",
            "user_id": user_id,
            "synced_posts": result.get("synced_posts"),
            "total_posts": result.get("total_posts"),
            "last_synced_at": (
                result["last_synced_at"].isoformat()
                if result.get("last_synced_at") and hasattr(result["last_synced_at"], "isoformat")
                else str(result.get("last_synced_at"))
            ),
            "sync_path": result.get("sync_path"),
            "ready_for_analysis": result.get("ready_for_analysis"),
            "message": result.get("message"),
        }

    except Exception as exc:
        logger.exception("scrape_linkedin_posts failed user_id=%s", user_id)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()


# ── Periodic fan-out: sync all active LinkedIn users ──────────────────────────

@celery_app.task(
    name="workers.celery.tasks.scraper.sync_all_linkedin_users",
    bind=True,
)
def sync_all_linkedin_users(self) -> dict:
    """
    Beat-scheduled task that fans out a scrape_linkedin_posts task for every
    user with an active LinkedIn connection.

    Runs at 3am UTC daily when ENABLE_LINKEDIN_SYNC=true.
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.social_connection import SocialConnection

    logger.info("sync_all_linkedin_users: starting fan-out")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        connections = (
            db.query(SocialConnection)
            .filter(
                SocialConnection.platform == "linkedin",
                SocialConnection.is_active == True,  # noqa: E712
            )
            .all()
        )
        user_ids = [c.user_id for c in connections]
        logger.info("sync_all_linkedin_users: queuing %d users", len(user_ids))

        for uid in user_ids:
            scrape_linkedin_posts.delay(uid)

        return {"status": "queued", "users_queued": len(user_ids)}
    finally:
        db.close()

