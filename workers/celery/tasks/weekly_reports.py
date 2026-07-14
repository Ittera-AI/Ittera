"""
Weekly learning report (Gap 6) — reimplemented on the Insight Memory Agent.

For each active user (a user with at least one published platform), this task reads
the active ``LearnedInsight`` per platform — synthesizing first when the insight is
missing or stale (older than 7 days) — and emails a digest via
``app/services/email.py``. It reuses the same active ``LearnedInsight`` version the
Context Assembler injects, so the weekly email and the prompt-injected learnings stay
consistent (no second synthesis path).

Design reference: design.md section B.5 ("Weekly report").

Requirements honored:
  - 6.1: read the active insight per platform for each active user and email a digest.
  - 6.2: synthesize first when a user's insight is stale (older than 7 days).
  - 6.3: skip users with no insight on any platform (no empty digest).
  - 6.4: derive the digest from the active LearnedInsight (summary / wins / recs).
  - 6.5: per-user failures are recorded and the loop continues to the next user.
  - 8.3: gated by ENABLE_LEARNING_LOOP (skip entirely when disabled).
"""

from __future__ import annotations

import logging
import sys
from datetime import timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from workers.celery.app import celery_app

logger = logging.getLogger(__name__)

# A LearnedInsight older than this is considered stale and re-synthesized first.
INSIGHT_STALE_DAYS = 7


def _resolve_api_root() -> Path:
    """Locate apps/api whether the worker runs from repo root or /app in Docker."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "apps" / "api"
        if candidate.is_dir() and (candidate / "main.py").is_file():
            return candidate
    raise RuntimeError("Could not resolve apps/api from weekly_reports task path")


def _bootstrap_path() -> None:
    """Ensure apps/api is importable under the worker's sys.path."""
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))


def _session():
    """Open a new DB session, bootstrapping the apps/api import path first."""
    _bootstrap_path()
    from app.config import settings

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def _learning_loop_enabled() -> bool:
    """Defensive gate on the loop feature flag (consistent with learning_loop.py)."""
    _bootstrap_path()
    from app.config import settings

    return bool(getattr(settings, "ENABLE_LEARNING_LOOP", False))


def _is_stale(insight, now) -> bool:
    """Whether an insight is missing or older than ``INSIGHT_STALE_DAYS``."""
    if insight is None:
        return True
    updated = getattr(insight, "updated_at", None)
    if updated is None:
        return True
    # Normalize to naive UTC: stored timestamps may be aware (Postgres) or naive.
    if updated.tzinfo is not None:
        from datetime import timezone

        updated = updated.astimezone(timezone.utc).replace(tzinfo=None)
    return updated < (now - timedelta(days=INSIGHT_STALE_DAYS))


def _insight_to_section(insight, platform: str) -> dict:
    """Project an active LearnedInsight into the digest section the email expects."""
    return {
        "platform": platform,
        "summary": insight.summary or "",
        "why_wins": list(insight.why_wins or []),
        "recommendations": list(insight.recommendations or []),
        "confidence": float(insight.confidence or 0.0),
        "based_on_posts": int(insight.based_on_posts or 0),
    }


@celery_app.task(
    name="workers.celery.tasks.weekly_reports.send_weekly_reports",
    bind=True,
    max_retries=2,
)
def send_weekly_reports(self):
    """Email a weekly learning digest to each active user (design B.5)."""
    if not _learning_loop_enabled():
        logger.debug("Learning loop disabled; skipping send_weekly_reports")
        return {"skipped": True, "reason": "learning_loop_disabled"}

    db = _session()
    try:
        from app.db.datetime_helpers import utc_now
        from app.models.post import Post
        from app.models.user import User
        from app.services import email as email_service
        from app.services import learning_insight_service

        now = utc_now()

        # Active users = active accounts that have at least one published post.
        user_ids = [
            row[0]
            for row in (
                db.query(Post.user_id)
                .join(User, User.id == Post.user_id)
                .filter(
                    Post.platform_post_id.isnot(None),
                    User.is_active.is_(True),
                )
                .distinct()
                .all()
            )
        ]

        emailed = 0
        skipped = 0
        failed = 0

        for user_id in user_ids:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    skipped += 1
                    continue

                # Platforms the user actually published on.
                platforms = [
                    row[0]
                    for row in (
                        db.query(Post.platform)
                        .filter(
                            Post.user_id == user_id,
                            Post.platform_post_id.isnot(None),
                        )
                        .distinct()
                        .all()
                    )
                ]

                sections: list[dict] = []
                for platform in platforms:
                    insight = learning_insight_service.get_active_insight(
                        db, user, platform
                    )
                    # 6.2: synthesize first when missing or stale (>7 days).
                    if _is_stale(insight, now):
                        learning_insight_service.synthesize_user_insights(
                            db, user, platform
                        )
                        insight = learning_insight_service.get_active_insight(
                            db, user, platform
                        )
                    if insight is not None:
                        sections.append(_insight_to_section(insight, platform))

                # 6.3: skip users with no insight on any platform (no empty digest).
                if not sections:
                    skipped += 1
                    continue

                # 6.1 / 6.4: email a digest derived from the active LearnedInsight.
                email_service.send_weekly_insight_email(
                    user.email, user.name, sections
                )
                emailed += 1

            except Exception:
                # 6.5: record the failure and continue with the remaining users.
                db.rollback()
                logger.exception("Weekly report failed for user %s", user_id)
                failed += 1

        logger.info(
            "Weekly reports: %d users, %d emailed, %d skipped, %d failed",
            len(user_ids),
            emailed,
            skipped,
            failed,
        )
        return {
            "users": len(user_ids),
            "emailed": emailed,
            "skipped": skipped,
            "failed": failed,
        }

    finally:
        db.close()
