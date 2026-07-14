"""
Celery tasks: learning_loop (Loop Orchestrator)

Sequences the asynchronous self-learning content loop (design B.5):

    publish -> on_post_published
            -> (delayed) pull_and_analyze_post  [sync metrics -> auto-analyze]
            -> (debounced) synthesize_user_insights  [memory + fact promotion]

and the steady-state heartbeat ``run_insight_cycle_all_users`` that fans synthesis
out across every active ``(user, platform)`` in case event-driven runs were missed.

Design notes honored here:
  - Idempotency: re-delivery of ``on_post_published`` simply re-schedules the same
    windows; synthesis is guarded by ``_has_new_analyses_since_last_synthesis`` and
    debounced by a 60s countdown so a burst of publishes collapses into one run.
  - Stop-at-failing-stage: each stage commits its own work in its own session, so a
    failing stage stops the chain while every stage that committed before it persists.
  - Per-(user, platform) isolation: the cadence fan-out enqueues an independent task
    per pair so one pair's failure never aborts the rest.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from workers.celery.app import celery_app

logger = logging.getLogger(__name__)

# Fixed positive post-publish windows (seconds) used when settings do not provide
# them: 1 hour, 24 hours, 72 hours. Metrics need time to accumulate before a pull.
DEFAULT_PULL_DELAYS = (3600, 86400, 259200)

# Debounce window for synthesis: a batch of publishes for the same (user, platform)
# within this window collapses into a single synthesis run (design B.6).
SYNTHESIS_DEBOUNCE_COUNTDOWN = 60

# Only fan the cadence out across posts published within this window.
CYCLE_CUTOFF_DAYS = 90


def _resolve_api_root() -> Path:
    """Locate apps/api whether the worker runs from repo root or /app in Docker."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "apps" / "api"
        if candidate.is_dir() and (candidate / "main.py").is_file():
            return candidate
    raise RuntimeError("Could not resolve apps/api from learning_loop task path")


def _bootstrap_path() -> None:
    """Ensure apps/api is importable under the worker's sys.path."""
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))


def _session():
    """Open a new DB session, bootstrapping the apps/api import path first.

    Reuses the app's shared, pooled sessionmaker (``app.db.session.SessionLocal``)
    rather than building a throwaway engine per task call, so the worker shares one
    engine with the API and respects test-time rebinding of the sessionmaker.
    """
    _bootstrap_path()
    from app.db.session import SessionLocal

    return SessionLocal()


def _pull_delays() -> list[int]:
    """
    Configured fixed positive post-publish delays (seconds).

    Reads ``settings.LEARNING_LOOP_PULL_DELAYS`` when present, otherwise falls back
    to :data:`DEFAULT_PULL_DELAYS`. Non-positive delays are skipped so a misconfigured
    ``0``/negative window never schedules an immediate pull (requirement 2.3).
    """
    _bootstrap_path()
    from app.config import settings

    configured = getattr(settings, "LEARNING_LOOP_PULL_DELAYS", None) or list(
        DEFAULT_PULL_DELAYS
    )
    return [int(d) for d in configured if d is not None and int(d) > 0]


def _learning_loop_enabled() -> bool:
    """Defensive gate on the loop feature flag (full gating lives in task 10.2)."""
    _bootstrap_path()
    from app.config import settings

    return bool(getattr(settings, "ENABLE_LEARNING_LOOP", False))


@celery_app.task(
    name="workers.celery.tasks.learning_loop.on_post_published",
    bind=True,
)
def on_post_published(self, post_id: str) -> dict:
    """
    Entry point fired by the Publication Bridge right after publish.

    Metrics need time to accumulate, so this schedules delayed
    ``pull_and_analyze_post`` passes at each configured positive delay rather than
    running now. Idempotent: a re-delivered publish notification simply re-schedules
    the same windows (requirement 2.3).
    """
    if not _learning_loop_enabled():
        logger.debug("Learning loop disabled; skipping on_post_published for %s", post_id)
        return {"skipped": True, "reason": "learning_loop_disabled", "post_id": post_id}

    delays = _pull_delays()
    for delay in delays:
        pull_and_analyze_post.apply_async(kwargs={"post_id": post_id}, countdown=delay)

    logger.info("Scheduled %d delayed pulls for post %s", len(delays), post_id)
    return {"post_id": post_id, "scheduled_pulls": len(delays)}


