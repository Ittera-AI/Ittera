"""Property-based tests for learning injection into the assembled prompt.

Encodes the design's Correctness Property for Gap 4 (context injection):

  - Property 6: Learnings reach the next prompt.
    If an active ``LearnedInsight`` exists for a ``(user, platform)``, then after
    ``context_service.assemble(...)`` the resulting ``system_prompt`` contains the
    insight's ``summary`` text, plus each ``why_win`` and ``recommendation`` that
    the builder emits. The builder truncates ``why_wins``/``recommendations`` to the
    first 4 of each (``app/services/context_service.py`` ``_build_system_prompt``),
    so containment is asserted for exactly those it includes.

    The converse degradation case is also asserted: when NO ``LearnedInsight``
    exists for the ``(user, platform)``, the "What We've Learned" block/marker is
    absent from the assembled prompt (prior behavior preserved).

**Validates: Requirements 4.1, 4.2**

These tests reuse the shared SQLite ``db`` fixture from conftest.py. Hypothesis runs
many examples against the single function-scoped ``db`` fixture, so every example
namespaces its ``platform`` with a unique run id (preventing cross-example collisions
on the ``uq_learned_insight_user_platform`` unique key) and deletes the rows it
created in a finally block to keep DB state controlled.
"""

import uuid

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.models.learned_insight import LearnedInsight
from app.models.user import User
from app.services import context_service
from app.services.learning_insight_service import get_active_insight

# The Layer 3 marker emitted by _build_system_prompt when an insight exists.
LEARNED_MARKER = "## What We've Learned (apply this)"

# The builder truncates each list to its first 4 entries.
MAX_EMITTED = 4

# Printable, non-whitespace text so generated values are always truthy and survive
# a round-trip through SQLite without encoding surprises.
_PRINTABLE = st.characters(min_codepoint=33, max_codepoint=126)

# Non-empty summary (Requirement 4.1 covers the "exactly one active insight" case).
summaries = st.text(alphabet=_PRINTABLE, min_size=1, max_size=200)

# Arbitrary win-pattern / recommendation text (each entry non-empty printable).
finding_lists = st.lists(
    st.text(alphabet=_PRINTABLE, min_size=1, max_size=60),
    min_size=0,
    max_size=8,
)


@pytest.fixture()
def user(db):
    u = User(
        id="test-user-learning-injection",
        email="learning-injection@example.com",
        name="Learning Injection Tester",
        hashed_password="fakehash",
    )
    u = db.merge(u)
    db.commit()
    return u


def _seed_insight(db, user, platform, summary, why_wins, recommendations):
    insight = LearnedInsight(
        user_id=user.id,
        platform=platform,
        summary=summary,
        why_wins=why_wins,
        why_losses=[],
        recommendations=recommendations,
        candidate_facts=[],
        version=1,
    )
    db.add(insight)
    db.commit()
    return insight


def _cleanup(db, user, platform):
    db.query(LearnedInsight).filter(
        LearnedInsight.user_id == user.id,
        LearnedInsight.platform == platform,
    ).delete(synchronize_session=False)
    db.commit()


@settings(
    max_examples=75,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(
    summary=summaries,
    why_wins=finding_lists,
    recommendations=finding_lists,
)
def test_property6_learnings_reach_the_next_prompt(
    db, user, summary, why_wins, recommendations
):
    """Property 6: an active insight's summary (and emitted wins/recs) reach the prompt.

    For any active LearnedInsight with a non-empty summary, assemble(...) produces a
    system_prompt that contains the summary text, the "What We've Learned" marker, and
    each why_win / recommendation the builder includes (the first 4 of each).
    """
    # Namespace the platform so examples never collide on the unique key.
    platform = f"linkedin-{uuid.uuid4().hex}"
    try:
        _seed_insight(db, user, platform, summary, why_wins, recommendations)

        ctx = context_service.assemble(db, user, platform)
        prompt = ctx.system_prompt

        # The learnings block is present and carries the summary verbatim (Req 4.1).
        assert LEARNED_MARKER in prompt
        assert summary in prompt

        # Each emitted win pattern and recommendation appears (Req 4.2). The builder
        # truncates to the first 4 of each, so assert containment only for those.
        for win in why_wins[:MAX_EMITTED]:
            assert win in prompt
        for rec in recommendations[:MAX_EMITTED]:
            assert rec in prompt
    finally:
        _cleanup(db, user, platform)


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(platform_seed=st.uuids())
def test_property6_converse_no_insight_omits_learnings_block(db, user, platform_seed):
    """Converse degradation: with NO LearnedInsight, the learnings block is absent.

    When no active insight exists for the (user, platform), the assembled prompt
    must omit the "What We've Learned" block entirely, preserving prior behavior.
    """
    platform = f"linkedin-{platform_seed.hex}"
    try:
        # Guard: ensure no insight exists for this (user, platform).
        assert get_active_insight(db, user, platform) is None

        ctx = context_service.assemble(db, user, platform)
        prompt = ctx.system_prompt

        assert LEARNED_MARKER not in prompt
        assert "What We've Learned" not in prompt
    finally:
        _cleanup(db, user, platform)
