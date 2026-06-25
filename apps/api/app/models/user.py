import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    niche = Column(String, nullable=True)
    goals = Column(Text, nullable=True)
    primary_platform = Column(String, nullable=False, default="linkedin")
    onboarding_complete = Column(Boolean, nullable=False, default=False)
    # Granular storage preferences - JSON allows per-content-type settings
    # Format: {"default": "google_drive", "drafts": "google_drive", "analysis": "local", ...}
    storage_preferences = Column(JSON, nullable=False, default=lambda: {"default": "google_drive"})
    # Legacy storage preference (for backwards compatibility)
    # If storage_preferences is not set, falls back to this
    storage_preference = Column(String, nullable=True, default="google_drive")  # DEPRECATED: use storage_preferences
    # Data retention policy in days (0 = never delete, null = use system default)
    data_retention_days = Column(Integer, nullable=True, default=365)
    auto_post_enabled = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # ── Permanent context identity fields (set during onboarding, editable) ──
    # These mirror the active UserContext row for fast access without a join.
    # Authoritative source-of-truth is the user_contexts table (versioned).
    brand_name = Column(String, nullable=True)     # Brand or personal name for content
    bio = Column(Text, nullable=True)              # 2–4 sentence bio in the user's own words
    target_audience = Column(Text, nullable=True)  # Who they create content for
    content_mission = Column(Text, nullable=True)  # Why they create content

    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    content_plans = relationship("ContentPlan", back_populates="user", cascade="all, delete-orphan")
    social_connections = relationship("SocialConnection", back_populates="user", cascade="all, delete-orphan")
    content_drafts = relationship("ContentDraft", back_populates="user", cascade="all, delete-orphan")
    brand_profile = relationship("BrandProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    user_contexts = relationship(
        "UserContext",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="UserContext.version",
    )
    persona_profile = relationship("PersonaProfile", back_populates="user", cascade="all, delete-orphan")
    learned_insights = relationship("LearnedInsight", back_populates="user", cascade="all, delete-orphan")
    
    # Analytics relationships
    analytics_snapshots = relationship(
        "DailyAnalyticsSnapshot",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="DailyAnalyticsSnapshot.snapshot_date.desc()",
    )
    analytics_events = relationship(
        "AnalyticsEvent",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="AnalyticsEvent.created_at.desc()",
    )
    
    # Organization/Agency relationships
    organization_memberships = relationship(
        "OrganizationMember",
        back_populates="user",
        foreign_keys="OrganizationMember.user_id",
        cascade="all, delete-orphan",
    )
    workspace_memberships = relationship(
        "WorkspaceMember",
        back_populates="user",
        foreign_keys="WorkspaceMember.user_id",
        cascade="all, delete-orphan",
    )
