import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    platform = Column(String, nullable=False)
    platform_post_id = Column(String, nullable=True, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=True)
    impressions = Column(Integer, nullable=False, default=0)
    likes = Column(Integer, nullable=False, default=0)
    comments = Column(Integer, nullable=False, default=0)
    shares = Column(Integer, nullable=False, default=0)
    engagement_rate = Column(Float, nullable=False, default=0.0)
    topics = Column(JSON, nullable=False, default=list)
    tone = Column(String, nullable=True)
    raw_api_response = Column(JSON, nullable=True)
    synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="posts")
    analysis = relationship("PostAnalysis", back_populates="post", cascade="all, delete-orphan", uselist=False)
