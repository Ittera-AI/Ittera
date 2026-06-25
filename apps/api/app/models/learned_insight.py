import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class LearnedInsight(Base):
    """
    Compact, summarized 'what we learned / why posts win or lose' memory for one
    user on one platform. Upserted in place and version-bumped on each synthesis,
    mirroring the BrandProfile single-active-row pattern (not append-only).
    Read by context_service Layer 3 to inject learnings into the next prompt.
    """

    __tablename__ = "learned_insights"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform = Column(String, nullable=False, index=True)

    # Human-readable synthesis (1 short paragraph) injected into the prompt.
    summary = Column(Text, nullable=False, default="")

    # Structured, prompt-ready learnings. Each is a list[str] of crisp findings.
    why_wins = Column(JSON, nullable=False, default=list)      # what makes posts succeed
    why_losses = Column(JSON, nullable=False, default=list)    # what makes posts underperform
    recommendations = Column(JSON, nullable=False, default=list)  # do-next guidance for generation

    # Candidate facts proposed for promotion into UserContext.platform_facts.
    # Shape: [{"key": "best_post_times", "value": ["08:00"], "confidence": 0.81,
    #          "evidence": "5 of top 6 posts published 07:00-09:00"}]
    candidate_facts = Column(JSON, nullable=False, default=list)

    # Provenance / confidence
    confidence = Column(Float, nullable=False, default=0.0)   # 0..1 overall trust
    based_on_posts = Column(Integer, nullable=False, default=0)
    based_on_analyses = Column(Integer, nullable=False, default=0)
    period_days = Column(Integer, nullable=False, default=30)
    model = Column(String, nullable=True)                     # engine model or "heuristic"
    is_mock = Column(Integer, nullable=False, default=0)      # 0/1 flag for fallback output

    version = Column(Integer, nullable=False, default=1)
    generated_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="learned_insights")

    __table_args__ = (
        UniqueConstraint("user_id", "platform", name="uq_learned_insight_user_platform"),
    )
