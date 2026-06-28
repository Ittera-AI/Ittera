import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class SocialConnection(Base):
    __tablename__ = "social_connections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    platform = Column(String, nullable=False, index=True)
    platform_user_id = Column(String, nullable=False)
    platform_username = Column(String, nullable=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    scopes = Column(JSON, nullable=False, default=list)
    last_synced_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    # Set when a stored token cannot be refreshed/decrypted and the user must
    # re-authorize the connection (R4.3).
    requires_reconnect = Column(Boolean, nullable=False, default=False, server_default="0")
    # Platform-specific extras: Drive folder IDs, encrypted LinkedIn creds, etc.
    # Renamed from 'metadata' to avoid SQL reserved keyword conflict
    connection_metadata = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="social_connections")
    workspace = relationship("Workspace", back_populates="social_connections")
