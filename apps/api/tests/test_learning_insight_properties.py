"""Property-based tests for the Insight Memory Agent (learning_insight_service).

Encodes the design's Correctness Properties for Gap 3 (cross-post synthesis memory):

  - Property 4: Synthesis is monotonic and non-destructive.
    Across any sequence of synthesis runs, the active LearnedInsight version never
    decreases and a previously-good insight is never wiped. When the engine returns
    degraded output (heuristic/mock or empty) AND a prior insight exists, the prior
    insight is retained unchanged (same version, same summary, same updated_at).
    When the engine returns good (usable, non-mock) output, the version increases by
    exactly one relative to the prior version (or is created at version 1 when none
    existed).

  - Property 7: Platform isolation.
    Synthesizing for one platform never creates or mutates the LearnedInsight row of
    any other platform. After synthesizing platform A, every other platform's row is
    byte-for-byte unchanged (version, summary, updated_at).

**Validates: Requirements 3.1, 3.3, 3.4**

These tests reuse the shared SQLite ``db`` fixture from conftest.py. Hypothesis runs
many examples against the single function-scoped ``db`` fixture, so every example
namespaces the rows it creates with a unique run id (preventing cross-example
collisions) and deletes those rows in a finally block to keep DB state controlled.
The :class:`InsightSynthesisEngine` is monkeypatched (where the service references it)
to return controlled good vs degraded output so the properties are deterministic and
no LLM is ever called.
"""

import uuid
from datetime import timedelta

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.db.datetime_helpers import utc_now
from app.models.analytics_snapshot import AnalyticsEvent
from app.models.learned_insight import LearnedInsight
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.user import User
from app.services import learning_insight_service
from app.services.learning_insight_service import (
    MIN_POSTS_FOR_SYNTHESIS,
    get_active_insight,
    synthesize_user_insights,
)
from iterra_ai.insight.schemas import InsightSynthesisOutput

PLATFORMS = ["linkedin", "twitter", "instagram"]


def _good_output(tag: str) -> InsightSynthesisOutput:
    """A usable, non-mock synthesis result that should be persisted/versioned."""
    return InsightSynthesisOutput(
        summary=f"Questions outperform statements ({tag}).",
        why_wins=["question-led hooks drive replies"],
        why_losses=["long preambles bury the point"],
        recommendations=["open with a question"],
        candidate_facts=[],
        confidence=0.82,
        model="gpt-4o-mini",
        is_mock=False,
    )


def _degraded_output() -> InsightSynthesisOutput:
    """A degraded (heuristic/mock + empty) result that must not wipe good data."""
    return InsightSynthesisOutput(
        summary="",
        why_wins=[],
        why_losses=[],
        recommendations=[],
        candidate_facts=[],
        confidence=0.0,
        model="heuristic",
        is_mock=True,
    )


class _EngineController:
    """Holds the next output the patched engine should return."""

    def __init__(self):
        self.output: InsightSynthesisOutput | None = None


@pytest.fixture()
def engine_control(monkeypatch):
    """Monkeypatch InsightSynthesisEngine.generate where the service references it."""
    controller = _EngineController()

    def fake_generate(self, _input):
        return controller.output

    # Patch the bound class the service imported so engine.generate is deterministic.
    monkeypatch.setattr(
        learning_insight_service.InsightSynthesisEngine,
        "generate",
        fake_generate,
        raising=True,
    )
    return controller


def _make_user(db, run_id: str) -> User:
    user = User(
        id=f"li-prop-user-{run_id}",
        email=f"li-prop-{run_id}@example.com",
        name="Insight Property Tester",
        hashed_password="fakehash",
    )
    db.add(user)
    db.commit()
    return user


def _seed_analyzed_posts(db, user_id: str, platform: str, n: int, run_id: str) -> list[str]:
    """Seed ``n`` analyzed posts (Post + PostAnalysis) within the 30-day window."""
    now = utc_now()
    post_ids: list[str] = []
    for i in range(n):
        post = Post(
            id=f"{run_id}-{platform}-post-{i}",
            user_id=user_id,
            platform=platform,
            platform_post_id=f"{run_id}-{platform}-ppid-{i}",
            content=f"{platform} post {i} content",
            content_type="post",
            published_at=now - timedelta(days=1, hours=i),
            source="iterra_published",
            likes=10 + i,
            comments=i,
            shares=i,
            impressions=100 + i,
            engagement_rate=round(0.05 * (i + 1), 4),
        )
        db.add(post)
        db.flush()
        db.add(
            PostAnalysis(
                post_id=post.id,
                hook_score=60 + i,
                tone_match_score=70,
                structure_score=70,
                cta_effectiveness="medium",
                coach_feedback={"top_strength": "hook", "top_improvement": "cta"},
            )
        )
        post_ids.append(post.id)
    db.commit()
    return post_ids


