from datetime import datetime

from pydantic import BaseModel


class TrendItem(BaseModel):
    topic: str
    score: float
    platforms: list[str]
    summary: str


class RadarInput(BaseModel):
    niche: str
    platforms: list[str]
    limit: int = 10


class RadarOutput(BaseModel):
    trends: list[TrendItem]
    scanned_at: datetime
