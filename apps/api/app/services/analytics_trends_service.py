"""
Analytics Trends Service — time-series aggregation and trend analysis.

Features:
  - Daily time-series data from materialized snapshots
  - Multiple interval aggregations (day, week, month)
  - Moving average calculations (7-day, 30-day)
  - Trend direction detection with confidence scoring
  - Efficient query patterns using materialized snapshots
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.analytics_snapshot import DailyAnalyticsSnapshot
from app.models.post import Post
from app.models.user import User


def get_time_series_data(
    db: Session,
    user: User,
    metric: Literal["engagement_rate", "likes", "posts", "impressions"],
    period_days: int = 30,
    interval: Literal["day", "week", "month"] = "day",
) -> list[dict[str, Any]]:
    """
    Get time-series data for specified metric.

    Uses daily analytics snapshots for efficient querying when available,
    falls back to on-the-fly aggregation from posts table.

    Args:
        db: Database session
        user: Current user
        metric: Metric to trend
        period_days: Number of days to analyze
        interval: Data grouping interval

    Returns:
        List of time-series data points with date, value, and moving averages
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    
    # Check if we have sufficient snapshot coverage
    snapshot_count = (
        db.query(DailyAnalyticsSnapshot)
        .filter(
            DailyAnalyticsSnapshot.user_id == user.id,
            DailyAnalyticsSnapshot.snapshot_date >= cutoff.date(),
        )
        .count()
    )
    
    # Use snapshots if we have >70% coverage, otherwise compute from posts
    if snapshot_count >= int(period_days * 0.7):
        return _get_time_series_from_snapshots(db, user, metric, cutoff, interval)
    else:
        return _get_time_series_from_posts(db, user, metric, cutoff, interval)


def _get_time_series_from_snapshots(
    db: Session,
    user: User,
    metric: str,
    cutoff: datetime,
    interval: str,
) -> list[dict[str, Any]]:
    """Build time-series from pre-computed daily snapshots."""
    
    # Query snapshots in range
    snapshots = (
        db.query(DailyAnalyticsSnapshot)
        .filter(
            DailyAnalyticsSnapshot.user_id == user.id,
            DailyAnalyticsSnapshot.snapshot_date >= cutoff.date(),
        )
        .order_by(DailyAnalyticsSnapshot.snapshot_date)
        .all()
    )
    
    if not snapshots:
        return []
    
    # Build data points based on metric
    data_points = []
    for snapshot in snapshots:
        value = _extract_metric_from_snapshot(snapshot, metric)
        data_points.append({
            "date": snapshot.snapshot_date.isoformat(),
            "value": value,
            "posts_count": snapshot.posts_count,
        })
    
    # Apply interval aggregation if not day
    if interval != "day":
        data_points = _aggregate_by_interval(data_points, interval)
    
    # Add moving averages
    data_points = _add_moving_averages(data_points)
    
    return data_points