@celery_app.task(
    name="workers.celery.tasks.learning_loop.pull_and_analyze_post",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def pull_and_analyze_post(self, post_id: str) -> dict:
    """
    Chain one pass: pull metrics (Metrics Sync Agent) -> auto-analyze
    (EngagementCoach), then enqueue debounced synthesis for the owning
    ``(user, platform)``.

    Stop-at-failing-stage: ``sync_single_post`` and ``analyze_post`` each commit in
    their own session, so any stage that completes before a failure persists. A
    failure stops the chain (no synthesis is enqueued) and the task retries; the
    fresh-analysis guard in ``analyze_post`` keeps the retry from double-charging.
    """
    db = _session()
    try:
        from app.models.post import Post
        from app.models.user import User
        from app.services import analytics_service
        from workers.celery.tasks.performance_sync import sync_single_post

        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return {"error": "post_not_found", "post_id": post_id}

        user = db.query(User).filter(User.id == post.user_id).first()
        if not user:
            return {"error": "user_not_found", "post_id": post_id}

        user_id = post.user_id
        platform = post.platform

        # Stage 1: pull metrics (platform-agnostic; commits its own session).
        sync_single_post(post_id)

        # Stage 2: auto-analysis — was manual-only. Idempotent via the fresh-analysis
        # (<30d) guard, and emits exactly one auto_analysis_complete event when it runs.
        analytics_service.analyze_post(db, user, post_id)

        # Stage 3: debounced synthesis for this user+platform (B.6).
        synthesize_user_insights.apply_async(
            kwargs={"user_id": user_id, "platform": platform},
            countdown=SYNTHESIS_DEBOUNCE_COUNTDOWN,
        )

        return {"post_id": post_id, "status": "analyzed"}

    except Exception as exc:
        # Prior committed stages persist; the chain stops here and retries.
        logger.exception("pull_and_analyze_post failed for %s: %s", post_id, exc)
        raise self.retry(exc=exc)

    finally:
        db.close()


@celery_app.task(
    name="workers.celery.tasks.learning_loop.synthesize_user_insights",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def synthesize_user_insights(self, user_id: str, platform: str) -> dict:
    """
    Insight Memory Agent + Fact Promotion Agent for one ``(user, platform)``.

    Guarded by ``_has_new_analyses_since_last_synthesis`` so a run with no new
    analyses since the last insight update is a no-op (idempotency, B.6). On success
    it upserts the versioned ``LearnedInsight`` then promotes its candidate facts.
    """
    db = _session()
    try:
        from app.models.user import User
        from app.services import fact_promotion_service, learning_insight_service
        from app.services.learning_insight_service import (
            _has_new_analyses_since_last_synthesis,
        )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"skipped": True, "reason": "user_not_found"}

        # Idempotency guard: nothing new to synthesize -> leave prior memory intact.
        if not _has_new_analyses_since_last_synthesis(db, user, platform):
            return {"skipped": True, "reason": "no_new_analyses"}

        insight = learning_insight_service.synthesize_user_insights(db, user, platform)
        if insight:
            fact_promotion_service.promote_facts(
                db, user, platform, insight.candidate_facts
            )

        db.commit()
        return {
            "user_id": user_id,
            "platform": platform,
            "version": insight.version if insight else None,
        }

    except Exception as exc:
        # Synthesis failure retains the prior LearnedInsight unchanged (requirement 3.3).
        db.rollback()
        logger.exception(
            "synthesize_user_insights failed for (%s, %s): %s", user_id, platform, exc
        )
        raise self.retry(exc=exc)

    finally:
        db.close()


@celery_app.task(
    name="workers.celery.tasks.learning_loop.run_insight_cycle_all_users",
    bind=True,
)
def run_insight_cycle_all_users(self) -> dict:
    """
    Beat-scheduled cadence: fan synthesis out across every active ``(user, platform)``.

    This is the steady-state heartbeat for runs that event-driven passes may have
    missed. Each pair is enqueued as an independent ``synthesize_user_insights`` task
    so a failure for one ``(user, platform)`` never prevents synthesis for any other
    (requirement 8.4); the per-task guard skips pairs with no new analyses.
    """
    if not _learning_loop_enabled():
        logger.debug("Learning loop disabled; skipping run_insight_cycle_all_users")
        return {"skipped": True, "reason": "learning_loop_disabled"}

    db = _session()
    try:
        from app.models.post import Post

        cutoff = datetime.now(timezone.utc) - timedelta(days=CYCLE_CUTOFF_DAYS)

        # Distinct active (user, platform) pairs from learnable (published) posts.
        pairs = (
            db.query(Post.user_id, Post.platform)
            .filter(
                Post.platform_post_id.isnot(None),
                Post.published_at >= cutoff,
            )
            .distinct()
            .all()
        )

        scheduled = 0
        failed = 0
        for user_id, platform in pairs:
            try:
                synthesize_user_insights.apply_async(
                    kwargs={"user_id": user_id, "platform": platform}
                )
                scheduled += 1
            except Exception:
                # Isolate per-(user, platform) enqueue failures from the rest.
                logger.exception(
                    "Failed to enqueue synthesis for (%s, %s)", user_id, platform
                )
                failed += 1

        logger.info(
            "Insight cycle fan-out: %d pairs, %d scheduled, %d failed",
            len(pairs),
            scheduled,
            failed,
        )
        return {"pairs": len(pairs), "scheduled": scheduled, "failed": failed}

    finally:
        db.close()
