import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String

from app.db.base import Base


class WaitlistEntry(Base):
    __tablename__ = "waitlist"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
