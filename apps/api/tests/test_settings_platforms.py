"""
Tests for GET /api/v1/social/platforms endpoint (task 9.2).

Validates:
  - Returns all connected platforms with rich status (username, connection date,
    last sync time, posting readiness, sync readiness, missing scopes)
  - Includes sync-in-progress indicator and error states
  - Supports disconnect/reconnect actions
  - Platforms with providers get rich status via provider.get_status()
  - Platforms without providers (instagram, google_drive) get basic connection info

Requirements: 5.1, 5.2, 5.3
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.services.content_sync_provider import PlatformStatus
from main import app


@pytest.fixture()
def mock_user():
    """Create a mock user without DB dependency."""
    return User(
        id="test-user-settings",
        email="settings@example.com",
        name="Settings Tester",
        hashed_password="fakehash",
    )


@pytest.fixture()
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture()
def authed_client(mock_user, mock_db):
    """Client with auth and DB overridden."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


class TestGetAllPlatformsStatus:
    """Tests for GET /api/v1/social/platforms."""

    def test_returns_platforms_with_provider_status(self, authed_client, mock_db):
        """Platforms in the sync provider registry get rich status from provider.get_status()."""
        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Mock connections
        linkedin_conn = MagicMock(spec=SocialConnection)
        linkedin_conn.platform = "linkedin"
        linkedin_conn.is_active = True
        linkedin_conn.platform_username = "testlinkedin"
        linkedin_conn.created_at = now
        linkedin_conn.last_synced_at = now

        twitter_conn = MagicMock(spec=SocialConnection)
        twitter_conn.platform = "twitter"
        twitter_conn.is_active = True
        twitter_conn.platform_username = "testtwitter"
        twitter_conn.created_at = now
        twitter_conn.last_synced_at = now

        # Mock DB query
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [linkedin_conn, twitter_conn]
        mock_db.query.return_value = mock_query

        # Mock provider statuses
        linkedin_status = PlatformStatus(
            connected=True,
            platform_username="testlinkedin",
            last_synced_at=now,
            synced_posts=15,
            scopes=["openid", "w_member_social"],
            posting_ready=True,
            read_sync_ready=False,
            missing_posting_scopes=[],
            missing_read_scopes=["r_member_social"],
            reconnect_required=False,
            message="LinkedIn posting is ready.",
            sync_status="completed",
            sync_error=None,
        )

        twitter_status = PlatformStatus(
            connected=True,
            platform_username="testtwitter",
            last_synced_at=now,
            synced_posts=42,
            scopes=["tweet.read", "tweet.write", "users.read", "offline.access"],
            posting_ready=True,
            read_sync_ready=True,
            missing_posting_scopes=[],
            missing_read_scopes=[],
            reconnect_required=False,
            message=None,
            sync_status="completed",
            sync_error=None,
        )

        mock_linkedin_provider = MagicMock(platform="linkedin")
        mock_linkedin_provider.get_status.return_value = linkedin_status

        mock_twitter_provider = MagicMock(platform="twitter")
        mock_twitter_provider.get_status.return_value = twitter_status

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"linkedin": mock_linkedin_provider, "twitter": mock_twitter_provider},
        ):
            response = authed_client.get("/api/v1/social/platforms")

        assert response.status_code == 200
        data = response.json()
        assert "platforms" in data
        platforms = data["platforms"]
        assert len(platforms) == 2

        # Check LinkedIn platform
        li = next(p for p in platforms if p["platform"] == "linkedin")
        assert li["connected"] is True
        assert li["platform_username"] == "testlinkedin"
        assert li["posting_ready"] is True
        assert li["read_sync_ready"] is False
        assert li["missing_read_scopes"] == ["r_member_social"]
        assert li["sync_status"] == "completed"
        assert li["sync_in_progress"] is False
        assert li["can_sync"] is True
        assert li["can_disconnect"] is True

        # Check Twitter platform
        tw = next(p for p in platforms if p["platform"] == "twitter")
        assert tw["connected"] is True
        assert tw["platform_username"] == "testtwitter"
        assert tw["posting_ready"] is True
        assert tw["read_sync_ready"] is True
        assert tw["missing_posting_scopes"] == []
        assert tw["sync_in_progress"] is False
        assert tw["can_sync"] is True

    def test_sync_in_progress_indicator(self, authed_client, mock_db):
        """Platforms with ongoing sync show sync_in_progress=True and can_sync=False."""
        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        twitter_conn = MagicMock(spec=SocialConnection)
        twitter_conn.platform = "twitter"
        twitter_conn.is_active = True
        twitter_conn.platform_username = "busyuser"
        twitter_conn.created_at = now
        twitter_conn.last_synced_at = now

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [twitter_conn]
        mock_db.query.return_value = mock_query

        twitter_status = PlatformStatus(
            connected=True,
            platform_username="busyuser",
            last_synced_at=now,
            synced_posts=10,
            posting_ready=True,
            read_sync_ready=True,
            sync_status="in_progress",
            sync_error=None,
        )

        mock_twitter_provider = MagicMock(platform="twitter")
        mock_twitter_provider.get_status.return_value = twitter_status

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"linkedin": MagicMock(platform="linkedin"), "twitter": mock_twitter_provider},
        ):
            response = authed_client.get("/api/v1/social/platforms")

        assert response.status_code == 200
        platforms = response.json()["platforms"]
        tw = next(p for p in platforms if p["platform"] == "twitter")
        assert tw["sync_in_progress"] is True
        assert tw["sync_status"] == "in_progress"
        assert tw["can_sync"] is False  # Can't trigger new sync while one is running

    def test_sync_error_state(self, authed_client, mock_db):
        """Platforms with sync errors show error info."""
        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        linkedin_conn = MagicMock(spec=SocialConnection)
        linkedin_conn.platform = "linkedin"
        linkedin_conn.is_active = True
        linkedin_conn.platform_username = "erroruser"
        linkedin_conn.created_at = now
        linkedin_conn.last_synced_at = now

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [linkedin_conn]
        mock_db.query.return_value = mock_query

        linkedin_status = PlatformStatus(
            connected=True,
            platform_username="erroruser",
            last_synced_at=now,
            synced_posts=0,
            posting_ready=True,
            read_sync_ready=False,
            sync_status="failed",
            sync_error="Token expired",
            reconnect_required=True,
        )

        mock_linkedin_provider = MagicMock(platform="linkedin")
        mock_linkedin_provider.get_status.return_value = linkedin_status

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"linkedin": mock_linkedin_provider, "twitter": MagicMock(platform="twitter")},
        ):
            response = authed_client.get("/api/v1/social/platforms")

        assert response.status_code == 200
        platforms = response.json()["platforms"]
        li = next(p for p in platforms if p["platform"] == "linkedin")
        assert li["sync_status"] == "failed"
        assert li["sync_error"] == "Token expired"
        assert li["reconnect_required"] is True

    def test_unregistered_platforms_get_basic_info(self, authed_client, mock_db):
        """Platforms not in the provider registry (instagram, google_drive) get basic status."""
        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        instagram_conn = MagicMock(spec=SocialConnection)
        instagram_conn.platform = "instagram"
        instagram_conn.is_active = True
        instagram_conn.platform_username = "insta_user"
        instagram_conn.created_at = now
        instagram_conn.last_synced_at = None

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [instagram_conn]
        mock_db.query.return_value = mock_query

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"linkedin": MagicMock(platform="linkedin"), "twitter": MagicMock(platform="twitter")},
        ):
            response = authed_client.get("/api/v1/social/platforms")

        assert response.status_code == 200
        platforms = response.json()["platforms"]
        # Should include linkedin/twitter (not connected) + instagram (connected)
        ig = next(p for p in platforms if p["platform"] == "instagram")
        assert ig["connected"] is True
        assert ig["platform_username"] == "insta_user"
        assert ig["posting_ready"] is False  # No provider = no posting
        assert ig["can_sync"] is False  # No sync provider

    def test_disconnected_provider_platform(self, authed_client, mock_db):
        """Provider platform with no active connection shows connected=False."""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"linkedin": MagicMock(platform="linkedin"), "twitter": MagicMock(platform="twitter")},
        ):
            response = authed_client.get("/api/v1/social/platforms")

        assert response.status_code == 200
        platforms = response.json()["platforms"]
        # Both providers should appear as not connected
        assert len(platforms) == 2
        for p in platforms:
            assert p["connected"] is False
            assert p["can_disconnect"] is False
            assert p["can_reconnect"] is True
            assert p["can_sync"] is False

    def test_requires_auth(self):
        """Endpoint returns 401/403 without authentication."""
        app.dependency_overrides.pop(get_current_user, None)
        with TestClient(app) as c:
            response = c.get("/api/v1/social/platforms")
        assert response.status_code in (401, 403)


