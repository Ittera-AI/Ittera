import json

import pytest

from iterra_ai.insight.engine import InsightSynthesisEngine
from iterra_ai.insight.schemas import (
    InsightSynthesisInput,
    InsightSynthesisOutput,
    PostPerformanceRecord,
)


@pytest.fixture()
def insight_input():
    """A small batch of analyzed posts with a clear top/bottom spread."""
    return InsightSynthesisInput(
        platform="linkedin",
        period_days=30,
        avg_engagement_rate=0.05,
        records=[
            PostPerformanceRecord(
                content="Why most founders fail at content marketing.",
                platform="linkedin",
                published_hour=8,
                likes=120,
                comments=30,
                shares=15,
                impressions=4000,
                engagement_rate=0.12,
                hook_score=9,
                tone_match_score=8,
                structure_score=9,
                cta_effectiveness="strong",
                top_strength="Strong contrarian hook",
                top_improvement="Add a clearer CTA",
            ),
            PostPerformanceRecord(
                content="How I grew my audience to 10k followers in 90 days.",
                platform="linkedin",
                published_hour=9,
                likes=90,
                comments=20,
                shares=10,
                impressions=3500,
                engagement_rate=0.09,
                hook_score=8,
                tone_match_score=7,
                structure_score=8,
                cta_effectiveness="medium",
                top_strength="Specific, numbers-driven opener",
                top_improvement="Tighten the middle section",
            ),
            PostPerformanceRecord(
                content="Some quick thoughts about our quarterly update today.",
                platform="linkedin",
                published_hour=14,
                likes=5,
                comments=1,
                shares=0,
                impressions=2000,
                engagement_rate=0.003,
                hook_score=3,
                tone_match_score=5,
                structure_score=4,
                cta_effectiveness="none",
                top_strength="On-brand voice",
                top_improvement="Add a hook",
            ),
        ],
    )


# --------------------------------------------------------------------------- #
# 1. Well-formed LLM response is parsed into a correct output (is_mock=False)
# --------------------------------------------------------------------------- #


def test_generate_parses_well_formed_llm_response(monkeypatch, insight_input):
    """A well-formed JSON response is parsed into a typed InsightSynthesisOutput."""
    llm_payload = {
        "summary": "Contrarian and numbers-driven hooks drive your top LinkedIn posts.",
        "why_wins": [
            "Strong opening hooks correlate with the highest engagement.",
            "Posts published in the morning outperform afternoon posts.",
        ],
        "why_losses": [
            "Vague update posts with no hook underperform.",
        ],
        "recommendations": [
            "Open with a contrarian or numbers-driven hook.",
            "Publish between 08:00 and 09:00 UTC.",
        ],
        "candidate_facts": [
            {
                "key": "best_post_times",
                "value": ["08:00", "09:00"],
                "confidence": 0.82,
                "evidence": "Top 2 posts published 08:00-09:00 UTC.",
            },
            {
                "key": "best_formats",
                "value": ["contrarian-style hook"],
                "confidence": 0.75,
                "evidence": "Highest-engagement post used a contrarian hook.",
            },
        ],
        "confidence": 0.8,
    }

    # A truthy client makes generate() take the LLM path instead of the fallback.
    engine = InsightSynthesisEngine(client=object())
    monkeypatch.setattr(
        engine, "_call_llm", lambda **kwargs: json.dumps(llm_payload)
    )

    output = engine.generate(insight_input)

    assert isinstance(output, InsightSynthesisOutput)
    assert output.is_mock is False
    assert output.model == engine.model
    assert output.summary == llm_payload["summary"]
    assert output.why_wins == llm_payload["why_wins"]
    assert output.why_losses == llm_payload["why_losses"]
    assert output.recommendations == llm_payload["recommendations"]
    assert output.confidence == pytest.approx(0.8)

    assert len(output.candidate_facts) == 2
    times_fact = next(f for f in output.candidate_facts if f.key == "best_post_times")
    assert times_fact.value == ["08:00", "09:00"]
    assert times_fact.confidence == pytest.approx(0.82)
    assert times_fact.evidence


def test_generate_parses_response_wrapped_in_code_fence(monkeypatch, insight_input):
    """JSON wrapped in a markdown code fence is still parsed correctly."""
    payload = {
        "summary": "Hooks matter.",
        "why_wins": ["Strong hooks win."],
        "why_losses": [],
        "recommendations": ["Lead with a hook."],
        "candidate_facts": [],
        "confidence": 0.5,
    }
    fenced = "```json\n" + json.dumps(payload) + "\n```"

    engine = InsightSynthesisEngine(client=object())
    monkeypatch.setattr(engine, "_call_llm", lambda **kwargs: fenced)

    output = engine.generate(insight_input)

    assert output.is_mock is False
    assert output.summary == "Hooks matter."
    assert output.why_wins == ["Strong hooks win."]
    assert output.confidence == pytest.approx(0.5)


def test_generate_falls_back_when_llm_returns_unparseable(monkeypatch, insight_input):
    """A non-JSON LLM response triggers the deterministic heuristic fallback."""
    engine = InsightSynthesisEngine(client=object())
    monkeypatch.setattr(
        engine, "_call_llm", lambda **kwargs: "sorry, I cannot help with that"
    )

    output = engine.generate(insight_input)

    assert output.is_mock is True
    assert output.model == "heuristic"


# --------------------------------------------------------------------------- #
# 2. Heuristic fallback path runs with no client / no API key
# --------------------------------------------------------------------------- #


def test_heuristic_fallback_when_no_client_or_key(monkeypatch, insight_input):
    """With no client and no API key, generate() uses the heuristic path."""
    monkeypatch.delenv("AIML_API_KEY", raising=False)

    engine = InsightSynthesisEngine()
    output = engine.generate(insight_input)

    assert isinstance(output, InsightSynthesisOutput)
    assert output.is_mock is True
    assert output.model == "heuristic"
    # Heuristic output is non-empty and derived from the records.
    assert output.summary
    assert output.recommendations
    assert 0.0 <= output.confidence <= 1.0
    for fact in output.candidate_facts:
        assert 0.0 <= fact.confidence <= 1.0


def test_heuristic_fallback_is_deterministic(monkeypatch, insight_input):
    """The heuristic path is deterministic for a given input."""
    monkeypatch.delenv("AIML_API_KEY", raising=False)

    first = InsightSynthesisEngine().generate(insight_input)
    second = InsightSynthesisEngine().generate(insight_input)

    assert first.model_dump() == second.model_dump()


def test_heuristic_fallback_empty_records_degrades_gracefully(monkeypatch):
    """Empty records produce safe, non-erroring output rather than crashing."""
    monkeypatch.delenv("AIML_API_KEY", raising=False)

    empty_input = InsightSynthesisInput(platform="linkedin", records=[])
    output = InsightSynthesisEngine().generate(empty_input)

    assert isinstance(output, InsightSynthesisOutput)
    assert output.is_mock is True
    assert output.model == "heuristic"
    assert output.summary  # a helpful "not enough posts" message
    assert output.recommendations
    assert output.candidate_facts == []
    assert output.confidence == 0.0
