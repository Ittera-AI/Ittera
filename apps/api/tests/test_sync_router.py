"""
Tests for the generic sync router (task 9.1).

Validates:
  - POST /api/v1/sync/{platform}: triggers manual sync for a valid platform
  - GET /api/v1/sync/{platform}/status: returns PlatformStatus
  - Invalid platform returns 404 with helpful error message
  - Provider registry correctly maps platform names to services
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.routers.sync import _SYNC_PROVIDERS, _SYNC_TASK_QUEUERS
from app.services.content_sync_provider import PlatformStatus
from main import app


@pytest.fixture()
def mock_user():
    """Create a mock user without DB dependency."""
    return User(
        id="test-user-sync-router",
        email="sync-router@example.com",
        name="Sync Router Tester",
        hashed_password="fakehash",
    )


@pytest.fixture()
def authed_client(mock_user):
    """Client with auth overridden to return the mock_user (no DB needed for routing tests)."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


class TestProviderRegistry:
    """Tests that the provider registry is correctly configured."""

    def test_linkedin_provider_registered(self):
        assert "linkedin" in _SYNC_PROVIDERS
        assert _SYNC_PROVIDERS["linkedin"].platform == "linkedin"

    def test_twitter_provider_registered(self):
        assert "twitter" in _SYNC_PROVIDERS
        assert _SYNC_PROVIDERS["twitter"].platform == "twitter"

    def test_task_queuers_registered(self):
        assert "linkedin" in _SYNC_TASK_QUEUERS
        assert "twitter" in _SYNC_TASK_QUEUERS
        assert callable(_SYNC_TASK_QUEUERS["linkedin"])
        assert callable(_SYNC_TASK_QUEUERS["twitter"])


class TestTriggerSync:
    """Tests for POST /api/v1/sync/{platform}."""

    def test_trigger_linkedin_sync(self, authed_client):
        """Valid linkedin platform triggers sync and returns task_id."""
        mock_task = MagicMock()
        mock_task.id = "celery-task-123"

        mock_queuer = MagicMock(return_value=mock_task)
        with patch.dict(
            _SYNC_TASK_QUEUERS,
            {"linkedin": mock_queuer, "twitter": MagicMock()},
        ):
            response = authed_client.post("/api/v1/sync/linkedin")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "celery-task-123"
        assert data["platform"] == "linkedin"
        assert "sync enqueued" in data["message"].lower()
        mock_queuer.assert_called_once_with("test-user-sync-router")

    def test_trigger_twitter_sync(self, authed_client):
        """Valid twitter platform triggers sync and returns task_id."""
        mock_task = MagicMock()
        mock_task.id = "celery-task-456"

        mock_queuer = MagicMock(return_value=mock_task)
        with patch.dict(
            _SYNC_TASK_QUEUERS,
            {"linkedin": MagicMock(), "twitter": mock_queuer},
        ):
            response = authed_client.post("/api/v1/sync/twitter")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "celery-task-456"
        assert data["platform"] == "twitter"
        assert "sync enqueued" in data["message"].lower()
        mock_queuer.assert_called_once_with("test-user-sync-router")

    def test_trigger_invalid_platform_returns_404(self, authed_client):
        """Unsupported platform returns 404 with supported platforms listed."""
        response = authed_client.post("/api/v1/sync/instagram")

        assert response.status_code == 404
        detail = response.json()["error"]["message"]
        assert "instagram" in detail.lower()
        assert "linkedin" in detail.lower()
        assert "twitter" in detail.lower()

    def test_trigger_sync_requires_auth(self):
        """Endpoint returns 401/403 without authentication."""
        app.dependency_overrides.pop(get_current_user, None)
        with TestClient(app) as c:
            response = c.post("/api/v1/sync/linkedin")
        assert response.status_code in (401, 403)