def _cleanup(db, user_id: str, post_ids: list[str]):
    """Delete rows created by one example to keep DB state controlled."""
    if post_ids:
        db.query(PostAnalysis).filter(PostAnalysis.post_id.in_(post_ids)).delete(
            synchronize_session=False
        )
        db.query(Post).filter(Post.id.in_(post_ids)).delete(synchronize_session=False)
    db.query(LearnedInsight).filter(LearnedInsight.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
    db.commit()


@settings(
    max_examples=40,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(
    platform=st.sampled_from(PLATFORMS),
    outcomes=st.lists(st.booleans(), min_size=1, max_size=6),
)
def test_property4_synthesis_monotonic_and_non_destructive(
    db, engine_control, platform, outcomes
):
    """Property 4: version never decreases; good data is never wiped.

    ``outcomes[i]`` True => the engine returns good output on run i; False =>
    degraded output. Across the whole sequence the invariant must hold every step.
    """
    run_id = uuid.uuid4().hex
    user = _make_user(db, run_id)
    post_ids = _seed_analyzed_posts(
        db, user.id, platform, MIN_POSTS_FOR_SYNTHESIS, run_id
    )
    try:
        max_seen_version = 0
        for step, good in enumerate(outcomes):
            engine_control.output = _good_output(f"r{step}") if good else _degraded_output()

            # Capture prior state BEFORE the call (the row may be mutated in place).
            prior = get_active_insight(db, user, platform)
            prior_version = prior.version if prior else None
            prior_summary = prior.summary if prior else None
            prior_updated_at = prior.updated_at if prior else None

            synthesize_user_insights(db, user, platform)

            after = get_active_insight(db, user, platform)

            if prior is None:
                # First persisted synthesis always creates version 1 (Req 3.1).
                assert after is not None
                assert after.version == 1
            elif good:
                # Good output bumps the existing row by exactly one (Req 3.7).
                assert after.version == prior_version + 1
            else:
                # Degraded output with a prior insight retains it unchanged (Req 3.3).
                assert after.version == prior_version
                assert after.summary == prior_summary
                assert after.updated_at == prior_updated_at

            # Monotonic: version never decreases across the sequence (Req 3.3).
            assert after.version >= max_seen_version
            max_seen_version = after.version
    finally:
        _cleanup(db, user.id, post_ids)


@settings(
    max_examples=40,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(data=st.data())
def test_property7_platform_isolation(db, engine_control, data):
    """Property 7: synthesizing one platform never touches another platform's row."""
    run_id = uuid.uuid4().hex
    target = data.draw(st.sampled_from(PLATFORMS), label="target_platform")
    others = [p for p in PLATFORMS if p != target]

    user = _make_user(db, run_id)
    post_ids = _seed_analyzed_posts(
        db, user.id, target, MIN_POSTS_FOR_SYNTHESIS, run_id
    )

    try:
        # Seed a distinct, pre-existing LearnedInsight for every OTHER platform.
        base_time = utc_now() - timedelta(days=3)
        for idx, other in enumerate(others):
            db.add(
                LearnedInsight(
                    user_id=user.id,
                    platform=other,
                    summary=f"pre-existing insight for {other}",
                    why_wins=[f"{other} win"],
                    why_losses=[],
                    recommendations=[f"{other} rec"],
                    candidate_facts=[],
                    confidence=0.5,
                    version=3 + idx,
                    generated_at=base_time,
                    updated_at=base_time,
                )
            )
        db.commit()

        # Snapshot the other platforms' rows before synthesizing the target.
        snapshot = {}
        for other in others:
            row = get_active_insight(db, user, other)
            snapshot[other] = (row.version, row.summary, row.updated_at)

        engine_control.output = _good_output("isolation")
        result = synthesize_user_insights(db, user, target)
        assert result is not None
        assert result.platform == target

        # Every other platform's row is unchanged (Req 3.4).
        for other in others:
            row = get_active_insight(db, user, other)
            assert (row.version, row.summary, row.updated_at) == snapshot[other]
    finally:
        _cleanup(db, user.id, post_ids)
