import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    content_plans = relationship("ContentPlan", back_populates="user", cascade="all, delete-orphan")
    social_connections = relationship("SocialConnection", back_populates="user", cascade="all, delete-orphan")
    content_drafts = relationship("ContentDraft", back_populates="user", cascade="all, delete-orphan")
    brand_profile = relationship("BrandProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
