"""Property-based tests for the Publication Bridge Agent (post_bridge_service).

Encodes the design's Correctness Properties for Gap 1:

  - Property 1: Bridge creates exactly one Post per published draft (idempotent).
    For any sequence of bridge calls that share the same (platform, platform_post_id)
    natural key — across one or more published drafts and regardless of how many
    times each draft is re-bridged — exactly one Post exists for that natural key
    afterward.

  - Property 2: A published draft is always linked to a learnable Post.
    For any published draft with a valid (non-empty) platform_post_id, after
    bridging the draft is linked (draft.post_id is set) and resolves to an existing
    Post carrying that natural key.

**Validates: Requirements 1.1, 1.2, 1.4**

These tests reuse the shared SQLite ``db`` fixture from conftest.py. Hypothesis runs
many examples against the single function-scoped ``db`` fixture, so every example
namespaces its generated ``platform_post_id`` with a unique run id (preventing
cross-example natural-key collisions) and deletes the rows it created in a finally
block to keep DB state controlled.
"""

import uuid

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.models.analytics_snapshot import AnalyticsEvent
from app.models.content_draft import ContentDraft
from app.models.post import Post
from app.models.user import User
from app.services.post_bridge_service import bridge_draft_to_post

# Platforms the loop supports; the natural key is (platform, platform_post_id).
PLATFORMS = ["linkedin", "twitter"]

# Non-empty platform_post_id fragments (1..255 chars per Requirement 1.1). We keep
# the alphabet to printable, non-whitespace characters so generated ids are always
# truthy and meaningful natural keys.
_PPID_ALPHABET = st.characters(
    min_codepoint=33,  # exclude space (32) and control chars
    max_codepoint=126,
)
ppid_fragments = st.text(alphabet=_PPID_ALPHABET, min_size=1, max_size=50)


@pytest.fixture()
def user(db):
    u = User(
        id="test-user-bridge-properties",
        email="bridge-properties@example.com",
        name="Bridge Property Tester",
        hashed_password="fakehash",
    )
    u = db.merge(u)
    db.commit()
    return u


def _make_draft(db, user, platform, **overrides):
    fields = {
        "user_id": user.id,
        "platform": platform,
        "content": "Property test content",
        "status": "published",
    }
    fields.update(overrides)
    draft = ContentDraft(**fields)
    db.add(draft)
    db.commit()
    return draft


def _cleanup(db, user, platform, ppid, draft_ids):
    """Delete the rows created by one example to keep DB state controlled."""
    db.query(ContentDraft).filter(ContentDraft.id.in_(draft_ids)).delete(
        synchronize_session=False
    )
    db.query(Post).filter(
        Post.platform == platform, Post.platform_post_id == ppid
    ).delete(synchronize_session=False)
    db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == user.id).delete(
        synchronize_session=False
    )
    db.commit()


@settings(
    max_examples=75,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(
    platform=st.sampled_from(PLATFORMS),
    ppid_fragment=ppid_fragments,
    num_drafts=st.integers(min_value=1, max_value=5),
    repeat_calls=st.integers(min_value=1, max_value=4),
)
def test_property1_exactly_one_post_per_natural_key(
    db, user, platform, ppid_fragment, num_drafts, repeat_calls
):
    """Property 1: idempotency holds regardless of draft count and call ordering.

    Many drafts published with the SAME (platform, platform_post_id) and bridged
    any number of times must collapse to exactly one Post for that natural key.
    """
    # Namespace the natural key so examples never collide in the shared test DB.
    ppid = f"{uuid.uuid4().hex}:{ppid_fragment}"
    result = {"platform_post_id": ppid}
    draft_ids = []
    try:
        returned_post_ids = set()
        for _ in range(num_drafts):
            draft = _make_draft(db, user, platform)
            draft_ids.append(draft.id)
            # Re-bridge the same draft multiple times — must be idempotent.
            for _ in range(repeat_calls):
                post = bridge_draft_to_post(db, user, draft, result)
                assert post is not None
                returned_post_ids.add(post.id)

        # Every call resolved to the same single Post.
        assert len(returned_post_ids) == 1

        # Exactly one Post exists for the natural key (Requirements 1.1, 1.7).
        count = (
            db.query(Post)
            .filter(Post.platform == platform, Post.platform_post_id == ppid)
            .count()
        )
        assert count == 1

        # Every draft is linked to that one Post (Requirement 1.4).
        only_post_id = next(iter(returned_post_ids))
        for draft_id in draft_ids:
            linked = db.query(ContentDraft).filter(ContentDraft.id == draft_id).one()
            assert linked.post_id == only_post_id
    finally:
        _cleanup(db, user, platform, ppid, draft_ids)


@settings(
    max_examples=75,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(
    platform=st.sampled_from(PLATFORMS),
    ppid_fragment=ppid_fragments,
)
def test_property2_published_draft_always_linked_to_learnable_post(
    db, user, platform, ppid_fragment
):
    """Property 2: a published draft with a valid platform_post_id is always linked.

    After bridging, draft.post_id is set and resolves to an existing Post carrying
    the natural key (Requirements 1.1, 1.2, 1.4).
    """
    ppid = f"{uuid.uuid4().hex}:{ppid_fragment}"
    draft = _make_draft(db, user, platform)
    draft_ids = [draft.id]
    try:
        post = bridge_draft_to_post(db, user, draft, {"platform_post_id": ppid})

        # The bridge produced a learnable Post (Requirement 1.1).
        assert post is not None

        # The draft is linked (Requirement 1.4) ...
        assert draft.post_id is not None
        assert draft.post_id == post.id

        # ... and the link resolves to an existing Post with the natural key.
        resolved = db.query(Post).filter(Post.id == draft.post_id).one_or_none()
        assert resolved is not None
        assert resolved.platform == platform
        assert resolved.platform_post_id == ppid

        # Re-reading the draft from the DB confirms the link persisted (Req 1.2).
        reloaded = db.query(ContentDraft).filter(ContentDraft.id == draft.id).one()
        assert reloaded.post_id == post.id
    finally:
        _cleanup(db, user, platform, ppid, draft_ids)
