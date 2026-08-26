"""
InsightSynthesisEngine — cross-post 'why we win/lose' synthesizer.

Reads many analyzed posts (Post + PostAnalysis, pre-joined into
``PostPerformanceRecord``) for one creator on one platform and distills a
compact, durable memory: a one-paragraph summary, win/loss patterns,
concrete recommendations, and candidate facts eligible for promotion into
``UserContext``.

Mirrors ``EngagementCoach`` exactly:
  - typed Pydantic I/O via ``BaseEngine[InsightSynthesisInput, InsightSynthesisOutput]``
  - cost-tracked ``_call_llm`` (logged by ``CostTracker`` like every other engine)
  - robust JSON parsing with multiple fallback strategies
  - a deterministic ``_heuristic_synthesize`` fallback when no LLM is available,
    reusing the pattern math proven in ``analytics_service.get_content_insights``
    (hook / length / time / quality-engagement-correlation), so a missing API
    key degrades quality, never correctness.
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections import Counter, defaultdict
from typing import Any, cast

from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.insight.schemas import (
    CandidateFact,
    InsightSynthesisInput,
    InsightSynthesisOutput,
    PostPerformanceRecord,
)
from iterra_ai.prompts.insight import format_insight_prompt

logger = logging.getLogger(__name__)

# Promotion threshold mirrors the Fact_Promotion_Agent contract (>= 0.7).
HEURISTIC_FACT_CONFIDENCE = 0.7

# Hook-pattern regexes mirror analytics_service._analyze_hook_patterns.
_HOOK_PATTERN_REGEX = {
    "question": r"^(Why\s|How\s|What\s|When\s|Where\s|Who\s|Can\s|Is\s|Are\s|Do\s|Does\s)",
    "number": r"^(\d+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)",
    "story": r"^(I\s|When\sI|My\s|Last\s|Yesterday|Today\s|This\s)",
    "contrarian": r"^(Most\s|Everyone\s|Stop\s|Don't\s|Never\s|Always\s|Wrong\s)",
}


class InsightSynthesisError(Exception):
    """Base exception for insight synthesis errors."""


class InsightSynthesisEngine(BaseEngine[InsightSynthesisInput, InsightSynthesisOutput]):
    """
    Production-grade cross-post insight synthesizer.

    Example:
        engine = InsightSynthesisEngine()
        result = engine.generate(InsightSynthesisInput(
            platform="linkedin",
            records=[...],
        ))
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 1500
    TEMPERATURE = 0.3

    def __init__(self, model: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.model: str = model or os.getenv("AIML_MODEL") or self.DEFAULT_MODEL

    def generate(self, input: InsightSynthesisInput) -> InsightSynthesisOutput:
        """
        Synthesize a compact insight from many analyzed posts.

        Falls back to a deterministic heuristic when no LLM client/API key is
        available or when the LLM call/parse fails, so the loop keeps learning.
        """
        if not self._client and not os.getenv("AIML_API_KEY"):
            logger.warning(
                "InsightSynthesisEngine: No API key available, using heuristic fallback"
            )
            return self._heuristic_synthesize(input)

        try:
            system, user = format_insight_prompt(input)
            raw_response = self._call_llm(
                system=system,
                user=user,
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE,
            )
            data = self._parse_llm_response(raw_response)
            return self._build_output(data, input)
        except Exception:
            logger.exception(
                "InsightSynthesisEngine failed; using heuristic fallback"
            )
            return self._heuristic_synthesize(input)

    # ------------------------------------------------------------------ #
    # LLM response parsing (coach-style multi-strategy)
    # ------------------------------------------------------------------ #

    def _parse_llm_response(self, raw_response: str) -> dict[str, Any]:
        """
        Parse the LLM response with multiple fallback strategies:
          1. Direct JSON parsing
          2. Extract JSON from markdown code blocks
          3. Extract content between the first { and last }
          4. Raise if all strategies fail
        """
        response = raw_response.strip()

        try:
            return cast(dict[str, Any], json.loads(response))
        except json.JSONDecodeError:
            pass

        code_block_patterns = [
            r"```json\n(.*?)\n```",
            r"```\n(.*?)\n```",
            r"```(.*?)```",
        ]
        for pattern in code_block_patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return cast(dict[str, Any], json.loads(match.group(1).strip()))
                except json.JSONDecodeError:
                    continue

        json_match = re.search(r"(\{.*\})", response, re.DOTALL)
        if json_match:
            try:
                return cast(dict[str, Any], json.loads(json_match.group(1)))
            except json.JSONDecodeError:
                pass

        logger.error(
            "Failed to parse insight LLM response. Preview: %s",
            response[:500],
        )
        raise InsightSynthesisError("Could not parse LLM response as JSON")

    def _build_output(
        self, data: dict[str, Any], input: InsightSynthesisInput
    ) -> InsightSynthesisOutput:
        """Build a validated InsightSynthesisOutput from parsed LLM data."""
        candidate_facts = self._build_candidate_facts(data.get("candidate_facts"))

        return InsightSynthesisOutput(
            summary=str(data.get("summary") or ""),
            why_wins=self._string_list(data.get("why_wins")),
            why_losses=self._string_list(data.get("why_losses")),
            recommendations=self._string_list(data.get("recommendations")),
            candidate_facts=candidate_facts,
            confidence=self._clamp_unit(data.get("confidence", 0.0)),
            model=self.model,
            is_mock=False,
        )

    def _build_candidate_facts(self, raw_facts: Any) -> list[CandidateFact]:
        """Coerce raw LLM fact dicts into validated CandidateFact objects."""
        facts: list[CandidateFact] = []
        if not isinstance(raw_facts, list):
            return facts
        for item in raw_facts:
            if not isinstance(item, dict):
                continue
            key = item.get("key")
            value = item.get("value")
            if not key or value is None:
                continue
            try:
                facts.append(
                    CandidateFact(
                        key=str(key),
                        value=self._string_list(value),
                        confidence=self._clamp_unit(item.get("confidence", 0.0)),
                        evidence=str(item.get("evidence") or ""),
                    )
                )
            except Exception:
                logger.debug("Skipping malformed candidate fact: %s", item)
                continue
        return facts

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        """Normalize a value into a list of non-empty strings."""
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list | tuple):
            return [str(v) for v in value if v is not None and str(v).strip()]
        return [str(value)]

    @staticmethod
    def _clamp_unit(value: Any) -> float:
        """Clamp a value into the [0.0, 1.0] range, defaulting to 0.0."""
        try:
            return max(0.0, min(1.0, float(value)))
        except (ValueError, TypeError):
            return 0.0

    # ------------------------------------------------------------------ #
    # Deterministic heuristic fallback
    # ------------------------------------------------------------------ #

    def _heuristic_synthesize(
        self, input: InsightSynthesisInput
    ) -> InsightSynthesisOutput:
        """
        Deterministic synthesis without an LLM.

        Ranks records by engagement rate, compares the top third vs the bottom
        third on hook / length / timing / quality patterns (mirroring
        analytics_service.get_content_insights), and produces win/loss patterns,
        recommendations, and candidate facts. Fully deterministic for a given
        input so the loop stays reproducible.
        """
        records = list(input.records)
        if not records:
            return InsightSynthesisOutput(
                summary="Not enough published posts yet to identify performance patterns.",
                why_wins=[],
                why_losses=[],
                recommendations=[
                    "Publish more posts so the system can learn what works for you."
                ],
                candidate_facts=[],
                confidence=0.0,
                model="heuristic",
                is_mock=True,
            )

        ranked = sorted(records, key=lambda r: r.engagement_rate, reverse=True)
        n = len(ranked)
        third = max(1, n // 3)
        top_third = ranked[:third]
        bottom_third = ranked[-third:]

        hook_patterns = self._heuristic_hook_patterns(ranked)
        length_patterns = self._heuristic_length_patterns(top_third, bottom_third)
        time_patterns = self._heuristic_time_patterns(ranked)
        quality = self._heuristic_quality_correlation(ranked)

        why_wins = self._heuristic_why_wins(
            top_third, hook_patterns, length_patterns, quality
        )
        why_losses = self._heuristic_why_losses(bottom_third, length_patterns)
        recommendations = self._heuristic_recommendations(
            hook_patterns, length_patterns, time_patterns
        )
        candidate_facts = self._heuristic_candidate_facts(
            hook_patterns, time_patterns, length_patterns
        )

        summary = self._heuristic_summary(
            input.platform, n, hook_patterns, length_patterns, time_patterns
        )

        # Confidence scales with sample size, capped at 0.6 for heuristic output.
        confidence = round(min(0.6, n / 20.0), 3)

        return InsightSynthesisOutput(
            summary=summary,
            why_wins=why_wins,
            why_losses=why_losses,
            recommendations=recommendations,
            candidate_facts=candidate_facts,
            confidence=confidence,
            model="heuristic",
            is_mock=True,
        )

    @staticmethod
    def _classify_hook(record: PostPerformanceRecord) -> str:
        opening = record.content.strip()[:100]
        for pattern, regex in _HOOK_PATTERN_REGEX.items():
            if re.search(regex, opening, re.IGNORECASE):
                return pattern
        return "other"

    def _heuristic_hook_patterns(
        self, records: list[PostPerformanceRecord]
    ) -> dict[str, Any]:
        counts: Counter[str] = Counter()
        for record in records:
            counts[self._classify_hook(record)] += 1

        total = sum(counts.values())
        if total == 0:
            return {"dominant_pattern": "unknown", "dominant_percentage": 0.0}

        dominant = max(counts, key=lambda k: (counts[k], k))
        return {
            "distribution": dict(counts),
            "dominant_pattern": dominant,
            "dominant_percentage": round(counts[dominant] / total * 100, 1),
        }

    @staticmethod
    def _heuristic_length_patterns(
        top_posts: list[PostPerformanceRecord],
        bottom_posts: list[PostPerformanceRecord],
    ) -> dict[str, Any]:
        def avg_length(posts: list[PostPerformanceRecord]) -> float:
            if not posts:
                return 0.0
            return sum(len(p.content) for p in posts) / len(posts)

        top_avg = avg_length(top_posts)
        bottom_avg = avg_length(bottom_posts)
        diff = top_avg - bottom_avg

        lengths = [len(p.content) for p in top_posts] or [0]
        ideal = int(sum(lengths) / len(lengths))

        return {
            "top_performer_avg_chars": round(top_avg, 0),
            "bottom_performer_avg_chars": round(bottom_avg, 0),
            "difference": round(diff, 0),
            "ideal": ideal,
        }

    @staticmethod
    def _heuristic_time_patterns(
        records: list[PostPerformanceRecord],
    ) -> dict[str, Any]:
        hour_perf: dict[int, dict[str, float]] = defaultdict(
            lambda: {"count": 0, "total_er": 0.0}
        )
        for record in records:
            if record.published_hour is None:
                continue
            hour = record.published_hour
            hour_perf[hour]["count"] += 1
            hour_perf[hour]["total_er"] += record.engagement_rate

        scored = [
            (hour, data["total_er"] / data["count"])
            for hour, data in hour_perf.items()
            if data["count"] >= 1
        ]
        # Deterministic order: by avg engagement desc, then hour asc.
        best = sorted(scored, key=lambda x: (-x[1], x[0]))[:3]
        return {"best_performing_hours": [hour for hour, _ in best]}

    @staticmethod
    def _heuristic_quality_correlation(
        records: list[PostPerformanceRecord],
    ) -> dict[str, Any]:
        quality_scores: list[float] = []
        engagement_rates: list[float] = []
        for record in records:
            scores = [
                s
                for s in (
                    record.hook_score,
                    record.tone_match_score,
                    record.structure_score,
                )
                if s is not None
            ]
            if not scores:
                continue
            quality_scores.append(sum(scores) / len(scores))
            engagement_rates.append(record.engagement_rate)

        if len(quality_scores) < 3:
            return {"correlation": 0.0, "strength": "weak"}

        n = len(quality_scores)
        sum_q = sum(quality_scores)
        sum_e = sum(engagement_rates)
        sum_qe = sum(q * e for q, e in zip(quality_scores, engagement_rates))
        sum_q2 = sum(q**2 for q in quality_scores)
        sum_e2 = sum(e**2 for e in engagement_rates)

        numerator = n * sum_qe - sum_q * sum_e
        denominator = ((n * sum_q2 - sum_q**2) * (n * sum_e2 - sum_e**2)) ** 0.5
        correlation = 0.0 if denominator == 0 else numerator / denominator

        strength = (
            "strong"
            if abs(correlation) > 0.7
            else "moderate"
            if abs(correlation) > 0.4
            else "weak"
        )
        return {"correlation": round(correlation, 3), "strength": strength}

    @staticmethod
    def _heuristic_why_wins(
        top_third: list[PostPerformanceRecord],
        hook_patterns: dict[str, Any],
        length_patterns: dict[str, Any],
        quality: dict[str, Any],
    ) -> list[str]:
        wins: list[str] = []
        dominant = hook_patterns.get("dominant_pattern")
        pct = hook_patterns.get("dominant_percentage", 0.0)
        if dominant and dominant not in ("other", "unknown") and pct >= 30:
            wins.append(
                f"{dominant.capitalize()}-style hooks lead your top posts "
                f"({pct:.0f}% of analyzed posts)."
            )

        diff = length_patterns.get("difference", 0)
        if diff > 100:
            wins.append(
                f"Longer posts outperform: top posts average "
                f"{length_patterns['top_performer_avg_chars']:.0f} characters."
            )
        elif diff < -100:
            wins.append(
                f"Shorter posts outperform: top posts average "
                f"{length_patterns['top_performer_avg_chars']:.0f} characters."
            )

        if quality.get("strength") == "strong" and quality.get("correlation", 0) > 0:
            wins.append(
                "Higher AI quality scores strongly track higher engagement."
            )

        strengths = [r.top_strength for r in top_third if r.top_strength]
        if strengths:
            most_common = Counter(strengths).most_common(1)[0][0]
            wins.append(f"Recurring strength in winners: {most_common}.")

        return wins

    @staticmethod
    def _heuristic_why_losses(
        bottom_third: list[PostPerformanceRecord],
        length_patterns: dict[str, Any],
    ) -> list[str]:
        losses: list[str] = []
        improvements = [r.top_improvement for r in bottom_third if r.top_improvement]
        if improvements:
            most_common = Counter(improvements).most_common(1)[0][0]
            losses.append(f"Underperformers most often need: {most_common}.")

        weak_cta = sum(
            1 for r in bottom_third if r.cta_effectiveness in ("weak", "none")
        )
        if bottom_third and weak_cta >= len(bottom_third) / 2:
            losses.append("Weak or missing calls-to-action drag down low performers.")

        return losses

    @staticmethod
    def _heuristic_recommendations(
        hook_patterns: dict[str, Any],
        length_patterns: dict[str, Any],
        time_patterns: dict[str, Any],
    ) -> list[str]:
        recs: list[str] = []
        dominant = hook_patterns.get("dominant_pattern")
        if dominant and dominant not in ("other", "unknown"):
            recs.append(f"Open the next post with a {dominant}-style hook.")

        ideal = length_patterns.get("ideal")
        if ideal:
            recs.append(f"Aim for roughly {ideal} characters of body content.")

        best_hours = time_patterns.get("best_performing_hours") or []
        if best_hours:
            formatted = ", ".join(f"{h:02d}:00 UTC" for h in best_hours)
            recs.append(f"Publish during your strongest windows: {formatted}.")

        if not recs:
            recs.append("Keep publishing consistently to surface clearer patterns.")
        return recs

    def _heuristic_candidate_facts(
        self,
        hook_patterns: dict[str, Any],
        time_patterns: dict[str, Any],
        length_patterns: dict[str, Any],
    ) -> list[CandidateFact]:
        facts: list[CandidateFact] = []

        best_hours = time_patterns.get("best_performing_hours") or []
        if best_hours:
            facts.append(
                CandidateFact(
                    key="best_post_times",
                    value=[f"{h:02d}:00" for h in best_hours],
                    confidence=HEURISTIC_FACT_CONFIDENCE,
                    evidence=(
                        "Highest average engagement observed at these UTC hours "
                        "across analyzed posts."
                    ),
                )
            )

        dominant = hook_patterns.get("dominant_pattern")
        pct = hook_patterns.get("dominant_percentage", 0.0)
        if dominant and dominant not in ("other", "unknown") and pct >= 40:
            facts.append(
                CandidateFact(
                    key="best_formats",
                    value=[f"{dominant}-style hook"],
                    confidence=HEURISTIC_FACT_CONFIDENCE,
                    evidence=f"{pct:.0f}% of analyzed posts use this dominant hook style.",
                )
            )

        return facts

    @staticmethod
    def _heuristic_summary(
        platform: str,
        count: int,
        hook_patterns: dict[str, Any],
        length_patterns: dict[str, Any],
        time_patterns: dict[str, Any],
    ) -> str:
        parts = [
            f"Across {count} analyzed {platform} post(s), "
        ]
        dominant = hook_patterns.get("dominant_pattern")
        if dominant and dominant not in ("other", "unknown"):
            parts.append(f"{dominant}-style hooks dominate your top performers")
        else:
            parts.append("hook styles are mixed with no clear winner yet")

        diff = length_patterns.get("difference", 0)
        if diff > 100:
            parts.append(", longer content tends to win")
        elif diff < -100:
            parts.append(", shorter content tends to win")

        best_hours = time_patterns.get("best_performing_hours") or []
        if best_hours:
            parts.append(
                f", and posting around {best_hours[0]:02d}:00 UTC "
                "correlates with stronger engagement"
            )
        parts.append(".")
        return "".join(parts)
