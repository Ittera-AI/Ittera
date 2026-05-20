from datetime import datetime
from typing import Any

from pydantic import BaseModel, ValidationError


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
    drive_analysis_file_id: str | None = None
    generated_at: datetime | None = None
    confirmed_at: datetime | None = None
    updated_at: datetime | None = None


class BrandProfileUpdateRequest(BaseModel):
    profile: BrandProfileData


class BrandProfileGenerateResponse(BrandProfileResponse):
    pass


def normalize_profile(raw: dict[str, Any] | None) -> BrandProfileData | None:
    """
    Hydrate BrandProfile JSON from DB. Empty or legacy/partial payloads must not 500 GET /brand-profile.
    """
    if raw is None or raw == {}:
        return None
    try:
        return BrandProfileData.model_validate(raw)
    except ValidationError:
        return BrandProfileData(
            voice_tone=str(raw.get("voice_tone") or ""),
            audience=str(raw.get("audience") or ""),
            core_topics=[str(x) for x in raw.get("core_topics") or []],
            writing_patterns=[str(x) for x in raw.get("writing_patterns") or []],
            content_pillars=[str(x) for x in raw.get("content_pillars") or []],
            hashtag_strategy=str(raw.get("hashtag_strategy") or ""),
            summary=str(raw.get("summary") or ""),
        )
