"""
Tests for auto-post toggle and preferred posting times per platform (task 9.3).

Validates:
  - PUT /{platform}/auto-post toggles auto_post_enabled in connection_metadata
  - GET /{platform}/auto-post reads current auto-post preference
  - PUT /{platform}/posting-times stores validated HH:MM times in connection_metadata
  - GET /{platform}/posting-times reads current posting times
  - GET /{platform}/preferences returns combined auto-post + posting times
  - Endpoints return 404 for missing/inactive connections
  - PostingTimesUpdateRequest validates HH:MM format

Requirements: 5.6, 5.7
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.social_connection import SocialConnection
from app.models.user import User
from main import app


# Patch flag_modified globally for this module since we use MagicMock connections
# (flag_modified requires real SQLAlchemy instances with _sa_instance_state)
@pytest.fixture(autouse=True)
def _patch_flag_modified():
    with patch("app.routers.social.flag_modified"):
        yield


@pytest.fixture()
def mock_user():
    """Create a mock user without DB dependency."""
    return User(
        id="test-user-prefs",
        email="prefs@example.com",
        name="Prefs Tester",
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


def _make_connection(platform: str = "twitter", metadata: dict | None = None) -> MagicMock:
    """Create a mock SocialConnection with optional metadata."""
    conn = MagicMock(spec=SocialConnection)
    conn.platform = platform
    conn.is_active = True
    conn.user_id = "test-user-prefs"
    conn.connection_metadata = metadata or {}
    return conn


class TestAutoPostToggle:
    """Tests for PUT/GET /{platform}/auto-post."""

    def test_enable_auto_post(self, authed_client, mock_db):
        """PUT auto-post with enabled=True stores it in connection_metadata."""
        conn = _make_connection("twitter", metadata={})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.put(
            "/api/v1/social/twitter/auto-post",
            json={"enabled": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "twitter"
        assert data["auto_post_enabled"] is True
        # Verify metadata was updated
        assert conn.connection_metadata["auto_post_enabled"] is True
        mock_db.commit.assert_called_once()

    def test_disable_auto_post(self, authed_client, mock_db):
        """PUT auto-post with enabled=False disables it."""
        conn = _make_connection("linkedin", metadata={"auto_post_enabled": True})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.put(
            "/api/v1/social/linkedin/auto-post",
            json={"enabled": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "linkedin"
        assert data["auto_post_enabled"] is False
        assert conn.connection_metadata["auto_post_enabled"] is False

    def test_get_auto_post_enabled(self, authed_client, mock_db):
        """GET auto-post returns current enabled state."""
        conn = _make_connection("twitter", metadata={"auto_post_enabled": True})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.get("/api/v1/social/twitter/auto-post")

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "twitter"
        assert data["auto_post_enabled"] is True

    def test_get_auto_post_defaults_to_false(self, authed_client, mock_db):
        """GET auto-post returns False when not set in metadata."""
        conn = _make_connection("twitter", metadata={})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.get("/api/v1/social/twitter/auto-post")

        assert response.status_code == 200
        data = response.json()
        assert data["auto_post_enabled"] is False

    def test_auto_post_no_connection_returns_404(self, authed_client, mock_db):
        """PUT auto-post for unconnected platform returns 404."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        response = authed_client.put(
            "/api/v1/social/youtube/auto-post",
            json={"enabled": True},
        )

        assert response.status_code == 404


class TestPostingTimes:
    """Tests for PUT/GET /{platform}/posting-times."""

    def test_set_posting_times(self, authed_client, mock_db):
        """PUT posting-times stores valid HH:MM times in metadata."""
        conn = _make_connection("twitter", metadata={})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.put(
            "/api/v1/social/twitter/posting-times",
            json={"times": ["09:00", "14:00", "18:30"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "twitter"
        assert data["preferred_posting_times"] == ["09:00", "14:00", "18:30"]
        assert conn.connection_metadata["preferred_posting_times"] == ["09:00", "14:00", "18:30"]
        mock_db.commit.assert_called_once()

    def test_set_empty_posting_times(self, authed_client, mock_db):
        """PUT posting-times with empty list clears the preference."""
        conn = _make_connection("linkedin", metadata={"preferred_posting_times": ["09:00"]})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.put(
            "/api/v1/social/linkedin/posting-times",
            json={"times": []},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["preferred_posting_times"] == []

    def test_get_posting_times(self, authed_client, mock_db):
        """GET posting-times returns stored times."""
        conn = _make_connection("twitter", metadata={"preferred_posting_times": ["08:00", "12:00"]})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.get("/api/v1/social/twitter/posting-times")

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "twitter"
        assert data["preferred_posting_times"] == ["08:00", "12:00"]

    def test_get_posting_times_defaults_to_empty(self, authed_client, mock_db):
        """GET posting-times returns empty list when not set."""
        conn = _make_connection("twitter", metadata={})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.get("/api/v1/social/twitter/posting-times")

        assert response.status_code == 200
        data = response.json()
        assert data["preferred_posting_times"] == []

    def test_invalid_time_format_rejected(self, authed_client, mock_db):
        """PUT posting-times rejects invalid time formats."""
        conn = _make_connection("twitter", metadata={})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.put(
            "/api/v1/social/twitter/posting-times",
            json={"times": ["9:00"]},  # Missing leading zero
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_invalid_time_24h_rejected(self, authed_client, mock_db):
        """PUT posting-times rejects hours >23 or minutes >59."""
        conn = _make_connection("twitter", metadata={})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.put(
            "/api/v1/social/twitter/posting-times",
            json={"times": ["25:00"]},
        )

        assert response.status_code == 422

    def test_posting_times_no_connection_returns_404(self, authed_client, mock_db):
        """PUT posting-times for unconnected platform returns 404."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        response = authed_client.put(
            "/api/v1/social/youtube/posting-times",
            json={"times": ["09:00"]},
        )

        assert response.status_code == 404


class TestPlatformPreferences:
    """Tests for GET /{platform}/preferences (combined endpoint)."""

    def test_get_combined_preferences(self, authed_client, mock_db):
        """GET preferences returns both auto-post and posting times."""
        conn = _make_connection(
            "twitter",
            metadata={
                "auto_post_enabled": True,
                "preferred_posting_times": ["09:00", "14:00"],
            },
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.get("/api/v1/social/twitter/preferences")

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "twitter"
        assert data["auto_post_enabled"] is True
        assert data["preferred_posting_times"] == ["09:00", "14:00"]

    def test_get_preferences_defaults(self, authed_client, mock_db):
        """GET preferences returns defaults when nothing is set."""
        conn = _make_connection("linkedin", metadata={})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = conn
        mock_db.query.return_value = mock_query

        response = authed_client.get("/api/v1/social/linkedin/preferences")

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "linkedin"
        assert data["auto_post_enabled"] is False
        assert data["preferred_posting_times"] == []

    def test_preferences_no_connection_returns_404(self, authed_client, mock_db):
        """GET preferences for unconnected platform returns 404."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        response = authed_client.get("/api/v1/social/youtube/preferences")

        assert response.status_code == 404