class TestDisconnectPlatform:
    """Tests for POST /api/v1/social/platforms/{platform}/disconnect."""

    def test_disconnect_active_platform(self, authed_client, mock_db):
        """Disconnecting an active platform sets is_active=False."""
        conn = MagicMock(spec=SocialConnection)
        conn.is_active = True
        conn.platform = "twitter"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.post("/api/v1/social/platforms/twitter/disconnect")

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "twitter"
        assert data["disconnected"] is True
        assert conn.is_active is False
        mock_db.commit.assert_called_once()

    def test_disconnect_nonexistent_platform_returns_404(self, authed_client, mock_db):
        """Disconnecting a platform with no connection returns 404."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        response = authed_client.post("/api/v1/social/platforms/youtube/disconnect")

        assert response.status_code == 404


class TestReconnectPlatform:
    """Tests for POST /api/v1/social/platforms/{platform}/reconnect."""

    def test_reconnect_returns_oauth_url(self, authed_client):
        """Reconnect returns the OAuth start path for supported platforms."""
        response = authed_client.post("/api/v1/social/platforms/twitter/reconnect")

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "twitter"
        assert "reconnect_url" in data
        assert "twitter" in data["reconnect_url"]

    def test_reconnect_linkedin(self, authed_client):
        """Reconnect works for LinkedIn."""
        response = authed_client.post("/api/v1/social/platforms/linkedin/reconnect")

        assert response.status_code == 200
        data = response.json()
        assert "linkedin" in data["reconnect_url"]

    def test_reconnect_unsupported_platform_returns_404(self, authed_client):
        """Reconnect for unsupported platform returns 404."""
        response = authed_client.post("/api/v1/social/platforms/youtube/reconnect")

        assert response.status_code == 404
