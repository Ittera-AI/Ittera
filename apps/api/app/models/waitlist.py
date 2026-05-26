import uuid

from sqlalchemy import Boolean, Column, DateTime, String

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class WaitlistEntry(Base):
    __tablename__ = "waitlist"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Access approval — added by migration 003_add_waitlist_access_approval
    access_approved = Column(Boolean, nullable=False, default=False)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)   # admin email that approved