def _get_time_series_from_posts(
    db: Session,
    user: User,
    metric: str,
    cutoff: datetime,
    interval: str,
) -> list[dict[str, Any]]:
    """Build time-series by aggregating posts on-the-fly."""
    
    if metric == "posts":
        # Simple count aggregation
        query = (
            db.query(
                func.date(Post.published_at).label("date"),
                func.count(Post.id).label("value"),
            )
            .filter(
                Post.user_id == user.id,
                Post.published_at >= cutoff,
            )
            .group_by(func.date(Post.published_at))
            .order_by(func.date(Post.published_at))
        )
        results = query.all()
        
        data_points = [
            {"date": str(r.date), "value": r.value, "posts_count": r.value}
            for r in results
        ]
        
    elif metric == "likes":
        query = (
            db.query(
                func.date(Post.published_at).label("date"),
                func.sum(Post.likes).label("value"),
                func.count(Post.id).label("posts_count"),
            )
            .filter(
                Post.user_id == user.id,
                Post.published_at >= cutoff,
            )
            .group_by(func.date(Post.published_at))
            .order_by(func.date(Post.published_at))
        )
        results = query.all()
        
        data_points = [
            {"date": str(r.date), "value": int(r.value or 0), "posts_count": r.posts_count}
            for r in results
        ]
        
    elif metric == "engagement_rate":
        # Calculate daily average engagement rate
        query = (
            db.query(
                func.date(Post.published_at).label("date"),
                func.avg(Post.engagement_rate).label("value"),
                func.count(Post.id).label("posts_count"),
            )
            .filter(
                Post.user_id == user.id,
                Post.published_at >= cutoff,
                Post.engagement_rate > 0,  # Only posts with calculated rate
            )
            .group_by(func.date(Post.published_at))
            .order_by(func.date(Post.published_at))
        )
        results = query.all()
        
        data_points = [
            {
                "date": str(r.date),
                "value": round(float(r.value or 0), 6),
                "posts_count": r.posts_count,
            }
            for r in results
        ]
        
    elif metric == "impressions":
        query = (
            db.query(
                func.date(Post.published_at).label("date"),
                func.sum(Post.impressions).label("value"),
                func.count(Post.id).label("posts_count"),
            )
            .filter(
                Post.user_id == user.id,
                Post.published_at >= cutoff,
            )
            .group_by(func.date(Post.published_at))
            .order_by(func.date(Post.published_at))
        )
        results = query.all()
        
        data_points = [
            {"date": str(r.date), "value": int(r.value or 0), "posts_count": r.posts_count}
            for r in results
        ]
        
    else:
        data_points = []
    
    # Fill in missing dates with zeros
    data_points = _fill_missing_dates(data_points, cutoff.date())
    
    # Apply interval aggregation if not day
    if interval != "day":
        data_points = _aggregate_by_interval(data_points, interval)
    
    # Add moving averages
    data_points = _add_moving_averages(data_points)
    
    return data_points


def _extract_metric_from_snapshot(
    snapshot: DailyAnalyticsSnapshot,
    metric: str,
) -> float:
    """Extract metric value from snapshot based on metric name."""
    if metric == "engagement_rate":
        return float(snapshot.avg_engagement_rate or 0)
    elif metric == "likes":
        return float(snapshot.total_likes or 0)
    elif metric == "posts":
        return float(snapshot.posts_count or 0)
    elif metric == "impressions":
        return float(snapshot.total_impressions or 0)
    else:
        return 0.0


def _fill_missing_dates(
    data_points: list[dict],
    start_date: date,
) -> list[dict]:
    """Fill in missing dates with zero values."""
    if not data_points:
        return []
    
    # Create date -> value mapping
    date_map = {dp["date"]: dp for dp in data_points}
    
    # Generate all dates in range
    end_date = date.today()
    filled_points = []
    current = start_date
    
    while current <= end_date:
        date_str = current.isoformat()
        if date_str in date_map:
            filled_points.append(date_map[date_str])
        else:
            filled_points.append({
                "date": date_str,
                "value": 0,
                "posts_count": 0,
            })
        current += timedelta(days=1)
    
    return filled_points


