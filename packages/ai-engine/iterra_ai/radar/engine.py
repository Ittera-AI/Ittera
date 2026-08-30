"""Experimental trend synthesis with deterministic fallback."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.prompts.radar import SCAN_PROMPT, SYSTEM_PROMPT
from iterra_ai.radar.schemas import RadarInput, RadarOutput, TrendItem


class TrendRadar(BaseEngine[RadarInput, RadarOutput]):
    """Scans and surfaces trending topics relevant to a given niche."""

    def scan(self, input: RadarInput) -> RadarOutput:
        if self._client or os.getenv("AIML_API_KEY"):
            try:
                prompt = SCAN_PROMPT.format(
                    limit=input.limit,
                    niche=input.niche,
                    platforms=", ".join(input.platforms or ["linkedin", "twitter"]),
                )
                prompt += (
                    '\n\nReturn only JSON in this shape: '
                    '{"trends":[{"topic":"...","score":8.5,"platforms":["linkedin"],'
                    '"summary":"..."}]}'
                )
                raw = self._call_llm(system=SYSTEM_PROMPT, user=prompt, max_tokens=1200)
                parsed = json.loads(self._strip_json_fence(raw))
                raw_trends = parsed.get("trends", parsed if isinstance(parsed, list) else [])
                trends = [
                    TrendItem(
                        topic=item.get("topic", ""),
                        score=float(item.get("score", 0)),
                        platforms=item.get("platforms") or input.platforms,
                        summary=item.get("summary", ""),
                    )
                    for item in raw_trends[: input.limit]
                    if item.get("topic")
                ]
                if trends:
                    return RadarOutput(trends=trends, scanned_at=datetime.now(UTC))
            except Exception:
                pass

        return self._synthetic_scan(input)

    def _synthetic_scan(self, input: RadarInput) -> RadarOutput:
        trends = [
            TrendItem(
                topic=f"{input.niche.title()} operating loops",
                score=9.2,
                platforms=input.platforms,
                summary="Creators are shifting from one-off posts to repeatable content systems.",
            ),
            TrendItem(
                topic="AI-assisted review",
                score=8.7,
                platforms=input.platforms,
                summary="Teams want speed without losing human taste and approval.",
            ),
        ][: input.limit]
        return RadarOutput(trends=trends, scanned_at=datetime.now(UTC))

    def generate(self, input: RadarInput) -> RadarOutput:
        return self.scan(input)
