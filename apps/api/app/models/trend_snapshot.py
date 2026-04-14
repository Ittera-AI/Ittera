import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, JSON, String, UniqueConstraint

from app.db.base import Base


class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"
    __table_args__ = (UniqueConstraint("niche", name="uq_trend_snapshots_niche"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    niche = Column(String, nullable=False)
    trends = Column(JSON, nullable=False, default=list)
    top_pick = Column(JSON, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
