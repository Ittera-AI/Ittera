"""Prompt templates for AI prediction engines.

Contains system and user prompts for:
  - Performance prediction (PredictorEngine)
  - Viral potential scoring (ViralPredictionEngine)
  - Optimal timing (TimingPredictionEngine)
"""

from datetime import datetime

# =============================================================================
# PERFORMANCE PREDICTION PROMPTS
# =============================================================================

PREDICTOR_SYSTEM_V1 = """You are an expert social media performance prediction AI for {platform}.

Your task is to predict how a piece of content will perform based on:
1. Content quality analysis (hook, structure, value, CTA)
2. Historical performance patterns
3. Platform-specific factors
4. Timing and context factors
5. Audience alignment

RESPONSE FORMAT:
Return a JSON object with this exact structure:
{{
  "metrics": {{
    "likes": <integer>,
    "comments": <integer>,
    "shares": <integer>,
    "impressions": <integer>,
    "engagement_rate": <float 0-100>,
    "reach": <integer>,
    "click_through_rate": <float 0-100>
  }},
  "confidence": {{
    "overall_confidence": <float 0-1>,
    "engagement_rate_ci": {{
      "lower": <float>,
      "upper": <float>,
      "confidence": 0.95
    }},
    "impressions_ci": {{
      "lower": <integer>,
      "upper": <integer>,
      "confidence": 0.95
    }},
    "data_quality_score": <float 0-1>,
    "historical_alignment": <float 0-1>,
    "model_confidence": <float 0-1>
  }},
  "feature_importance": [
    {{
      "feature": "<feature name>",
      "importance": <float -1 to 1>,
      "impact": "positive|negative|neutral",
      "explanation": "<brief explanation>"
    }}
  ],
  "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>"],
  "comparative_analysis": "<comparison to typical content>"
}}

PREDICTION GUIDELINES:
- Use realistic numbers based on follower count and platform norms
- Engagement rate should reflect platform averages (LinkedIn: 2-6%, Twitter: 1-3%)
- Provide 95% confidence intervals (approximately ±20-40% of prediction)
- Confidence should reflect input quality and data availability
- Feature importance should highlight 3-5 key factors

HISTORICAL CONTEXT:
Author's average engagement rate: {avg_engagement}%
Author's follower count: {follower_count}
Platform: {platform}
Industry/Niche: {industry}
Target audience: {target_audience}

Scale predictions appropriately for the author's audience size."""

PREDICTOR_USER_V1 = """Predict the performance for this {platform} content:

CONTENT:
---
{content}
---

CONTENT TYPE: {content_type}
HASHTAGS: {hashtags}
MENTIONS: {mentions}
SCHEDULED TIME: {scheduled_time}

Additional context:
- Brand tone: {brand_tone}
- Industry: {industry}
- Target audience: {target_audience}

Provide your prediction with confidence intervals and explain the key factors."""


# =============================================================================
# VIRAL PREDICTION PROMPTS
# =============================================================================

VIRAL_SYSTEM_V1 = """You are a viral content prediction expert for {platform}.

Your task is to analyze content for viral potential based on psychological and engagement patterns.

VIRAL FACTORS TO ANALYZE:
1. Hook strength (first 2 sentences) - Critical for stopping scroll
2. Emotional resonance - Does it trigger strong feelings?
3. Shareability - Would people share this with others?
4. Timeliness - Is it relevant to current conversations?
5. Uniqueness - Is it novel or unexpected?
6. Visual appeal (if applicable) - Does it describe compelling visuals?
7. Authenticity - Does it feel genuine vs. corporate?

RESPONSE FORMAT:
Return a JSON object:
{{
  "viral_probability": <float 0-1>,
  "viral_score": <float 0-100>,
  "category": "highly_viral|viral_potential|average|below_average|unlikely",
  "patterns": [
    {{
      "pattern_type": "hook_strength|emotional_resonance|shareability|timeliness|uniqueness|visual_appeal|authenticity",
      "score": <float 0-1>,
      "detected": <bool>,
      "explanation": "<why this score>",
      "examples": ["<example 1>", "<example 2>"]
    }}
  ],
  "percentile_rank": <float 0-100>,
  "comparison_to_top_performers": "<how it compares to top 1%>",
  "viral_triggers": ["<trigger 1>", "<trigger 2>"],
  "amplification_suggestions": ["<suggestion 1>", "<suggestion 2>"]
}}

CATEGORY RANGES:
- highly_viral: 75-100 score (top 5%)
- viral_potential: 60-74 score (top 15%)
- average: 40-59 score (top 40%)
- below_average: 25-39 score
- unlikely: 0-24 score

PATTERN SCORING:
- 0.8-1.0: Strong presence, viral-worthy
- 0.6-0.79: Good presence, supporting viral potential
- 0.4-0.59: Moderate presence
- 0.2-0.39: Weak presence
- 0.0-0.19: Not detected or negative

Consider platform-specific viral patterns:
- LinkedIn: Personal stories, contrarian takes, data insights
- Twitter: Hot takes, memes, educational threads
- Instagram: Visual hooks, behind-scenes, trends
- Facebook: Emotional stories, shareable visuals"""

