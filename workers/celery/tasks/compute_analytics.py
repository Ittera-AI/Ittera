"""
Celery tasks: compute_analytics

Background jobs for pre-computing and caching analytics data.

Tasks:
  - compute_daily_snapshot: Generate daily analytics snapshot for a user
  - compute_all_users_snapshots: Generate snapshots for all active users
  - backfill_snapshots: Generate historical snapshots for date range

Schedule:
  - Daily at 1 AM UTC: compute_all_users_snapshots
"""

from __future__ import annotations

import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, distinct, func
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
    raise RuntimeError("Could not resolve apps/api from compute_analytics task path")


@celery_app.task(
    name="workers.celery.tasks.compute_analytics.compute_daily_snapshot",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=600,  # 10 minutes
)
def compute_daily_snapshot(self, user_id: str, snapshot_date: str | None = None) -> dict:
    """
    Compute and store daily analytics snapshot for a user.

    Args:
        user_id: User ID to compute snapshot for
        snapshot_date: Date string (YYYY-MM-DD) or None for today

    Returns:
        Dict with snapshot data and metadata
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.analytics_snapshot import DailyAnalyticsSnapshot
    from app.models.post import Post
    from app.models.post_analysis import PostAnalysis
    from app.models.user import User

    # Parse snapshot date
    if snapshot_date:
        target_date = date.fromisoformat(snapshot_date)
    else:
        target_date = date.today()

    logger.info("Computing daily snapshot for user %s, date %s", user_id, target_date)

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found", "user_id": user_id}

        # Define time boundaries for the snapshot date
        date_start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        date_end = date_start + timedelta(days=1)

        # Query posts for this user on this date
        posts_query = db.query(Post).filter(
            Post.user_id == user_id,
            Post.published_at >= date_start,
            Post.published_at < date_end,
        )
        posts = posts_query.all()

        if not posts:
            logger.debug("No posts for user %s on %s", user_id, target_date)
            # Still create a snapshot with zeros to indicate "no data"

        # Calculate aggregates
        posts_count = len(posts)
        total_likes = sum(p.likes or 0 for p in posts)
        total_comments = sum(p.comments or 0 for p in posts)
        total_shares = sum(p.shares or 0 for p in posts)
        total_impressions = sum(p.impressions or 0 for p in posts)

        # Calculate average engagement rate
        engagement_rates = [p.engagement_rate for p in posts if p.engagement_rate and p.engagement_rate > 0]
        avg_engagement_rate = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0

        # Calculate analysis coverage
        analyzed_count = (
            db.query(Post)
            .join(PostAnalysis, Post.id == PostAnalysis.post_id)
            .filter(
                Post.user_id == user_id,
                Post.published_at >= date_start,
                Post.published_at < date_end,
            )
            .count()
        )
        analysis_coverage = (analyzed_count / posts_count * 100) if posts_count > 0 else 0.0

        # Platform breakdown
        platform_counts = {}
        for post in posts:
            platform_counts[post.platform] = platform_counts.get(post.platform, 0) + 1

        # Find top performing post (by engagement rate)
        top_post = None
        if posts:
            top_post = max(posts, key=lambda p: p.engagement_rate or 0)

        # Check for existing snapshot (update or create)
        existing_snapshot = (
            db.query(DailyAnalyticsSnapshot)
            .filter(
                DailyAnalyticsSnapshot.user_id == user_id,
                DailyAnalyticsSnapshot.snapshot_date == target_date,
            )
            .first()
        )

        if existing_snapshot:
            # Update existing snapshot
            existing_snapshot.posts_count = posts_count
            existing_snapshot.total_likes = total_likes
            existing_snapshot.total_comments = total_comments
            existing_snapshot.total_shares = total_shares
            existing_snapshot.total_impressions = total_impressions
            existing_snapshot.avg_engagement_rate = avg_engagement_rate
            existing_snapshot.analysis_coverage_percent = analysis_coverage
            existing_snapshot.platform_breakdown = platform_counts
            existing_snapshot.top_performing_post_id = top_post.id if top_post else None
            snapshot = existing_snapshot
        else:
            # Create new snapshot
            snapshot = DailyAnalyticsSnapshot(
                user_id=user_id,
                snapshot_date=target_date,
                posts_count=posts_count,
                total_likes=total_likes,
                total_comments=total_comments,
                total_shares=total_shares,
                total_impressions=total_impressions,
                avg_engagement_rate=avg_engagement_rate,
                analysis_coverage_percent=analysis_coverage,
                platform_breakdown=platform_counts,
                top_performing_post_id=top_post.id if top_post else None,
            )
            db.add(snapshot)

        db.commit()

        # Log analytics event
        from app.models.analytics_snapshot import AnalyticsEvent
        event = AnalyticsEvent(
            user_id=user_id,
            event_type="snapshot_computed",
            post_id=None,
            metrics={
                "snapshot_date": target_date.isoformat(),
                "posts_count": posts_count,
                "avg_engagement_rate": avg_engagement_rate,
                "analysis_coverage": analysis_coverage,
            },
        )
        db.add(event)
        db.commit()

        logger.info(
            "Snapshot computed for user %s, date %s: %d posts, %.4f avg engagement",
            user_id,
            target_date,
            posts_count,
            avg_engagement_rate,
        )

        return {
            "user_id": user_id,
            "snapshot_date": target_date.isoformat(),
            "posts_count": posts_count,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_impressions": total_impressions,
            "avg_engagement_rate": avg_engagement_rate,
            "analysis_coverage_percent": analysis_coverage,
            "platform_breakdown": platform_counts,
            "top_post_id": top_post.id if top_post else None,
            "updated_existing": existing_snapshot is not None,
        }

    except Exception as e:
        db.rollback()
        logger.exception("Failed to compute snapshot for user %s: %s", user_id, e)
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(
    name="workers.celery.tasks.compute_analytics.compute_all_users_snapshots",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def compute_all_users_snapshots(self, snapshot_date: str | None = None) -> dict:
    """
    Compute daily snapshots for all users with posts in the last 90 days.

    Scheduled to run daily at 1 AM UTC.

    Args:
        snapshot_date: Date to compute for (default: today)

    Returns:
        Dict with processing summary
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.post import Post

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Find users with posts in last 90 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        active_user_ids = (
            db.query(distinct(Post.user_id))
            .filter(Post.published_at >= cutoff)
            .all()
        )
        user_ids = [uid for (uid,) in active_user_ids]

        logger.info("Computing snapshots for %d active users", len(user_ids))

        # Queue individual snapshot tasks with staggered delays
        queued = 0
        for i, user_id in enumerate(user_ids):
            compute_daily_snapshot.apply_async(
                kwargs={"user_id": user_id, "snapshot_date": snapshot_date},
                countdown=i * 2,  # Stagger by 2 seconds each
            )
            queued += 1

        return {
            "users_found": len(user_ids),
            "tasks_queued": queued,
            "snapshot_date": snapshot_date or date.today().isoformat(),
        }

    except Exception as e:
        logger.exception("Failed to queue snapshots: %s", e)
        raise self.retry(exc=e, countdown=300)

    finally:
        db.close()


