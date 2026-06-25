"""Full-loop integration test for the Self-Learning Content Loop (spec task 12.1).

Drives the whole agentic chain end to end with no network/LLM calls:

    publish → bridge → metrics sync (stubbed provider) → per-post analysis
    (stubbed coach) → cross-post synthesis (stubbed engine) → fact promotion
    → context re-assembly

and asserts the two externally observable guarantees the loop exists to provide:

  1. Happy path (Requirement 8.1): a learning that the loop synthesizes reaches
     the next generation prompt. The known synthesized summary appears verbatim in
     the regenerated system prompt, and a confident candidate fact is promoted into
     the active ``UserContext.platform_facts``.

  2. Failing-stage isolation (Requirements 8.5, 8.6): when a later stage fails
     (the synthesis engine raises), prior committed memory is left intact — the
     pre-existing ``LearnedInsight`` keeps its version and summary, and the prior
     committed stages (the bridged ``Post`` and its ``PostAnalysis``) still persist.

Everything is monkeypatched so no real provider/LLM is ever called. Each test uses
unique ids namespaced by a per-run uuid and deletes the rows it created in a finally
block to keep the shared SQLite ``db`` fixture's state controlled.
"""

import sys
import uuid
from datetime import timedelta
from pathlib import Path

import pytest

# Ensure the repo root is importable so ``workers.*`` resolves (mirrors conftest).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import workers.celery.tasks.performance_sync as ps  # noqa: E402

from app.db.datetime_helpers import utc_now  # noqa: E402
from app.models.analytics_snapshot import AnalyticsEvent  # noqa: E402
from app.models.content_draft import ContentDraft  # noqa: E402
from app.models.learned_insight import LearnedInsight  # noqa: E402
from app.models.post import Post  # noqa: E402
from app.models.post_analysis import PostAnalysis  # noqa: E402
from app.models.social_connection import SocialConnection  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_context import UserContext  # noqa: E402
from app.services import analytics_service, context_service, learning_insight_service  # noqa: E402
from app.services.fact_promotion_service import promote_facts  # noqa: E402
from app.services.learning_insight_service import (  # noqa: E402
    MIN_POSTS_FOR_SYNTHESIS,
    synthesize_user_insights,
)
from app.services.post_bridge_service import bridge_draft_to_post  # noqa: E402

import iterra_ai.coach.engine as coach_engine  # noqa: E402
from iterra_ai.coach.schemas import CoachOutput  # noqa: E402
from iterra_ai.insight.schemas import (  # noqa: E402
    CandidateFact,
    InsightSynthesisOutput,
)

PLATFORM = "linkedin"

# The summary the stubbed synthesis engine produces. Asserted verbatim in the
# regenerated system prompt so we know the learning truly reached generation.
KNOWN_SUMMARY = "Question-led hooks and 08:00 posting drive your strongest engagement."

# A confident fact (>= 0.7) that must be promoted into UserContext.platform_facts.
PROMOTED_FACT_KEY = "best_post_times"
PROMOTED_FACT_VALUE = ["08:00"]


# ── Stubs (no network / no LLM) ───────────────────────────────────────────────


def _deterministic_coach_output() -> CoachOutput:
    """A fixed CoachOutput so per-post analysis is deterministic and LLM-free."""
    return CoachOutput(
        hook_score=8,
        tone_match_score=7,
        structure_score=7,
        cta_effectiveness="strong",
        top_strength="Strong question-led opening",
        top_improvement="Tighten the closing call-to-action",
        detailed_feedback="Opening hooks the reader; body is well structured.",
        predicted_engagement="high",
        rewrite_suggestion=None,
    )