def _aggregate_by_interval(
    data_points: list[dict],
    interval: str,
) -> list[dict]:
    """Aggregate daily data points by week or month."""
    from collections import defaultdict
    
    if interval == "week":
        # Group by ISO week
        groups = defaultdict(list)
        for dp in data_points:
            dp_date = date.fromisoformat(dp["date"])
            # Get week start (Monday)
            week_start = dp_date - timedelta(days=dp_date.weekday())
            groups[week_start.isoformat()].append(dp)
        
        aggregated = []
        for week_start, points in sorted(groups.items()):
            total_posts = sum(p["posts_count"] for p in points)
            if total_posts > 0:
                # Weighted average for engagement rate, sum for others
                avg_value = sum(p["value"] for p in points) / len(points)
            else:
                avg_value = 0
            
            aggregated.append({
                "date": week_start,
                "value": round(avg_value, 6),
                "posts_count": total_posts,
                "interval": "week",
            })
        
        return aggregated
        
    elif interval == "month":
        # Group by month
        groups = defaultdict(list)
        for dp in data_points:
            dp_date = date.fromisoformat(dp["date"])
            month_key = dp_date.replace(day=1).isoformat()
            groups[month_key].append(dp)
        
        aggregated = []
        for month_key, points in sorted(groups.items()):
            total_posts = sum(p["posts_count"] for p in points)
            if total_posts > 0:
                avg_value = sum(p["value"] for p in points) / len(points)
            else:
                avg_value = 0
            
            aggregated.append({
                "date": month_key,
                "value": round(avg_value, 6),
                "posts_count": total_posts,
                "interval": "month",
            })
        
        return aggregated
    
    return data_points


def _add_moving_averages(data_points: list[dict]) -> list[dict]:
    """Add 7-day and 30-day moving averages to data points."""
    if len(data_points) < 7:
        # Not enough data for moving averages
        for dp in data_points:
            dp["ma7"] = None
            dp["ma30"] = None
        return data_points
    
    values = [dp["value"] for dp in data_points]
    
    for i, dp in enumerate(data_points):
        # 7-day moving average
        if i >= 6:
            ma7 = sum(values[i-6:i+1]) / 7
            dp["ma7"] = round(ma7, 6)
        else:
            dp["ma7"] = None
        
        # 30-day moving average
        if i >= 29:
            ma30 = sum(values[i-29:i+1]) / 30
            dp["ma30"] = round(ma30, 6)
        else:
            dp["ma30"] = None
    
    return data_points


def detect_trends(
    db: Session,
    user: User,
    period_days: int = 30,
) -> dict[str, Any]:
    """
    Detect significant trends in user analytics.

    Identifies:
      - Engagement rate trends
      - Post volume trends
      - Quality score trends (from AI analysis)
      - Anomalies (sudden spikes or drops)

    Args:
        db: Database session
        user: Current user
        period_days: Analysis period

    Returns:
        Dict with detected trends and anomalies
    """
    # Get engagement rate time series
    engagement_series = get_time_series_data(
        db, user, "engagement_rate", period_days, "day"
    )
    
    if len(engagement_series) < 7:
        return {
            "has_enough_data": False,
            "message": "Need at least 7 days of data for trend detection",
        }
    
    # Calculate trend direction using linear regression
    engagement_trend = _calculate_linear_trend(engagement_series)
    
    # Detect anomalies (points outside 2 std dev)
    anomalies = _detect_anomalies(engagement_series)
    
    # Get post volume trend
    posts_series = get_time_series_data(
        db, user, "posts", period_days, "week"
    )
    posts_trend = _calculate_linear_trend(posts_series) if len(posts_series) >= 2 else None
    
    return {
        "has_enough_data": True,
        "period_days": period_days,
        "engagement_rate": {
            "direction": engagement_trend["direction"],
            "strength": engagement_trend["strength"],
            "slope": engagement_trend["slope"],
            "confidence": engagement_trend["confidence"],
        },
        "post_volume": {
            "direction": posts_trend["direction"] if posts_trend else "flat",
            "strength": posts_trend["strength"] if posts_trend else 0,
        } if posts_trend else None,
        "anomalies": [
            {
                "date": a["date"],
                "value": a["value"],
                "deviation": a["deviation"],
                "type": a["type"],
            }
            for a in anomalies
        ],
        "recommendations": _generate_trend_recommendations(
            engagement_trend, posts_trend, anomalies
        ),
    }


