import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now


class ContentDraft(Base):
    __tablename__ = "content_drafts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    platform = Column(String, nullable=False, default="linkedin")
    content = Column(Text, nullable=True)  # nullable: Drive-backed drafts store content in Drive
    drive_file_id = Column(String, nullable=True)  # Google Drive file ID for draft content
    repurposed_versions = Column(JSON, nullable=False, default=dict)
    prompt_used = Column(Text, nullable=True)
    trend_used = Column(String, nullable=True)
    # Fallback only; real generations set this to the actual model used
    # (output.model). The active default provider is the AIML OpenAI-compatible
    # gateway, not Anthropic.
    generation_model = Column(String, nullable=False, default="gpt-4o-mini")
    status = Column(String, nullable=False, default="draft")
    review_status = Column(String, nullable=False, default="draft")
    scheduled_for = Column(DateTime, nullable=True)
    celery_task_id = Column(String, nullable=True)
    platform_post_id = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    publish_error = Column(Text, nullable=True)
    review_email_sent_at = Column(DateTime, nullable=True)
    auto_post_enabled_snapshot = Column(Boolean, nullable=False, default=False)
    persona_fit_score = Column(Integer, nullable=True)
    persona_fit_notes = Column(JSON, nullable=False, default=list)
    platform_media = Column(JSON, nullable=True, default=dict)  # Platform-specific metadata (e.g., google_calendar_event_id)
    post_id = Column(String, ForeignKey("posts.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="content_drafts")
    workspace = relationship("Workspace", back_populates="content_drafts")
    media = relationship("ContentDraftMedia", back_populates="draft", cascade="all, delete-orphan", order_by="ContentDraftMedia.position")
    post = relationship("Post", foreign_keys=[post_id])


class ContentDraftMedia(Base):
    __tablename__ = "content_draft_media"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    draft_id = Column(String, ForeignKey("content_drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    local_path = Column(Text, nullable=False)
    public_path = Column(Text, nullable=True)
    drive_file_id = Column(String, nullable=True)
    platform_media = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default="ready")
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now)

    draft = relationship("ContentDraft", back_populates="media")
    user = relationship("User")

    @property
    def preview_url(self) -> str | None:
        return self.public_path