def _good_synthesis_output() -> InsightSynthesisOutput:
    """A usable, non-mock synthesis result carrying the known summary + a fact."""
    return InsightSynthesisOutput(
        summary=KNOWN_SUMMARY,
        why_wins=["question-led hooks drive replies"],
        why_losses=["long preambles bury the point"],
        recommendations=["open the next post with a question"],
        candidate_facts=[
            CandidateFact(
                key=PROMOTED_FACT_KEY,
                value=PROMOTED_FACT_VALUE,
                confidence=0.85,
                evidence="Top posts cluster around 08:00 UTC.",
            )
        ],
        confidence=0.85,
        model="gpt-4o-mini",
        is_mock=False,
    )


def _make_fake_provider(metrics: ps.PostMetrics):
    """Build a stub MetricsProvider whose async fetch returns fixed metrics."""

    class _FakeProvider:
        platform = PLATFORM

        async def fetch(self, conn, post):
            return metrics

    return _FakeProvider()


# ── Seeding / cleanup helpers ──────────────────────────────────────────────────


def _make_user(db, run_id: str) -> User:
    user = User(
        id=f"loop-user-{run_id}",
        email=f"loop-{run_id}@example.com",
        name="Full Loop Tester",
        hashed_password="fakehash",
        primary_platform=PLATFORM,
    )
    db.add(user)
    db.commit()
    return user


def _make_active_context(db, user_id: str) -> UserContext:
    """Seed the active v1 UserContext with empty platform_facts."""
    ctx = UserContext(
        user_id=user_id,
        brand_name="Loop Brand",
        bio="We build in public.",
        target_audience="Founders",
        content_mission="Share what we learn.",
        platform_facts={},
        version=1,
        change_source="onboarding",
        is_active=True,
    )
    db.add(ctx)
    db.commit()
    return ctx


def _make_active_connection(db, user_id: str) -> SocialConnection:
    """Seed an active social connection so metrics-sync routing resolves it."""
    conn = SocialConnection(
        user_id=user_id,
        platform=PLATFORM,
        platform_user_id=f"pu-{user_id}",
        platform_username="loop-tester",
        access_token="real-test-token",  # not a mock/cookie token
        is_active=True,
    )
    db.add(conn)
    db.commit()
    return conn


def _make_published_draft(db, user_id: str, run_id: str) -> ContentDraft:
    draft = ContentDraft(
        user_id=user_id,
        platform=PLATFORM,
        content="Why do most launches flop? Here is what we learned.",
        status="published",
        published_at=utc_now() - timedelta(hours=2),
    )
    db.add(draft)
    db.commit()
    return draft


def _seed_analyzed_posts(db, user_id: str, n: int, run_id: str) -> list[str]:
    """Seed ``n`` analyzed posts (Post + PostAnalysis) within the 30-day window."""
    now = utc_now()
    post_ids: list[str] = []
    for i in range(n):
        post = Post(
            id=f"{run_id}-seed-post-{i}",
            user_id=user_id,
            platform=PLATFORM,
            platform_post_id=f"{run_id}-seed-ppid-{i}",
            content=f"Why does pattern {i} matter? A short thread.",
            content_type="post",
            published_at=now - timedelta(days=1, hours=i),
            source="iterra_published",
            likes=20 + i,
            comments=3 + i,
            shares=1 + i,
            impressions=500 + i,
            engagement_rate=round(0.04 * (i + 1), 4),
        )
        db.add(post)
        db.flush()
        db.add(
            PostAnalysis(
                post_id=post.id,
                hook_score=7,
                tone_match_score=7,
                structure_score=7,
                cta_effectiveness="strong",
                coach_feedback={"top_strength": "hook", "top_improvement": "cta"},
            )
        )
        post_ids.append(post.id)
    db.commit()
    return post_ids


