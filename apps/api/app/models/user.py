import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
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
    storage_preference = Column(String, nullable=False, default="google_drive")  # "google_drive"|"local"|"iterra"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    content_plans = relationship("ContentPlan", back_populates="user", cascade="all, delete-orphan")
    social_connections = relationship("SocialConnection", back_populates="user", cascade="all, delete-orphan")
    content_drafts = relationship("ContentDraft", back_populates="user", cascade="all, delete-orphan")
    brand_profile = relationship("BrandProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
