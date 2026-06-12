from datetime import datetime

from pydantic import BaseModel, Field


class TrendMetrics(BaseModel):
    """Week-over-week or period-over-period trend metrics."""

    direction: str = Field(..., pattern="^(up|down|flat)$")
    percent_change: float | None = None
    absolute_change: float


class EngagementDistribution(BaseModel):
    """Distribution of posts by engagement rate ranges."""

    high: int = Field(description="Posts with > 5% engagement rate")
    good: int = Field(description="Posts with 2-5% engagement rate")
    average: int = Field(description="Posts with 1-2% engagement rate")
    low: int = Field(description="Posts with < 1% engagement rate")


class AverageAnalysisScores(BaseModel):
    """Average AI analysis scores for the period."""

    hook_score: float | None = None
    structure_score: float | None = None
    tone_score: float | None = None


class PostAnalysisResponse(BaseModel):
    post_id: str
    hook_score: int
    tone_match_score: int
    structure_score: int
    cta_effectiveness: str
    top_strength: str
    top_improvement: str
    detailed_feedback: str | None = None
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
    impressions: int | None = None
    engagement_rate: float
    analysis: PostAnalysisResponse | None = None


class AnalyticsTrends(BaseModel):
    """Period-over-period trend data."""

    posts_change: TrendMetrics
    engagement_rate_change: TrendMetrics
    likes_change: TrendMetrics


class AnalyticsSummaryResponse(BaseModel):
    """Dashboard KPI summary for analytics page."""

    total_posts: int
    total_likes: int
    total_comments: int
    total_shares: int
    total_impressions: int
    avg_engagement_rate: float
    best_performing_post: PostWithAnalysis | None = None
    posts_analyzed: int
    analysis_coverage_percent: float  # % of posts with AI analysis
    platform_breakdown: dict[str, int]  # {"linkedin": 15, "twitter": 3}
    period_days: int = 30  # Data from last N days

    # New fields for enhanced analytics
    trends: AnalyticsTrends | None = None
    engagement_distribution: EngagementDistribution | None = None
    avg_analysis_scores: AverageAnalysisScores | None = None


class ContentInsightRecommendation(BaseModel):
    """A single content recommendation."""

    type: str = Field(..., pattern="^(strength|improvement)$")
    message: str
    related_metric: str | None = None


class ContentInsightsResponse(BaseModel):
    """AI-generated content insights based on analysis data."""

    period_days: int
    analyzed_posts_count: int
    top_performer_avg_scores: AverageAnalysisScores
    identified_strengths: list[str]
    recommendations: list[str]
    message: str | None = None


class TimeSeriesDataPoint(BaseModel):
    """A single data point in a time series."""

    date: str  # ISO date string (YYYY-MM-DD)
    value: float  # The metric value
    posts_count: int  # Number of posts aggregated into this point
    interval: str | None = None  # "day", "week", or "month"
    ma7: float | None = None  # 7-day moving average
    ma30: float | None = None  # 30-day moving average


class AnomalyDetection(BaseModel):
    """Detected anomaly in time series data."""

    date: str
    value: float
    deviation: float  # Standard deviations from mean
    type: str  # "spike" or "drop"


class EngagementRateTrend(BaseModel):
    """Trend analysis for engagement rate."""

    direction: str  # "up", "down", or "flat"
    strength: float  # 0-100 strength of trend
    slope: float  # Linear regression slope
    confidence: float  # Correlation coefficient (0-1)


class PostVolumeTrend(BaseModel):
    """Trend analysis for post volume."""

    direction: str  # "up", "down", or "flat"
    strength: float  # 0-100 strength of trend


class TrendDetectionResult(BaseModel):
    """Results from trend detection analysis."""

    has_enough_data: bool
    period_days: int | None = None
    message: str | None = None
    engagement_rate: EngagementRateTrend | None = None
    post_volume: PostVolumeTrend | None = None
    anomalies: list[AnomalyDetection] = []
    recommendations: list[str] = []


# ---------------------------------------------------------------------------
# Cross-Platform Engagement Comparison
# ---------------------------------------------------------------------------


class PlatformBestPost(BaseModel):
    """The best performing post on a platform."""

    id: str
    content: str
    engagement_rate: float
    published_at: str | None = None


class ContentTypePerformance(BaseModel):
    """Performance metrics for a content type."""

    content_type: str
    post_count: int
    avg_engagement_rate: float


class PlatformEngagementMetrics(BaseModel):
    """Engagement metrics for a single platform."""

    platform: str
    total_posts: int
    avg_engagement_rate: float
    total_likes: int
    total_comments: int
    total_shares: int
    total_impressions: int
    best_content_types: list[ContentTypePerformance]
    best_post: PlatformBestPost


class CrossPlatformComparisonResponse(BaseModel):
    """Cross-platform engagement comparison response."""

    period_days: int
    platforms: list[PlatformEngagementMetrics]
    best_platform: str | None = None
    comparison_insights: list[str]
    message: str | None = None
