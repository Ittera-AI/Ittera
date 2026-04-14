from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BrandProfileData(BaseModel):
    voice_tone: str
    audience: str
    core_topics: list[str]
    writing_patterns: list[str]
    content_pillars: list[str]
    hashtag_strategy: str
    summary: str


class BrandProfileResponse(BaseModel):
    id: str | None = None
    profile: BrandProfileData | None = None
    version: int = 1
    ai_confidence_score: float = 0.0
    is_confirmed: bool = False
    analysis_based_on_posts: int = 0
    generated_at: datetime | None = None
    confirmed_at: datetime | None = None
    updated_at: datetime | None = None


class BrandProfileUpdateRequest(BaseModel):
    profile: BrandProfileData


class BrandProfileGenerateResponse(BrandProfileResponse):
    pass


def normalize_profile(raw: dict[str, Any]) -> BrandProfileData:
    return BrandProfileData.model_validate(raw)
