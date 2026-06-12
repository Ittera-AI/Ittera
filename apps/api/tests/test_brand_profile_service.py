"""Unit tests for BrandProfileService multi-platform updates (Task 5.1)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.services.brand_profile_service import (
    MIN_POSTS_FOR_ANALYSIS,
    _build_platform_style_notes,
    _format_posts_for_engine,
    ready_for_analysis,
)


def _make_post(platform: str, content: str, engagement_rate: float = 0.05, published_at=None):
    """Create a mock Post object."""
    post = MagicMock()
    post.platform = platform
    post.content = content
    post.engagement_rate = engagement_rate
    post.published_at = published_at or datetime(2024, 6, 15, tzinfo=timezone.utc)
    return post


class TestMinPostsThreshold:
    """Requirement 3.5: Minimum 5 posts threshold across all platforms."""

    def test_min_posts_constant_is_five(self):
        assert MIN_POSTS_FOR_ANALYSIS == 5

    def test_ready_for_analysis_below_threshold(self, db):
        """Below 5 posts should not be ready for analysis."""
        user = MagicMock()
        user.id = "test-user-below-threshold"

        # Mock the query to return fewer than 5
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 3
        db.query = MagicMock(return_value=mock_query)

        assert ready_for_analysis(db, user) is False

    def test_ready_for_analysis_at_threshold(self, db):
        """Exactly 5 posts should be ready for analysis."""
        user = MagicMock()
        user.id = "test-user-at-threshold"

        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 5
        db.query = MagicMock(return_value=mock_query)

        assert ready_for_analysis(db, user) is True

    def test_ready_for_analysis_above_threshold(self, db):
        """More than 5 posts should be ready for analysis."""
        user = MagicMock()
        user.id = "test-user-above-threshold"

        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 12
        db.query = MagicMock(return_value=mock_query)

        assert ready_for_analysis(db, user) is True


class TestFormatPostsForEngine:
    """Requirement 3.1, 3.2: Posts annotated with platform label."""

    def test_single_platform_post_has_label(self):
        posts = [_make_post("linkedin", "Test post content")]
        result = _format_posts_for_engine(posts)

        assert len(result) == 1
        assert "LINKEDIN" in result[0]
        assert "Test post content" in result[0]

    def test_multi_platform_posts_labeled_correctly(self):
        posts = [
            _make_post("linkedin", "LinkedIn post", published_at=datetime(2024, 6, 15, tzinfo=timezone.utc)),
            _make_post("twitter", "Tweet content", published_at=datetime(2024, 6, 14, tzinfo=timezone.utc)),
        ]
        result = _format_posts_for_engine(posts)

        assert len(result) == 2
        # First post should be the more recent one (LinkedIn, June 15)
        assert "LINKEDIN" in result[0]
        assert "TWITTER" in result[1]

    def test_format_includes_engagement_rate(self):
        posts = [_make_post("twitter", "Engaging tweet", engagement_rate=0.123)]
        result = _format_posts_for_engine(posts)

        assert "12.3%" in result[0]

    def test_format_includes_date(self):
        posts = [_make_post("linkedin", "Post", published_at=datetime(2024, 3, 20, tzinfo=timezone.utc))]
        result = _format_posts_for_engine(posts)

        assert "2024-03-20" in result[0]

    def test_format_handles_none_platform(self):
        post = _make_post("linkedin", "Content")
        post.platform = None
        result = _format_posts_for_engine([post])

        assert "UNKNOWN" in result[0]

    def test_post_header_format(self):
        posts = [_make_post("twitter", "Hello", engagement_rate=0.05,
                           published_at=datetime(2024, 1, 10, tzinfo=timezone.utc))]
        result = _format_posts_for_engine(posts)

        assert result[0].startswith("Post #1 | TWITTER | 2024-01-10 | Engagement: 5.0%")


class TestBuildPlatformStyleNotes:
    """Requirement 3.3: Platform-specific style variation notes."""

    def test_single_platform_returns_empty(self):
        posts = [
            _make_post("linkedin", "Post 1"),
            _make_post("linkedin", "Post 2"),
        ]
        result = _build_platform_style_notes(posts)
        assert result == ""

    def test_multi_platform_returns_notes(self):
        posts = [
            _make_post("linkedin", "Post 1"),
            _make_post("twitter", "Tweet 1"),
        ]
        result = _build_platform_style_notes(posts)

        assert "Platform-specific style notes" in result
        assert "LINKEDIN" in result
        assert "TWITTER" in result

    def test_includes_platform_counts(self):
        posts = [
            _make_post("linkedin", "Post 1"),
            _make_post("linkedin", "Post 2"),
            _make_post("linkedin", "Post 3"),
            _make_post("twitter", "Tweet 1"),
        ]
        result = _build_platform_style_notes(posts)

        assert "3 posts" in result
        assert "1 posts" in result

    def test_includes_cross_platform_instruction(self):
        posts = [
            _make_post("linkedin", "Post"),
            _make_post("twitter", "Tweet"),
        ]
        result = _build_platform_style_notes(posts)

        assert "cross-platform patterns" in result

    def test_twitter_guidance(self):
        posts = [
            _make_post("linkedin", "Post"),
            _make_post("twitter", "Tweet"),
        ]
        result = _build_platform_style_notes(posts)

        assert "shorter, punchier" in result

    def test_linkedin_guidance(self):
        posts = [
            _make_post("linkedin", "Post"),
            _make_post("twitter", "Tweet"),
        ]
        result = _build_platform_style_notes(posts)

        assert "longer-form" in result

    def test_unknown_platform_has_fallback_guidance(self):
        posts = [
            _make_post("linkedin", "Post"),
            _make_post("mastodon", "Toot"),
        ]
        result = _build_platform_style_notes(posts)

        assert "MASTODON" in result
        assert "distinct style conventions" in result
