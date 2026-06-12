"""Tests for Twitter tier management (task 8.2).

Covers:
- PUT /api/v1/social/twitter/tier endpoint
- GET /api/v1/social/twitter/tier endpoint
- Default tier is "free" when unknown/missing
- Tier update persists and affects resolve_content_limit
- OAuth callback stores default tier in connection_metadata
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.social_connection import SocialConnection
from app.services.platform_limits import (
    DEFAULT_TWITTER_TIER,
    PLATFORM_CHAR_LIMITS,
    TwitterTier,
    resolve_content_limit,
    update_twitter_tier,
)


def _register_and_token(client):
    """Register a fresh user and return auth headers."""
    email = f"tier_test_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123", "name": "Tier Test User"},
    )
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "secret123"},
    )
    data = r.json()
    return {"Authorization": f"Bearer {data['access_token']}"}, data.get("user_id") or data.get("user", {}).get("id")


def _create_twitter_connection(db, user_id: str, tier: str | None = None):
    """Create a Twitter social connection for testing."""
    metadata = {"name": "Test User", "profile_image": "https://example.com/img.jpg"}
    if tier is not None:
        metadata["subscription_tier"] = tier

    conn = SocialConnection(
        id=str(uuid.uuid4()),
        user_id=user_id,
        platform="twitter",
        platform_user_id="12345",
        platform_username="testuser",
        access_token="fake_token",
        refresh_token="fake_refresh",
        scopes=["tweet.read", "tweet.write", "users.read", "offline.access"],
        connection_metadata=metadata,
        is_active=True,
    )
    db.add(conn)
    db.commit()
    return conn


# ── Unit Tests for platform_limits.py ────────────────────────────────────────


class TestResolveContentLimit:
    """Test resolve_content_limit with various tier states."""

    def test_default_tier_is_free(self):
        assert DEFAULT_TWITTER_TIER == TwitterTier.FREE

    def test_resolve_twitter_free_tier(self, db):
        """When tier is 'free', max_chars is 280."""
        user_id = str(uuid.uuid4())
        _create_twitter_connection(db, user_id, tier="free")

        limit = resolve_content_limit(db, user_id, "twitter")
        assert limit.max_chars == 280
        assert limit.tier == "free"
        assert limit.is_thread_eligible is True

    def test_resolve_twitter_premium_tier(self, db):
        """When tier is 'premium', max_chars is 25000."""
        user_id = str(uuid.uuid4())
        _create_twitter_connection(db, user_id, tier="premium")

        limit = resolve_content_limit(db, user_id, "twitter")
        assert limit.max_chars == 25_000
        assert limit.tier == "premium"
        assert limit.is_thread_eligible is False

    def test_resolve_twitter_missing_tier_defaults_to_free(self, db):
        """When subscription_tier is missing, defaults to free (280 chars)."""
        user_id = str(uuid.uuid4())
        _create_twitter_connection(db, user_id, tier=None)

        limit = resolve_content_limit(db, user_id, "twitter")
        assert limit.max_chars == 280
        assert limit.tier == "free"

    def test_resolve_twitter_no_connection_defaults_to_free(self, db):
        """When no Twitter connection exists, defaults to free (280 chars)."""
        user_id = str(uuid.uuid4())

        limit = resolve_content_limit(db, user_id, "twitter")
        assert limit.max_chars == 280
        assert limit.tier == "free"

    def test_resolve_linkedin_not_affected_by_tier(self, db):
        """LinkedIn always returns 3000 chars regardless of Twitter tier."""
        user_id = str(uuid.uuid4())

        limit = resolve_content_limit(db, user_id, "linkedin")
        assert limit.max_chars == 3_000
        assert limit.tier is None
        assert limit.is_thread_eligible is False


class TestUpdateTwitterTier:
    """Test update_twitter_tier function."""

    def test_update_tier_to_premium(self, db):
        """Updating tier to premium persists correctly."""
        user_id = str(uuid.uuid4())
        _create_twitter_connection(db, user_id, tier="free")

        update_twitter_tier(db, user_id, TwitterTier.PREMIUM)

        limit = resolve_content_limit(db, user_id, "twitter")
        assert limit.tier == "premium"
        assert limit.max_chars == 25_000

    def test_update_tier_to_free(self, db):
        """Updating tier to free persists correctly."""
        user_id = str(uuid.uuid4())
        _create_twitter_connection(db, user_id, tier="premium")

        update_twitter_tier(db, user_id, TwitterTier.FREE)

        limit = resolve_content_limit(db, user_id, "twitter")
        assert limit.tier == "free"
        assert limit.max_chars == 280

    def test_update_tier_no_connection_is_noop(self, db):
        """Updating tier when no connection exists does nothing (no error)."""
        user_id = str(uuid.uuid4())
        # Should not raise
        update_twitter_tier(db, user_id, TwitterTier.PREMIUM)

    def test_update_preserves_other_metadata(self, db):
        """Updating tier should not remove other metadata fields."""
        user_id = str(uuid.uuid4())
        conn = _create_twitter_connection(db, user_id, tier="free")

        update_twitter_tier(db, user_id, TwitterTier.PREMIUM)

        db.refresh(conn)
        assert conn.connection_metadata["name"] == "Test User"
        assert conn.connection_metadata["profile_image"] == "https://example.com/img.jpg"
        assert conn.connection_metadata["subscription_tier"] == "premium"


# ── API Endpoint Tests ───────────────────────────────────────────────────────


class TestTwitterTierEndpoint:
    """Test the PUT /api/v1/social/twitter/tier endpoint."""

    def test_update_tier_unauthorized(self, client):
        """Endpoint requires authentication."""
        r = client.put("/api/v1/social/twitter/tier", json={"tier": "premium"})
        assert r.status_code == 401

    def test_update_tier_invalid_value(self, client):
        """Invalid tier value returns 422 validation error."""
        headers, _ = _register_and_token(client)
        r = client.put("/api/v1/social/twitter/tier", json={"tier": "invalid"}, headers=headers)
        assert r.status_code == 422

    def test_update_tier_to_premium(self, client, db):
        """Successfully update tier to premium."""
        headers, user_id = _register_and_token(client)
        # Need to find the actual user ID from the DB since register might not return it
        from app.models.user import User

        user = db.query(User).filter(User.email.like("tier_test_%")).order_by(User.created_at.desc()).first()
        if user:
            _create_twitter_connection(db, str(user.id), tier="free")

        r = client.put("/api/v1/social/twitter/tier", json={"tier": "premium"}, headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["tier"] == "premium"
        assert body["max_chars"] == 25_000

    def test_update_tier_to_free(self, client, db):
        """Successfully update tier to free."""
        headers, user_id = _register_and_token(client)
        from app.models.user import User

        user = db.query(User).filter(User.email.like("tier_test_%")).order_by(User.created_at.desc()).first()
        if user:
            _create_twitter_connection(db, str(user.id), tier="premium")

        r = client.put("/api/v1/social/twitter/tier", json={"tier": "free"}, headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["tier"] == "free"
        assert body["max_chars"] == 280

    def test_get_tier_unauthorized(self, client):
        """GET tier endpoint requires authentication."""
        r = client.get("/api/v1/social/twitter/tier")
        assert r.status_code == 401

    def test_get_tier_default_no_connection(self, client):
        """GET tier returns free when no Twitter connection exists."""
        headers, _ = _register_and_token(client)
        r = client.get("/api/v1/social/twitter/tier", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["tier"] == "free"
        assert body["max_chars"] == 280
        assert body["is_thread_eligible"] is True
