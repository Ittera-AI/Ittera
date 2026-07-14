"""
Unit tests for per-post metrics-sync routing in
``workers.celery.tasks.performance_sync`` (spec task 3.2).

Covers requirement 7.5 (route to the provider matching ``post.platform``) and
requirement 7.6 (unsupported platform -> skip retrieval, record an error, leave
existing metric values unchanged).
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import workers.celery.tasks.performance_sync as ps  # noqa: E402
from workers.celery.tasks.performance_sync import PostMetrics  # noqa: E402


class _FakeDB:
    """Minimal session stand-in that records ``add`` calls."""

    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


class _FakePost:
    def __init__(self, platform):
        self.id = "post-1"
        self.user_id = "user-1"
        self.platform = platform
        self.platform_post_id = "urn:123"
        self.likes = 1
        self.comments = 1
        self.shares = 1
        self.impressions = 500
        self.engagement_rate = 0.42
        self.synced_at = None


def _make_provider(platform, metrics):
    class _FakeProvider:
        def __init__(self):
            self.platform = platform
            self.called_with = None

        async def fetch(self, conn, post):
            self.called_with = (conn, post)
            return metrics

    return _FakeProvider()


def test_routes_to_provider_matching_platform(monkeypatch):
    """7.5: the fetch is routed to the provider whose platform matches the post."""
    provider = _make_provider(
        "faketest", PostMetrics(likes=100, comments=20, shares=5, impressions=1000)
    )
    monkeypatch.setitem(ps.PROVIDERS, "faketest", provider)

    db = _FakeDB()
    post = _FakePost("faketest")

    result = ps._sync_single_post(db, conn=object(), post=post)

    assert result is True
    assert provider.called_with is not None  # provider was actually invoked
    assert post.likes == 100
    assert post.comments == 20
    assert post.shares == 5
    assert post.impressions == 1000
    # interactions / impressions = 125 / 1000
    assert post.engagement_rate == pytest.approx(0.125)
    assert post.synced_at is not None
    assert db.added == []  # no error recorded on the happy path


def test_unsupported_platform_records_error_and_preserves_metrics():
    """7.6: no matching provider -> skip retrieval, record error, leave metrics."""
    db = _FakeDB()
    post = _FakePost("instagram")  # not in PROVIDERS
    before = (post.likes, post.comments, post.shares, post.impressions, post.engagement_rate)

    result = ps._sync_single_post(db, conn=None, post=post)

    assert result is False
    # Existing metric values are untouched.
    assert (post.likes, post.comments, post.shares, post.impressions, post.engagement_rate) == before
    assert post.synced_at is None
    # Exactly one unsupported-platform error event was recorded.
    assert len(db.added) == 1
    event = db.added[0]
    assert event.event_type == "metrics_sync_unsupported"
    assert event.post_id == post.id
    assert event.metrics.get("platform") == "instagram"


def test_impressions_preserved_when_provider_reports_none(monkeypatch):
    """7.3/7.4: a None impressions value preserves the prior stored value."""
    provider = _make_provider(
        "faketest", PostMetrics(likes=50, comments=10, shares=10, impressions=None)
    )
    monkeypatch.setitem(ps.PROVIDERS, "faketest", provider)

    post = _FakePost("faketest")
    post.impressions = 777  # prior value that must be preserved

    result = ps._sync_single_post(_FakeDB(), conn=object(), post=post)

    assert result is True
    assert post.impressions == 777


def test_no_metrics_returns_false(monkeypatch):
    """A provider returning None metrics is a non-fatal failure (caller counts it)."""
    provider = _make_provider("faketest", None)
    monkeypatch.setitem(ps.PROVIDERS, "faketest", provider)

    post = _FakePost("faketest")
    before = (post.likes, post.comments, post.shares, post.impressions)

    result = ps._sync_single_post(_FakeDB(), conn=object(), post=post)

    assert result is False
    assert (post.likes, post.comments, post.shares, post.impressions) == before