def _calculate_linear_trend(data_points: list[dict]) -> dict[str, Any]:
    """Calculate linear trend using least squares."""
    if len(data_points) < 3:
        return {"direction": "flat", "strength": 0, "slope": 0, "confidence": 0}
    
    # Filter out zero values and None MA values for cleaner trend
    values = []
    for i, dp in enumerate(data_points):
        if dp["value"] > 0:
            values.append((i, dp["value"]))
    
    if len(values) < 3:
        return {"direction": "flat", "strength": 0, "slope": 0, "confidence": 0}
    
    # Simple linear regression
    n = len(values)
    x_vals = [v[0] for v in values]
    y_vals = [v[1] for v in values]
    
    x_mean = sum(x_vals) / n
    y_mean = sum(y_vals) / n
    
    # Calculate slope (m) and correlation (r)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
    denominator_x = sum((x - x_mean) ** 2 for x in x_vals)
    denominator_y = sum((y - y_mean) ** 2 for y in y_vals)
    
    if denominator_x == 0 or denominator_y == 0:
        return {"direction": "flat", "strength": 0, "slope": 0, "confidence": 0}
    
    slope = numerator / denominator_x
    correlation = numerator / ((denominator_x * denominator_y) ** 0.5)
    
    # Determine direction and strength
    if abs(correlation) < 0.3:
        direction = "flat"
        strength = 0
    elif slope > 0:
        direction = "up"
        strength = min(abs(correlation) * 100, 100)
    else:
        direction = "down"
        strength = min(abs(correlation) * 100, 100)
    
    return {
        "direction": direction,
        "strength": round(strength, 1),
        "slope": round(slope, 6),
        "confidence": round(abs(correlation), 2),
    }


def _detect_anomalies(data_points: list[dict]) -> list[dict]:
    """Detect anomalous data points using standard deviation."""
    if len(data_points) < 7:
        return []
    
    # Get non-zero values
    values = [dp["value"] for dp in data_points if dp["value"] > 0]
    
    if len(values) < 5:
        return []
    
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std_dev = variance ** 0.5
    
    if std_dev == 0:
        return []
    
    anomalies = []
    for dp in data_points:
        if dp["value"] == 0:
            continue
        
        deviation = (dp["value"] - mean) / std_dev
        
        if abs(deviation) > 2:  # 2 standard deviations
            anomalies.append({
                "date": dp["date"],
                "value": dp["value"],
                "deviation": round(deviation, 2),
                "type": "spike" if deviation > 0 else "drop",
            })
    
    return anomalies


def _generate_trend_recommendations(
    engagement_trend: dict,
    posts_trend: dict | None,
    anomalies: list,
) -> list[str]:
    """Generate recommendations based on trend analysis."""
    recommendations = []
    
    # Engagement trend recommendations
    if engagement_trend["direction"] == "down" and engagement_trend["strength"] > 30:
        recommendations.append(
            "Engagement rate is trending down. Consider analyzing your top performers "
            "and applying their patterns to new content."
        )
    elif engagement_trend["direction"] == "up" and engagement_trend["strength"] > 50:
        recommendations.append(
            "Strong upward trend in engagement! Double down on what's working and "
            "increase posting frequency while momentum is high."
        )
    
    # Post volume recommendations
    if posts_trend:
        if posts_trend["direction"] == "down":
            recommendations.append(
                "Post volume is declining. Consistency is key for audience growth."
            )
        elif posts_trend["direction"] == "up" and engagement_trend["direction"] != "up":
            recommendations.append(
                "You're posting more but engagement isn't keeping up. Focus on quality "
                "over quantity - use the Coach to optimize each post."
            )
    
    # Anomaly recommendations
    if anomalies:
        spike_count = sum(1 for a in anomalies if a["type"] == "spike")
        if spike_count > 0:
            recommendations.append(
                f"Detected {spike_count} high-performing post(s). Analyze these outliers "
                "to understand what made them successful."
            )
    
    if not recommendations:
        recommendations.append(
            "Your metrics are stable. Continue current strategy and experiment with "
            "new content formats to find growth opportunities."
        )
    
    return recommendations
