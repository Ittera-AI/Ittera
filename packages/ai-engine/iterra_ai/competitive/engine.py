"""CompetitiveAnalysisEngine: AI-powered competitor intelligence.

Analyzes competitor content strategies to identify:
- Content gaps and opportunities
- Successful tactics and themes
- Competitive positioning
- Trend performance benchmarking

Features:
- Strategy pattern detection
- Content gap analysis
- Trend benchmarking
- Actionable recommendations
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any

from openai import OpenAI

from iterra_ai.competitive.schemas import (
    CompetitorProfileInput,
    CompetitorStrategyOutput,
    ContentGapAnalysisInput,
    ContentGapOutput,
    TrendBenchmarkInput,
    TrendBenchmarkOutput,
)

logger = logging.getLogger(__name__)


class CompetitiveAnalysisEngine:
    """
    AI engine for competitive intelligence analysis.
    
    Provides three main analysis types:
    1. Competitor Strategy Analysis - Deep dive into a competitor's approach
    2. Content Gap Analysis - Identify topics and formats you're missing
    3. Trend Benchmarking - Compare performance on specific trends
    """
    
    SYSTEM_PROMPT_STRATEGY = """You are a competitive intelligence analyst for social media content.

Your task is to analyze competitor content and extract actionable insights about their strategy.

ANALYSIS FRAMEWORK:
1. Content Strategy
   - What topics do they focus on?
   - What's their unique angle/positioning?
   - How do they differentiate?

2. Posting Patterns
   - Frequency and timing
   - Content formats (text, images, video, carousels)
   - Consistency and scheduling

3. Engagement Tactics
   - How do they drive interaction?
   - CTA strategies
   - Community building techniques

4. Content Quality
   - Hook patterns
   - Storytelling techniques
   - Value delivery methods

5. Competitive Positioning
   - Their strengths vs weaknesses
   - Comparison to author's position
   - Market differentiation

RESPONSE FORMAT:
Return a JSON object with this structure:
{{
  "content_strategy": {{
    "primary_topics": ["topic1", "topic2"],
    "positioning": "How they position themselves",
    "unique_angle": "What makes them different",
    "content_pillars": ["pillar1", "pillar2"]
  }},
  "posting_patterns": {{
    "frequency": "Daily|3x/week|Weekly",
    "optimal_times": ["9am", "5pm"],
    "formats_used": ["text", "carousel", "video"],
    "consistency_score": 0.8
  }},
  "engagement_tactics": [
    "Tactic 1: description",
    "Tactic 2: description"
  ],
  "top_performing_themes": [
    {{
      "theme": "Theme name",
      "why_works": "Why this performs well",
      "examples": ["example content"]
    }}
  ],
  "content_format_preferences": ["format1", "format2"],
  "tone_and_voice": "Description of their tone",
  "competitive_advantages": [
    "Advantage 1: What they do better"
  ],
  "your_advantages": [
    "Your advantage 1: Where you're stronger"
  ],
  "opportunities": [
    {{
      "opportunity": "What to pursue",
      "rationale": "Why this works",
      "priority": "high|medium|low"
    }}
  ],
  "threats": [
    "Threat 1: Competitive risk"
  ],
  "recommended_actions": [
    "Specific action 1",
    "Specific action 2"
  ],
  "content_ideas_inspired_by": [
    "Content idea 1",
    "Content idea 2"
  ],
  "confidence_score": 0.75
}}

Be specific and data-driven. Reference actual post examples where possible."""

    SYSTEM_PROMPT_GAPS = """You are a content strategy analyst specializing in competitive gap analysis.

Your task is to identify content gaps between the author and their competitors - topics, formats, and approaches that competitors are using successfully but the author is missing.

GAP ANALYSIS FRAMEWORK:

1. Topic Coverage Gaps
   - What topics do competitors cover that author doesn't?
   - What's the engagement potential of those topics?
   - Are there underserved angles within covered topics?

2. Format Gaps
   - What content formats are competitors using?
   - Which formats perform best for competitors?
   - What formats is the author underutilizing?

3. Audience Gaps
   - Are there audience segments competitors reach that the author doesn't?
   - What pain points are being addressed?
   - What content depth levels are covered?

4. Timing/Frequency Gaps
   - How does competitor posting frequency compare?
   - Are there timing opportunities being missed?

PRIORITIZATION CRITERIA:
- High Impact: High engagement potential, aligned with author niche
- Quick Wins: Easy to implement, proven performance
- Strategic: Long-term opportunities worth investing in

