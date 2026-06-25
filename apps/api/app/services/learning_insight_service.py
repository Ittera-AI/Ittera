"""
Insight Memory Agent (Gap 3).

Owns the lifecycle of the summarized "what we learned / why posts win or lose"
memory (``LearnedInsight``) for one user on one platform. It:

  - reads the single active insight row for ``(user, platform)``
    (:func:`get_active_insight`),
  - builds an :class:`InsightSynthesisInput` from the recently analyzed posts,
    runs the :class:`InsightSynthesisEngine`, and upserts/version-bumps the
    ``LearnedInsight`` row (:func:`synthesize_user_insights`),
  - guards re-synthesis so it only runs when new analyses have arrived since the
    last run (:func:`_has_new_analyses_since_last_synthesis`).

Design reference: design.md section B.3.2.

Key guarantees:
  - Creates version 1 when no insight exists for ``(user, platform)``; updates the
    same row and bumps ``version`` by exactly one otherwise (Requirements 3.1, 3.7).
  - Skips synthesis and leaves any prior insight unchanged when fewer than
    ``MIN_POSTS_FOR_SYNTHESIS`` analyzed posts exist (Requirement 3.2).
  - Retains the prior insight rather than overwriting good data with a degraded
    (heuristic/empty) synthesis result (Requirement 3.3).
  - Touches only the ``(user, platform)`` row, leaving every other platform's
    insight unchanged (Requirement 3.4).
  - Records an ``insight_synthesized`` ``AnalyticsEvent`` on each persisted
    synthesis so the loop can detect new analyses since the last run
    (Requirements 3.5, 3.7).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.datetime_helpers import utc_now
from app.models.learned_insight import LearnedInsight
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.user import User

from iterra_ai.insight.engine import InsightSynthesisEngine
from iterra_ai.insight.schemas import InsightSynthesisInput, PostPerformanceRecord

# Minimum number of analyzed posts required before synthesis runs. Mirrors
# Requirement 3.2 ("fewer than 5 analyzed posts ... skip synthesis").
MIN_POSTS_FOR_SYNTHESIS = 5

# Default lookback window for building the synthesis input.
DEFAULT_PERIOD_DAYS = 30


def get_active_insight(
    db: Session, user: User, platform: str
) -> LearnedInsight | None:
    """
    Return the single active ``LearnedInsight`` for ``(user, platform)``.

    There is at most one row per ``(user, platform)`` (enforced by
    ``uq_learned_insight_user_platform``), so this returns that row or ``None``.
    """
    return (
        db.query(LearnedInsight)
        .filter(
            LearnedInsight.user_id == user.id,
            LearnedInsight.platform == platform,
        )
        .first()
    )


def synthesize_user_insights(
    db: Session,
    user: User,
    platform: str,
    period_days: int = DEFAULT_PERIOD_DAYS,
) -> LearnedInsight | None:
    """
    Synthesize cross-post insights for ``(user, platform)`` and upsert the memory.

    Builds an :class:`InsightSynthesisInput` from the last ``period_days`` of
    joined ``Post`` + ``PostAnalysis`` records, runs the
    :class:`InsightSynthesisEngine`, and upserts the ``LearnedInsight`` row.

    Returns the persisted (or retained) ``LearnedInsight``, or ``None`` when there
    are too few analyzed posts to synthesize (Requirement 3.2).
    """
    records = _build_records(db, user, platform, period_days)
    if len(records) < MIN_POSTS_FOR_SYNTHESIS:
        # Not enough signal yet — leave any prior insight untouched.
        return None

    prior = get_active_insight(db, user, platform)
    engine = InsightSynthesisEngine()
    output = engine.generate(
        InsightSynthesisInput(
            platform=platform,
            period_days=period_days,
            avg_engagement_rate=_avg_engagement_rate(records),
            records=records,
            prior_summary=prior.summary if prior else None,
        )
    )

    return _upsert_insight(db, user, platform, output, records, period_days, prior)


def _build_records(
    db: Session, user: User, platform: str, period_days: int
) -> list[PostPerformanceRecord]:
    """
    Build the ranked list of :class:`PostPerformanceRecord` for ``(user, platform)``.

    Joins ``Post`` with its ``PostAnalysis`` within the lookback window (so only
    analyzed posts contribute) and orders by engagement rate descending, matching
    the ``analytics_service`` join pattern. Only the requested platform's posts are
    considered (per-platform isolation).
    """
    cutoff = utc_now() - timedelta(days=period_days)

    rows = (
        db.query(Post, PostAnalysis)
        .join(PostAnalysis, Post.id == PostAnalysis.post_id)
        .filter(
            Post.user_id == user.id,
            Post.platform == platform,
            Post.published_at >= cutoff,
        )
        .order_by(Post.engagement_rate.desc())
        .all()
    )

    records: list[PostPerformanceRecord] = []
    for post, analysis in rows:
        feedback = analysis.coach_feedback or {}
        records.append(
            PostPerformanceRecord(
                content=post.content or "",
                platform=post.platform,
                published_hour=(
                    post.published_at.hour if post.published_at else None
                ),
                likes=post.likes or 0,
                comments=post.comments or 0,
                shares=post.shares or 0,
                # Treat a stored 0 as "no impressions reported"; the engine's
                # engagement math already handles a None/0 denominator safely.
                impressions=post.impressions if post.impressions else None,
                engagement_rate=post.engagement_rate or 0.0,
                hook_score=analysis.hook_score,
                tone_match_score=analysis.tone_match_score,
                structure_score=analysis.structure_score,
                cta_effectiveness=analysis.cta_effectiveness,
                top_strength=feedback.get("top_strength"),
                top_improvement=feedback.get("top_improvement"),
            )
        )
    return records


def _avg_engagement_rate(records: list[PostPerformanceRecord]) -> float | None:
    """Average engagement rate across the records, or ``None`` when empty."""
    if not records:
        return None
    return round(sum(r.engagement_rate for r in records) / len(records), 4)


def _is_degraded(output) -> bool:
    """
    Whether a synthesis result is degraded and should not overwrite good data.

    A result is degraded when it is a heuristic/mock fallback (the LLM was
    unavailable or failed) or when it carries no usable content at all. Retaining
    the prior insight in this case satisfies Requirement 3.3 (never wipe a good
    insight with empty/degraded content).
    """
    if getattr(output, "is_mock", False):
        return True
    has_content = bool(
        (output.summary and output.summary.strip())
        or output.why_wins
        or output.why_losses
        or output.recommendations
        or output.candidate_facts
    )
    return not has_content


def _upsert_insight(
    db: Session,
    user: User,
    platform: str,
    output,
    records: list[PostPerformanceRecord],
    period_days: int,
    prior: LearnedInsight | None,
) -> LearnedInsight:
    """
    Create or update the single ``(user, platform)`` ``LearnedInsight`` row.

    - When a prior insight exists and the new ``output`` is degraded, the prior is
      retained unchanged (Requirement 3.3).
    - When no insight exists, a new row is created at version 1 (Requirement 3.1).
    - When an insight exists and the output is usable, the same row is updated and
      its version is incremented by exactly one (Requirement 3.7).

    Only the ``(user, platform)`` row is touched (Requirement 3.4).
    """
    # Don't overwrite a good prior insight with degraded/empty output.
    if prior is not None and _is_degraded(output):
        return prior

    candidate_facts = [_fact_to_dict(f) for f in output.candidate_facts]
    is_mock = 1 if getattr(output, "is_mock", False) else 0
    now = utc_now()

    if prior is None:
        insight = LearnedInsight(
            user_id=user.id,
            platform=platform,
            version=1,
            generated_at=now,
            updated_at=now,
        )
        db.add(insight)
    else:
        insight = prior
        insight.version = (insight.version or 0) + 1
        insight.generated_at = now
        insight.updated_at = now

    insight.summary = output.summary or ""
    insight.why_wins = list(output.why_wins or [])
    insight.why_losses = list(output.why_losses or [])
    insight.recommendations = list(output.recommendations or [])
    insight.candidate_facts = candidate_facts
    insight.confidence = float(output.confidence or 0.0)
    insight.based_on_posts = len(records)
    insight.based_on_analyses = len(records)
    insight.period_days = period_days
    insight.model = output.model or None
    insight.is_mock = is_mock

    db.commit()
    db.refresh(insight)

    _emit_event(
        db,
        user.id,
        "insight_synthesized",
        metrics={
            "platform": platform,
            "version": insight.version,
            "based_on_posts": insight.based_on_posts,
            "based_on_analyses": insight.based_on_analyses,
            "confidence": insight.confidence,
            "model": insight.model,
            "is_mock": bool(is_mock),
        },
    )

    return insight


def _fact_to_dict(fact) -> dict:
    """
    Serialize a ``CandidateFact`` (or already-dict fact) into the JSON shape stored
    on ``LearnedInsight.candidate_facts`` and consumed by the Fact Promotion Agent.
    """
    if isinstance(fact, dict):
        return {
            "key": fact.get("key"),
            "value": list(fact.get("value") or []),
            "confidence": fact.get("confidence", 0.0),
            "evidence": fact.get("evidence", ""),
        }
    return {
        "key": fact.key,
        "value": list(fact.value or []),
        "confidence": fact.confidence,
        "evidence": fact.evidence,
    }


def _has_new_analyses_since_last_synthesis(
    db: Session, user: User, platform: str
) -> bool:
    """
    Return whether new ``auto_analysis_complete`` events exist for ``(user, platform)``
    since the last synthesis for that pair (Requirement 3.5).

    The last synthesis is marked by the active insight's ``updated_at``. When no
    insight exists yet, any analyzed post counts as new so the first synthesis can
    run. Events are scoped to the platform by joining through ``Post`` so other
    platforms' analyses never trigger this platform's synthesis.
    """
    from app.models.analytics_snapshot import AnalyticsEvent

    latest_event_at = (
        db.query(AnalyticsEvent.created_at)
        .join(Post, AnalyticsEvent.post_id == Post.id)
        .filter(
            AnalyticsEvent.user_id == user.id,
            AnalyticsEvent.event_type == "auto_analysis_complete",
            Post.platform == platform,
        )
        .order_by(AnalyticsEvent.created_at.desc())
        .first()
    )
    if latest_event_at is None or latest_event_at[0] is None:
        return False

    insight = get_active_insight(db, user, platform)
    if insight is None or insight.updated_at is None:
        # Never synthesized for this pair, but analyses exist -> there is new work.
        return True

    return _as_naive_utc(latest_event_at[0]) > _as_naive_utc(insight.updated_at)


def _as_naive_utc(value: datetime) -> datetime:
    """
    Normalize a datetime to naive UTC for safe comparison.

    Stored timestamps may be timezone-aware (Postgres ``timezone=True`` columns)
    or naive (e.g. SQLite in tests). Both sides are UTC, so we drop the tzinfo to
    compare consistently without raising on aware/naive mismatches.
    """
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _emit_event(
    db: Session,
    user_id: str,
    event_type: str,
    post_id: str | None = None,
    metrics: dict | None = None,
) -> None:
    """
    Record an ``AnalyticsEvent`` for synthesis audit/idempotency.

    Imported locally to mirror ``analytics_service`` / ``post_bridge_service`` and
    avoid import cycles.
    """
    from app.models.analytics_snapshot import AnalyticsEvent

    event = AnalyticsEvent(
        user_id=user_id,
        event_type=event_type,
        post_id=post_id,
        metrics=metrics or {},
    )
    db.add(event)
    db.commit()
