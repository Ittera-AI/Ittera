"""Unit tests for the Publication Bridge Agent (post_bridge_service).

Covers the design B.3.1 contract / Requirements 1.1-1.5, 1.7:
  - create exactly one Post per published draft (idempotent on natural key)
  - reuse the existing Post when draft.post_id is already set
  - link to a pre-existing Post and set source="iterra_published"
  - set draft.post_id before returning
  - emit post_bridge_failed and return None when platform_post_id missing
  - publish never rolls back (draft remains published)
"""

import json

import pytest

from app.models.analytics_snapshot import AnalyticsEvent
from app.models.content_draft import ContentDraft
from app.models.post import Post
from app.models.user import User
from app.services.post_bridge_service import bridge_draft_to_post


@pytest.fixture()
def user(db):
    u = User(
        id="test-user-bridge",
        email="bridge@example.com",
        name="Bridge Tester",
        hashed_password="fakehash",
    )
    u = db.merge(u)
    db.commit()
    return u


def _make_draft(db, user, **overrides):
    fields = {
        "user_id": user.id,
        "platform": "linkedin",
        "content": "Hello world",
        "status": "published",
    }
    fields.update(overrides)
    draft = ContentDraft(**fields)
    db.add(draft)
    db.commit()
    return draft


def test_creates_exactly_one_post(db, user):
    draft = _make_draft(db, user)
    result = {"platform_post_id": "urn:li:share:111"}

    post = bridge_draft_to_post(db, user, draft, result)

    assert post is not None
    assert post.platform == "linkedin"
    assert post.platform_post_id == "urn:li:share:111"
    assert post.source == "iterra_published"
    assert post.content == "Hello world"
    assert draft.post_id == post.id  # Req 1.4
    count = (
        db.query(Post)
        .filter(Post.platform == "linkedin", Post.platform_post_id == "urn:li:share:111")
        .count()
    )
    assert count == 1  # Req 1.1


def test_idempotent_on_natural_key(db, user):
    draft1 = _make_draft(db, user)
    result = {"platform_post_id": "urn:li:share:dup"}
    post1 = bridge_draft_to_post(db, user, draft1, result)

    # A second draft published with the same platform_post_id must reuse the Post.
    draft2 = _make_draft(db, user)
    post2 = bridge_draft_to_post(db, user, draft2, result)

    assert post1.id == post2.id  # Req 1.7 — at most one Post per natural key
    assert draft2.post_id == post1.id
    count = (
        db.query(Post)
        .filter(Post.platform == "linkedin", Post.platform_post_id == "urn:li:share:dup")
        .count()
    )
    assert count == 1


def test_returns_existing_when_already_bridged(db, user):
    draft = _make_draft(db, user)
    post = bridge_draft_to_post(db, user, draft, {"platform_post_id": "urn:li:share:222"})

    # Second call with the draft already linked returns the same Post, no new row.
    again = bridge_draft_to_post(db, user, draft, {"platform_post_id": "urn:li:share:222"})

    assert again.id == post.id  # Req 1.2
    count = (
        db.query(Post)
        .filter(Post.platform_post_id == "urn:li:share:222")
        .count()
    )
    assert count == 1


def test_links_existing_scraped_post_and_sets_source(db, user):
    # A scraper created the Post first with the default "imported" source.
    scraped = Post(
        user_id=user.id,
        platform="linkedin",
        platform_post_id="urn:li:share:scraped",
        content="scraped content",
        content_type="post",
        source="imported",
    )
    db.add(scraped)
    db.commit()

    draft = _make_draft(db, user)
    post = bridge_draft_to_post(db, user, draft, {"platform_post_id": "urn:li:share:scraped"})

    assert post.id == scraped.id  # Req 1.3 — linked, not duplicated
    assert post.source == "iterra_published"
    assert draft.post_id == scraped.id
    count = (
        db.query(Post)
        .filter(Post.platform_post_id == "urn:li:share:scraped")
        .count()
    )
    assert count == 1


def test_missing_platform_post_id_emits_event_and_succeeds(db, user):
    draft = _make_draft(db, user)

    post = bridge_draft_to_post(db, user, draft, {})

    assert post is None  # Req 1.5
    assert draft.post_id is None
    # publish not rolled back — draft remains in published status
    assert draft.status == "published"
    event = (
        db.query(AnalyticsEvent)
        .filter(
            AnalyticsEvent.user_id == user.id,
            AnalyticsEvent.event_type == "post_bridge_failed",
        )
        .first()
    )
    assert event is not None
    assert event.metrics["reason"] == "no_platform_post_id"


def test_falls_back_to_draft_platform_post_id(db, user):
    draft = _make_draft(db, user, platform_post_id="urn:li:share:fromdraft")

    post = bridge_draft_to_post(db, user, draft, {})

    assert post is not None
    assert post.platform_post_id == "urn:li:share:fromdraft"


def test_thread_content_joined_and_typed(db, user):
    segments = ["First tweet", "Second tweet", "Third tweet"]
    draft = _make_draft(db, user, platform="twitter", content=json.dumps(segments))

    post = bridge_draft_to_post(db, user, draft, {"platform_post_id": "tw-123"})

    assert post.content_type == "thread"
    assert post.content == "First tweet\n\nSecond tweet\n\nThird tweet"
