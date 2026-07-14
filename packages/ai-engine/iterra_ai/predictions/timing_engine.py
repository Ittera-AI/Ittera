"""TimingPredictionEngine: ML-based optimal posting time prediction.

Predicts the best times to post content based on:
- Historical post performance patterns
- Platform-specific audience behavior
- Content type and complexity
- Day-of-week patterns
- Competition analysis

Features:
- Week-long heatmap generation
- Alternative time slot recommendations
- Pattern detection from historical data
- Confidence scoring
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

from openai import OpenAI

from iterra_ai.predictions.schemas import (
    TimingInput,
    TimingOutput,
    TimeSlotScore,
    TimingPattern,
)
from iterra_ai.predictions.prompts import build_timing_prompt
from iterra_ai.core.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


class TimingPredictionEngine:
    """
    AI engine for predicting optimal posting times.
    
    Analyzes historical performance and content characteristics
    to recommend the single best posting time with alternatives.
    
    Platform-specific patterns:
    - LinkedIn: Commute times, Tue-Thu 8-10am, 5-6pm
    - Twitter: Tue-Thu 9-11am, 12-1pm
    - Instagram: Tue-Thu 11am-1pm, evenings 8-10pm for Reels
    - Facebook: Weekdays 1-3pm, weekends 12-1pm
    """
    
    # Platform default patterns (used when no historical data)
    PLATFORM_PATTERNS = {
        "linkedin": {
            "best_days": ["tue", "wed", "thu"],
            "best_hours": [8, 9, 17, 18],  # 8-10am, 5-6pm
            "avoid_hours": [0, 1, 2, 3, 4, 5, 6, 22, 23],
            "weekend_ok": False,
        },
        "twitter": {
            "best_days": ["tue", "wed", "thu"],
            "best_hours": [9, 10, 11, 12, 17, 18],
            "avoid_hours": [0, 1, 2, 3, 4, 5, 6],
            "weekend_ok": True,
        },
        "instagram": {
            "best_days": ["tue", "wed", "thu"],
            "best_hours": [11, 12, 13, 19, 20, 21],
            "avoid_hours": [0, 1, 2, 3, 4, 5, 6],
            "weekend_ok": True,
        },
        "facebook": {
            "best_days": ["wed", "thu", "fri"],
            "best_hours": [13, 14, 15, 12, 13],  # 1-3pm weekdays
            "avoid_hours": [0, 1, 2, 3, 4, 5, 6, 21, 22, 23],
            "weekend_ok": True,
        },
    }
    
    DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    
    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize the timing prediction engine.
        
        Args:
            api_key: AIML/OpenAI-compatible API key
            model: Chat model to use
        """
        self.client = OpenAI(
            api_key=api_key or os.getenv("AIML_API_KEY"),
            base_url=os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1"),
        )
        self.model = model or os.getenv("AIML_MODEL", "gpt-4o-mini")
        self.max_tokens = 4096
        self.cost_tracker = CostTracker()
    
    def _compute_content_hash(self, content: str, context: dict) -> str:
        """Compute hash for caching."""
        normalized = content.strip().lower()[:200]  # First 200 chars
        hash_input = json.dumps({
            "content": normalized,
            "platform": context.get("platform"),
            "timezone": context.get("timezone"),
        }, sort_keys=True)
        return hashlib.sha256(hash_input.encode()).hexdigest()[:32]
    
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
            self.cost_tracker.log(
                "timing", usage["input_tokens"], usage["output_tokens"]
            )
            return content or "", usage
        except Exception as e:
            logger.error(f"Timing LLM call failed: {e}")
            raise
    
    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        import re
        
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not extract JSON from timing response: {text[:200]}")
    
    def _analyze_historical_patterns(
        self,
        historical_posts: list[dict],
        platform: str,
    ) -> dict[str, Any]:
        """
        Analyze historical posts to detect timing patterns.
        
        Returns:
            Dictionary with detected patterns and scores per day/hour
        """
        if not historical_posts:
            return {
                "has_data": False,
                "patterns": [],
                "day_scores": {},
                "hour_scores": {},
            }
        
        # Group by day and hour
        day_performance: dict[str, list[float]] = {d: [] for d in self.DAY_NAMES}
        hour_performance: dict[int, list[float]] = {h: [] for h in range(24)}
        
        for post in historical_posts:
            day = post.get("day", "").lower()
            hour = post.get("hour")
            engagement = post.get("engagement_rate", 0)
            
            if day in day_performance:
                day_performance[day].append(engagement)
            
            if hour is not None and 0 <= hour <= 23:
                hour_performance[hour].append(engagement)
        
        # Calculate average performance per day/hour
        day_scores = {
            day: (sum(rates) / len(rates) if rates else 0)
            for day, rates in day_performance.items()
        }
        
        hour_scores = {
            hour: (sum(rates) / len(rates) if rates else 0)
            for hour, rates in hour_performance.items()
        }
        
        # Detect patterns
        patterns: list[dict] = []
        
        # Best day pattern
        if day_scores:
            best_day = max(day_scores, key=day_scores.get)
            best_day_score = day_scores[best_day]
            if best_day_score > 0:
                patterns.append({
                    "type": "peak_engagement_time",
                    "description": f"Posts on {best_day.capitalize()} show highest engagement ({best_day_score:.2f}%)",
                    "confidence": 0.7 if len(historical_posts) > 10 else 0.5,
                    "action": f"Prioritize posting on {best_day.capitalize()}",
                })
        
        # Best hour pattern
        if hour_scores:
            valid_hours = {h: s for h, s in hour_scores.items() if s > 0}
            if valid_hours:
                best_hour = max(valid_hours, key=valid_hours.get)
                patterns.append({
                    "type": "audience_active_hours",
                    "description": f"Engagement peaks at {best_hour}:00 ({valid_hours[best_hour]:.2f}%)",
                    "confidence": 0.6,
                    "action": f"Try posting between {best_hour-1}:00 and {best_hour+1}:00",
                })
        
        return {
            "has_data": True,
            "patterns": patterns,
            "day_scores": day_scores,
            "hour_scores": hour_scores,
            "data_points": len(historical_posts),
        }
    
    def _build_heuristic_output(
        self,
        input_data: TimingInput,
        content_hash: str,
        historical_analysis: dict,
    ) -> TimingOutput:
        """
        Build timing output using heuristics when LLM fails.
        
        Combines platform defaults with historical patterns.
        """
        platform = input_data.platform
        platform_defaults = self.PLATFORM_PATTERNS.get(platform, self.PLATFORM_PATTERNS["linkedin"])
        
        # Start with platform defaults
        best_days = platform_defaults["best_days"].copy()
        best_hours = platform_defaults["best_hours"].copy()
        
        # Adjust with historical data
        if historical_analysis.get("has_data"):
            day_scores = historical_analysis.get("day_scores", {})
            if day_scores:
                # Sort days by historical performance
                sorted_days = sorted(
                    [(d, s) for d, s in day_scores.items() if s > 0],
                    key=lambda x: x[1],
                    reverse=True,
                )
                # Blend with platform defaults
                top_hist_days = [d for d, _ in sorted_days[:3]]
                best_days = list(dict.fromkeys(top_hist_days + best_days))[:3]
            
            hour_scores = historical_analysis.get("hour_scores", {})
            if hour_scores:
                sorted_hours = sorted(
                    [(h, s) for h, s in hour_scores.items() if s > 0],
                    key=lambda x: x[1],
                    reverse=True,
                )
                top_hist_hours = [h for h, _ in sorted_hours[:4]]
                best_hours = list(dict.fromkeys(top_hist_hours + best_hours))[:4]
        
        # Filter by constraints
        allowed_days = [d.lower() for d in input_data.allowed_days]
        filtered_days = [d for d in best_days if d in allowed_days]
        if not filtered_days and allowed_days:
            filtered_days = allowed_days[:3]
        
        filtered_hours = [
            h for h in best_hours
            if input_data.allowed_hours_start <= h <= input_data.allowed_hours_end
        ]
        if not filtered_hours:
            filtered_hours = [
                input_data.allowed_hours_start,
                (input_data.allowed_hours_start + input_data.allowed_hours_end) // 2,
            ]
        
        # Generate optimal time (next occurrence)
        now = datetime.now()
        current_day_idx = now.weekday()
        
        # Find next allowed day
        optimal_day = None
        days_checked = 0
        while days_checked < 7 and optimal_day is None:
            check_idx = (current_day_idx + days_checked) % 7
            check_day = self.DAY_NAMES[check_idx]
            if check_day in filtered_days:
                optimal_day = check_day
                break
            days_checked += 1
        
        if optimal_day is None:
            optimal_day = filtered_days[0] if filtered_days else "tue"
        
        # Pick hour
        optimal_hour = filtered_hours[0] if filtered_hours else 10
        
        # Calculate datetime
        days_until = (self.DAY_NAMES.index(optimal_day) - current_day_idx) % 7
        if days_until == 0 and now.hour >= optimal_hour:
            days_until = 7  # Next week
        
        optimal_time = now + timedelta(days=days_until)
        optimal_time = optimal_time.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)
        
        # Build alternative slots
        alternative_slots: list[TimeSlotScore] = []
        for day in filtered_days[:3]:
            for hour in filtered_hours[:2]:
                if day == optimal_day and hour == optimal_hour:
                    continue
                
                # Score based on position in best lists
                day_score = (len(filtered_days) - filtered_days.index(day)) / len(filtered_days)
                hour_score = (len(filtered_hours) - filtered_hours.index(hour)) / len(filtered_hours)
                score = (day_score + hour_score) / 2 * 0.8  # Slightly lower than optimal
                
                # Historical boost
                if historical_analysis.get("has_data"):
                    day_hist = historical_analysis.get("day_scores", {}).get(day, 0)
                    hour_hist = historical_analysis.get("hour_scores", {}).get(hour, 0)
                    if day_hist > 0 or hour_hist > 0:
                        score = min(1.0, score + 0.1)
                
                alternative_slots.append(TimeSlotScore(
                    day=day,
                    hour=hour,
                    score=score,
                    predicted_engagement_rate=score * 5,  # Rough estimate
                    predicted_reach=int(score * 1000),
                    audience_availability=score,
                    competition_level="medium",
                    historical_performance=historical_analysis.get("day_scores", {}).get(day, 0) / 10 if historical_analysis.get("has_data") else None,
                    reasoning=f"Good {platform} posting time based on platform patterns",
                ))
        
        # Sort and limit
        alternative_slots.sort(key=lambda x: x.score, reverse=True)
        alternative_slots = alternative_slots[:5]
        
        # Build patterns
        detected_patterns: list[TimingPattern] = []
        
        for p in historical_analysis.get("patterns", []):
            detected_patterns.append(TimingPattern(
                pattern_type=p.get("type", "peak_engagement_time"),
                description=p.get("description", ""),
                confidence=p.get("confidence", 0.5),
                recommended_action=p.get("action"),
            ))
        
        # Add platform patterns
        if platform == "linkedin":
            detected_patterns.append(TimingPattern(
                pattern_type="audience_active_hours",
                description="LinkedIn engagement peaks during commute times (8-10am, 5-6pm)",
                confidence=0.8,
                recommended_action="Post on Tuesday-Thursday during commute times",
            ))
        
        return TimingOutput(
            prediction_id=f"timing_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{content_hash[:8]}",
            content_hash=content_hash,
            optimal_time=optimal_time,
            confidence_score=0.6 if historical_analysis.get("has_data") else 0.5,
            alternative_slots=alternative_slots,
            detected_patterns=detected_patterns,
            best_days=filtered_days,
            best_hours=filtered_hours,
            worst_times_to_post=[
                f"Late night hours ({h}:00)" for h in platform_defaults.get("avoid_hours", [])[:3]
            ],
            platform_insights=f"{platform.capitalize()} performs best during professional hours" if platform == "linkedin" else None,
            prediction_time=datetime.utcnow(),
            processing_time_ms=50,
            historical_data_points_used=historical_analysis.get("data_points", 0),
        )
    
    def _parse_timing_response(
        self,
        response: dict,
        content_hash: str,
        historical_count: int,
    ) -> TimingOutput:
        """Parse LLM response into typed output."""
        
        # Parse alternative slots
        alternative_slots = []
        for slot in response.get("alternative_slots", []):
            alternative_slots.append(TimeSlotScore(
                day=slot.get("day", "tue"),
                hour=slot.get("hour", 10),
                score=slot.get("score", 0.5),
                predicted_engagement_rate=slot.get("predicted_engagement_rate", 0),
                predicted_reach=slot.get("predicted_reach", 0),
                audience_availability=slot.get("audience_availability", 0.5),
                competition_level=slot.get("competition_level", "medium"),
                historical_performance=slot.get("historical_performance"),
                reasoning=slot.get("reasoning", ""),
            ))
        
        # Parse patterns
        detected_patterns = []
        for p in response.get("detected_patterns", []):
            detected_patterns.append(TimingPattern(
                pattern_type=p.get("pattern_type", "peak_engagement_time"),
                description=p.get("description", ""),
                confidence=p.get("confidence", 0.5),
                recommended_action=p.get("recommended_action"),
            ))
        
        # Parse optimal time
        optimal_time_str = response.get("optimal_time")
        try:
            if optimal_time_str:
                optimal_time = datetime.fromisoformat(optimal_time_str.replace("Z", "+00:00"))
            else:
                optimal_time = datetime.now() + timedelta(days=1)
        except ValueError:
            optimal_time = datetime.now() + timedelta(days=1)
        
        return TimingOutput(
            prediction_id=f"timing_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{content_hash[:8]}",
            content_hash=content_hash,
            optimal_time=optimal_time,
            confidence_score=response.get("confidence_score", 0.7),
            alternative_slots=alternative_slots,
            weekly_heatmap=None,  # Not generated by default
            detected_patterns=detected_patterns,
            best_days=response.get("best_days", []),
            best_hours=response.get("best_hours", []),
            worst_times_to_post=response.get("worst_times_to_post", []),
            platform_insights=response.get("platform_insights"),
            prediction_time=datetime.utcnow(),
            processing_time_ms=0,  # Set by caller
            historical_data_points_used=historical_count,
        )
    
    def predict(self, input_data: TimingInput) -> TimingOutput:
        """
        Predict optimal posting time for content.
        
        Args:
            input_data: TimingInput with content and constraints
            
        Returns:
            TimingOutput with optimal time and alternatives
        """
        import time
        start_time = time.time()
        
        # Compute hash
        context = {
            "platform": input_data.platform,
            "timezone": input_data.timezone,
        }
        content_hash = self._compute_content_hash(input_data.content, context)
        
        # Analyze historical data
        historical_analysis = self._analyze_historical_patterns(
            input_data.author_historical_posts,
            input_data.platform,
        )
        
        # Build prompts
        system_prompt, user_prompt = build_timing_prompt(
            content=input_data.content,
            platform=input_data.platform,
            timezone=input_data.timezone,
            allowed_days=input_data.allowed_days,
            allowed_hours_start=input_data.allowed_hours_start,
            allowed_hours_end=input_data.allowed_hours_end,
            historical_posts=input_data.author_historical_posts,
        )
        
        try:
            # Call LLM
            response_text, usage = self._call_llm(system_prompt, user_prompt)
            
            # Parse response
            response_json = self._extract_json(response_text)
            output = self._parse_timing_response(
                response_json,
                content_hash,
                historical_analysis.get("data_points", 0),
            )
            
        except Exception as e:
            logger.warning(f"Timing LLM failed, using heuristics: {e}")
            # Use heuristic fallback
            output = self._build_heuristic_output(input_data, content_hash, historical_analysis)
        
        output.processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Timing prediction: optimal={output.optimal_time.strftime('%Y-%m-%d %H:%M')}, "
            f"confidence={output.confidence_score:.2f}"
        )
        
        return output
    
    def generate_weekly_heatmap(
        self,
        platform: str,
        timezone: str,
        historical_posts: list[dict],
        allowed_days: list[str],
        allowed_hours_start: int,
        allowed_hours_end: int,
    ) -> list[TimeSlotScore]:
        """
        Generate a full week heatmap of posting quality scores.
        
        This is a separate operation that generates all 7 days × 24 hours
        with quality scores for visualization.
        
        Args:
            platform: Target platform
            timezone: Target timezone
            historical_posts: Author's historical post data
            allowed_days: Days allowed for posting
            allowed_hours_start: Earliest allowed hour
            allowed_hours_end: Latest allowed hour
            
        Returns:
            List of TimeSlotScore for all slots
        """
        # Get platform defaults
        platform_defaults = self.PLATFORM_PATTERNS.get(platform, self.PLATFORM_PATTERNS["linkedin"])
        
        # Analyze historical data
        historical_analysis = self._analyze_historical_patterns(historical_posts, platform)
        
        heatmap: list[TimeSlotScore] = []
        
        for day in self.DAY_NAMES:
            if day not in allowed_days:
                continue
            
            for hour in range(24):
                if not (allowed_hours_start <= hour <= allowed_hours_end):
                    continue
                
                # Calculate base score from platform patterns
                base_score = 0.3
                
                if day in platform_defaults["best_days"]:
                    base_score += 0.2
                
                if hour in platform_defaults["best_hours"]:
                    base_score += 0.2
                
                if hour in platform_defaults["avoid_hours"]:
                    base_score -= 0.3
                
                # Adjust with historical data
                if historical_analysis.get("has_data"):
                    day_score = historical_analysis.get("day_scores", {}).get(day, 0)
                    hour_score = historical_analysis.get("hour_scores", {}).get(hour, 0)
                    
                    # Normalize scores
                    max_day = max(historical_analysis.get("day_scores", {}).values()) or 1
                    max_hour = max(historical_analysis.get("hour_scores", {}).values()) or 1
                    
                    if max_day > 0:
                        base_score += (day_score / max_day) * 0.15
                    if max_hour > 0:
                        base_score += (hour_score / max_hour) * 0.15
                
                # Clamp score
                score = max(0.1, min(1.0, base_score))
                
                heatmap.append(TimeSlotScore(
                    day=day,
                    hour=hour,
                    score=score,
                    predicted_engagement_rate=score * 5,
                    predicted_reach=int(score * 1000),
                    audience_availability=score,
                    competition_level="medium" if 9 <= hour <= 17 else "low",
                    historical_performance=historical_analysis.get("day_scores", {}).get(day, 0) / 10 if historical_analysis.get("has_data") else None,
                    reasoning=f"Score: {score:.2f} based on platform patterns and historical data",
                ))
        
        return heatmap


# Global instance
_timing_engine: TimingPredictionEngine | None = None


def get_timing_engine(api_key: str | None = None) -> TimingPredictionEngine:
    """Get or create timing engine singleton."""
    global _timing_engine
    if _timing_engine is None:
        _timing_engine = TimingPredictionEngine(api_key=api_key)
    return _timing_engine