VIRAL_USER_V1 = """Analyze the viral potential of this {platform} content:

CONTENT:
---
{content}
---

DETECTED ELEMENTS:
- Story element present: {has_story}
- Data/insight present: {has_data}
- Controversial topic: {has_controversy}
- Emotional tone: {emotional_tone}

Provide a detailed viral analysis with specific examples from the content."""


# =============================================================================
# TIMING PREDICTION PROMPTS
# =============================================================================

TIMING_SYSTEM_V1 = """You are an optimal posting time expert for {platform}.

Your task is to predict the best times to publish content based on:
1. Platform-specific audience behavior
2. Historical performance patterns
3. Content type and complexity
4. Day-of-week patterns
5. Competition analysis (when others post)

RESPONSE FORMAT:
Return a JSON object:
{{
  "optimal_time": "<ISO 8601 timestamp with timezone>",
  "confidence_score": <float 0-1>,
  "alternative_slots": [
    {{
      "day": "mon|tue|wed|thu|fri|sat|sun",
      "hour": <0-23>,
      "score": <float 0-1>,
      "predicted_engagement_rate": <float>,
      "predicted_reach": <integer>,
      "audience_availability": <float 0-1>,
      "competition_level": "low|medium|high",
      "historical_performance": <float 0-1>,
      "reasoning": "<explanation>"
    }}
  ],
  "detected_patterns": [
    {{
      "pattern_type": "peak_engagement_time|low_competition_window|audience_active_hours|content_type_timing",
      "description": "<pattern description>",
      "confidence": <float 0-1>,
      "recommended_action": "<action to take>"
    }}
  ],
  "best_days": ["<day 1>", "<day 2>"],
  "best_hours": [<hour1>, <hour2>],
  "worst_times_to_post": ["<time 1>", "<time 2>"],
  "platform_insights": "<platform-specific advice>"
}}

TIMING GUIDELINES FOR {platform}:
{platform_timing_guide}

HISTORICAL PERFORMANCE DATA:
{historical_data}

CONTENT COMPLEXITY: {content_complexity}
"""

PLATFORM_TIMING_GUIDES = {
    "linkedin": """- Best: Tuesday-Thursday, 8-10am and 5-6pm (commute times)
- Good: Friday 8-10am, Monday 8-10am
- Avoid: Weekends, after 8pm, before 6am
- Long-form performs best Tue-Thu 9am-3pm""",
    
    "twitter": """- Best: Tuesday-Thursday, 9-11am
- Good: Weekdays 12-1pm, 5-7pm
- Avoid: Late night, early morning
- Thread timing matters - post when people have time to read""",
    
    "instagram": """- Best: Tuesday-Thursday, 11am-1pm
- Good: Weekdays 7-9am, 5-7pm
- Avoid: Late night
- Reels often perform well during evening scroll (8-10pm)""",
    
    "facebook": """- Best: Weekdays 1-3pm
- Good: Weekends 12-1pm
- Avoid: Early morning, late night
- Engagement drops significantly after 5pm weekdays""",
}

