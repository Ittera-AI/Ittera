from datetime import datetime

from pydantic import BaseModel


class PostAnalysisResponse(BaseModel):
    post_id: str
    hook_score: int
    tone_match_score: int
    structure_score: int
    cta_effectiveness: str
    top_strength: str
    top_improvement: str
    predicted_engagement: str
    rewrite_suggestion: str | None = None


class PostWithAnalysis(BaseModel):
    id: str
    platform: str
    content: str
    published_at: datetime | None = None
    likes: int
    comments: int
    shares: int
    engagement_rate: float
    analysis: PostAnalysisResponse | None = None
