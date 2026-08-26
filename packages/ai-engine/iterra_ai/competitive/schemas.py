"""Pydantic schemas for competitive intelligence AI."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

JsonObject = dict[str, Any]


class CompetitorProfileInput(BaseModel):
    """Input for analyzing a competitor's content strategy."""
    
    competitor_id: str
    competitor_name: str
    platform: Literal["linkedin", "twitter", "instagram", "facebook"]
    handle: str
    
    # Scraped/cached data about competitor
    recent_posts: list[JsonObject] = Field(
        default_factory=list,
        description="Recent posts from competitor",
    )
    follower_count: int | None = None
    niche_tags: list[str] = Field(default_factory=list)
    
    # Context
    author_niche: str | None = None  # Your niche for comparison
    author_avg_engagement: float | None = None


class ContentGapAnalysisInput(BaseModel):
    """Input for identifying content gaps vs competitors."""
    
    author_content_pillars: list[str] = Field(default_factory=list)
    author_recent_topics: list[str] = Field(default_factory=list)
    
    competitor_posts: list[JsonObject] = Field(default_factory=list)
    competitor_content_themes: list[str] = Field(default_factory=list)
    
    industry_trends: list[str] = Field(default_factory=list)


class TrendBenchmarkInput(BaseModel):
    """Input for trend benchmarking vs competitors."""
    
    trend_topic: str
    author_performance: JsonObject | None = None
    competitor_performances: list[JsonObject] = Field(default_factory=list)
    
    time_period: str = Field(default="30d")


class CompetitorStrategyOutput(BaseModel):
    """Output from competitor strategy analysis."""
    
    analysis_id: str
    competitor_id: str
    analysis_type: Literal["strategy", "content_gaps", "trend_benchmark"] = "strategy"
    
    # Strategic findings
    content_strategy: JsonObject = Field(
        default_factory=dict,
        description="Identified content strategy patterns",
    )
    posting_patterns: JsonObject = Field(
        default_factory=dict,
        description="When and how often they post",
    )
    engagement_tactics: list[str] = Field(
        default_factory=list,
        description="Tactics used to drive engagement",
    )
    
    # Content analysis
    top_performing_themes: list[JsonObject] = Field(
        default_factory=list,
        description="Themes that perform well for competitor",
    )
    content_format_preferences: list[str] = Field(
        default_factory=list,
        description="Preferred content formats",
    )
    tone_and_voice: str | None = Field(
        None,
        description="Competitor's tone analysis",
    )
    
    # Competitive positioning
    competitive_advantages: list[str] = Field(
        default_factory=list,
        description="What they do better than you",
    )
    your_advantages: list[str] = Field(
        default_factory=list,
        description="What you do better than them",
    )
    
    # Opportunities
    opportunities: list[JsonObject] = Field(
        default_factory=list,
        description="Identified opportunities",
    )
    threats: list[str] = Field(
        default_factory=list,
        description="Competitive threats",
    )
    
    # Actionable recommendations
    recommended_actions: list[str] = Field(
        default_factory=list,
        description="Specific actions to take",
    )
    content_ideas_inspired_by: list[str] = Field(
        default_factory=list,
        description="Content ideas inspired by competitor",
    )
    
    # Metadata
    model_version: str = Field(default="competitive-v1")
    analysis_time: datetime = Field(default_factory=datetime.utcnow)
    posts_analyzed: int = Field(default=0)
    confidence_score: float = Field(default=0.7, ge=0, le=1)


class ContentGapOutput(BaseModel):
    """Output from content gap analysis."""
    
    analysis_id: str
    analysis_type: Literal["content_gaps"] = "content_gaps"
    
    # Gap identification
    covered_topics: list[JsonObject] = Field(
        default_factory=list,
        description="Topics you cover well",
    )
    gap_topics: list[JsonObject] = Field(
        default_factory=list,
        description="Topics competitors cover that you don't",
    )
    underserved_topics: list[JsonObject] = Field(
        default_factory=list,
        description="Topics with low competition",
    )
    
    # Format gaps
    format_gaps: list[JsonObject] = Field(
        default_factory=list,
        description="Content formats you underutilize",
    )
    
    # Audience gaps
    audience_segment_gaps: list[JsonObject] = Field(
        default_factory=list,
        description="Audience segments not addressed",
    )
    
    # Priority recommendations
    high_impact_opportunities: list[JsonObject] = Field(
        default_factory=list,
        description="Highest priority gaps to fill",
    )
    quick_wins: list[str] = Field(
        default_factory=list,
        description="Easy opportunities to pursue",
    )
    
    # Content calendar suggestions
    suggested_content_calendar: list[JsonObject] = Field(
        default_factory=list,
        description="Suggested content based on gaps",
    )
    
    # Metadata
    model_version: str = Field(default="gaps-v1")
    analysis_time: datetime = Field(default_factory=datetime.utcnow)
    competitors_analyzed: int = Field(default=0)


class TrendBenchmarkOutput(BaseModel):
    """Output from trend benchmarking analysis."""
    
    analysis_id: str
    analysis_type: Literal["trend_benchmark"] = "trend_benchmark"
    trend_topic: str
    
    # Performance comparison
    your_performance: JsonObject = Field(
        default_factory=dict,
        description="Your performance on this trend",
    )
    competitor_performances: list[JsonObject] = Field(
        default_factory=list,
        description="Competitor performances",
    )
    
    # Rankings
    your_rank: int | None = Field(
        None,
        description="Your rank among competitors (1 = best)",
    )
    total_competitors: int = Field(default=0)
    
    # Analysis
    why_top_performers_succeeded: list[str] = Field(
        default_factory=list,
        description="Reasons for top performer success",
    )
    your_gaps_vs_top: list[str] = Field(
        default_factory=list,
        description="What top performers did differently",
    )
    
    # Timing analysis
    trend_lifecycle: Literal[
        "emerging", "peak", "saturated", "declining", "unknown"
    ] = Field(
        default="emerging",
    )
    window_of_opportunity: str | None = Field(
        None,
        description="How long to capitalize on this trend",
    )
    
    # Recommendations
    how_to_improve: list[str] = Field(
        default_factory=list,
        description="Specific improvements for this trend",
    )
    similar_trends_to_watch: list[str] = Field(
        default_factory=list,
        description="Related trends to monitor",
    )
    
    # Metadata
    model_version: str = Field(default="trend-benchmark-v1")
    analysis_time: datetime = Field(default_factory=datetime.utcnow)
