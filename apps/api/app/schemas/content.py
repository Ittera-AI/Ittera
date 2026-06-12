from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Platform = Literal["linkedin", "instagram", "twitter"]


class ContentSuggestion(BaseModel):
    hook: str
    angle: str
    format: str
    trend_tie: str
    why_it_works: str


class SuggestRequest(BaseModel):
    platform: Platform = "linkedin"
    topic: str | None = None


class SuggestResponse(BaseModel):
    suggestions: list[ContentSuggestion]
    context_warnings: list[str] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    platform: Platform = "linkedin"
    prompt: str
    trend_used: str | None = None
    suggestion: ContentSuggestion | None = None


class GenerateResponse(BaseModel):
    draft_id: str
    content: str
    drive_file_id: str | None = None  # set when content is written to Google Drive
    word_count: int
    within_platform_limit: bool
    thread_segments: list[str] | None = None  # set when content was auto-split into a thread
    content_limit: dict | None = None  # tier-aware limit metadata (platform, max_chars, tier)
    context_warnings: list[str] = Field(default_factory=list)
    context_summary: dict = Field(default_factory=dict)
    generation_mode: str = "live"


class RepurposeRequest(BaseModel):
    draft_id: str
    target_platform: Literal["instagram", "twitter"]
    scheduled_for: datetime | None = None  # Allow independent scheduling of repurposed draft


class RepurposeResponse(BaseModel):
    draft_id: str
    content: str
    platform: str
    new_draft_id: str | None = None  # ID of the independently schedulable repurposed draft
    thread_segments: list[str] | None = None  # Thread segments if auto-split
    within_platform_limit: bool = True
    content_limit: dict | None = None  # Tier-aware limit metadata


class DraftCreateRequest(BaseModel):
    platform: Platform
    content: str | list[str]
    scheduled_for: datetime | None = None


class DraftUpdateRequest(BaseModel):
    content: str | None = None
    status: str | None = None
    scheduled_for: datetime | None = None


class DraftMediaResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    preview_url: str | None = None
    drive_file_id: str | None = None
    status: str
    position: int = 0

    model_config = ConfigDict(from_attributes=True)


class DraftResponse(BaseModel):
    id: str
    platform: str
    content: str | None = None      # None when content lives in Google Drive
    drive_file_id: str | None = None  # Google Drive file ID for draft content
    media: list[DraftMediaResponse] = Field(default_factory=list)
    repurposed_versions: dict[str, str] = Field(default_factory=dict)
    status: str
    review_status: str = "draft"
    scheduled_for: datetime | None = None
    platform_post_id: str | None = None
    published_at: datetime | None = None
    publish_error: str | None = None
    auto_post_enabled_snapshot: bool = False
    persona_fit_score: int | None = None
    persona_fit_notes: list[str] = Field(default_factory=list)
    trend_used: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PublishRequest(BaseModel):
    draft_id: str


class ScheduleRequest(BaseModel):
    draft_id: str
    scheduled_for: datetime


class PublishResponse(BaseModel):
    platform_post_id: str
    published_at: datetime


class ScheduleResponse(BaseModel):
    celery_task_id: str
    scheduled_for: datetime
    suggested_times: list[datetime]


class CalendarEventResponse(BaseModel):
    id: str
    title: str
    platform: str
    status: str
    review_status: str = "draft"
    starts_at: datetime
    content: str
    media: list[DraftMediaResponse] = Field(default_factory=list)