RESPONSE FORMAT:
{{
  "covered_topics": [
    {{
      "topic": "Topic name",
      "coverage_quality": "strong|adequate|weak",
      "competitor_comparison": "How you compare"
    }}
  ],
  "gap_topics": [
    {{
      "topic": "Missing topic",
      "competitor_performance": "How well it does for them",
      "opportunity_score": 0.85,
      "why_valuable": "Why this matters",
      "difficulty": "easy|medium|hard"
    }}
  ],
  "underserved_topics": [
    {{
      "topic": "Low competition topic",
      "rationale": "Why it's available",
      "potential": "high|medium|low"
    }}
  ],
  "format_gaps": [
    {{
      "format": "Missing format",
      "competitor_usage": "How they use it",
      "your_opportunity": "Why you should use it",
      "implementation_effort": "easy|medium|hard"
    }}
  ],
  "audience_segment_gaps": [
    {{
      "segment": "Audience segment",
      "competitor_approach": "How they address it",
      "your_gap": "What you're missing"
    }}
  ],
  "high_impact_opportunities": [
    {{
      "opportunity": "High priority gap",
      "expected_impact": "Why it's valuable",
      "effort_required": "Time/resources needed",
      "priority": 1
    }}
  ],
  "quick_wins": [
    "Quick win 1: Easy opportunity",
    "Quick win 2: Easy opportunity"
  ],
  "suggested_content_calendar": [
    {{
      "week": 1,
      "content_idea": "Specific content suggestion",
      "rationale": "Why this works",
      "format": "Recommended format"
    }}
  ],
  "competitors_analyzed": 3
}}"""

    SYSTEM_PROMPT_TREND = """You are a trend analysis expert comparing content performance on specific topics.

Your task is to analyze how different creators (author + competitors) perform on a specific trend/topic and identify success factors.

ANALYSIS FRAMEWORK:

1. Performance Ranking
   - Rank all creators by engagement rate on this topic
   - Calculate relative performance
   - Identify outliers (over/under performers)

2. Success Factor Analysis
   - What did top performers do differently?
   - Content format choices
   - Timing and presentation
   - Hook and angle selection
   - Engagement tactics

3. Gap Analysis
   - What do top performers do that others don't?
   - Common mistakes by lower performers
   - Missed opportunities

4. Trend Lifecycle Assessment
   - Is this trend growing, peaking, or declining?
   - How much time remains to capitalize?
   - Related emerging trends

5. Actionable Recommendations
   - Specific improvements for the author
   - Format/timing adjustments
   - Content strategy pivots

RESPONSE FORMAT:
{{
  "your_performance": {{
    "engagement_rate": 3.5,
    "rank": 3,
    "total_posts": 5,
    "best_performing_post": "Summary",
    "avg_reach": 1000
  }},
  "competitor_performances": [
    {{
      "competitor": "Name",
      "engagement_rate": 5.2,
      "rank": 1,
      "what_they_did_differently": "Key differentiators",
      "best_post_example": "Example"
    }}
  ],
  "your_rank": 3,
  "total_competitors": 5,
  "why_top_performers_succeeded": [
    "Reason 1: What worked",
    "Reason 2: What worked"
  ],
  "your_gaps_vs_top": [
    "Gap 1: What top did that you didn't",
    "Gap 2: What top did that you didn't"
  ],
  "trend_lifecycle": "emerging|peak|saturated|declining",
  "window_of_opportunity": "Time remaining to capitalize",
  "how_to_improve": [
    "Improvement 1: Specific action",
    "Improvement 2: Specific action"
  ],
  "similar_trends_to_watch": [
    "Related trend 1",
    "Related trend 2"
  ],
  "confidence_score": 0.75
}}"""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the competitive analysis engine."""
        self.client = OpenAI(
            api_key=api_key or os.getenv("AIML_API_KEY"),
            base_url=os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1"),
        )
        self.model = model or os.getenv("AIML_MODEL", "gpt-4o-mini")
        self.max_tokens = 4096
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> tuple[str, dict]:
        """Call the configured OpenAI-compatible API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content if response.choices else ""
            usage = {
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0),
            }
            return content or "", usage
        except Exception as e:
            logger.error(f"Competitive analysis LLM call failed: {e}")
            raise
    
    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from LLM response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        import re
        
        # Try markdown code block
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try finding JSON object
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not extract JSON: {text[:200]}")
    
    def analyze_competitor_strategy(
        self,
        input_data: CompetitorProfileInput,
    ) -> CompetitorStrategyOutput:
        """
        Deep dive analysis of a competitor's content strategy.
        
        Analyzes their posting patterns, content themes, engagement tactics,
        and identifies opportunities and threats.
        """
        import time
        start_time = time.time()
        
        # Build user prompt
        posts_summary = "\n\n".join([
            f"Post {i+1} ({p.get('published_at', 'unknown')}):\n{p.get('content', 'N/A')[:200]}...\n"
            f"Engagement: {p.get('engagement_rate', 'N/A')}%"
            for i, p in enumerate(input_data.recent_posts[:10])
        ])
        
        user_prompt = f"""Analyze this competitor's content strategy:

