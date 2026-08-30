"""
Tests for LinkedIn sync progress tracking (task 2.3).

Validates:
  - Sync progress states are stored in connection_metadata
  - get_status includes sync progress info
  - Token expiry preserves previously fetched data and marks reconnect_required
  - Sync state transitions: initiated → in_progress → completed/failed
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models.post import Post
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.services.linkedin_service import (
    SYNC_STATUS_COMPLETED,
    SYNC_STATUS_FAILED,
    SYNC_STATUS_IN_PROGRESS,
    SYNC_STATUS_INITIATED,
    LinkedInSyncService,
    _get_sync_progress,
    _update_sync_progress,
)


@pytest.fixture()
def user(db):
    """Create a test user."""
    u = User(
        id="test-user-sync-progress",
        email="synctest@example.com",
        name="Sync Tester",
        hashed_password="fakehash",
    )
    u = db.merge(u)
    db.commit()
    return u


@pytest.fixture()
def linkedin_connection(db, user):
    """Create a LinkedIn connection with OAuth token and r_member_social scope."""
    conn = SocialConnection(
        id="test-linkedin-conn-sync",
        user_id=user.id,
        platform="linkedin",
        platform_user_id="urn:li:person:abc123",
        platform_username="Sync Tester",
        access_token="valid-token",
        scopes=["openid", "profile", "email", "w_member_social", "r_member_social"],
        is_active=True,
        connection_metadata={},
    )
    conn = db.merge(conn)
    db.commit()
    return conn


class TestSyncProgressHelpers:
    """Tests for _update_sync_progress and _get_sync_progress helpers."""

    def test_update_sync_progress_initiated(self, db, linkedin_connection):
        _update_sync_progress(db, linkedin_connection, SYNC_STATUS_INITIATED)
        progress = _get_sync_progress(linkedin_connection)

        assert progress["sync_status"] == "initiated"
        assert progress["sync_started_at"] is not None
        assert progress["sync_completed_at"] is None
        assert progress["sync_error"] is None
        assert progress["reconnect_required"] is False

    def test_update_sync_progress_in_progress(self, db, linkedin_connection):
        _update_sync_progress(db, linkedin_connection, SYNC_STATUS_INITIATED)
        _update_sync_progress(db, linkedin_connection, SYNC_STATUS_IN_PROGRESS)
        progress = _get_sync_progress(linkedin_connection)

        assert progress["sync_status"] == "in_progress"
        assert progress["sync_started_at"] is not None
        assert progress["sync_error"] is None

    def test_update_sync_progress_completed(self, db, linkedin_connection):
        _update_sync_progress(db, linkedin_connection, SYNC_STATUS_INITIATED)
        _update_sync_progress(db, linkedin_connection, SYNC_STATUS_IN_PROGRESS)
        _update_sync_progress(
            db, linkedin_connection, SYNC_STATUS_COMPLETED, posts_fetched=7
        )
        progress = _get_sync_progress(linkedin_connection)

        assert progress["sync_status"] == "completed"
        assert progress["sync_completed_at"] is not None
        assert progress["sync_error"] is None
        assert progress["sync_posts_fetched"] == 7
        assert progress["reconnect_required"] is False

    def test_update_sync_progress_failed_with_error(self, db, linkedin_connection):
        _update_sync_progress(db, linkedin_connection, SYNC_STATUS_INITIATED)
        _update_sync_progress(
            db,
            linkedin_connection,
            SYNC_STATUS_FAILED,
            error="Token expired",
            reconnect_required=True,
        )
        progress = _get_sync_progress(linkedin_connection)

        assert progress["sync_status"] == "failed"
        assert progress["sync_error"] == "Token expired"
        assert progress["reconnect_required"] is True

    def test_get_sync_progress_none_connection(self):
        assert _get_sync_progress(None) == {}

    def test_get_sync_progress_no_metadata(self, db, linkedin_connection):
        linkedin_connection.connection_metadata = None
        db.commit()
        assert _get_sync_progress(linkedin_connection) == {}

    def test_update_preserves_existing_metadata(self, db, linkedin_connection):
        """Existing metadata keys are not overwritten."""
        linkedin_connection.connection_metadata = {"drive_posts_file_id": "abc123"}
        db.commit()

        _update_sync_progress(db, linkedin_connection, SYNC_STATUS_INITIATED)

        meta = linkedin_connection.connection_metadata
        assert meta["drive_posts_file_id"] == "abc123"
        assert "sync_progress" in meta


class TestGetStatusIncludesSyncProgress:
    """Tests that get_status returns sync progress info."""

    def test_status_includes_sync_fields_when_no_progress(self, db, user, linkedin_connection):
        service = LinkedInSyncService()
        status = service.get_status(db, user)

        # sync fields should be None when no progress recorded
        assert status.sync_status is None
        assert status.sync_error is None
        assert status.sync_started_at is None

    def test_status_includes_sync_completed(self, db, user, linkedin_connection):
        _update_sync_progress(db, linkedin_connection, SYNC_STATUS_COMPLETED, posts_fetched=10)

        # Re-query connection from db to get updated state
        from app.models.social_connection import SocialConnection
        conn = db.query(SocialConnection).filter(SocialConnection.id == linkedin_connection.id).first()
        progress = _get_sync_progress(conn)
        assert progress["sync_status"] == "completed"

        service = LinkedInSyncService()
        status = service.get_status(db, user)

        assert status.sync_status == "completed"
        assert status.sync_error is None

    def test_status_includes_sync_failed_with_reconnect(self, db, user, linkedin_connection):
        _update_sync_progress(
            db,
            linkedin_connection,
            SYNC_STATUS_FAILED,
            error="Token expired",
            reconnect_required=True,
        )

        service = LinkedInSyncService()
        status = service.get_status(db, user)

        assert status.sync_status == "failed"
        assert status.sync_error == "Token expired"
        assert status.reconnect_required is True


class TestTokenExpiryHandling:
    """Tests that token expiry during sync preserves data and marks reconnect."""

    @pytest.mark.asyncio
    async def test_token_expiry_preserves_existing_posts(self, db, user, linkedin_connection):
        """When token expires, existing posts are preserved (not deleted)."""
        # Pre-insert some posts to simulate previously fetched data
        for i in range(3):
            post = Post(
                user_id=user.id,
                platform="linkedin",
                platform_post_id=f"existing-post-{i}",
                content=f"Existing post {i}",
                content_type="text",
            )
            db.merge(post)
        db.commit()

        from app.core.linkedin_client import TokenExpiredError

        # Mock the client to raise TokenExpiredError
        with patch(
            "app.services.linkedin_service.LinkedInClient"
        ) as MockClient:
            instance = MockClient.return_value
            instance.get_posts = AsyncMock(
                side_effect=TokenExpiredError("Token expired")
            )

            service = LinkedInSyncService()
            result = await service.sync_posts(db, user)

        # Existing posts should still be there
        post_count = (
            db.query(Post)
            .filter(Post.user_id == user.id, Post.platform == "linkedin")
            .count()
        )
        assert post_count == 3  # Data preserved

        # Result should indicate token expiry
        assert "expired" in result.message.lower()
        assert result.synced_posts == 0
        assert result.total_posts == 3

        # Sync progress should show failed with reconnect_required
        conn = db.query(SocialConnection).filter(SocialConnection.id == linkedin_connection.id).first()
        progress = _get_sync_progress(conn)
        assert progress["sync_status"] == "failed"
        assert progress["reconnect_required"] is True

    @pytest.mark.asyncio
    async def test_successful_sync_marks_completed(self, db, user, linkedin_connection):
        """A successful sync marks status as completed with post count."""
        mock_posts = [
            {
                "id": f"urn:li:ugcPost:post-{i}",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": f"Test post {i}"},
                    }
                },
                "created": {"time": 1700000000000 + i * 1000},
            }
            for i in range(3)
        ]

        with patch(
            "app.services.linkedin_service.LinkedInClient"
        ) as MockClient, patch(
            "app.services.linkedin_service._save_scraped_posts_to_drive_if_connected"
        ):
            instance = MockClient.return_value
            instance.get_posts = AsyncMock(return_value=mock_posts)

            service = LinkedInSyncService()
            result = await service.sync_posts(db, user)

        assert result.synced_posts == 3
        assert result.sync_path == "oauth_api"

        # Sync progress should show completed
        conn = db.query(SocialConnection).filter(SocialConnection.id == linkedin_connection.id).first()
        progress = _get_sync_progress(conn)
        assert progress["sync_status"] == "completed"
        assert progress["sync_posts_fetched"] == 3
        assert progress["reconnect_required"] is False