@celery_app.task(
    name="workers.celery.tasks.compute_analytics.backfill_snapshots",
    bind=True,
    max_retries=2,
    time_limit=3600,  # 1 hour
)
def backfill_snapshots(
    self,
    user_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Backfill historical daily snapshots for a date range.

    Useful for initial population or recomputing after schema changes.

    Args:
        user_id: Specific user to backfill (None = all users)
        start_date: Start date (YYYY-MM-DD), default 90 days ago
        end_date: End date (YYYY-MM-DD), default today

    Returns:
        Dict with backfill summary
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.post import Post
    from app.models.user import User

    # Default date range: 90 days
    if end_date:
        end = date.fromisoformat(end_date)
    else:
        end = date.today()

    if start_date:
        start = date.fromisoformat(start_date)
    else:
        start = end - timedelta(days=90)

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Determine which users to process
        if user_id:
            user_ids = [user_id]
        else:
            # Get users with posts in the range
            start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
            end_dt = datetime.combine(end, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)
            
            user_ids_result = (
                db.query(distinct(Post.user_id))
                .filter(
                    Post.published_at >= start_dt,
                    Post.published_at < end_dt,
                )
                .all()
            )
            user_ids = [uid for (uid,) in user_ids_result]

        # Generate all date-user combinations
        tasks = []
        current = start
        while current <= end:
            for uid in user_ids:
                tasks.append((uid, current.isoformat()))
            current += timedelta(days=1)

        logger.info("Backfilling %d snapshots (%d users x %d days)", len(tasks), len(user_ids), (end - start).days + 1)

        # Queue tasks in batches
        batch_size = 100
        queued = 0
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            for user_id, snap_date in batch:
                compute_daily_snapshot.apply_async(
                    kwargs={"user_id": user_id, "snapshot_date": snap_date},
                    countdown=(i // batch_size) * 10,  # Stagger batches
                )
                queued += 1

        return {
            "users": len(user_ids),
            "date_range": {"start": start.isoformat(), "end": end.isoformat()},
            "total_snapshots": len(tasks),
            "tasks_queued": queued,
        }

    except Exception as e:
        logger.exception("Failed to backfill snapshots: %s", e)
        raise self.retry(exc=e, countdown=300)

    finally:
        db.close()


@celery_app.task(
    name="workers.celery.tasks.compute_analytics.delete_old_snapshots",
    bind=True,
)
def delete_old_snapshots(self, retention_days: int = 365) -> dict:
    """
    Delete analytics snapshots older than retention period.

    Scheduled monthly to prevent unbounded storage growth.

    Args:
        retention_days: Keep snapshots newer than this many days

    Returns:
        Dict with deletion summary
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.analytics_snapshot import DailyAnalyticsSnapshot

    cutoff = date.today() - timedelta(days=retention_days)

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        old_snapshots = (
            db.query(DailyAnalyticsSnapshot)
            .filter(DailyAnalyticsSnapshot.snapshot_date < cutoff)
            .all()
        )

        deleted_count = len(old_snapshots)
        
        for snapshot in old_snapshots:
            db.delete(snapshot)

        db.commit()

        logger.info("Deleted %d snapshots older than %s", deleted_count, cutoff)

        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff.isoformat(),
            "retention_days": retention_days,
        }

    except Exception as e:
        db.rollback()
        logger.exception("Failed to delete old snapshots: %s", e)
        raise

    finally:
        db.close()
