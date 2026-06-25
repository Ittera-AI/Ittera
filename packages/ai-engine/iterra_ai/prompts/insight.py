"""
Prompt templates for the InsightSynthesisEngine.

Versioned prompts for cross-post insight synthesis. Follows the coach.py
convention exactly: module-level versioned constants plus a
`format_insight_prompt(input) -> tuple[str, str]` helper.

The engine reads many analyzed posts (Post + PostAnalysis) for one creator on
one platform and distills a compact, durable narrative + structured
recommendations + candidate facts.
"""

from iterra_ai.insight.schemas import InsightSynthesisInput

# ═══════════════════════════════════════════════════════════════════════════════
# V1: Cross-Post Insight Synthesis (Production)
# ═══════════════════════════════════════════════════════════════════════════════

INSIGHT_SYNTHESIS_SYSTEM_V1 = """You are a content performance analyst. You receive a creator's recent posts with engagement metrics and per-post AI scores. Identify the PATTERNS that separate winners from losers for THIS creator on THIS platform.
Be specific and evidence-based. Output ONLY JSON matching the schema:
{
  "summary": str,                 // one tight paragraph
  "why_wins": [str],              // patterns that drive success
  "why_losses": [str],            // patterns that drag performance
  "recommendations": [str],       // concrete guidance for the NEXT post
  "candidate_facts": [            // only facts you are confident enough to promote
     {"key": "best_post_times|best_formats|avoid", "value": [str],
      "confidence": float, "evidence": str}],
  "confidence": float             // overall 0..1
}
Never invent facts not supported by the records. Prefer fewer, higher-confidence facts."""


INSIGHT_SYNTHESIS_USER_V1 = """Platform: {platform}
Period: last {period_days} days | Avg engagement rate: {avg_er}
{prior_block}
POSTS (ranked by engagement):
{records_block}
{signals_block}
Respond with JSON per the system instructions."""


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════


def build_prior_block(prior_summary: str | None) -> str:
    """Build the prior-memory section so synthesis is incremental, not amnesiac."""
    if not prior_summary:
        return ""
    return f"PRIOR LEARNINGS (refine, do not discard):\n{prior_summary}\n"


def _format_record(index: int, record) -> str:
    """Format a single PostPerformanceRecord into a compact, scannable line."""
    parts = [f"#{index} [ER {record.engagement_rate:.2%}]"]

    metrics = f"likes={record.likes} comments={record.comments} shares={record.shares}"
    if record.impressions is not None:
        metrics += f" impressions={record.impressions}"
    parts.append(metrics)

    if record.published_hour is not None:
        parts.append(f"hour={record.published_hour:02d}:00 UTC")

    scores = []
    if record.hook_score is not None:
        scores.append(f"hook={record.hook_score}")
    if record.tone_match_score is not None:
        scores.append(f"tone={record.tone_match_score}")
    if record.structure_score is not None:
        scores.append(f"structure={record.structure_score}")
    if record.cta_effectiveness is not None:
        scores.append(f"cta={record.cta_effectiveness}")
    if scores:
        parts.append("scores: " + " ".join(scores))

    if record.top_strength:
        parts.append(f"strength: {record.top_strength}")
    if record.top_improvement:
        parts.append(f"improvement: {record.top_improvement}")

    header = " | ".join(parts)
    content = record.content.strip().replace("\n", " ")
    if len(content) > 400:
        content = content[:400] + "..."
    return f"{header}\nCONTENT: {content}"


def build_records_block(records) -> str:
    """Build the ranked posts block, highest engagement first."""
    if not records:
        return "(no posts available)"

    ranked = sorted(records, key=lambda r: r.engagement_rate, reverse=True)
    return "\n\n".join(
        _format_record(i, record) for i, record in enumerate(ranked, start=1)
    )


def build_signals_block(
    predicted_signals: dict | None,
    competitive_signals: dict | None,
) -> str:
    """Build the optional off-loop signals block (soft context only)."""
    parts = []
    if predicted_signals:
        parts.append(f"PREDICTED SIGNALS (soft context): {predicted_signals}")
    if competitive_signals:
        parts.append(f"COMPETITIVE SIGNALS (soft context): {competitive_signals}")
    if not parts:
        return ""
    return "\n".join(parts) + "\n"


def format_insight_prompt(input: InsightSynthesisInput) -> tuple[str, str]:
    """
    Format the insight synthesis prompt with all context.

    Args:
        input: InsightSynthesisInput carrying the platform, period, ranked
            performance records, optional off-loop signals, and prior memory.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    avg_er = (
        f"{input.avg_engagement_rate:.2%}"
        if input.avg_engagement_rate is not None
        else "n/a"
    )

    prior_block = build_prior_block(input.prior_summary)
    records_block = build_records_block(input.records)
    signals_block = build_signals_block(
        input.predicted_signals, input.competitive_signals
    )

    user_prompt = INSIGHT_SYNTHESIS_USER_V1.format(
        platform=input.platform,
        period_days=input.period_days,
        avg_er=avg_er,
        prior_block=prior_block,
        records_block=records_block,
        signals_block=signals_block,
    )

    return INSIGHT_SYNTHESIS_SYSTEM_V1, user_prompt