def _cleanup(db, user_id: str):
    """Delete every row created for ``user_id`` to keep DB state controlled."""
    db.rollback()  # discard any failed/partial transaction before cleaning up
    post_ids = [
        pid for (pid,) in db.query(Post.id).filter(Post.user_id == user_id).all()
    ]
    if post_ids:
        db.query(PostAnalysis).filter(PostAnalysis.post_id.in_(post_ids)).delete(
            synchronize_session=False
        )
    db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(ContentDraft).filter(ContentDraft.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(Post).filter(Post.user_id == user_id).delete(synchronize_session=False)
    db.query(LearnedInsight).filter(LearnedInsight.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(UserContext).filter(UserContext.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(SocialConnection).filter(SocialConnection.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
    db.commit()


# ── Tests ───────────────────────────────────────────────────────────────────


def test_happy_path_full_loop_learning_reaches_next_prompt(db, monkeypatch):
    """Drive the full loop and assert the learned summary reaches the next prompt.

    publish → bridge → sync (stub) → analyze (stub) → synthesize (stub) → promote
    → re-assemble. The known synthesized summary must appear in the regenerated
    system prompt (Req 8.1) and the confident fact must land in the active
    UserContext.platform_facts.
    """
    run_id = uuid.uuid4().hex
    user = _make_user(db, run_id)
    try:
        _make_active_context(db, user.id)
        _make_active_connection(db, user.id)

        # ── Publish + bridge ───────────────────────────────────────────────
        draft = _make_published_draft(db, user.id, run_id)
        ppid = f"{run_id}-main-ppid"
        post = bridge_draft_to_post(db, user, draft, {"platform_post_id": ppid})
        assert post is not None
        assert draft.post_id == post.id

        # ── Metrics sync via a stubbed provider (deterministic, no network) ──
        fake_provider = _make_fake_provider(
            ps.PostMetrics(likes=120, comments=30, shares=15, impressions=2000)
        )
        monkeypatch.setitem(ps.PROVIDERS, PLATFORM, fake_provider)
        ps._sync_user_posts(db, user.id, [post])
        db.commit()
        db.refresh(post)
        # interactions / impressions = 165 / 2000
        assert post.likes == 120
        assert post.engagement_rate == pytest.approx(0.0825)

        # ── Per-post analysis via a stubbed coach ───────────────────────────
        monkeypatch.setattr(
            coach_engine.EngagementCoach,
            "analyze",
            lambda self, _input: _deterministic_coach_output(),
            raising=True,
        )
        analysis_payload = analytics_service.analyze_post(db, user, post.id)
        assert analysis_payload["hook_score"] == 8

        # exactly one auto_analysis_complete event was recorded for this post
        completion_events = (
            db.query(AnalyticsEvent)
            .filter(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.event_type == "auto_analysis_complete",
                AnalyticsEvent.post_id == post.id,
            )
            .count()
        )
        assert completion_events == 1

        # ── Seed enough additional analyzed posts for synthesis to run ──────
        # The bridged+analyzed post is one record; add the rest to reach the
        # minimum so synthesis has real input.
        _seed_analyzed_posts(
            db, user.id, MIN_POSTS_FOR_SYNTHESIS - 1, run_id
        )

        # ── Cross-post synthesis via a stubbed engine ───────────────────────
        monkeypatch.setattr(
            learning_insight_service.InsightSynthesisEngine,
            "generate",
            lambda self, _input: _good_synthesis_output(),
            raising=True,
        )
        insight = synthesize_user_insights(db, user, PLATFORM)
        assert insight is not None
        assert insight.summary == KNOWN_SUMMARY
        assert insight.version == 1  # first synthesis for this (user, platform)
        # the confident candidate fact was persisted for promotion
        assert any(
            f.get("key") == PROMOTED_FACT_KEY for f in insight.candidate_facts
        )

        # ── Fact promotion ──────────────────────────────────────────────────
        new_ctx = promote_facts(db, user, PLATFORM, insight.candidate_facts)
        assert new_ctx is not None
        assert new_ctx.change_source == "fact_promotion"

        # ── Re-assemble the context and assert the learning reached the prompt
        assembled = context_service.assemble(db, user, PLATFORM)
        assert KNOWN_SUMMARY in assembled.system_prompt  # Requirement 8.1

        # The confident fact is now part of the single active UserContext.
        active = context_service.get_active_user_context(db, user)
        assert active is not None
        assert active.id == new_ctx.id
        assert active.platform_facts[PLATFORM][PROMOTED_FACT_KEY] == PROMOTED_FACT_VALUE
    finally:
        _cleanup(db, user.id)


def test_failing_stage_leaves_prior_memory_intact(db, monkeypatch):
    """A failing synthesis stage must not corrupt prior memory or committed stages.

    With a pre-existing good LearnedInsight (version N) and committed prior stages
    (a bridged Post + its PostAnalysis), a synthesis engine that raises must leave
    the prior insight unchanged (same version N, same summary) and leave the prior
    committed stages persisted (Requirements 8.5, 8.6).
    """
    run_id = uuid.uuid4().hex
    prior_version = 4
    prior_summary = "Prior learned memory that must survive a failed synthesis."

    user = _make_user(db, run_id)
    try:
        _make_active_context(db, user.id)
        _make_active_connection(db, user.id)

        # ── Prior committed stages: a bridged Post + a real PostAnalysis ────
        draft = _make_published_draft(db, user.id, run_id)
        ppid = f"{run_id}-main-ppid"
        bridged = bridge_draft_to_post(db, user, draft, {"platform_post_id": ppid})
        assert bridged is not None
        bridged_post_id = bridged.id

        monkeypatch.setattr(
            coach_engine.EngagementCoach,
            "analyze",
            lambda self, _input: _deterministic_coach_output(),
            raising=True,
        )
        analytics_service.analyze_post(db, user, bridged_post_id)
        assert (
            db.query(PostAnalysis)
            .filter(PostAnalysis.post_id == bridged_post_id)
            .count()
            == 1
        )

        # ── Establish a pre-existing good LearnedInsight at version N ───────
        seeded_at = utc_now() - timedelta(days=2)
        prior_insight = LearnedInsight(
            user_id=user.id,
            platform=PLATFORM,
            summary=prior_summary,
            why_wins=["prior win"],
            why_losses=[],
            recommendations=["prior rec"],
            candidate_facts=[],
            confidence=0.6,
            based_on_posts=9,
            based_on_analyses=9,
            period_days=30,
            model="gpt-4o-mini",
            is_mock=0,
            version=prior_version,
            generated_at=seeded_at,
            updated_at=seeded_at,
        )
        db.add(prior_insight)
        db.commit()
        prior_insight_id = prior_insight.id

        # ── Enough analyzed posts that synthesis would actually run the engine
        _seed_analyzed_posts(db, user.id, MIN_POSTS_FOR_SYNTHESIS - 1, run_id)

        # ── Make the synthesis stage fail ───────────────────────────────────
        def _boom(self, _input):
            raise RuntimeError("synthesis engine exploded")

        monkeypatch.setattr(
            learning_insight_service.InsightSynthesisEngine,
            "generate",
            _boom,
            raising=True,
        )

        # The failing stage raises and must not have mutated prior memory.
        with pytest.raises(RuntimeError):
            synthesize_user_insights(db, user, PLATFORM)

        db.rollback()  # clear the failed transaction before re-reading state

        # ── Prior LearnedInsight is byte-for-byte unchanged (Req 8.5) ───────
        after = (
            db.query(LearnedInsight)
            .filter(LearnedInsight.id == prior_insight_id)
            .one()
        )
        assert after.version == prior_version
        assert after.summary == prior_summary

        # Exactly one insight row still exists for this (user, platform).
        assert (
            db.query(LearnedInsight)
            .filter(
                LearnedInsight.user_id == user.id,
                LearnedInsight.platform == PLATFORM,
            )
            .count()
            == 1
        )

        # ── Prior committed stages persist (Req 8.6) ────────────────────────
        persisted_post = db.query(Post).filter(Post.id == bridged_post_id).one_or_none()
        assert persisted_post is not None
        assert (
            db.query(PostAnalysis)
            .filter(PostAnalysis.post_id == bridged_post_id)
            .count()
            == 1
        )
    finally:
        _cleanup(db, user.id)
