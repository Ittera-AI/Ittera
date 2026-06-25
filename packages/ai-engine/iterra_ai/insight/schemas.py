from pydantic import BaseModel, Field


class PostPerformanceRecord(BaseModel):
    """One analyzed post fed into synthesis. Pre-joined Post + PostAnalysis."""

    content: str
    platform: str
    published_hour: int | None = None  # 0-23 UTC, for timing patterns
    likes: int = 0
    comments: int = 0
    shares: int = 0
    impressions: int | None = None
    engagement_rate: float = 0.0
    hook_score: int | None = None  # from PostAnalysis
    tone_match_score: int | None = None
    structure_score: int | None = None
    cta_effectiveness: str | None = None
    top_strength: str | None = None
    top_improvement: str | None = None


class InsightSynthesisInput(BaseModel):
    """Input for cross-post insight synthesis."""

    platform: str
    period_days: int = 30
    avg_engagement_rate: float | None = None
    records: list[PostPerformanceRecord]
    # Optional off-loop signals (Gap 8); engine treats them as soft context.
    predicted_signals: dict | None = None  # from PredictorEngine
    competitive_signals: dict | None = None  # from competitive engine
    # Prior memory so synthesis is incremental, not amnesiac.
    prior_summary: str | None = None


class CandidateFact(BaseModel):
    """A proposed learned fact eligible for promotion into UserContext."""

    key: str = Field(..., description="e.g. best_post_times | best_formats | avoid")
    value: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: str


class InsightSynthesisOutput(BaseModel):
    """Output from cross-post insight synthesis."""

    summary: str  # 1 short paragraph
    why_wins: list[str] = Field(default_factory=list)
    why_losses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    candidate_facts: list[CandidateFact] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    model: str = ""
    is_mock: bool = False
