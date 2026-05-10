import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class ContentPlan(Base):
    __tablename__ = "content_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    niche = Column(String, nullable=False)
    platforms = Column(JSON, nullable=False, default=list)
    slots = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="content_plans")
