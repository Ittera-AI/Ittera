"""
Celery task: data_cleanup

Scheduled task for enforcing data retention policies.
Runs weekly to clean up old data based on user preferences.

Features:
  - Respects user-defined retention periods
  - Never deletes from user's Google Drive
  - Dry run mode for testing
  - Detailed reporting
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    raise RuntimeError("Could not resolve apps/api from data_cleanup task path")


@celery_app.task(
    name="workers.celery.tasks.data_cleanup.run_retention_cleanup",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes between retries
    time_limit=3600,  # 1 hour hard limit
    soft_time_limit=3000,  # 50 minute soft limit
)
def run_retention_cleanup(
    self,
    user_id: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """
    Run data retention cleanup for all users or a specific user.

    This task runs weekly (scheduled via Celery Beat) to enforce
    data retention policies. Users with data_retention_days=0 are skipped
    (they have opted to never delete data).

    Args:
        user_id: Optional user ID to clean specific user only
        dry_run: If True, only report what would be deleted without deleting
        force: If True, clean even if user has disabled auto-delete

    Returns:
        Dict with detailed cleanup results
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.user import User
    from app.services.data_retention import DataRetentionService

    logger.info(
        "Starting data retention cleanup (user=%s, dry_run=%s, force=%s)",
        user_id or "all",
        dry_run,
        force,
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    results = {
        "processed_users": 0,
        "skipped_users": 0,
        "total_drafts_deleted": 0,
        "total_analytics_deleted": 0,
        "errors": [],
        "user_results": [],
        "dry_run": dry_run,
    }

    try:
        # Build query
        query = db.query(User).filter(User.is_active == True)

        if user_id:
            query = query.filter(User.id == user_id)
        else:
            # Skip users with no retention policy set (use system default)
            # Or users who have disabled auto-delete
            if not force:
                query = query.filter(
                    User.data_retention_days.isnot(None),
                    User.data_retention_days > 0,
                )

        users = query.all()

        logger.info("Found %d users to process", len(users))

        for user in users:
            try:
                # Skip users with retention disabled (0 = never delete)
                if not force and user.data_retention_days == 0:
                    logger.debug("Skipping user %s (retention disabled)", user.id)
                    results["skipped_users"] += 1
                    continue

                service = DataRetentionService(db)
                user_result = service.clean_user_data(user, dry_run=dry_run)

                results["processed_users"] += 1
                results["user_results"].append({
                    "user_id": user.id,
                    "email": user.email,
                    "retention_days": user.data_retention_days,
                    "result": user_result,
                })

                # Accumulate totals (only if not dry run)
                if not dry_run:
                    drafts_result = user_result.get("drafts", {})
                    analytics_result = user_result.get("analytics", {})
                    results["total_drafts_deleted"] += drafts_result.get("deleted", 0)
                    results["total_analytics_deleted"] += analytics_result.get("deleted", 0)

            except Exception as e:
                logger.exception("Failed to process user %s: %s", user.id, e)
                results["errors"].append(f"user_{user.id}: {str(e)}")
                # Continue with next user

        # Commit all changes
        if not dry_run:
            db.commit()

        logger.info(
            "Data retention cleanup complete: %d users processed, %d drafts deleted, %d analytics deleted",
            results["processed_users"],
            results["total_drafts_deleted"],
            results["total_analytics_deleted"],
        )

        return results

    except Exception as e:
        db.rollback()
        logger.exception("Data retention cleanup task failed: %s", e)
        raise self.retry(exc=e, countdown=600)

    finally:
        db.close()


@celery_app.task(
    name="workers.celery.tasks.data_cleanup.get_retention_summary",
    bind=True,
    max_retries=2,
)
def get_retention_summary(self, user_id: str) -> dict:
    """
    Get retention summary for a specific user.

    Args:
        user_id: User ID to get summary for

    Returns:
        Dict with retention summary
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.user import User
    from app.services.data_retention import DataRetentionService

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}

        service = DataRetentionService(db)
        summary = service.get_retention_summary(user)

        return summary

    except Exception as e:
        logger.exception("Failed to get retention summary: %s", e)
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()