COMPETITOR: {input_data.competitor_name} (@{input_data.handle}) on {input_data.platform}
Followers: {input_data.follower_count or 'Unknown'}
Niche: {', '.join(input_data.niche_tags) if input_data.niche_tags else 'General'}

YOUR CONTEXT:
Your niche: {input_data.author_niche or 'Not specified'}
Your avg engagement: {input_data.author_avg_engagement or 'Not known'}%

RECENT POSTS (last {len(input_data.recent_posts)}):
{posts_summary}

Provide a comprehensive competitive analysis with actionable recommendations."""
        
        # Call LLM
        response_text, usage = self._call_llm(self.SYSTEM_PROMPT_STRATEGY, user_prompt)
        
        # Parse response
        try:
            response_json = self._extract_json(response_text)
        except ValueError as e:
            logger.error(f"Failed to parse strategy analysis: {e}")
            # Return basic fallback
            return self._generate_fallback_strategy(input_data)
        
        # Build output
        return CompetitorStrategyOutput(
            analysis_id=f"strategy_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{input_data.competitor_id[:8]}",
            competitor_id=input_data.competitor_id,
            analysis_type="strategy",
            content_strategy=response_json.get("content_strategy", {}),
            posting_patterns=response_json.get("posting_patterns", {}),
            engagement_tactics=response_json.get("engagement_tactics", []),
            top_performing_themes=response_json.get("top_performing_themes", []),
            content_format_preferences=response_json.get("content_format_preferences", []),
            tone_and_voice=response_json.get("tone_and_voice"),
            competitive_advantages=response_json.get("competitive_advantages", []),
            your_advantages=response_json.get("your_advantages", []),
            opportunities=response_json.get("opportunities", []),
            threats=response_json.get("threats", []),
            recommended_actions=response_json.get("recommended_actions", []),
            content_ideas_inspired_by=response_json.get("content_ideas_inspired_by", []),
            model_version="competitive-strategy-v1",
            analysis_time=datetime.utcnow(),
            posts_analyzed=len(input_data.recent_posts),
            confidence_score=response_json.get("confidence_score", 0.7),
        )
    
    def analyze_content_gaps(
        self,
        input_data: ContentGapAnalysisInput,
    ) -> ContentGapOutput:
        """
        Identify content gaps between author and competitors.
        
        Finds topics, formats, and approaches that competitors use
        successfully but the author doesn't cover.
        """
        # Build prompt
        author_topics = ", ".join(input_data.author_content_pillars)
        author_recent = ", ".join(input_data.author_recent_topics)
        competitor_themes = ", ".join(input_data.competitor_content_themes)
        
        user_prompt = f"""Analyze content gaps between the author and competitors:

AUTHOR CONTENT PILLARS:
{author_topics}

AUTHOR RECENT TOPICS:
{author_recent}

COMPETITOR THEMES:
{competitor_themes}

INDUSTRY TRENDS:
{', '.join(input_data.industry_trends)}

COMPETITOR POST EXAMPLES:
"""
        
        # Add competitor post samples
        for i, post in enumerate(input_data.competitor_posts[:5]):
            user_prompt += f"\nPost {i+1}: {post.get('content', 'N/A')[:150]}...\n"
        
        # Call LLM
        response_text, usage = self._call_llm(self.SYSTEM_PROMPT_GAPS, user_prompt)
        
        try:
            response_json = self._extract_json(response_text)
        except ValueError:
            return self._generate_fallback_gaps(input_data)
        
        return ContentGapOutput(
            analysis_id=f"gaps_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            covered_topics=response_json.get("covered_topics", []),
            gap_topics=response_json.get("gap_topics", []),
            underserved_topics=response_json.get("underserved_topics", []),
            format_gaps=response_json.get("format_gaps", []),
            audience_segment_gaps=response_json.get("audience_segment_gaps", []),
            high_impact_opportunities=response_json.get("high_impact_opportunities", []),
            quick_wins=response_json.get("quick_wins", []),
            suggested_content_calendar=response_json.get("suggested_content_calendar", []),
            model_version="gaps-v1",
            analysis_time=datetime.utcnow(),
            competitors_analyzed=len(input_data.competitor_posts),
        )
    
    def benchmark_trend(
        self,
        input_data: TrendBenchmarkInput,
    ) -> TrendBenchmarkOutput:
        """
        Compare author and competitor performance on a specific trend.
        
        Identifies why some creators succeed more than others on the same topic.
        """
        # Build prompt
        user_prompt = f"""Benchmark performance on the trend: "{input_data.trend_topic}"

