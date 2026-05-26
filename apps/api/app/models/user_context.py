"""
UserContext — versioned, append-only permanent context snapshots.

Every time the user's permanent context changes (onboarding, manual edit, or
fact promotion from the learning loop), a new row is inserted rather than
updating in place. The active context is the row with is_active=True.

This means we never lose prior context — downgrading or auditing past state
is always possible.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class UserContext(Base):
    __tablename__ = "user_contexts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Identity fields (captured during onboarding, editable later) ─────────
    brand_name = Column(String, nullable=True)           # "Iterra" or "John Smith" for personal brand
    bio = Column(Text, nullable=True)                    # Who you are, in your own words (2-4 sentences)
    target_audience = Column(Text, nullable=True)        # Who you create content for
    content_mission = Column(Text, nullable=True)        # Why you create content / what change you drive

    # ── Platform-specific learned facts (proposed + user-approved) ───────────
    # Structure: { "linkedin": { "best_post_times": ["17:00"], "best_formats": ["listicle"],
    #                             "avoid": [], "confirmed_at": "ISO datetime" },
    #              "twitter":  { ... } }
    platform_facts = Column(JSON, nullable=False, default=dict)

    # ── Version tracking ─────────────────────────────────────────────────────
    version = Column(Integer, nullable=False, default=1)

    # Source of this version: "onboarding" | "manual_edit" | "fact_promotion"
    change_source = Column(String, nullable=False, default="onboarding")

    # Human-readable note about what changed in this version
    change_summary = Column(Text, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="user_contexts")
