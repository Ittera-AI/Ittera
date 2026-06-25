"""Property-based test for automatic per-post analysis idempotency.

Encodes the design's Correctness Property for Gap 2 (auto-analysis orchestration):

  - Property 3: Auto-analysis never double-charges.
    ``analytics_service.analyze_post`` has a fresh-analysis short-circuit: when a
    PostAnalysis already exists and is strictly younger than 30 days, the call
    returns the cached result WITHOUT invoking the LLM (``EngagementCoach.analyze``)
    and WITHOUT emitting an ``auto_analysis_complete`` AnalyticsEvent. Only a real
    analysis run (no prior analysis, or a stale one) calls the coach and emits
    exactly one completion event.

    Therefore, for ANY number N >= 1 of repeated ``analyze_post`` calls on the same
    post within the fresh window, the underlying coach ``analyze`` is invoked AT MOST
    once (the first call runs it; every subsequent call hits the short-circuit) and
    exactly ONE ``auto_analysis_complete`` AnalyticsEvent exists for that post
    afterward — never N. This proves repeated analysis never double-charges.

**Validates: Requirements 2.2**

This test reuses the shared SQLite ``db`` fixture from conftest.py. Hypothesis runs
many examples against the single function-scoped ``db`` fixture, so every example
namespaces the rows it creates with a unique run id (preventing cross-example
collisions) and deletes those rows in a finally block to keep DB state controlled.
``EngagementCoach.analyze`` is monkeypatched (where analytics_service references it)
with a call-counting fake returning a valid coach result, so no LLM is ever called
and "charging" is directly observable as the coach call count.
"""

import uuid

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.db.datetime_helpers import utc_now
from app.models.analytics_snapshot import AnalyticsEvent
from app.models.brand_profile import BrandProfile
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.user import User
from app.services import analytics_service

# The coach lives in iterra_ai; analytics_service imports it lazily inside
# analyze_post, so patching the class method here is what the service will use.
from iterra_ai.coach.engine import EngagementCoach
from iterra_ai.coach.schemas import CoachOutput


class _CoachController:
    """Counts how many times the (fake) coach.analyze is invoked."""

    def __init__(self):
        self.calls = 0

    def make_output(self) -> CoachOutput:
        return CoachOutput(
            hook_score=8,
            tone_match_score=7,
            structure_score=7,
            cta_effectiveness="strong",
            top_strength="Strong, specific opening line",
            top_improvement="Tighten the closing call to action",
            detailed_feedback="Clear hook and good flow; the CTA could be sharper.",
            predicted_engagement="high",
            rewrite_suggestion=None,
        )


@pytest.fixture()
def coach_control(monkeypatch):
    """Monkeypatch EngagementCoach.analyze with a call-counting fake.

    The fake records every invocation (so a re-analysis would be observable as an
    extra "charge") and returns a valid CoachOutput. No real LLM call happens.
    """
    controller = _CoachController()

    def fake_analyze(self, _coach_input):
        controller.calls += 1
        return controller.make_output()

    monkeypatch.setattr(EngagementCoach, "analyze", fake_analyze, raising=True)
    return controller


def _make_user(db, run_id: str) -> User:
    user = User(
        id=f"idem-prop-user-{run_id}",
        email=f"idem-prop-{run_id}@example.com",
        name="Idempotency Property Tester",
        hashed_password="fakehash",
    )
    db.add(user)
    db.commit()
    return user


def _make_post(db, user_id: str, run_id: str) -> Post:
    post = Post(
        id=f"idem-prop-post-{run_id}",
        user_id=user_id,
        platform="linkedin",
        platform_post_id=f"idem-prop-ppid-{run_id}",
        content="A property-test post body that the coach will analyze once.",
        content_type="post",
        published_at=utc_now(),
        source="iterra_published",
        likes=12,
        comments=3,
        shares=1,
        impressions=200,
        engagement_rate=0.08,
    )
    db.add(post)
    db.commit()
    return post


def _auto_analysis_event_count(db, post_id: str) -> int:
    return (
        db.query(AnalyticsEvent)
        .filter(
            AnalyticsEvent.post_id == post_id,
            AnalyticsEvent.event_type == "auto_analysis_complete",
        )
        .count()
    )


def _cleanup(db, user_id: str, post_id: str):
    """Delete rows created by one example to keep DB state controlled."""
    db.query(PostAnalysis).filter(PostAnalysis.post_id == post_id).delete(
        synchronize_session=False
    )
    db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(BrandProfile).filter(BrandProfile.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(Post).filter(Post.id == post_id).delete(synchronize_session=False)
    db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
    db.commit()


@settings(
    max_examples=40,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(num_calls=st.integers(min_value=1, max_value=6))
def test_property3_auto_analysis_never_double_charges(db, coach_control, num_calls):
    """Property 3: N repeated analyze_post calls charge at most once.

    For any N >= 1 repeated analyses of the same fresh post, the coach is invoked at
    most once and exactly one auto_analysis_complete event exists afterward.
    """
    run_id = uuid.uuid4().hex
    user = _make_user(db, run_id)
    post = _make_post(db, user.id, run_id)
    # The coach_control fixture is created once for the whole @given run and is NOT
    # reset between Hypothesis examples (function_scoped_fixture health check is
    # suppressed), so its call counter accumulates across examples. Measure the
    # per-example delta to assert "at most one charge for THIS example's post".
    calls_before = coach_control.calls
    try:
        for _ in range(num_calls):
            analytics_service.analyze_post(db, user, post.id)

        # The LLM/coach was charged at most once across all N calls: the first call
        # runs analysis; every later call hits the fresh-analysis (<30d) short-circuit.
        assert coach_control.calls - calls_before <= 1

        # Since N >= 1, exactly one real analysis ran, so exactly one completion
        # event exists for the post — never N (Requirement 2.2).
        assert _auto_analysis_event_count(db, post.id) == 1
    finally:
        _cleanup(db, user.id, post.id)
