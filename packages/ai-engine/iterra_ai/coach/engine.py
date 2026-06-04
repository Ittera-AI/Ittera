"""
EngagementCoach — AI-powered post analysis for engagement optimization.

Production-grade implementation with:
  - Sophisticated prompt engineering (few-shot, rubric-based)
  - Robust error handling with graceful degradation
  - Multi-provider LLM support (Anthropic Claude primary)
  - Token usage tracking and cost optimization
  - Response validation and repair
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from iterra_ai.coach.schemas import CoachInput, CoachOutput
from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.prompts.coach import format_coach_prompt, COACH_ANALYSIS_SYSTEM_V2

logger = logging.getLogger(__name__)


class CoachEngineError(Exception):
    """Base exception for coach engine errors."""
    pass


class LLMResponseError(CoachEngineError):
    """Raised when LLM response is invalid or unparseable."""
    pass


class EngagementCoach(BaseEngine[CoachInput, CoachOutput]):
    """
    Production-grade AI coach for social media post analysis.

    Features:
        - Uses Anthropic Claude 3.5 Sonnet for high-quality analysis
        - Sophisticated prompt engineering with few-shot examples
        - Robust JSON parsing with extraction fallback
        - Heuristic fallback when API unavailable
        - Token usage tracking

    Example:
        coach = EngagementCoach()
        result = coach.analyze(CoachInput(
            content="Your post content here...",
            platform="linkedin",
            voice_tone="Clear, analytical, opinionated",
        ))
    """

    # Default model - can be overridden via env or constructor
    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 2000
    TEMPERATURE = 0.2  # Lower for consistent scoring

    def __init__(self, model: str | None = None, use_v2_prompts: bool = True):
        """
        Initialize the EngagementCoach.

        Args:
            model: LLM model to use (defaults to Claude 3.5 Sonnet)
            use_v2_prompts: Use advanced V2 prompts with few-shot examples
        """
        super().__init__()
        self.model = model or os.getenv("AIML_MODEL", self.DEFAULT_MODEL)
        self.use_v2_prompts = use_v2_prompts
        self._system_prompt = COACH_ANALYSIS_SYSTEM_V2 if use_v2_prompts else None

    def analyze(self, input: CoachInput) -> CoachOutput:
        """
        Analyze a post and return detailed engagement feedback.

        Args:
            input: CoachInput with post content and context

        Returns:
            CoachOutput with scores, feedback, and suggestions

        Raises:
            CoachEngineError: If analysis fails and heuristic fallback also fails
        """
        # Check if API is available
        if not self._client and not os.getenv("AIML_API_KEY"):
            logger.warning("EngagementCoach: No API key available, using heuristic fallback")
            return self._heuristic_analyze(input)

        try:
            # Format prompts with all context
            system_prompt, user_prompt = format_coach_prompt(
                content=input.content,
                platform=input.platform,
                voice_tone=input.voice_tone,
                content_pillars=input.content_pillars,
                target_audience=input.target_audience,
                goal=input.goal,
                likes=input.likes,
                comments=input.comments,
                shares=input.shares,
                impressions=input.impressions,
                engagement_rate=input.engagement_rate,
                avg_engagement_rate=input.avg_engagement_rate,
                top_performing_topics=input.top_performing_topics,
                use_few_shot=self.use_v2_prompts,
            )

            logger.debug(
                "Analyzing post for %s (length=%d)",
                input.platform,
                len(input.content),
            )

            # Call LLM with retry logic in base engine
            raw_response = self._call_llm(
                system=system_prompt,
                user=user_prompt,
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE,
            )

            # Parse and validate response
            analysis_data = self._parse_llm_response(raw_response)

            # Build CoachOutput with validation
            return self._build_output(analysis_data, input)

        except Exception as e:
            logger.exception("EngagementCoach: LLM analysis failed: %s", e)
            # Fall back to heuristic analysis
            logger.info("Falling back to heuristic analysis")
            return self._heuristic_analyze(input)

    def generate(self, input: CoachInput) -> CoachOutput:
        """Alias for analyze() - BaseEngine compatibility."""
        return self.analyze(input)

    def _parse_llm_response(self, raw_response: str) -> dict[str, Any]:
        """
        Parse LLM response with multiple fallback strategies.

        Strategy 1: Direct JSON parsing
        Strategy 2: Extract JSON from markdown code blocks
        Strategy 3: Extract JSON-like structure with regex
        Strategy 4: Raise LLMResponseError if all fail

        Args:
            raw_response: Raw LLM output

        Returns:
            Parsed JSON dict

        Raises:
            LLMResponseError: If parsing fails after all strategies
        """
        response = raw_response.strip()

        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code blocks
        code_block_patterns = [
            r'```json\n(.*?)\n```',  # ```json\n...\n```
            r'```\n(.*?)\n```',      # ```\n...\n```
            r'```(.*?)```',          # ```...```
        ]
        for pattern in code_block_patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    continue

        # Strategy 3: Extract JSON-like structure
        # Look for content between first { and last }
        json_match = re.search(r'(\{.*\})', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 4: Log and raise
        logger.error(
            "Failed to parse LLM response after all strategies. Response preview: %s",
            response[:500],
        )
        raise LLMResponseError("Could not parse LLM response as JSON")

    def _build_output(self, data: dict[str, Any], input: CoachInput) -> CoachOutput:
        """
        Build CoachOutput from parsed LLM response with validation.

        Args:
            data: Parsed JSON data from LLM
            input: Original input for context

        Returns:
            Validated CoachOutput
        """
        # Validate and clamp scores to valid ranges
        hook_score = self._clamp_score(data.get("hook_score", 5))
        tone_match_score = self._clamp_score(data.get("tone_match_score", 5))
        structure_score = self._clamp_score(data.get("structure_score", 5))

        # Validate CTA effectiveness
        cta = data.get("cta_effectiveness", "weak")
        if cta not in ("strong", "weak", "none"):
            cta = "weak"

        # Validate predicted engagement
        predicted = data.get("predicted_engagement", "medium")
        if predicted not in ("low", "medium", "high"):
            predicted = "medium"

        # Build output with defaults for missing fields
        return CoachOutput(
            hook_score=hook_score,
            tone_match_score=tone_match_score,
            structure_score=structure_score,
            cta_effectiveness=cta,
            top_strength=data.get("top_strength", "Clear content structure"),
            top_improvement=data.get("top_improvement", "Add a stronger opening hook"),
            detailed_feedback=data.get("detailed_feedback"),
            predicted_engagement=predicted,
            rewrite_suggestion=data.get("rewrite_suggestion"),
        )

    def _clamp_score(self, score: int | float | None) -> int:
        """Clamp score to valid 0-10 range."""
        if score is None:
            return 5
        try:
            return max(0, min(10, int(score)))
        except (ValueError, TypeError):
            return 5

    def _heuristic_analyze(self, input: CoachInput) -> CoachOutput:
        """
        Production-grade heuristic analysis when LLM unavailable.

        Uses pattern matching and statistical heuristics calibrated
        against platform norms for reasonable estimates.
        """
        content = input.content.strip()
        
        # Platform-specific constants
        PLATFORM_CONFIG = {
            "linkedin": {"optimal_length": (800, 3000), "line_break_ideal": 4},
            "twitter": {"optimal_length": (100, 280), "line_break_ideal": 2},
            "instagram": {"optimal_length": (100, 2200), "line_break_ideal": 3},
        }
        config = PLATFORM_CONFIG.get(input.platform, PLATFORM_CONFIG["linkedin"])

        # Hook analysis (first 100 chars)
        opening = content[:100].lower()
        hook_score = 5  # baseline
        
        # Strong hook patterns
        strong_patterns = [
            r'\b(why |how |what |when |where )',
            r'\b(never |always |stop |start |most )',
            r'\d+\s+(ways?|tips?|lessons?|things?|reasons?)',
            r'[?!]',
            r'\b(i fired|i quit|i learned|i failed)',
        ]
        for pattern in strong_patterns:
            if re.search(pattern, opening):
                hook_score += 1
        
        # Weak hook patterns
        weak_patterns = [
            r'^i think',
            r'^today i',
            r'^just wanted',
            r'^sharing',
            r'^so ',
        ]
        for pattern in weak_patterns:
            if re.search(pattern, opening):
                hook_score -= 2
        
        hook_score = self._clamp_score(hook_score)

        # Structure analysis
        lines = content.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        
        structure_score = 5  # baseline
        
        # Optimal line break count
        if len(non_empty_lines) >= config["line_break_ideal"]:
            structure_score += 2
        elif len(non_empty_lines) > 1:
            structure_score += 1
        else:
            structure_score -= 2  # Wall of text
        
        # Length optimization
        content_length = len(content)
        min_len, max_len = config["optimal_length"]
        if min_len <= content_length <= max_len:
            structure_score += 1
        elif content_length < min_len:
            structure_score -= 1  # Too short
        
        # Has formatting (bullet points, emojis as separators)
        if re.search(r'([•\-\*]\s|\n\n)', content):
            structure_score += 1
        
        structure_score = self._clamp_score(structure_score)

        # Tone analysis (compare to target if available)
        tone_score = 6  # default neutral
        if input.voice_tone:
            voice_keywords = input.voice_tone.lower().split(',')
            content_lower = content.lower()
            matches = sum(1 for kw in voice_keywords if kw.strip() in content_lower)
            tone_score = 5 + min(matches, 3)
        tone_score = self._clamp_score(tone_score)

        # CTA analysis
        ending = content[-150:].lower()
        cta = "weak"
        if re.search(r'(comment|share|thoughts?|agree|disagree|\?)', ending):
            cta = "strong"
        elif re.search(r'(follow|click|dm|message|let me know)', ending):
            cta = "strong"
        elif len(ending.strip().split()) < 3:
            cta = "none"

        # Generate contextual feedback
        top_strength = self._identify_top_strength(
            hook_score, tone_score, structure_score, content
        )
        top_improvement = self._identify_top_improvement(
            hook_score, tone_score, structure_score, cta, content
        )

        # Predict engagement
        avg_score = (hook_score + tone_score + structure_score) / 3
        if cta == "strong":
            avg_score += 0.5
        
        if avg_score >= 7.5:
            predicted = "high"
        elif avg_score >= 5:
            predicted = "medium"
        else:
            predicted = "low"

        # Generate rewrite if hook is weak
        rewrite = None
        if hook_score < 6:
            rewrite = self._generate_rewrite_suggestion(content, input.platform)

        return CoachOutput(
            hook_score=hook_score,
            tone_match_score=tone_score,
            structure_score=structure_score,
            cta_effectiveness=cta,
            top_strength=top_strength,
            top_improvement=top_improvement,
            detailed_feedback=self._generate_detailed_feedback(
                hook_score, tone_score, structure_score, cta, content
            ),
            predicted_engagement=predicted,
            rewrite_suggestion=rewrite,
        )

    def _identify_top_strength(
        self, hook: int, tone: int, structure: int, content: str
    ) -> str:
        """Identify the strongest aspect of the post."""
        scores = {"hook": hook, "tone": tone, "structure": structure}
        best = max(scores, key=scores.get)
        
        if best == "hook" and hook >= 7:
            return "Strong opening that creates curiosity or pattern interrupt"
        elif best == "structure" and structure >= 7:
            return "Well-formatted with good readability and visual breaks"
        elif best == "tone" and tone >= 7:
            return "Authentic voice that matches your brand identity"
        else:
            return "Clear content that communicates your message"

    def _identify_top_improvement(
        self, hook: int, tone: int, structure: int, cta: str, content: str
    ) -> str:
        """Identify the highest-impact improvement opportunity."""
        scores = {"hook": hook, "structure": structure, "cta": cta}
        
        if hook < 6:
            return "Strengthen the opening hook - make the first 2 sentences unmissable"
        elif structure < 6:
            return "Add more line breaks - shorter paragraphs improve readability"
        elif cta == "weak" or cta == "none":
            return "End with a clear call-to-action or question to drive engagement"
        elif tone < 6:
            return "Align the voice more closely with your stated brand tone"
        else:
            return "Consider adding a specific story or example to make it more concrete"

    def _generate_detailed_feedback(
        self, hook: int, tone: int, structure: int, cta: str, content: str
    ) -> str:
        """Generate detailed feedback summary."""
        parts = []
        
        if hook >= 8:
            parts.append("Opening is compelling and creates curiosity.")
        elif hook < 5:
            parts.append("Opening could be stronger - consider a pattern interrupt or curiosity gap.")
        
        if structure >= 8:
            parts.append("Excellent formatting and readability.")
        elif structure < 5:
            parts.append("Structure needs improvement - add white space and break up long paragraphs.")
        
        if cta == "strong":
            parts.append("Call-to-action is clear and drives engagement.")
        elif cta == "none":
            parts.append("Missing a clear ending - add a question or specific ask.")
        
        return " ".join(parts) if parts else "Post is competent but could be strengthened in key areas."

    def _generate_rewrite_suggestion(self, content: str, platform: str) -> str:
        """Generate a stronger opening based on content."""
        # Extract key topic from content
        words = content.split()
        if len(words) < 5:
            return "Consider a more specific, concrete opening hook."
        
        # Find main topic (nouns, key phrases)
        topic_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[a-z]+){0,3}', content[:200])
        topic = topic_phrases[0] if topic_phrases else words[2:4]
        
        # Generate platform-appropriate hook
        if platform == "linkedin":
            hooks = [
                f"I was wrong about {topic}. Here's what I learned...",
                f"The most underrated skill in {topic}? It's not what you think.",
                f"3 lessons from failing at {topic} (so you don't have to).",
                f"Stop focusing on {topic}. Start focusing on what actually matters.",
            ]
        else:
            hooks = [
                f"Hot take: {topic} is overrated. Here's why.",
                f"Unpopular opinion about {topic}...",
            ]
        
        import random
        return random.choice(hooks)
