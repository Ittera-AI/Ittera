from datetime import datetime

from pydantic import BaseModel


class TrendItemResponse(BaseModel):
    topic: str
    raw_score: int
    niche_relevance: float
    related_queries: list[str]
    content_angle: str


class TrendResponse(BaseModel):
    niche: str
    trends: list[TrendItemResponse]
    top_pick: TrendItemResponse | None = None
    fetched_at: datetime
    cache_age_minutes: int
