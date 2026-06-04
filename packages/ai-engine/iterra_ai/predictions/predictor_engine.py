"""PredictorEngine: AI-powered content performance prediction.

Predicts engagement metrics with confidence intervals based on:
- Content quality analysis
- Historical performance patterns
- Platform-specific factors
- Audience context

Features:
- Confidence intervals for all predictions
- Feature importance analysis
- Improvement suggestions
- Caching support via input hashing
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any

from openai import OpenAI

from iterra_ai.predictions.schemas import (
    ContentInput,
    ContentPredictionOutput,
    ConfidenceInterval,
    FeatureImportance,
    PredictionConfidence,
    PredictionMetrics,
)
from iterra_ai.predictions.prompts import build_predictor_prompt

logger = logging.getLogger(__name__)


class PredictorEngine:
    """
    AI engine for predicting content performance metrics.
    
    Uses Claude to analyze content and predict:
    - Likes, comments, shares, impressions
    - Engagement rate with confidence intervals
    - Feature importance (what drives performance)
    - Improvement suggestions
    """
    
    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize the predictor engine.
        
        Args:
            api_key: AIML/OpenAI-compatible API key (optional, will use env var if not provided)
            model: Chat model to use
        """
        self.client = OpenAI(
            api_key=api_key or os.getenv("AIML_API_KEY"),
            base_url=os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1"),
        )
        self.model = model or os.getenv("AIML_MODEL", "gpt-4o-mini")
        self.max_tokens = 4096
        
    def _compute_content_hash(self, content: str, context: dict) -> str:
        """
        Compute hash of input for caching.
        
        Creates deterministic hash that can be used to
        check if we've already predicted for this content.
        """
        # Normalize content
        normalized = content.strip().lower().replace("\n", " ")
        
        # Include context factors that affect prediction
        hash_input = {
            "content": normalized[:500],  # First 500 chars
            "platform": context.get("platform", "unknown"),
            "content_type": context.get("content_type", "post"),
            "follower_count": context.get("follower_count"),
            "avg_engagement": context.get("avg_engagement"),
        }
        
        hash_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()[:32]
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> tuple[str, dict]:
        """
        Call the configured OpenAI-compatible API with prompts.
        
        Returns:
            Tuple of (raw response, usage info)
        """
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
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _extract_json(self, text: str) -> dict[str, Any]:
        """
        Extract JSON from LLM response.
        
        Handles various response formats:
        - Raw JSON
        - JSON in markdown code blocks
        - Mixed text/JSON
        """
        # Try direct JSON parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try finding JSON object in text
        # Look for opening brace to end of text
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not extract JSON from response: {text[:200]}")
    
    def _parse_prediction_response(self, response: dict) -> ContentPredictionOutput:
        """
        Parse LLM response into typed prediction output.
        """
        metrics_data = response.get("metrics", {})
        confidence_data = response.get("confidence", {})
        
        # Build metrics
        metrics = PredictionMetrics(
            likes=metrics_data.get("likes", 0),
            comments=metrics_data.get("comments", 0),
            shares=metrics_data.get("shares", 0),
            impressions=metrics_data.get("impressions", 0),
            engagement_rate=metrics_data.get("engagement_rate", 0),
            reach=metrics_data.get("reach"),
            click_through_rate=metrics_data.get("click_through_rate"),
        )
        
        # Build confidence intervals
        engagement_ci = confidence_data.get("engagement_rate_ci", {})
        impressions_ci = confidence_data.get("impressions_ci", {})
        
        confidence = PredictionConfidence(
            overall_confidence=confidence_data.get("overall_confidence", 0.7),
            engagement_rate_ci=ConfidenceInterval(
                lower=engagement_ci.get("lower", metrics.engagement_rate * 0.7),
                upper=engagement_ci.get("upper", metrics.engagement_rate * 1.3),
                confidence=0.95,
            ),
            impressions_ci=ConfidenceInterval(
                lower=impressions_ci.get("lower", metrics.impressions * 0.7),
                upper=impressions_ci.get("upper", metrics.impressions * 1.3),
                confidence=0.95,
            ) if impressions_ci else None,
            data_quality_score=confidence_data.get("data_quality_score", 0.5),
            historical_alignment=confidence_data.get("historical_alignment", 0.5),
            model_confidence=confidence_data.get("model_confidence", 0.7),
        )
        
        # Build feature importance
        features = [
            FeatureImportance(
                feature=f.get("feature", "unknown"),
                importance=f.get("importance", 0),
                impact=f.get("impact", "neutral"),
                explanation=f.get("explanation", ""),
            )
            for f in response.get("feature_importance", [])
        ]
        
        return ContentPredictionOutput(
            prediction_id=f"pred_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self._compute_content_hash('', {})[:8]}",
            content_hash="",  # Will be set by caller
            metrics=metrics,
            confidence=confidence,
            feature_importance=features,
            improvement_suggestions=response.get("improvement_suggestions", []),
            comparative_analysis=response.get("comparative_analysis"),
            prediction_time=datetime.utcnow(),
            processing_time_ms=0,  # Will be set by caller
            tokens_used=0,  # Will be set by caller
            estimated_cost_usd=0,  # Will be set by caller
        )
    
    def predict(self, input_data: ContentInput) -> ContentPredictionOutput:
        """
        Generate performance prediction for content.
        
        Args:
            input_data: ContentInput with all context
            
        Returns:
            ContentPredictionOutput with metrics and confidence
            
        Raises:
            Exception: If LLM call fails or response is invalid
        """
        import time
        start_time = time.time()
        
        # Compute hash for caching
        context = {
            "platform": input_data.platform,
            "content_type": input_data.content_type,
            "follower_count": input_data.author_follower_count,
            "avg_engagement": input_data.author_avg_engagement,
        }
        content_hash = self._compute_content_hash(input_data.content, context)
        
        # Build prompts
        system_prompt, user_prompt = build_predictor_prompt(
            content=input_data.content,
            platform=input_data.platform,
            content_type=input_data.content_type,
            hashtags=input_data.hashtags,
            mentions=input_data.mentioned_accounts,
            scheduled_time=input_data.scheduled_time,
            industry=input_data.industry,
            target_audience=input_data.target_audience,
            brand_tone=input_data.brand_tone,
            avg_engagement=input_data.author_avg_engagement,
            follower_count=input_data.author_follower_count,
        )
        
        # Call LLM
        response_text, usage = self._call_llm(system_prompt, user_prompt)
        
        # Parse response
        try:
            response_json = self._extract_json(response_text)
        except ValueError as e:
            logger.error(f"Failed to parse prediction response: {e}")
            logger.error(f"Response: {response_text[:500]}")
            raise
        
        # Parse into output schema
        output = self._parse_prediction_response(response_json)
        
        # Add metadata
        output.content_hash = content_hash
        output.processing_time_ms = int((time.time() - start_time) * 1000)
        output.tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        output.estimated_cost_usd = (output.tokens_used / 1000) * 0.003  # Approximate cost
        
        logger.info(
            f"Prediction generated for {input_data.platform} content: "
            f"engagement_rate={output.metrics.engagement_rate:.2f}%, "
            f"confidence={output.confidence.overall_confidence:.2f}, "
            f"tokens={output.tokens_used}"
        )
        
        return output
    
    def predict_batch(self, inputs: list[ContentInput]) -> list[ContentPredictionOutput]:
        """
        Generate predictions for multiple content items.
        
        Note: This runs sequentially. For parallel processing,
        use the Celery task queue.
        
        Args:
            inputs: List of ContentInput objects
            
        Returns:
            List of ContentPredictionOutput objects
        """
        results = []
        for inp in inputs:
            try:
                result = self.predict(inp)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch prediction failed for item: {e}")
                # Return None for failed items
                results.append(None)
        return results


# Global instance for singleton pattern
_predictor_engine: PredictorEngine | None = None


def get_predictor_engine(api_key: str | None = None) -> PredictorEngine:
    """
    Get or create predictor engine singleton.
    
    Args:
        api_key: Optional API key (only used on first call)
        
    Returns:
        PredictorEngine instance
    """
    global _predictor_engine
    if _predictor_engine is None:
        _predictor_engine = PredictorEngine(api_key=api_key)
    return _predictor_engine
