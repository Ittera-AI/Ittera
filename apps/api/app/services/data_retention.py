"""
Data Retention Service — manages automatic data cleanup based on user preferences.

Implements data retention policies for:
- Content drafts
- Analytics snapshots
- Scrape data
- Reports and exports

Respects user privacy by only cleaning Iterra-stored data,
never touching user's Google Drive data.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.analytics_snapshot import DailyAnalyticsSnapshot
from app.models.content_draft import ContentDraft
from app.models.user import User

logger = logging.getLogger("iterra.data_retention")

# Default retention period in days (1 year)
DEFAULT_RETENTION_DAYS = 365

# Minimum retention period (7 days) - to prevent accidental data loss
MIN_RETENTION_DAYS = 7

# Content types that can be cleaned
RETAINABLE_CONTENT_TYPES = {
    "drafts": "Content drafts",
    "analytics": "Analytics snapshots",
    "scraped_posts": "Scraped social media data",
    "reports": "Generated reports",
}


class DataRetentionService:
    """
    Service for enforcing data retention policies.

    Cleans up old data based on user preferences while respecting:
    - User's retention settings (data_retention_days)
    - Minimum retention period (safety)
    - Never deletes from user's Google Drive
    """

    def __init__(self, db: Session):
        self.db = db

    def get_retention_period(self, user: User) -> int:
        """
        Get the effective retention period for a user.

        Args:
            user: User to get retention period for

        Returns:
            Retention period in days
        """
        if user.data_retention_days is None:
            return DEFAULT_RETENTION_DAYS

        # Enforce minimum retention period
        return max(user.data_retention_days, MIN_RETENTION_DAYS)

    def calculate_cutoff_date(self, user: User) -> datetime:
        """
        Calculate the cutoff date for data retention.

        Args:
            user: User to calculate cutoff for

        Returns:
            Datetime before which data should be deleted
        """
        retention_days = self.get_retention_period(user)
        return datetime.now(timezone.utc) - timedelta(days=retention_days)

    def clean_user_drafts(self, user: User, dry_run: bool = False) -> dict:
        """
        Clean old content drafts for a user.

        Only deletes drafts stored on Iterra servers (drive_file_id is null).
        Drafts stored on user's Drive are NOT touched.

        Args:
            user: User to clean drafts for
            dry_run: If True, only count what would be deleted

        Returns:
            Dict with deletion statistics
        """
        cutoff = self.calculate_cutoff_date(user)

        # Find old drafts that are NOT on Drive (drive_file_id is null)
        # These are drafts stored on Iterra servers
        query = self.db.query(ContentDraft).filter(
            ContentDraft.user_id == user.id,
            ContentDraft.created_at < cutoff,
            ContentDraft.drive_file_id.is_(None),  # Only Iterra-stored drafts
            ContentDraft.status.in_(["draft", "archived"]),  # Don't delete published
        )

        count = query.count()

        if not dry_run and count > 0:
            # Delete the drafts
            deleted = query.delete(synchronize_session=False)
            logger.info(
                "Deleted %d old drafts for user %s (retention: %d days)",
                deleted,
                user.id,
                self.get_retention_period(user),
            )
            return {
                "deleted": deleted,
                "retention_days": self.get_retention_period(user),
                "cutoff_date": cutoff.isoformat(),
            }

        return {
            "would_delete": count,
            "retention_days": self.get_retention_period(user),
            "cutoff_date": cutoff.isoformat(),
            "dry_run": dry_run,
        }

    def clean_user_analytics(self, user: User, dry_run: bool = False) -> dict:
        """
        Clean old analytics snapshots for a user.

        Args:
            user: User to clean analytics for
            dry_run: If True, only count what would be deleted

        Returns:
            Dict with deletion statistics
        """
        cutoff = self.calculate_cutoff_date(user)

        # Find old analytics snapshots
        query = self.db.query(DailyAnalyticsSnapshot).filter(
            DailyAnalyticsSnapshot.user_id == user.id,
            DailyAnalyticsSnapshot.snapshot_date < cutoff.date(),
        )

        count = query.count()

        if not dry_run and count > 0:
            # Keep the most recent snapshot even if it's past cutoff
            # (for baseline comparison)
            most_recent = (
                self.db.query(DailyAnalyticsSnapshot)
                .filter(DailyAnalyticsSnapshot.user_id == user.id)
                .order_by(DailyAnalyticsSnapshot.snapshot_date.desc())
                .first()
            )

            if most_recent and most_recent.snapshot_date < cutoff.date():
                # Exclude most recent from deletion
                query = query.filter(
                    DailyAnalyticsSnapshot.id != most_recent.id
                )
                count = query.count()

            deleted = query.delete(synchronize_session=False)
            logger.info(
                "Deleted %d old analytics snapshots for user %s (retention: %d days)",
                deleted,
                user.id,
                self.get_retention_period(user),
            )
            return {
                "deleted": deleted,
                "retention_days": self.get_retention_period(user),
                "cutoff_date": cutoff.isoformat(),
            }

        return {
            "would_delete": count,
            "retention_days": self.get_retention_period(user),
            "cutoff_date": cutoff.isoformat(),
            "dry_run": dry_run,
        }

    def clean_user_data(self, user: User, dry_run: bool = False) -> dict:
        """
        Clean all retainable data for a user according to their retention policy.

        Args:
            user: User to clean data for
            dry_run: If True, only count what would be deleted

        Returns:
            Dict with deletion statistics by content type
        """
        if user.data_retention_days == 0:
            # 0 means never delete
            return {
                "user_id": user.id,
                "skipped": True,
                "reason": "Retention policy set to never delete",
            }

        drafts_result = self.clean_user_drafts(user, dry_run)
        analytics_result = self.clean_user_analytics(user, dry_run)

        return {
            "user_id": user.id,
            "dry_run": dry_run,
            "retention_days": self.get_retention_period(user),
            "cutoff_date": self.calculate_cutoff_date(user).isoformat(),
            "drafts": drafts_result,
            "analytics": analytics_result,
        }

    def get_retention_summary(self, user: User) -> dict:
        """
        Get a summary of data retention status for a user.

        Args:
            user: User to get summary for

        Returns:
            Dict with retention status
        """
        cutoff = self.calculate_cutoff_date(user)

        # Count drafts that would be affected
        drafts_count = (
            self.db.query(ContentDraft)
            .filter(
                ContentDraft.user_id == user.id,
                ContentDraft.created_at < cutoff,
                ContentDraft.drive_file_id.is_(None),
            )
            .count()
        )

        # Count analytics snapshots that would be affected
        analytics_count = (
            self.db.query(DailyAnalyticsSnapshot)
            .filter(
                DailyAnalyticsSnapshot.user_id == user.id,
                DailyAnalyticsSnapshot.snapshot_date < cutoff.date(),
            )
            .count()
        )

        # Total data sizes (approximate)
        total_drafts = (
            self.db.query(ContentDraft)
            .filter(ContentDraft.user_id == user.id)
            .count()
        )

        total_analytics = (
            self.db.query(DailyAnalyticsSnapshot)
            .filter(DailyAnalyticsSnapshot.user_id == user.id)
            .count()
        )

        return {
            "user_id": user.id,
            "retention_policy": {
                "days": user.data_retention_days,
                "effective_days": self.get_retention_period(user),
                "auto_delete_enabled": user.data_retention_days is not None and user.data_retention_days > 0,
            },
            "data_summary": {
                "total_drafts": total_drafts,
                "drafts_eligible_for_deletion": drafts_count,
                "total_analytics_snapshots": total_analytics,
                "analytics_eligible_for_deletion": analytics_count,
            },
            "next_cleanup_date": self._get_next_cleanup_date().isoformat(),
        }

    def _get_next_cleanup_date(self) -> datetime:
        """Calculate the next scheduled cleanup date."""
        # Cleanup runs weekly, next run is next Sunday at 2 AM
        from datetime import datetime, timedelta
        now = datetime.now(timezone.utc)
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0 and now.hour >= 2:
            days_until_sunday = 7
        next_sunday = now + timedelta(days=days_until_sunday)
        return next_sunday.replace(hour=2, minute=0, second=0, microsecond=0)


def get_data_retention_service(db: Session) -> DataRetentionService:
    """Get a DataRetentionService instance."""
    return DataRetentionService(db)
