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


class RepurposeRequest(BaseModel):
    draft_id: str
    target_platform: Literal["instagram", "twitter"]


class RepurposeResponse(BaseModel):
    draft_id: str
    content: str
    platform: str


class DraftUpdateRequest(BaseModel):
    content: str | None = None
    status: str | None = None
    scheduled_for: datetime | None = None


class DraftResponse(BaseModel):
    id: str
    platform: str
    content: str | None = None      # None when content lives in Google Drive
    drive_file_id: str | None = None  # Google Drive file ID for draft content
    repurposed_versions: dict[str, str] = Field(default_factory=dict)
    status: str
    scheduled_for: datetime | None = None
    platform_post_id: str | None = None
    published_at: datetime | None = None
    publish_error: str | None = None
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
    starts_at: datetime
    content: str
