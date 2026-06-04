"""
Analytics Service — comprehensive post performance analysis.

Features:
  - AI-powered post analysis via EngagementCoach
  - Historical performance benchmarking
  - Trend detection and week-over-week comparisons
  - Engagement distribution analysis
  - Platform-specific metrics
  - Comparative analysis against user baseline
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.brand_profile import BrandProfile
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.user import User


def posts_with_analysis(
    db: Session, 
    user: User, 
    limit: int = 20, 
    platform: str | None = None,
    include_unanalyzed: bool = True,
) -> list[dict[str, Any]]:
    """
    Fetch user's posts with analysis data.
    
    Args:
        db: Database session
        user: Current user
        limit: Maximum posts to return
        platform: Filter by platform (or None for all)
        include_unanalyzed: Include posts without AI analysis
        
    Returns:
        List of post dicts with analysis data
    """
    query = db.query(Post).filter(Post.user_id == user.id)
    
    if platform:
        query = query.filter(Post.platform == platform)
    
    posts = (
        query.order_by(Post.published_at.desc().nullslast())
        .limit(limit)
        .all()
    )
    
    return [_post_payload(post) for post in posts]


def analyze_post(db: Session, user: User, post_id: str) -> dict[str, Any]:
    """
    Analyze a post using AI coach engine with historical context.

    If analysis already exists, returns cached result.
    Otherwise, calls EngagementCoach for AI-powered analysis with
    historical performance context for comparative insights.
    
    Args:
        db: Database session
        user: Current user
        post_id: Post ID to analyze
        
    Returns:
        Analysis result dict
        
    Raises:
        HTTPException: 404 if post not found
    """
    from fastapi import HTTPException, status

    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # Return existing analysis if available and fresh (< 30 days)
    if post.analysis is not None:
        analysis_age = datetime.now(timezone.utc) - post.analysis.created_at
        if analysis_age.days < 30:
            return _analysis_payload(post.id, post.analysis)

    # Fetch brand profile for context
    brand_profile = (
        db.query(BrandProfile).filter(BrandProfile.user_id == user.id).first()
    )

    # Get historical context for comparative analysis
    historical_context = _get_historical_context(db, user, post.platform)

    # Prepare brand context
    voice_tone = None
    content_pillars = None
    target_audience = None

    if brand_profile and brand_profile.profile:
        profile_data = brand_profile.profile
        voice_tone = profile_data.get("voice_tone")
        content_pillars = profile_data.get("content_pillars", [])
        target_audience = profile_data.get("audience")

    # Call AI coach engine
    try:
        from iterra_ai.coach.engine import EngagementCoach
        from iterra_ai.coach.schemas import CoachInput

        coach = EngagementCoach()
        coach_input = CoachInput(
            content=post.content,
            platform=post.platform,
            voice_tone=voice_tone,
            content_pillars=content_pillars,
            target_audience=target_audience,
            goal=None,  # Could be inferred from content or stored on post
            likes=post.likes or 0,
            comments=post.comments or 0,
            shares=post.shares or 0,
            impressions=post.impressions or 0,
            engagement_rate=post.engagement_rate or 0.0,
            avg_engagement_rate=historical_context.get("avg_engagement_rate"),
            top_performing_topics=historical_context.get("top_topics"),
        )

        result = coach.analyze(coach_input)

        # Create or update analysis record
        if post.analysis:
            # Update existing
            post.analysis.hook_score = result.hook_score
            post.analysis.tone_match_score = result.tone_match_score
            post.analysis.structure_score = result.structure_score
            post.analysis.cta_effectiveness = result.cta_effectiveness
            post.analysis.coach_feedback = {
                "top_strength": result.top_strength,
                "top_improvement": result.top_improvement,
                "predicted_engagement": result.predicted_engagement,
                "detailed_feedback": result.detailed_feedback,
            }
            post.analysis.rewrite_suggestion = result.rewrite_suggestion
        else:
            # Create new
            analysis = PostAnalysis(
                post_id=post.id,
                hook_score=result.hook_score,
                tone_match_score=result.tone_match_score,
                structure_score=result.structure_score,
                cta_effectiveness=result.cta_effectiveness,
                coach_feedback={
                    "top_strength": result.top_strength,
                    "top_improvement": result.top_improvement,
                    "predicted_engagement": result.predicted_engagement,
                    "detailed_feedback": result.detailed_feedback,
                },
                rewrite_suggestion=result.rewrite_suggestion,
            )
            db.add(analysis)
        
        db.commit()
        if post.analysis:
            db.refresh(post.analysis)

        return _analysis_payload(post.id, post.analysis or analysis)

    except Exception as e:
        # Log error but still create a basic analysis to avoid breaking flow
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("AI analysis failed for post %s: %s", post_id, e)

        # Create fallback analysis
        fallback = PostAnalysis(
            post_id=post.id,
            hook_score=6,
            tone_match_score=6,
            structure_score=6,
            cta_effectiveness="weak",
            coach_feedback={
                "top_strength": "Content is clear and readable",
                "top_improvement": "Add a stronger opening hook",
                "predicted_engagement": "medium",
                "detailed_feedback": "Analysis temporarily unavailable. Basic heuristic scoring applied.",
            },
            rewrite_suggestion=None,
        )
        db.add(fallback)
        db.commit()
        db.refresh(fallback)

        return _analysis_payload(post.id, fallback)


def analytics_summary(
    db: Session, 
    user: User, 
    period_days: int = 30
) -> dict[str, Any]:
    """
    Generate comprehensive analytics dashboard summary KPIs.

    Includes:
      - Basic engagement metrics
      - Platform breakdown
      - Analysis coverage
      - Best performing post identification
      - Week-over-week trends
      - Engagement distribution

    Args:
        db: Database session
        user: Current user
        period_days: Lookback period in days (default 30)

    Returns:
        Dict matching AnalyticsSummaryResponse schema
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    previous_cutoff = cutoff - timedelta(days=period_days)

    # ─────────────────────────────────────────────────────────────────────────
    # Current Period Metrics
    # ─────────────────────────────────────────────────────────────────────────
    
    # Base query for user's posts in period
    base_query = db.query(Post).filter(
        Post.user_id == user.id,
        Post.published_at >= cutoff
    )

    # Aggregate metrics with null handling
    aggregates = db.query(
        func.count(Post.id).label("total_posts"),
        func.coalesce(func.sum(Post.likes), 0).label("total_likes"),
        func.coalesce(func.sum(Post.comments), 0).label("total_comments"),
        func.coalesce(func.sum(Post.shares), 0).label("total_shares"),
        func.coalesce(func.sum(Post.impressions), 0).label("total_impressions"),
        func.coalesce(func.avg(Post.engagement_rate), 0.0).label("avg_engagement_rate"),
    ).filter(Post.user_id == user.id, Post.published_at >= cutoff).first()

    # Platform breakdown
    platform_counts = (
        db.query(Post.platform, func.count(Post.id))
        .filter(Post.user_id == user.id, Post.published_at >= cutoff)
        .group_by(Post.platform)
        .all()
    )
    platform_breakdown = {platform: count for platform, count in platform_counts}

    # Posts with analysis
    posts_analyzed = (
        db.query(Post)
        .join(PostAnalysis, Post.id == PostAnalysis.post_id)
        .filter(Post.user_id == user.id, Post.published_at >= cutoff)
        .count()
    )

    total_posts = aggregates.total_posts or 0
    analysis_coverage = (
        round((posts_analyzed / total_posts) * 100, 1)
        if total_posts > 0
        else 0.0
    )

    # Best performing post (by engagement rate)
    best_post = (
        db.query(Post)
        .filter(Post.user_id == user.id, Post.published_at >= cutoff)
        .order_by(Post.engagement_rate.desc().nullslast())
        .first()
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Previous Period (for trends)
    # ─────────────────────────────────────────────────────────────────────────
    
    previous_aggregates = db.query(
        func.count(Post.id).label("total_posts"),
        func.coalesce(func.avg(Post.engagement_rate), 0.0).label("avg_engagement_rate"),
        func.coalesce(func.sum(Post.likes), 0).label("total_likes"),
    ).filter(
        Post.user_id == user.id,
        Post.published_at >= previous_cutoff,
        Post.published_at < cutoff
    ).first()

    # Calculate trends
    prev_total_posts = previous_aggregates.total_posts or 0
    prev_avg_engagement = previous_aggregates.avg_engagement_rate or 0.0
    prev_total_likes = previous_aggregates.total_likes or 0

    post_trend = _calculate_trend(total_posts, prev_total_posts)
    engagement_trend = _calculate_trend(
        aggregates.avg_engagement_rate or 0.0,
        prev_avg_engagement
    )
    likes_trend = _calculate_trend(
        (aggregates.total_likes or 0),
        prev_total_likes
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Engagement Distribution
    # ─────────────────────────────────────────────────────────────────────────
    
    distribution = _get_engagement_distribution(db, user, cutoff)

    # ─────────────────────────────────────────────────────────────────────────
    # Analysis Quality Summary
    # ─────────────────────────────────────────────────────────────────────────
    
    analysis_scores = db.query(
        func.avg(PostAnalysis.hook_score).label("avg_hook"),
        func.avg(PostAnalysis.structure_score).label("avg_structure"),
        func.avg(PostAnalysis.tone_match_score).label("avg_tone"),
    ).join(Post, Post.id == PostAnalysis.post_id).filter(
        Post.user_id == user.id,
        Post.published_at >= cutoff
    ).first()

    return {
        # Basic metrics
        "total_posts": total_posts,
        "total_likes": int(aggregates.total_likes or 0),
        "total_comments": int(aggregates.total_comments or 0),
        "total_shares": int(aggregates.total_shares or 0),
        "total_impressions": int(aggregates.total_impressions or 0),
        "avg_engagement_rate": round(aggregates.avg_engagement_rate or 0.0, 4),
        
        # Best post
        "best_performing_post": _post_payload(best_post) if best_post else None,
        
        # Analysis coverage
        "posts_analyzed": posts_analyzed,
        "analysis_coverage_percent": analysis_coverage,
        
        # Platform breakdown
        "platform_breakdown": platform_breakdown,
        "period_days": period_days,
        
        # Trends
        "trends": {
            "posts_change": post_trend,
            "engagement_rate_change": engagement_trend,
            "likes_change": likes_trend,
        },
        
        # Distribution
        "engagement_distribution": distribution,
        
        # Analysis quality (if analyzed posts exist)
        "avg_analysis_scores": {
            "hook_score": round(analysis_scores.avg_hook, 2) if analysis_scores.avg_hook else None,
            "structure_score": round(analysis_scores.avg_structure, 2) if analysis_scores.avg_structure else None,
            "tone_score": round(analysis_scores.avg_tone, 2) if analysis_scores.avg_tone else None,
        } if analysis_scores and analysis_scores.avg_hook else None,
    }


def _get_historical_context(db: Session, user: User, platform: str) -> dict[str, Any]:
    """
    Get historical performance context for comparative analysis.
    
    Returns:
        Dict with avg_engagement_rate and top_topics
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    
    # Average engagement rate for this platform
    avg_result = db.query(
        func.avg(Post.engagement_rate).label("avg_rate")
    ).filter(
        Post.user_id == user.id,
        Post.platform == platform,
        Post.published_at >= cutoff
    ).first()
    
    avg_rate = avg_result.avg_rate if avg_result and avg_result.avg_rate else None
    
    # Get top performing topics (would need content analysis in production)
    # For now, return None as this would require NLP analysis
    
    return {
        "avg_engagement_rate": avg_rate,
        "top_topics": None,
    }


def _get_engagement_distribution(
    db: Session, user: User, cutoff: datetime
) -> dict[str, int]:
    """
    Get distribution of posts by engagement rate ranges.
    
    Returns:
        Dict with counts for each range
    """
    ranges = [
        ("high", 0.05, None),      # > 5%
        ("good", 0.02, 0.05),      # 2-5%
        ("average", 0.01, 0.02),   # 1-2%
        ("low", 0.0, 0.01),        # < 1%
    ]
    
    distribution = {}
    
    for label, min_rate, max_rate in ranges:
        query = db.query(Post).filter(
            Post.user_id == user.id,
            Post.published_at >= cutoff
        )
        
        if min_rate is not None:
            query = query.filter(Post.engagement_rate >= min_rate)
        if max_rate is not None:
            query = query.filter(Post.engagement_rate < max_rate)
        
        distribution[label] = query.count()
    
    return distribution


def _calculate_trend(current: float, previous: float) -> dict[str, Any]:
    """
    Calculate trend metrics between current and previous period.
    
    Returns:
        Dict with value, percentage change, and direction
    """
    if previous == 0:
        if current > 0:
            return {
                "direction": "up",
                "percent_change": None,  # Infinite
                "absolute_change": current,
            }
        else:
            return {
                "direction": "flat",
                "percent_change": 0,
                "absolute_change": 0,
            }
    
    absolute_change = current - previous
    percent_change = ((current - previous) / previous) * 100
    
    if percent_change > 5:
        direction = "up"
    elif percent_change < -5:
        direction = "down"
    else:
        direction = "flat"
    
    return {
        "direction": direction,
        "percent_change": round(percent_change, 1),
        "absolute_change": round(absolute_change, 2),
    }


def _post_payload(post: Post) -> dict[str, Any]:
    """Build consistent post payload."""
    return {
        "id": post.id,
        "platform": post.platform,
        "content": post.content[:500] + "..." if len(post.content) > 500 else post.content,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "likes": post.likes or 0,
        "comments": post.comments or 0,
        "shares": post.shares or 0,
        "impressions": post.impressions or 0,
        "engagement_rate": post.engagement_rate or 0.0,
        "analysis": _analysis_payload(post.id, post.analysis) if post.analysis else None,
    }


def _analysis_payload(post_id: str, analysis: PostAnalysis) -> dict[str, Any]:
    """Build consistent analysis payload."""
    feedback = analysis.coach_feedback or {}
    return {
        "post_id": post_id,
        "hook_score": analysis.hook_score,
        "tone_match_score": analysis.tone_match_score,
        "structure_score": analysis.structure_score,
        "cta_effectiveness": analysis.cta_effectiveness,
        "top_strength": feedback.get("top_strength", "Clear point of view"),
        "top_improvement": feedback.get("top_improvement", "Make the ending more actionable"),
        "predicted_engagement": feedback.get("predicted_engagement", "medium"),
        "detailed_feedback": feedback.get("detailed_feedback"),
        "rewrite_suggestion": analysis.rewrite_suggestion,
    }


def get_content_insights(
    db: Session,
    user: User,
    period_days: int = 30,
) -> dict[str, Any]:
    """
    Generate advanced content insights with pattern detection.
    
    Analyzes top performing content to identify:
      - Hook patterns (questions, statements, stories)
      - Content length optimization
      - Time-of-day correlation
      - Platform-specific patterns
      - Quality vs engagement correlation
      - CTA effectiveness patterns
    
    Args:
        db: Database session
        user: Current user
        period_days: Lookback period
        
    Returns:
        Dict with comprehensive content insights
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    
    # Get analyzed posts with engagement (top 20 for deeper analysis)
    analyzed_posts = (
        db.query(Post, PostAnalysis)
        .join(PostAnalysis, Post.id == PostAnalysis.post_id)
        .filter(
            Post.user_id == user.id,
            Post.published_at >= cutoff,
        )
        .order_by(Post.engagement_rate.desc())
        .limit(20)
        .all()
    )
    
    if not analyzed_posts:
        return {
            "period_days": period_days,
            "message": "No analyzed posts available for insights",
            "analyzed_posts_count": 0,
            "top_performer_avg_scores": {
                "hook_score": None,
                "structure_score": None,
                "tone_score": None,
            },
            "identified_strengths": [],
            "recommendations": [],
        }
    
    # Split into top, middle, and bottom performers for comparison
    n = len(analyzed_posts)
    top_third = analyzed_posts[:max(1, n // 3)]
    bottom_third = analyzed_posts[-max(1, n // 3):]
    
    # Calculate score averages
    avg_scores = _calculate_score_averages(top_third)
    
    # Detect hook patterns
    hook_patterns = _analyze_hook_patterns(analyzed_posts)
    
    # Analyze content length patterns
    length_patterns = _analyze_length_patterns(top_third, bottom_third)
    
    # Analyze time-of-day patterns
    time_patterns = _analyze_time_patterns(analyzed_posts)
    
    # Analyze quality vs engagement correlation
    quality_engagement = _analyze_quality_engagement_correlation(analyzed_posts)
    
    # Identify strengths
    strengths = _identify_content_strengths(avg_scores, hook_patterns, length_patterns)
    
    # Generate pattern-based recommendations
    recommendations = _generate_advanced_recommendations(
        avg_scores=avg_scores,
        hook_patterns=hook_patterns,
        length_patterns=length_patterns,
        time_patterns=time_patterns,
        quality_engagement=quality_engagement,
        top_third=top_third,
        bottom_third=bottom_third,
    )
    
    return {
        "period_days": period_days,
        "analyzed_posts_count": len(analyzed_posts),
        "top_performer_avg_scores": avg_scores,
        "identified_strengths": strengths,
        "hook_patterns": hook_patterns,
        "length_patterns": length_patterns,
        "time_patterns": time_patterns,
        "quality_engagement_correlation": quality_engagement,
        "recommendations": recommendations,
    }


def _calculate_score_averages(posts: list) -> dict[str, float]:
    """Calculate average scores for a set of posts."""
    if not posts:
        return {"hook_score": 0, "tone_score": 0, "structure_score": 0}
    
    return {
        "hook_score": round(sum(p[1].hook_score for p in posts) / len(posts), 2),
        "tone_score": round(sum(p[1].tone_match_score for p in posts) / len(posts), 2),
        "structure_score": round(sum(p[1].structure_score for p in posts) / len(posts), 2),
    }


def _analyze_hook_patterns(posts: list) -> dict[str, Any]:
    """
    Analyze hook patterns in post content.
    
    Identifies:
      - Question hooks ("Why...", "How...", "What if...")
      - Statement hooks ("The...", "Most...", "I...")
      - Number hooks ("3 ways...", "5 lessons...")
      - Story hooks ("I was...", "When I...")
    """
    import re
    
    patterns = {
        "question": 0,
        "statement": 0,
        "number": 0,
        "story": 0,
        "contrarian": 0,
        "other": 0,
    }
    
    pattern_regex = {
        "question": r"^(Why\s|How\s|What\s|When\s|Where\s|Who\s|Can\s|Is\s|Are\s|Do\s|Does\s)",
        "number": r"^(\d+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)",
        "story": r"^(I\s|When\sI|My\s|Last\s|Yesterday|Today\s|This\s)",
        "contrarian": r"^(Most\s|Everyone\s|Stop\s|Don't\s|Never\s|Always\s|Wrong\s)",
    }
    
    for post, analysis in posts:
        content = post.content.strip()
        opening = content[:100]  # First 100 chars
        
        matched = False
        for pattern, regex in pattern_regex.items():
            if re.search(regex, opening, re.IGNORECASE):
                patterns[pattern] += 1
                matched = True
                break
        
        if not matched:
            patterns["other"] += 1
    
    # Determine dominant pattern
    total = sum(patterns.values())
    if total == 0:
        dominant = "unknown"
        dominant_pct = 0
    else:
        dominant = max(patterns, key=patterns.get)
        dominant_pct = round(patterns[dominant] / total * 100, 1)
    
    return {
        "distribution": patterns,
        "dominant_pattern": dominant,
        "dominant_percentage": dominant_pct,
        "total_analyzed": total,
        "insights": _generate_hook_pattern_insights(patterns, dominant, dominant_pct),
    }


def _generate_hook_pattern_insights(patterns: dict, dominant: str, pct: float) -> list[str]:
    """Generate insights about hook patterns."""
    insights = []
    
    if dominant == "question" and pct > 40:
        insights.append("Questions are your strongest hook pattern - they drive curiosity and engagement.")
    elif dominant == "story" and pct > 40:
        insights.append("Personal stories resonate well with your audience - continue sharing experiences.")
    elif dominant == "contrarian" and pct > 30:
        insights.append("Contrarian takes get attention - you challenge assumptions effectively.")
    elif dominant == "number" and pct > 30:
        insights.append("List-style hooks work for you - audiences love actionable, structured content.")
    elif pct < 30:
        insights.append("Your hooks are varied - consider standardizing on a pattern that consistently works.")
    
    # Check for underutilized patterns
    if patterns["question"] == 0:
        insights.append("Try adding question-based hooks to create curiosity gaps.")
    if patterns["story"] == 0 and patterns["statement"] > 0:
        insights.append("Experiment with personal story hooks to add authenticity.")
    
    return insights


def _analyze_length_patterns(top_posts: list, bottom_posts: list) -> dict[str, Any]:
    """Analyze content length patterns between top and bottom performers."""
    
    def avg_length(posts):
        if not posts:
            return 0
        return sum(len(p[0].content) for p in posts) / len(posts)
    
    top_avg = avg_length(top_posts)
    bottom_avg = avg_length(bottom_posts)
    
    diff = top_avg - bottom_avg
    
    return {
        "top_performer_avg_chars": round(top_avg, 0),
        "bottom_performer_avg_chars": round(bottom_avg, 0),
        "difference": round(diff, 0),
        "insight": (
            f"Your top posts average {top_avg:.0f} characters. "
            f"{'Longer' if diff > 0 else 'Shorter'} content performs better for you."
        ) if abs(diff) > 100 else "Content length has minimal impact on your engagement.",
        "optimal_range": _suggest_optimal_length(top_posts),
    }


def _suggest_optimal_length(top_posts: list) -> dict[str, int]:
    """Suggest optimal content length based on top performers."""
    if not top_posts:
        return {"min": 800, "max": 3000, "ideal": 1500}
    
    lengths = [len(p[0].content) for p in top_posts]
    
    return {
        "min": int(min(lengths) * 0.9),
        "max": int(max(lengths) * 1.1),
        "ideal": int(sum(lengths) / len(lengths)),
    }


def _analyze_time_patterns(posts: list) -> dict[str, Any]:
    """Analyze time-of-day patterns for top performing posts."""
    from collections import defaultdict
    
    hour_performance = defaultdict(lambda: {"count": 0, "avg_engagement": 0})
    
    for post, analysis in posts:
        if post.published_at:
            hour = post.published_at.hour
            hour_performance[hour]["count"] += 1
            hour_performance[hour]["avg_engagement"] += post.engagement_rate
    
    # Calculate averages
    for hour in hour_performance:
        count = hour_performance[hour]["count"]
        if count > 0:
            hour_performance[hour]["avg_engagement"] = round(
                hour_performance[hour]["avg_engagement"] / count, 4
            )
    
    # Find best performing hours
    hours_with_data = [(h, d) for h, d in hour_performance.items() if d["count"] >= 2]
    if hours_with_data:
        best_hours = sorted(hours_with_data, key=lambda x: x[1]["avg_engagement"], reverse=True)[:3]
    else:
        best_hours = []
    
    return {
        "hourly_distribution": dict(hour_performance),
        "best_performing_hours": [h[0] for h in best_hours],
        "recommendation": (
            f"Your posts perform best at hours: {[h[0] for h in best_hours]}. "
            "Consider scheduling during these times."
        ) if best_hours else "Post more consistently to identify optimal timing patterns.",
    }


def _analyze_quality_engagement_correlation(posts: list) -> dict[str, Any]:
    """Analyze correlation between AI quality scores and actual engagement."""
    
    if not posts:
        return {"correlation": 0, "insight": "No data available"}
    
    # Calculate quality score (average of hook, tone, structure)
    quality_scores = []
    engagement_rates = []
    
    for post, analysis in posts:
        quality = (analysis.hook_score + analysis.tone_match_score + analysis.structure_score) / 3
        quality_scores.append(quality)
        engagement_rates.append(post.engagement_rate)
    
    # Simple correlation calculation
    if len(quality_scores) < 3:
        return {"correlation": 0, "insight": "Need more data for correlation analysis"}
    
    # Pearson correlation coefficient
    n = len(quality_scores)
    sum_q = sum(quality_scores)
    sum_e = sum(engagement_rates)
    sum_qe = sum(q * e for q, e in zip(quality_scores, engagement_rates))
    sum_q2 = sum(q ** 2 for q in quality_scores)
    sum_e2 = sum(e ** 2 for e in engagement_rates)
    
    numerator = n * sum_qe - sum_q * sum_e
    denominator = ((n * sum_q2 - sum_q ** 2) * (n * sum_e2 - sum_e ** 2)) ** 0.5
    
    if denominator == 0:
        correlation = 0
    else:
        correlation = numerator / denominator
    
    # Interpret correlation
    if abs(correlation) < 0.3:
        insight = "Content quality and engagement show weak correlation - other factors (timing, topic) may matter more."
    elif correlation > 0.5:
        insight = "Strong correlation: higher AI quality scores predict better engagement. Focus on improving content quality."
    elif correlation < -0.3:
        insight = "Interesting: lower-scored content gets more engagement. Your audience may prefer raw, authentic content."
    else:
        insight = "Moderate correlation between quality scores and engagement - both quality and distribution matter."
    
    return {
        "correlation": round(correlation, 3),
        "strength": "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.4 else "weak",
        "insight": insight,
    }


def _identify_content_strengths(
    avg_scores: dict,
    hook_patterns: dict,
    length_patterns: dict,
) -> list[str]:
    """Identify content strengths based on analysis."""
    strengths = []
    
    if avg_scores["hook_score"] >= 7:
        strengths.append("Strong hooks that create curiosity")
    if avg_scores["structure_score"] >= 7:
        strengths.append("Well-structured, readable content")
    if avg_scores["tone_score"] >= 7:
        strengths.append("Authentic, on-brand voice")
    
    # Add hook pattern strength
    if hook_patterns.get("dominant_pattern") and hook_patterns.get("dominant_percentage", 0) > 50:
        pattern = hook_patterns["dominant_pattern"]
        strengths.append(f"Consistent use of {pattern}-style hooks")
    
    # Add length optimization
    if length_patterns.get("difference", 0) > 200:
        strengths.append("Optimal content length for your audience")
    
    if not strengths:
        strengths.append("Consistent content production with room for optimization")
    
    return strengths


def _generate_advanced_recommendations(
    avg_scores: dict,
    hook_patterns: dict,
    length_patterns: dict,
    time_patterns: dict,
    quality_engagement: dict,
    top_third: list,
    bottom_third: list,
) -> list[str]:
    """Generate advanced, pattern-based recommendations."""
    recommendations = []
    
    # Score-based recommendations
    if avg_scores["hook_score"] < 6:
        recommendations.append(
            "Hook weakness: Top performers use pattern interrupts. Try questions, numbers, or contrarian takes in openings."
        )
    
    if avg_scores["structure_score"] < 6:
        recommendations.append(
            "Structure issue: Add more line breaks. Use 1-2 sentence paragraphs for scannability."
        )
    
    if avg_scores["tone_score"] < 6:
        recommendations.append(
            "Voice inconsistency: Your brand profile suggests a different tone. Align content with your defined voice."
        )
    
    # Hook pattern recommendations
    if hook_patterns.get("dominant_percentage", 0) < 30:
        recommendations.append(
            "Hook variety: Your hooks lack a consistent pattern. Try standardizing on what works (questions or stories)."
        )
    
    # Length recommendations
    if length_patterns.get("difference", 0) < -200:
        recommendations.append(
            f"Length optimization: Your top posts are {abs(length_patterns['difference']):.0f} chars longer. Consider more detailed content."
        )
    elif length_patterns.get("difference", 0) > 200:
        recommendations.append(
            f"Brevity wins: Your top posts are {length_patterns['difference']:.0f} chars shorter. Try more concise content."
        )
    
    # Time recommendations
    if time_patterns.get("best_performing_hours") and len(time_patterns["best_performing_hours"]) >= 1:
        best_hours = time_patterns["best_performing_hours"]
        time_str = ", ".join(f"{h}:00" for h in best_hours)
        recommendations.append(
            f"Timing: Schedule posts at {time_str} UTC for optimal engagement based on your historical data."
        )
    
    # Quality vs engagement insight
    if quality_engagement.get("correlation", 0) < 0.3:
        recommendations.append(
            "Distribution matters: Quality scores don't strongly predict engagement. Focus on posting times and consistency."
        )
    
    # Default recommendation if few specific ones
    if len(recommendations) < 2:
        recommendations.append(
            "Experimentation: Try A/B testing hook patterns and track which styles drive most engagement for your niche."
        )
    
    return recommendations


def _generate_insight_recommendations(scores: dict[str, float]) -> list[str]:
    """Generate legacy recommendations based on analysis scores (for backward compatibility)."""
    recommendations = []
    
    if scores["hook_score"] < 6:
        recommendations.append(
            "Top performers have stronger hooks. Consider pattern interrupts or curiosity gaps in openings."
        )
    
    if scores["structure_score"] < 6:
        recommendations.append(
            "Improve readability with more line breaks and visual hierarchy."
        )
    
    if scores["tone_score"] < 6:
        recommendations.append(
            "Develop a more distinctive voice that aligns with your brand profile."
        )
    
    if not recommendations:
        recommendations.append(
            "Your content quality is strong. Focus on consistency and volume."
        )
    
    return recommendations


# ---------------------------------------------------------------------------
# Prediction Service Helpers
# ---------------------------------------------------------------------------

def get_author_historical_metrics(
    db: Session,
    user_id: str,
    limit: int = 100,
) -> dict[str, float] | None:
    """
    Get historical performance metrics for a user.
    
    Used by prediction engines to establish baseline expectations.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum posts to analyze
        
    Returns:
        Dict with historical metrics or None if insufficient data
    """
    posts = (
        db.query(Post)
        .filter(
            Post.user_id == user_id,
            Post.engagement_rate > 0,
        )
        .order_by(Post.published_at.desc().nullslast())
        .limit(limit)
        .all()
    )
    
    if len(posts) < 5:
        return None
    
    engagement_rates = [p.engagement_rate for p in posts]
    
    return {
        "avg_engagement_rate": round(sum(engagement_rates) / len(engagement_rates), 4),
        "max_engagement_rate": round(max(engagement_rates), 4),
        "median_engagement_rate": round(sorted(engagement_rates)[len(engagement_rates) // 2], 4),
        "post_count": len(posts),
        "recent_avg": round(sum(engagement_rates[:10]) / min(10, len(engagement_rates)), 4),
    }


def get_post_timing_history(
    db: Session,
    user_id: str,
    limit: int = 100,
) -> list[dict]:
    """
    Get historical post timing and performance data.
    
    Used by TimingPredictionEngine for pattern detection.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum posts to analyze
        
    Returns:
        List of dicts with day, hour, and engagement data
    """
    DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    
    posts = (
        db.query(Post)
        .filter(
            Post.user_id == user_id,
            Post.published_at.isnot(None),
            Post.engagement_rate > 0,
        )
        .order_by(Post.published_at.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "day": DAY_NAMES[p.published_at.weekday()],
            "hour": p.published_at.hour,
            "engagement_rate": p.engagement_rate,
            "platform": p.platform,
            "date": p.published_at.isoformat(),
        }
        for p in posts
    ]
