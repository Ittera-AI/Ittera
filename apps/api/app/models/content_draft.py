import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class ContentDraft(Base):
    __tablename__ = "content_drafts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String, nullable=False, default="linkedin")
    content = Column(Text, nullable=False)
    repurposed_versions = Column(JSON, nullable=False, default=dict)
    prompt_used = Column(Text, nullable=True)
    trend_used = Column(String, nullable=True)
    generation_model = Column(String, nullable=False, default="claude-sonnet-4-5")
    status = Column(String, nullable=False, default="draft")
    scheduled_for = Column(DateTime, nullable=True)
    celery_task_id = Column(String, nullable=True)
    platform_post_id = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    publish_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="content_drafts")