TIME PERIOD: {input_data.time_period}

AUTHOR PERFORMANCE:
{json.dumps(input_data.author_performance, indent=2) if input_data.author_performance else 'No posts on this trend'}

COMPETITOR PERFORMANCES:
"""
        
        for comp in input_data.competitor_performances:
            user_prompt += f"\n{comp.get('competitor_name', 'Competitor')}:\n"
            user_prompt += f"  Engagement: {comp.get('engagement_rate', 'N/A')}%\n"
            user_prompt += f"  Best post: {comp.get('best_post', 'N/A')[:150]}...\n"
        
        # Call LLM
        response_text, usage = self._call_llm(self.SYSTEM_PROMPT_TREND, user_prompt)
        
        try:
            response_json = self._extract_json(response_text)
        except ValueError:
            return self._generate_fallback_trend(input_data)
        
        return TrendBenchmarkOutput(
            analysis_id=f"trend_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            trend_topic=input_data.trend_topic,
            your_performance=response_json.get("your_performance", {}),
            competitor_performances=response_json.get("competitor_performances", []),
            your_rank=response_json.get("your_rank"),
            total_competitors=response_json.get("total_competitors", len(input_data.competitor_performances) + 1),
            why_top_performers_succeeded=response_json.get("why_top_performers_succeeded", []),
            your_gaps_vs_top=response_json.get("your_gaps_vs_top", []),
            trend_lifecycle=response_json.get("trend_lifecycle", "emerging"),
            window_of_opportunity=response_json.get("window_of_opportunity"),
            how_to_improve=response_json.get("how_to_improve", []),
            similar_trends_to_watch=response_json.get("similar_trends_to_watch", []),
            model_version="trend-benchmark-v1",
            analysis_time=datetime.utcnow(),
        )
    
    def _generate_fallback_strategy(self, input_data: CompetitorProfileInput) -> CompetitorStrategyOutput:
        """Generate basic strategy analysis when LLM fails."""
        return CompetitorStrategyOutput(
            analysis_id=f"strategy_fallback_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            competitor_id=input_data.competitor_id,
            analysis_type="strategy",
            content_strategy={
                "primary_topics": input_data.niche_tags,
                "positioning": f"{input_data.competitor_name} on {input_data.platform}",
            },
            posting_patterns={},
            engagement_tactics=["Analyze posts manually for engagement patterns"],
            top_performing_themes=[],
            recommended_actions=["Re-run analysis with more sample posts"],
            model_version="fallback",
            analysis_time=datetime.utcnow(),
            posts_analyzed=len(input_data.recent_posts),
            confidence_score=0.3,
        )
    
    def _generate_fallback_gaps(self, input_data: ContentGapAnalysisInput) -> ContentGapOutput:
        """Generate basic gap analysis when LLM fails."""
        # Simple topic comparison
        author_set = set(t.lower() for t in input_data.author_content_pillars)
        competitor_set = set(t.lower() for t in input_data.competitor_content_themes)
        
        gaps = competitor_set - author_set
        
        return ContentGapOutput(
            analysis_id=f"gaps_fallback_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            gap_topics=[
                {"topic": g, "opportunity_score": 0.6, "difficulty": "unknown"}
                for g in gaps
            ],
            high_impact_opportunities=[
                {"opportunity": f"Explore topic: {g}", "priority": 1}
                for g in list(gaps)[:3]
            ],
            quick_wins=list(gaps)[:3],
            model_version="fallback",
            analysis_time=datetime.utcnow(),
        )
    
    def _generate_fallback_trend(self, input_data: TrendBenchmarkInput) -> TrendBenchmarkOutput:
        """Generate basic trend benchmark when LLM fails."""
        return TrendBenchmarkOutput(
            analysis_id=f"trend_fallback_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            trend_topic=input_data.trend_topic,
            your_performance=input_data.author_performance or {},
            trend_lifecycle="unknown",
            how_to_improve=["Analyze top performing posts manually"],
            model_version="fallback",
            analysis_time=datetime.utcnow(),
        )


# Global instance
_competitive_engine: CompetitiveAnalysisEngine | None = None


def get_competitive_engine(api_key: str | None = None) -> CompetitiveAnalysisEngine:
    """Get or create competitive analysis engine singleton."""
    global _competitive_engine
    if _competitive_engine is None:
        _competitive_engine = CompetitiveAnalysisEngine(api_key=api_key)
    return _competitive_engine