class TestGetAllPlatformsStatus:
    """Tests for GET /api/v1/sync/all (task 9.2)."""

    def test_returns_all_platforms(self, authed_client):
        """Returns status for all registered providers."""
        mock_linkedin_status = PlatformStatus(
            connected=True,
            platform_username="testlinkedin",
            last_synced_at=None,
            synced_posts=5,
            scopes=["openid", "w_member_social"],
            posting_ready=True,
            read_sync_ready=False,
            missing_posting_scopes=[],
            missing_read_scopes=["r_member_social"],
            reconnect_required=False,
            message="LinkedIn posting is ready.",
        )
        mock_twitter_status = PlatformStatus(
            connected=True,
            platform_username="testtwitter",
            last_synced_at=None,
            synced_posts=10,
            scopes=["tweet.read", "tweet.write", "users.read", "offline.access"],
            posting_ready=True,
            read_sync_ready=True,
            missing_posting_scopes=[],
            missing_read_scopes=[],
            reconnect_required=False,
            message=None,
        )

        mock_li_provider = MagicMock(platform="linkedin", get_status=MagicMock(return_value=mock_linkedin_status))
        mock_tw_provider = MagicMock(platform="twitter", get_status=MagicMock(return_value=mock_twitter_status))

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"linkedin": mock_li_provider, "twitter": mock_tw_provider},
        ):
            response = authed_client.get("/api/v1/sync/all")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        platforms = {item["platform"] for item in data}
        assert platforms == {"linkedin", "twitter"}

        # Verify LinkedIn entry
        li = next(d for d in data if d["platform"] == "linkedin")
        assert li["connected"] is True
        assert li["platform_username"] == "testlinkedin"
        assert li["synced_posts"] == 5
        assert li["posting_ready"] is True
        assert li["read_sync_ready"] is False
        assert li["missing_read_scopes"] == ["r_member_social"]

        # Verify Twitter entry
        tw = next(d for d in data if d["platform"] == "twitter")
        assert tw["connected"] is True
        assert tw["platform_username"] == "testtwitter"
        assert tw["synced_posts"] == 10
        assert tw["posting_ready"] is True
        assert tw["read_sync_ready"] is True

    def test_includes_sync_in_progress_indicator(self, authed_client):
        """Sync status and error fields are included in the response."""
        mock_status = PlatformStatus(
            connected=True,
            platform_username="busy_user",
            last_synced_at=None,
            synced_posts=0,
            sync_status="in_progress",
            sync_error=None,
        )

        mock_provider = MagicMock(platform="linkedin", get_status=MagicMock(return_value=mock_status))

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"linkedin": mock_provider},
        ):
            response = authed_client.get("/api/v1/sync/all")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sync_status"] == "in_progress"
        assert data[0]["sync_error"] is None

    def test_includes_error_state(self, authed_client):
        """Error states are surfaced in the response."""
        mock_status = PlatformStatus(
            connected=True,
            platform_username="error_user",
            last_synced_at=None,
            synced_posts=0,
            sync_status="failed",
            sync_error="Token expired, please reconnect.",
            reconnect_required=True,
        )

        mock_provider = MagicMock(platform="twitter", get_status=MagicMock(return_value=mock_status))

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"twitter": mock_provider},
        ):
            response = authed_client.get("/api/v1/sync/all")

        assert response.status_code == 200
        data = response.json()
        assert data[0]["sync_status"] == "failed"
        assert data[0]["sync_error"] == "Token expired, please reconnect."
        assert data[0]["reconnect_required"] is True

    def test_returns_empty_list_if_no_providers(self, authed_client):
        """Returns empty list when no providers are registered (edge case)."""
        with patch("app.routers.sync._SYNC_PROVIDERS", {}):
            response = authed_client.get("/api/v1/sync/all")

        assert response.status_code == 200
        assert response.json() == []

    def test_all_endpoint_requires_auth(self):
        """Endpoint returns 401/403 without authentication."""
        app.dependency_overrides.pop(get_current_user, None)
        with TestClient(app) as c:
            response = c.get("/api/v1/sync/all")
        assert response.status_code in (401, 403)


class TestGetPlatformStatus:
    """Tests for GET /api/v1/sync/{platform}/status."""

    def test_get_linkedin_status(self, authed_client):
        """Returns PlatformStatus for linkedin."""
        mock_status = PlatformStatus(
            connected=True,
            platform_username="testlinkedin",
            last_synced_at=None,
            synced_posts=5,
            scopes=["openid", "w_member_social"],
            posting_ready=True,
            read_sync_ready=False,
            missing_posting_scopes=[],
            missing_read_scopes=["r_member_social"],
            reconnect_required=False,
            message="LinkedIn posting is ready.",
        )

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"linkedin": MagicMock(platform="linkedin", get_status=MagicMock(return_value=mock_status)),
             "twitter": MagicMock(platform="twitter")},
        ):
            response = authed_client.get("/api/v1/sync/linkedin/status")

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "linkedin"
        assert data["connected"] is True
        assert data["platform_username"] == "testlinkedin"
        assert data["synced_posts"] == 5
        assert data["posting_ready"] is True
        assert data["read_sync_ready"] is False
        assert data["missing_read_scopes"] == ["r_member_social"]

    def test_get_twitter_status(self, authed_client):
        """Returns PlatformStatus for twitter."""
        mock_status = PlatformStatus(
            connected=True,
            platform_username="testtwitter",
            last_synced_at=None,
            synced_posts=10,
            scopes=["tweet.read", "tweet.write", "users.read", "offline.access"],
            posting_ready=True,
            read_sync_ready=True,
            missing_posting_scopes=[],
            missing_read_scopes=[],
            reconnect_required=False,
            message=None,
        )

        with patch(
            "app.routers.sync._SYNC_PROVIDERS",
            {"linkedin": MagicMock(platform="linkedin"),
             "twitter": MagicMock(platform="twitter", get_status=MagicMock(return_value=mock_status))},
        ):
            response = authed_client.get("/api/v1/sync/twitter/status")

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "twitter"
        assert data["connected"] is True
        assert data["platform_username"] == "testtwitter"
        assert data["synced_posts"] == 10
        assert data["posting_ready"] is True
        assert data["read_sync_ready"] is True

    def test_get_invalid_platform_status_returns_404(self, authed_client):
        """Unsupported platform returns 404."""
        response = authed_client.get("/api/v1/sync/youtube/status")

        assert response.status_code == 404
        detail = response.json()["error"]["message"]
        assert "youtube" in detail.lower()

    def test_get_status_requires_auth(self):
        """Endpoint returns 401/403 without authentication."""
        app.dependency_overrides.pop(get_current_user, None)
        with TestClient(app) as c:
            response = c.get("/api/v1/sync/linkedin/status")
        assert response.status_code in (401, 403)
