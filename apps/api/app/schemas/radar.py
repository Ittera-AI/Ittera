from datetime import datetime

from pydantic import BaseModel, Field


class TrendItem(BaseModel):
    topic: str
    score: float
    platforms: list[str]
    summary: str


class RadarInput(BaseModel):
    niche: str = Field(min_length=1, max_length=160)
    platforms: list[str] = Field(default_factory=list, max_length=5)
    limit: int = Field(default=10, ge=1, le=25)


class RadarOutput(BaseModel):
    trends: list[TrendItem]
    scanned_at: datetime
