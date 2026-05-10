"""LinkedIn scrape task — persists mock posts via API linkedin_service (real pipeline TBD)."""

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
    raise RuntimeError("Could not resolve apps/api from scraper task path")


@celery_app.task(name="workers.celery.tasks.scraper.scrape_linkedin_posts", bind=True, max_retries=3)
def scrape_linkedin_posts(self, user_id: str):
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.user import User
    from app.services import linkedin_service

    logger.info("LinkedIn scrape started user_id=%s", user_id)
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            return {
                "status": "error",
                "user_id": user_id,
                "message": "User not found",
            }
        result = linkedin_service.sync_mock_posts(db, user)
        return {
            "status": "completed",
            "user_id": user_id,
            "synced_posts": result.get("synced_posts"),
            "last_synced_at": result.get("last_synced_at").isoformat()
            if result.get("last_synced_at")
            else None,
            "message": result.get("message"),
        }
    except Exception as exc:
        logger.exception("scrape_linkedin_posts failed user_id=%s", user_id)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
