from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    ContentInsightsResponse,
    CrossPlatformComparisonResponse,
    PostAnalysisResponse,
    PostWithAnalysis,
    TimeSeriesDataPoint,
    TrendDetectionResult,
)
from app.services import analytics_service, analytics_trends_service

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def summary(
    period_days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get analytics dashboard summary KPIs.

    Returns aggregated metrics including:
      - Total posts, likes, comments, shares, impressions
      - Average engagement rate
      - Best performing post identification
      - AI analysis coverage
      - Week-over-week trends
      - Engagement distribution by performance tier
      - Average AI analysis scores
    """
    return analytics_service.analytics_summary(db, current_user, period_days)


@router.get("/posts", response_model=list[PostWithAnalysis])
async def posts(
    limit: int = Query(default=20, ge=1, le=100),
    platform: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's posts with AI analysis data.

    Args:
        limit: Maximum posts to return (1-100)
        platform: Filter by platform (linkedin, twitter, etc.) or None for all
    """
    return analytics_service.posts_with_analysis(db, current_user, limit, platform)


@router.post("/analyze/{post_id}", response_model=PostAnalysisResponse)
async def analyze(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze a specific post using the AI Engagement Coach.

    If analysis already exists and is recent (< 30 days), returns cached result.
    Otherwise, generates new AI analysis with historical context for comparative insights.

    Args:
        post_id: The post ID to analyze
    """
    return analytics_service.analyze_post(db, current_user, post_id)


@router.get("/insights", response_model=ContentInsightsResponse)
async def insights(
    period_days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get AI-generated content insights based on analyzed posts.

    Identifies patterns in your top-performing content and provides
    actionable recommendations for improvement.

    Args:
        period_days: Analysis period in days (max 90)
    """
    return analytics_service.get_content_insights(db, current_user, period_days)


@router.get("/trends", response_model=list[TimeSeriesDataPoint])
async def trends(
    metric: str = Query(default="engagement_rate", pattern="^(engagement_rate|likes|posts|impressions)$"),
    period_days: int = Query(default=30, ge=7, le=365),
    interval: str = Query(default="week", pattern="^(day|week|month)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get time-series trend data for specified metric.

    Returns daily or aggregated time series data for charting.
    Uses materialized daily snapshots when available for performance,
    falls back to on-the-fly aggregation from posts table.

    Args:
        metric: Metric to trend (engagement_rate, likes, posts, impressions)
        period_days: Number of days to analyze (7-365)
        interval: Data grouping interval (day, week, month)

    Returns:
        Time series data points with date, value, and moving averages
    """
    data = analytics_trends_service.get_time_series_data(
        db=db,
        user=current_user,
        metric=metric,  # type: ignore
        period_days=period_days,
        interval=interval,  # type: ignore
    )
    return data


@router.get("/trends/detect", response_model=TrendDetectionResult)
async def detect_trends(
    period_days: int = Query(default=30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Detect significant trends and anomalies in analytics data.

    Uses linear regression and statistical analysis to identify:
      - Engagement rate trends (up/down/flat with confidence)
      - Post volume trends
      - Anomalies (spikes or drops outside 2 standard deviations)
      - Actionable recommendations

    Args:
        period_days: Analysis period in days (7-90)

    Returns:
        Trend detection results with recommendations
    """
    result = analytics_trends_service.detect_trends(
        db=db,
        user=current_user,
        period_days=period_days,
    )
    return result


@router.get("/platforms/comparison", response_model=CrossPlatformComparisonResponse)
async def platform_comparison(
    period_days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compare engagement patterns across connected platforms.

    Returns per-platform engagement metrics including:
      - Average engagement rate per platform
      - Best-performing content types per platform
      - Overall platform ranking by engagement
      - Cross-platform comparison insights and recommendations

    Args:
        period_days: Lookback period in days (1-365, default 30)

    Returns:
        Cross-platform engagement comparison data
    """
    return analytics_service.cross_platform_engagement_comparison(
        db, current_user, period_days
    )
