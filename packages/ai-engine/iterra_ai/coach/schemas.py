from pydantic import BaseModel, Field


class CoachInput(BaseModel):
    """Input for engagement coach analysis."""

    content: str
    platform: str
    goal: str | None = None

    # Brand context for tone matching
    voice_tone: str | None = None
    content_pillars: list[str] | None = None
    target_audience: str | None = None

    # Metrics for context (optional)
    likes: int = 0
    comments: int = 0
    shares: int = 0
    impressions: int = 0
    engagement_rate: float = 0.0

    # Historical context for comparative analysis
    avg_engagement_rate: float | None = None
    """User's historical average engagement rate for comparison."""

    top_performing_topics: list[str] | None = None
    """User's historically best performing topics for context."""


class CoachAnalysisScores(BaseModel):
    """Detailed scoring breakdown."""

    hook_score: int = Field(..., ge=0, le=10, description="Opening strength 0-10")
    tone_match_score: int = Field(..., ge=0, le=10, description="Brand voice alignment 0-10")
    structure_score: int = Field(..., ge=0, le=10, description="Readability and flow 0-10")
    cta_effectiveness: str = Field(..., pattern="^(strong|weak|none)$")


class CoachOutput(BaseModel):
    """Output from engagement coach analysis."""

    # Detailed scores
    hook_score: int = Field(..., ge=0, le=10)
    tone_match_score: int = Field(..., ge=0, le=10)
    structure_score: int = Field(..., ge=0, le=10)
    cta_effectiveness: str = Field(..., pattern="^(strong|weak|none)$")

    # Feedback
    top_strength: str
    top_improvement: str
    detailed_feedback: str | None = None
    """2-3 sentences of specific analysis explaining the scores."""

    predicted_engagement: str = Field(..., pattern="^(low|medium|high)$")
    rewrite_suggestion: str | None = None

    # Legacy fields for backward compatibility
    score: float = Field(default=0.0, ge=0.0, le=10.0)
    suggestions: list[str] = Field(default_factory=list)
    summary: str = ""

    def model_post_init(self, __context: object) -> None:
        """Calculate legacy score field from individual scores."""
        if self.score == 0.0:
            self.score = round(
                (self.hook_score + self.tone_match_score + self.structure_score) / 3, 1
            )
        if not self.suggestions and self.top_improvement:
            self.suggestions = [self.top_improvement]
        if not self.summary and self.top_strength:
            self.summary = self.top_strength
