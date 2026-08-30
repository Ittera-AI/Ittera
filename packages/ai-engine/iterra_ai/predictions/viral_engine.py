"""ViralPredictionEngine: AI-powered viral potential analysis.

Analyzes content for viral potential based on:
- Hook strength and scroll-stopping power
- Emotional resonance and shareability
- Pattern detection (story elements, controversy, timeliness)
- Platform-specific viral factors

Outputs:
- Viral probability score (0-1)
- Pattern-by-pattern breakdown
- Category classification
- Amplification suggestions
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any, cast

from openai import OpenAI

from iterra_ai.core.cost_tracker import CostTracker
from iterra_ai.predictions.prompts import build_viral_prompt
from iterra_ai.predictions.schemas import (
    ViralCategory,
    ViralPattern,
    ViralPotentialOutput,
    ViralScoreInput,
)

logger = logging.getLogger(__name__)


class ViralPredictionEngine:
    """
    AI engine for predicting viral potential of content.
    
    Analyzes content through multiple viral pattern lenses:
    - Hook strength: Does it stop the scroll?
    - Emotional resonance: Does it trigger feelings?
    - Shareability: Would people share it?
    - Timeliness: Is it relevant now?
    - Uniqueness: Is it novel?
    - Visual appeal: Does it paint a picture?
    - Authenticity: Does it feel real?
    """
    
    # Score thresholds for categories
    CATEGORY_THRESHOLDS: dict[ViralCategory, int] = {
        "highly_viral": 75,
        "viral_potential": 60,
        "average": 40,
        "below_average": 25,
        "unlikely": 0,
    }
    
    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize the viral prediction engine.
        
        Args:
            api_key: AIML/OpenAI-compatible API key
            model: Chat model to use
        """
        self.client = OpenAI(
            api_key=api_key or os.getenv("AIML_API_KEY"),
            base_url=os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1"),
        )
        self.model: str = model or os.getenv("AIML_MODEL") or "gpt-4o-mini"
        self.max_tokens = 4096
        self.cost_tracker = CostTracker()
    
    def _compute_content_hash(self, content: str, platform: str) -> str:
        """Compute hash for caching."""
        normalized = content.strip().lower().replace("\n", " ")
        hash_input = f"{normalized[:500]}:{platform}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:32]
    
    def _call_llm(
        self, system_prompt: str, user_prompt: str
    ) -> tuple[str, dict[str, int]]:
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
            raw_content = response.choices[0].message.content if response.choices else ""
            content = raw_content if isinstance(raw_content, str) else ""
            usage: dict[str, int] = {
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0),
            }
            self.cost_tracker.log(
                "viral", usage["input_tokens"], usage["output_tokens"]
            )
            return content, usage
        except Exception as e:
            logger.error(f"Viral LLM call failed: {e}")
            raise
    
    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from response."""
        try:
            return cast(dict[str, Any], json.loads(text))
        except json.JSONDecodeError:
            pass
        
        import re
        
        # Try markdown code block
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)```', text)
        if json_match:
            try:
                return cast(dict[str, Any], json.loads(json_match.group(1)))
            except json.JSONDecodeError:
                pass
        
        # Try finding JSON object
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return cast(dict[str, Any], json.loads(brace_match.group(0)))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not extract JSON from viral response: {text[:200]}")
    
    def _determine_category(self, score: float) -> ViralCategory:
        """Determine viral category from score."""
        if score >= self.CATEGORY_THRESHOLDS["highly_viral"]:
            return "highly_viral"
        elif score >= self.CATEGORY_THRESHOLDS["viral_potential"]:
            return "viral_potential"
        elif score >= self.CATEGORY_THRESHOLDS["average"]:
            return "average"
        elif score >= self.CATEGORY_THRESHOLDS["below_average"]:
            return "below_average"
        else:
            return "unlikely"
    
    def _parse_viral_response(
        self, response: dict[str, Any], content_hash: str
    ) -> ViralPotentialOutput:
        """Parse LLM response into typed output."""
        
        # Build patterns
        patterns = []
        for p in response.get("patterns", []):
            patterns.append(ViralPattern(
                pattern_type=p.get("pattern_type", "unknown"),
                score=p.get("score", 0.5),
                detected=p.get("detected", False),
                explanation=p.get("explanation", ""),
                examples=p.get("examples", []),
            ))
        
        # Get or calculate viral score
        viral_score = response.get("viral_score")
        viral_probability = response.get("viral_probability")
        
        # Derive score from probability if needed
        if viral_score is None and viral_probability is not None:
            viral_score = viral_probability * 100
        elif viral_score is None:
            # Calculate from pattern scores
            if patterns:
                avg_pattern = sum(p.score for p in patterns) / len(patterns)
                viral_score = avg_pattern * 100
            else:
                viral_score = 50
        
        if viral_probability is None:
            viral_probability = viral_score / 100
        
        # Determine category
        raw_category = response.get("category")
        category = (
            cast(ViralCategory, raw_category)
            if isinstance(raw_category, str)
            and raw_category in self.CATEGORY_THRESHOLDS
            else self._determine_category(viral_score)
        )
        
        return ViralPotentialOutput(
            prediction_id=f"viral_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{content_hash[:8]}",
            content_hash=content_hash,
            viral_probability=viral_probability,
            viral_score=viral_score,
            category=category,
            patterns=patterns,
            percentile_rank=response.get("percentile_rank", 50),
            comparison_to_top_performers=response.get("comparison_to_top_performers"),
            viral_triggers=response.get("viral_triggers", []),
            amplification_suggestions=response.get("amplification_suggestions", []),
            prediction_time=datetime.utcnow(),
            processing_time_ms=0,  # Set by caller
        )
    
    def analyze(self, input_data: ViralScoreInput) -> ViralPotentialOutput:
        """
        Analyze content for viral potential.
        
        Args:
            input_data: ViralScoreInput with content and context
            
        Returns:
            ViralPotentialOutput with detailed viral analysis
        """
        import time
        start_time = time.time()
        
        # Compute hash
        content_hash = self._compute_content_hash(input_data.content, input_data.platform)
        
        # Build prompts
        system_prompt, user_prompt = build_viral_prompt(
            content=input_data.content,
            platform=input_data.platform,
            has_story=input_data.has_story_element,
            has_data=input_data.has_data_insight,
            has_controversy=input_data.has_controversy,
            emotional_tone=input_data.emotional_tone,
        )
        
        # Call LLM
        response_text, usage = self._call_llm(system_prompt, user_prompt)
        
        # Parse response
        try:
            response_json = self._extract_json(response_text)
        except ValueError as e:
            logger.error(f"Failed to parse viral response: {e}")
            # Return fallback analysis
            return self._generate_fallback_analysis(input_data.content, content_hash)
        
        # Parse output
        output = self._parse_viral_response(response_json, content_hash)
        output.processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Viral analysis complete: score={output.viral_score:.1f}, "
            f"category={output.category}, "
            f"tokens={usage.get('input_tokens', 0) + usage.get('output_tokens', 0)}"
        )
        
        return output
    
    def _generate_fallback_analysis(
        self,
        content: str,
        content_hash: str,
    ) -> ViralPotentialOutput:
        """Generate heuristic fallback analysis when LLM fails."""
        
        # Simple heuristic analysis
        content_lower = content.lower()
        
        patterns = []
        
        # Hook strength - first sentence length and punchiness
        first_sentence = content.split(".")[0] if content else ""
        hook_score = 0.5
        if len(first_sentence) < 50:
            hook_score = 0.7  # Short, punchy opening
        if "?" in first_sentence:
            hook_score += 0.1  # Question hook
        if any(word in first_sentence.lower() for word in ["stop", "wait", "imagine", "what if"]):
            hook_score += 0.15
        patterns.append(ViralPattern(
            pattern_type="hook_strength",
            score=min(1.0, hook_score),
            detected=hook_score > 0.6,
            explanation=(
                "Based on opening sentence structure"
                if first_sentence
                else "No clear hook detected"
            ),
            examples=[first_sentence[:100]] if first_sentence else [],
        ))
        
        # Emotional resonance
        emotion_words = [
            "love",
            "hate",
            "amazing",
            "terrible",
            "shocking",
            "incredible",
            "never",
            "always",
        ]
        emotion_count = sum(1 for w in emotion_words if w in content_lower)
        emotion_score = min(1.0, 0.3 + emotion_count * 0.15)
        patterns.append(ViralPattern(
            pattern_type="emotional_resonance",
            score=emotion_score,
            detected=emotion_score > 0.5,
            explanation=f"Found {emotion_count} emotional trigger words",
            examples=[w for w in emotion_words if w in content_lower][:3],
        ))
        
        # Shareability
        share_indicators = ["share", "tag", "send", "retweet", "repost", "spread"]
        has_cta = any(w in content_lower for w in share_indicators)
        share_score = 0.6 if has_cta else 0.4
        patterns.append(ViralPattern(
            pattern_type="shareability",
            score=share_score,
            detected=has_cta,
            explanation="Contains share call-to-action" if has_cta else "No explicit share request",
        ))
        
        # Calculate overall score from patterns
        avg_score = sum(p.score for p in patterns) / len(patterns) if patterns else 0.5
        viral_score = avg_score * 100

        viral_triggers: list[str] = []
        if hook_score > 0.6:
            viral_triggers.append("Short punchy opening")
        if emotion_score > 0.5:
            viral_triggers.append("Emotional language detected")
        
        return ViralPotentialOutput(
            prediction_id=f"viral_fallback_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            content_hash=content_hash,
            viral_probability=avg_score,
            viral_score=viral_score,
            category=self._determine_category(viral_score),
            patterns=patterns,
            percentile_rank=50,
            comparison_to_top_performers="Heuristic analysis (LLM unavailable)",
            viral_triggers=viral_triggers,
            amplification_suggestions=[
                "Add a question hook in first sentence",
                "Include emotional trigger words",
                "Add explicit share call-to-action",
            ],
            prediction_time=datetime.utcnow(),
            processing_time_ms=100,
        )


# Global instance
_viral_engine: ViralPredictionEngine | None = None


def get_viral_engine(api_key: str | None = None) -> ViralPredictionEngine:
    """Get or create viral engine singleton."""
    global _viral_engine
    if _viral_engine is None:
        _viral_engine = ViralPredictionEngine(api_key=api_key)
    return _viral_engine
