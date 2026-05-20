import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class PostAnalysis(Base):
    __tablename__ = "post_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, unique=True)
    hook_score = Column(Integer, nullable=False)
    tone_match_score = Column(Integer, nullable=False)
    structure_score = Column(Integer, nullable=False)
    cta_effectiveness = Column(String, nullable=False)
    coach_feedback = Column(JSON, nullable=False, default=dict)
    rewrite_suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    post = relationship("Post", back_populates="analysis")