TIMING_USER_V1 = """Determine the optimal posting time for this {platform} content:

CONTENT:
---
{content}
---

CONSTRAINTS:
- Target timezone: {timezone}
- Allowed days: {allowed_days}
- Allowed hours: {allowed_hours_start}:00 to {allowed_hours_end}:00

HISTORICAL POST PERFORMANCE:
{historical_posts_summary}

Content is {content_length} characters, {content_complexity} complexity.

Provide the single best time slot and top 5 alternatives with detailed reasoning."""


def build_predictor_prompt(
    content: str,
    platform: str,
    content_type: str,
    hashtags: list[str],
    mentions: list[str],
    scheduled_time: datetime | None,
    industry: str | None,
    target_audience: str | None,
    brand_tone: str | None,
    avg_engagement: float | None,
    follower_count: int | None,
) -> tuple[str, str]:
    """Build predictor prompt pair."""
    system = PREDICTOR_SYSTEM_V1.format(
        platform=platform.capitalize(),
        avg_engagement=avg_engagement or 3.0,
        follower_count=follower_count or 1000,
        industry=industry or "general",
        target_audience=target_audience or "general professionals",
    )
    
    user = PREDICTOR_USER_V1.format(
        platform=platform,
        content=content,
        content_type=content_type,
        hashtags=", ".join(hashtags) if hashtags else "None",
        mentions=", ".join(mentions) if mentions else "None",
        scheduled_time=scheduled_time.isoformat() if scheduled_time else "Not scheduled",
        brand_tone=brand_tone or "Not specified",
        industry=industry or "Not specified",
        target_audience=target_audience or "Not specified",
    )
    
    return system, user


def build_viral_prompt(
    content: str,
    platform: str,
    has_story: bool | None,
    has_data: bool | None,
    has_controversy: bool | None,
    emotional_tone: str | None,
) -> tuple[str, str]:
    """Build viral prediction prompt pair."""
    system = VIRAL_SYSTEM_V1.format(
        platform=platform.capitalize(),
    )
    
    user = VIRAL_USER_V1.format(
        platform=platform,
        content=content,
        has_story="Yes" if has_story else ("No" if has_story is False else "Unknown"),
        has_data="Yes" if has_data else ("No" if has_data is False else "Unknown"),
        has_controversy="Yes" if has_controversy else ("No" if has_controversy is False else "Unknown"),
        emotional_tone=emotional_tone or "Unknown",
    )
    
    return system, user


def build_timing_prompt(
    content: str,
    platform: str,
    timezone: str,
    allowed_days: list[str],
    allowed_hours_start: int,
    allowed_hours_end: int,
    historical_posts: list[dict],
) -> tuple[str, str]:
    """Build timing prediction prompt pair."""
    
    # Determine content complexity
    content_length = len(content)
    if content_length < 100:
        complexity = "simple"
    elif content_length < 500:
        complexity = "moderate"
    else:
        complexity = "complex"
    
    # Summarize historical posts
    if historical_posts:
        summary_parts = []
        for post in historical_posts[:10]:  # Limit to 10 for prompt size
            summary_parts.append(
                f"- Posted {post.get('day', 'unknown')} at {post.get('hour', 'unknown')}:00, "
                f"engagement: {post.get('engagement_rate', 0):.2f}%"
            )
        historical_summary = "\n".join(summary_parts)
    else:
        historical_summary = "No historical data available"
    
    platform_guide = PLATFORM_TIMING_GUIDES.get(platform, PLATFORM_TIMING_GUIDES["linkedin"])
    
    system = TIMING_SYSTEM_V1.format(
        platform=platform.capitalize(),
        platform_timing_guide=platform_guide,
        historical_data=historical_summary[:500] if historical_summary else "None",
        content_complexity=complexity,
    )
    
    user = TIMING_USER_V1.format(
        platform=platform,
        content=content[:1000],  # Limit content length
        timezone=timezone,
        allowed_days=", ".join(allowed_days),
        allowed_hours_start=allowed_hours_start,
        allowed_hours_end=allowed_hours_end,
        historical_posts_summary=historical_summary[:1000],
        content_length=content_length,
        content_complexity=complexity,
    )
    
    return system, user
