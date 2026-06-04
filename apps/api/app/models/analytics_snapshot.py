import uuid
from datetime import date

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class DailyAnalyticsSnapshot(Base):
    """
    Daily snapshot of analytics metrics for fast trend queries.
    
    Materialized daily to avoid expensive aggregations on every request.
    Updated by background Celery job (compute_analytics.py).
    """
    
    __tablename__ = "daily_analytics_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    workspace_id = Column(
        String,
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    snapshot_date = Column(Date, nullable=False, index=True)
    
    # Aggregated metrics for the day
    posts_count = Column(Integer, nullable=False, default=0)
    total_likes = Column(Integer, nullable=False, default=0)
    total_comments = Column(Integer, nullable=False, default=0)
    total_shares = Column(Integer, nullable=False, default=0)
    total_impressions = Column(Integer, nullable=False, default=0)
    
    # Calculated metrics
    avg_engagement_rate = Column(Numeric(8, 6), nullable=False, default=0.0)
    analysis_coverage_percent = Column(Numeric(5, 2), nullable=False, default=0.0)
    
    # References
    top_performing_post_id = Column(
        String, 
        ForeignKey("posts.id", ondelete="SET NULL"), 
        nullable=True
    )
    platform_breakdown = Column(JSON, nullable=True, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="analytics_snapshots")
    workspace = relationship("Workspace", back_populates="analytics_snapshots")
    top_post = relationship("Post", foreign_keys=[top_performing_post_id])
    
    __table_args__ = (
        # Unique constraint to prevent duplicate snapshots per user per day
        {"sqlite_autoincrement": True},
    )


class AnalyticsEvent(Base):
    """
    Track analytics-related events for auditing and time-series analysis.
    
    Events:
      - 'engagement_sync': When post metrics are synced from platform
      - 'post_published': When a post is published
      - 'analysis_complete': When AI analysis is completed
      - 'trend_calculated': When trend metrics are computed
    """
    
    __tablename__ = "analytics_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    event_type = Column(String(50), nullable=False, index=True)
    post_id = Column(
        String, 
        ForeignKey("posts.id", ondelete="CASCADE"), 
        nullable=True
    )
    
    # Flexible metrics storage (varies by event type)
    # Examples:
    #   engagement_sync: {likes: N, delta: N, platform: "linkedin"}
    #   analysis_complete: {hook_score: N, tone_score: N, model: "claude-3.5"}
    metrics = Column(JSON, nullable=True, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")
    post = relationship("Post")
