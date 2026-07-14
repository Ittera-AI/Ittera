"""Orchestration wiring tests for the self-learning loop Celery tasks.

The P1-P8 property tests exercise the loop *services* directly. This module covers
the previously-untested Celery *task* layer: the ENABLE_LEARNING_LOOP gate and the
on_post_published -> pull_and_analyze_post -> synthesize_user_insights chain.

It runs the chain in-process (conftest sets task_always_eager), stubbing the leaf
functions so no network or LLM is hit. This is the verifiable substitute for live
staging validation, which requires a real Celery worker + Redis broker.
"""

import uuid

import pytest

from app.config import settings
from app.db.datetime_helpers import utc_now
from app.models.post import Post
from app.models.user import User
from app.services import analytics_service, learning_insight_service
from workers.celery.tasks import learning_loop
from workers.celery.tasks import performance_sync


def _make_user_and_post(db):
    run = uuid.uuid4().hex
    user = User(
        id=f"ll-user-{run}",
        email=f"ll-{run}@example.com",
        hashed_password="x",
        name="Loop Orchestration",
        primary_platform="linkedin",
    )
    post = Post(
        id=f"ll-post-{run}",
        user_id=user.id,
        platform="linkedin",
        content="hello world",
        content_type="post",
        source="iterra_published",
        published_at=utc_now(),
    )
    db.add(user)
    db.add(post)
    db.commit()
    return user, post


def test_on_post_published_skips_when_loop_disabled(db, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_LEARNING_LOOP", False)
    _, post = _make_user_and_post(db)

    result = learning_loop.on_post_published.apply(args=[post.id]).get()

    assert result["skipped"] is True
    assert result["reason"] == "learning_loop_disabled"


def test_on_post_published_runs_full_chain_when_enabled(db, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_LEARNING_LOOP", True)
    # One pull pass keeps the assertion deterministic (default is three windows).
    monkeypatch.setattr(learning_loop, "_pull_delays", lambda: [1])

    user, post = _make_user_and_post(db)
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        performance_sync, "sync_single_post", lambda post_id: calls.append(("sync", post_id))
    )
    monkeypatch.setattr(
        analytics_service,
        "analyze_post",
        lambda db, user, post_id: calls.append(("analyze", post_id)) or {},
    )
    monkeypatch.setattr(
        learning_insight_service,
        "_has_new_analyses_since_last_synthesis",
        lambda db, user, platform: True,
    )
    monkeypatch.setattr(
        learning_insight_service,
        "synthesize_user_insights",
        lambda db, user, platform: calls.append(("synth", platform)) or None,
    )

    result = learning_loop.on_post_published.apply(args=[post.id]).get()

    assert result["scheduled_pulls"] == 1
    assert ("sync", post.id) in calls
    assert ("analyze", post.id) in calls
    assert ("synth", "linkedin") in calls
