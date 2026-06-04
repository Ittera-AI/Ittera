"""Pydantic schemas for AI-powered content predictions."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ContentInput(BaseModel):
    """Input for predicting content performance."""
    
    content: str = Field(..., description="The content to analyze")
    platform: Literal["linkedin", "twitter", "instagram", "facebook"] = Field(
        default="linkedin",
        description="Target platform",
    )
    content_type: Literal["post", "article", "video", "image", "poll"] = Field(
        default="post",
        description="Type of content",
    )
    hashtags: list[str] = Field(default_factory=list, description="Hashtags used")
    mentioned_accounts: list[str] = Field(
        default_factory=list,
        description="@mentions in content",
    )
    scheduled_time: datetime | None = Field(
        None,
        description="When content is planned to be published",
    )
    
    # Context from workspace/organization
    industry: str | None = Field(None, description="Industry/niche")
    target_audience: str | None = Field(None, description="Target audience description")
    brand_tone: str | None = Field(None, description="Brand voice/tone")
    
    # Historical context
    author_avg_engagement: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Author's historical average engagement rate (%)",
    )
    author_follower_count: int | None = Field(
        None,
        ge=0,
        description="Author's follower count",
    )


class PredictionMetrics(BaseModel):
    """Predicted engagement metrics."""
    
    likes: int = Field(..., ge=0, description="Predicted likes")
    comments: int = Field(..., ge=0, description="Predicted comments")
    shares: int = Field(..., ge=0, description="Predicted shares")
    impressions: int = Field(..., ge=0, description="Predicted impressions")
    engagement_rate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Predicted engagement rate (%)",
    )
    
    # Platform-specific
    reach: int | None = Field(None, ge=0, description="Predicted reach")
    click_through_rate: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Predicted CTR (%)",
    )


class ConfidenceInterval(BaseModel):
    """Confidence interval for a predicted value."""
    
    lower: float = Field(..., description="Lower bound")
    upper: float = Field(..., description="Upper bound")
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence level (e.g., 0.95 for 95%)",
    )
    
    @field_validator("upper")
    @classmethod
    def upper_gt_lower(cls, v: float, info) -> float:
        if "lower" in info.data and v < info.data["lower"]:
            raise ValueError("Upper bound must be >= lower bound")
        return v


class PredictionConfidence(BaseModel):
    """Confidence metrics for predictions."""
    
    overall_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Overall confidence in prediction (0-1)",
    )
    engagement_rate_ci: ConfidenceInterval = Field(
        ...,
        description="Confidence interval for engagement rate",
    )
    impressions_ci: ConfidenceInterval | None = Field(
        None,
        description="Confidence interval for impressions",
    )
    
    # Confidence factors
    data_quality_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Quality of input data",
    )
    historical_alignment: float = Field(
        ...,
        ge=0,
        le=1,
        description="How similar this is to historical successes",
    )
    model_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Model's internal confidence score",
    )


class FeatureImportance(BaseModel):
    """Importance of features in the prediction."""
    
    feature: str = Field(..., description="Feature name")
    importance: float = Field(
        ...,
        ge=-1,
        le=1,
        description="Importance score (-1 to 1, negative = harmful)",
    )
    impact: Literal["positive", "negative", "neutral"] = Field(
        ...,
        description="Direction of impact",
    )
    explanation: str = Field(..., description="Human-readable explanation")


class ContentPredictionOutput(BaseModel):
    """Output from PredictorEngine."""
    
    prediction_id: str = Field(..., description="Unique prediction ID")
    content_hash: str = Field(..., description="Hash of input for caching")
    
    # Predictions
    metrics: PredictionMetrics
    confidence: PredictionConfidence
    
    # Analysis
    feature_importance: list[FeatureImportance] = Field(
        default_factory=list,
        description="Key factors in prediction",
    )
    
    # Recommendations
    improvement_suggestions: list[str] = Field(
        default_factory=list,
        description="Ways to improve predicted performance",
    )
    comparative_analysis: str | None = Field(
        None,
        description="How this compares to typical content",
    )
    
    # Metadata
    model_version: str = Field(default="predictor-v1")
    prediction_time: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = Field(..., ge=0)
    tokens_used: int | None = Field(None, ge=0)
    estimated_cost_usd: float | None = Field(None, ge=0)


class ViralScoreInput(BaseModel):
    """Input for viral potential prediction."""
    
    content: str = Field(..., description="Content to analyze")
    platform: Literal["linkedin", "twitter", "instagram", "facebook"] = Field(
        default="linkedin",
    )
    
    # Pattern detection inputs
    has_story_element: bool | None = Field(
        None,
        description="Content includes narrative/story",
    )
    has_data_insight: bool | None = Field(
        None,
        description="Content includes data/insights",
    )
    has_controversy: bool | None = Field(
        None,
        description="Content touches controversial topic",
    )
    emotional_tone: Literal[
        "inspirational", "controversial", "educational", "entertaining",
        "emotional", "professional", "neutral"
    ] | None = Field(None)


class ViralPattern(BaseModel):
    """Detected viral pattern."""
    
    pattern_type: Literal[
        "hook_strength", "emotional_resonance", "shareability",
        "timeliness", "uniqueness", "visual_appeal", "authenticity"
    ] = Field(..., description="Type of viral pattern")
    score: float = Field(..., ge=0, le=1, description="Pattern strength (0-1)")
    detected: bool = Field(..., description="Whether pattern is present")
    explanation: str = Field(..., description="Why this score was given")
    examples: list[str] = Field(
        default_factory=list,
        description="Examples from the content",
    )


class ViralPotentialOutput(BaseModel):
    """Output from ViralPredictionEngine."""
    
    prediction_id: str = Field(...)
    content_hash: str = Field(...)
    
    # Overall score
    viral_probability: float = Field(
        ...,
        ge=0,
        le=1,
        description="Probability of viral success (0-1)",
    )
    viral_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Viral score 0-100",
    )
    
    # Category scoring
    category: Literal[
        "highly_viral", "viral_potential", "average", "below_average", "unlikely"
    ] = Field(..., description="Viral potential category")
    
    # Pattern analysis
    patterns: list[ViralPattern] = Field(
        default_factory=list,
        description="Detected viral patterns",
    )
    
    # Benchmarks
    percentile_rank: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentile vs. analyzed content",
    )
    comparison_to_top_performers: str | None = Field(
        None,
        description="Comparison to top 1% viral content",
    )
    
    # Actionable insights
    viral_triggers: list[str] = Field(
        default_factory=list,
        description="Elements that could trigger viral spread",
    )
    amplification_suggestions: list[str] = Field(
        default_factory=list,
        description="How to increase viral potential",
    )
    
    # Metadata
    model_version: str = Field(default="viral-v1")
    prediction_time: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = Field(..., ge=0)


class TimingInput(BaseModel):
    """Input for optimal timing prediction."""
    
    content: str = Field(..., description="Content to schedule")
    platform: Literal["linkedin", "twitter", "instagram", "facebook"] = Field(
        default="linkedin",
    )
    timezone: str = Field(default="UTC", description="Target audience timezone")
    
    # Historical data
    author_historical_posts: list[dict] = Field(
        default_factory=list,
        description="Historical posts with timing and performance",
    )
    
    # Constraints
    allowed_days: list[Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]] = Field(
        default_factory=lambda: ["mon", "tue", "wed", "thu", "fri"],
        description="Days allowed for posting",
    )
    allowed_hours_start: int = Field(
        default=8,
        ge=0,
        le=23,
        description="Earliest hour to post (24h)",
    )
    allowed_hours_end: int = Field(
        default=18,
        ge=0,
        le=23,
        description="Latest hour to post (24h)",
    )


class TimeSlotScore(BaseModel):
    """Score for a specific time slot."""
    
    day: Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"] = Field(...)
    hour: int = Field(..., ge=0, le=23)
    score: float = Field(..., ge=0, le=1, description="Quality score (0-1)")
    
    # Predicted outcomes
    predicted_engagement_rate: float = Field(..., ge=0, le=100)
    predicted_reach: int = Field(..., ge=0)
    
    # Factors
    audience_availability: float = Field(
        ...,
        ge=0,
        le=1,
        description="How available is target audience",
    )
    competition_level: Literal["low", "medium", "high"] = Field(
        ...,
        description="Content competition at this time",
    )
    historical_performance: float | None = Field(
        None,
        ge=0,
        le=1,
        description="Your historical performance at this time",
    )
    
    # Explanation
    reasoning: str = Field(..., description="Why this time was scored this way")


class TimingPattern(BaseModel):
    """Detected timing pattern from historical data."""
    
    pattern_type: Literal[
        "peak_engagement_time", "low_competition_window",
        "audience_active_hours", "content_type_timing"
    ] = Field(...)
    description: str = Field(...)
    confidence: float = Field(..., ge=0, le=1)
    recommended_action: str | None = Field(None)


class TimingOutput(BaseModel):
    """Output from TimingPredictionEngine."""
    
    prediction_id: str = Field(...)
    content_hash: str = Field(...)
    
    # Primary recommendation
    optimal_time: datetime = Field(..., description="Recommended publish time")
    confidence_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in recommendation",
    )
    
    # Ranked alternatives
    alternative_slots: list[TimeSlotScore] = Field(
        default_factory=list,
        description="Top 5 alternative time slots",
    )
    
    # Full week heatmap (optional)
    weekly_heatmap: list[TimeSlotScore] | None = Field(
        None,
        description="All scored time slots",
    )
    
    # Pattern insights
    detected_patterns: list[TimingPattern] = Field(
        default_factory=list,
        description="Detected patterns from analysis",
    )
    
    # Global insights
    best_days: list[str] = Field(default_factory=list)
    best_hours: list[int] = Field(default_factory=list)
    worst_times_to_post: list[str] = Field(default_factory=list)
    
    # Platform-specific
    platform_insights: str | None = Field(
        None,
        description="Platform-specific timing insights",
    )
    
    # Metadata
    model_version: str = Field(default="timing-v1")
    prediction_time: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = Field(..., ge=0)
    historical_data_points_used: int = Field(default=0, ge=0)
