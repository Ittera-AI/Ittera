import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    profile = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    ai_confidence_score = Column(Float, nullable=False, default=0.0)
    is_confirmed = Column(Boolean, nullable=False, default=False)
    analysis_based_on_posts = Column(Integer, nullable=False, default=0)
    generated_at = Column(DateTime, default=utc_now)
    confirmed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    # Google Drive file ID for the full AI analysis JSON (content lives in Drive, not our DB)
    drive_analysis_file_id = Column(String, nullable=True)

    user = relationship("User", back_populates="brand_profile")
