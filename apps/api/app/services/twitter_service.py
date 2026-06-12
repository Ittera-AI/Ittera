"""
TwitterSyncService — fetches and persists a user's Twitter/X posts.

Implements the ContentSyncProvider protocol for Twitter/X using API v2.
Mirrors the linkedin_service.py structure: OAuth API → unavailable fallback.

Sync path:
  OAuth API — Uses the access_token stored during Twitter OAuth 2.0 + PKCE flow.
              Fetches tweets via GET /2/users/:id/tweets with public_metrics.
              Handles pagination via next_token for up to MAX_RESULTS tweets.

Token refresh is handled by reusing _refresh_x_token_if_needed from publisher_service.py.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx
from celery import Celery
from sqlalchemy.orm import Session

from app.db.datetime_helpers import utc_now
from app.models.post import Post
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.services.content_sync_provider import PlatformStatus, SyncResult
from app.services.publishing_state import X_POSTING_SCOPES, missing_scopes

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

TWEETS_URL = "https://api.twitter.com/2/users/{user_id}/tweets"
TWEET_FIELDS = "created_at,public_metrics,conversation_id,in_reply_to_user_id,referenced_tweets"
MAX_RESULTS = 100
MIN_POSTS_FOR_ANALYSIS = 5
HTTP_TIMEOUT_SECONDS = 30

# Twitter read scopes required for content sync
TWITTER_READ_SCOPES = {"tweet.read", "users.read", "offline.access"}

# ── Celery task dispatch helpers ──────────────────────────────────────────────

SYNC_TWITTER_TASK = "workers.celery.tasks.twitter_sync.sync_twitter_posts"
_celery_client: Celery | None = None


def _get_celery_client() -> Celery:
    global _celery_client
    if _celery_client is None:
        from app.config import settings

        _celery_client = Celery(
            "iterra-api",
            broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
            backend=settings.CELERY_RESULT_BACKEND,
        )
    return _celery_client


def queue_twitter_sync_task(user_id: str):
    """Queue the Twitter content sync Celery task for a user."""
    return _get_celery_client().send_task(SYNC_TWITTER_TASK, args=[str(user_id)])


def get_twitter_sync_task_result(task_id: str):
    """Retrieve the result of a queued Twitter sync task."""
    return _get_celery_client().AsyncResult(task_id)


# ── TwitterSyncService — ContentSyncProvider implementation ───────────────────


class TwitterSyncService:
    """
    Implements the ContentSyncProvider protocol for Twitter/X API v2.

    Provides:
      - sync_posts: fetch and upsert tweets via Twitter API v2
      - get_status: return PlatformStatus for Twitter connection
      - map_post: map a Twitter v2 tweet object to Post model fields
      - detect_threads: group tweets by conversation_id where author replied to self
    """

    platform: str = "twitter"

    async def sync_posts(self, db: Session, user: User) -> SyncResult:
        """
        Fetch and upsert Twitter posts. Returns SyncResult matching the protocol.

        - Refreshes token if needed (reuses _refresh_x_token_if_needed)
        - Fetches up to MAX_RESULTS tweets with pagination
        - Detects threads (conversation_id grouping)
        - Upserts into posts table with deduplication on platform_post_id
        """
        connection = _connection(db, user)
        if connection is None:
            logger.warning("sync_posts: no Twitter connection for user_id=%s", user.id)
            return self._sync_unavailable(db, user, "No Twitter/X connection configured.")

        if not connection.is_active:
            logger.warning("sync_posts: Twitter connection is disconnected user_id=%s", user.id)
            return self._sync_unavailable(db, user, "Twitter/X is disconnected. Reconnect before syncing.")

        # Update sync status to in-progress
        _update_sync_status(db, connection, "in_progress")

        # Refresh token if needed
        try:
            await _refresh_token(db, connection)
        except Exception as e:
            logger.warning("sync_posts: token refresh failed user_id=%s: %s", user.id, e)
            _update_sync_status(db, connection, "failed")
            return self._sync_unavailable(
                db, user, "Twitter session expired. Please reconnect your Twitter account."
            )

        # Fetch tweets via API v2
        twitter_user_id = connection.platform_user_id
        if not twitter_user_id:
            logger.warning("sync_posts: no platform_user_id for user_id=%s", user.id)
            _update_sync_status(db, connection, "failed")
            return self._sync_unavailable(db, user, "Twitter user ID not found. Please reconnect.")

        try:
            tweets = await self._fetch_tweets(connection.access_token, twitter_user_id)
        except Exception as e:
            logger.exception("sync_posts: failed to fetch tweets user_id=%s", user.id)
            _update_sync_status(db, connection, "failed")
            return self._sync_unavailable(db, user, f"Failed to fetch tweets: {e}")

        # Detect threads
        threads = self.detect_threads(tweets)

        # Map tweets to post dicts
        posts_data = []
        for tweet in tweets:
            mapped = self.map_post(tweet)
            if mapped is None:
                continue
            # Mark thread tweets
            conv_id = tweet.get("conversation_id")
            if conv_id and conv_id in threads and len(threads[conv_id]) > 1:
                mapped["content_type"] = "thread"
            posts_data.append(mapped)

        # Upsert posts
        synced = _upsert_posts(db, user, posts_data)

        # Update connection last_synced_at and sync status
        _update_last_synced(db, connection)
        _update_sync_status(db, connection, "completed")

        post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "twitter").count()

        logger.info(
            "sync_posts: synced %d new tweets (total %d) user_id=%s",
            synced,
            post_count,
            user.id,
        )
        return SyncResult(
            synced_posts=synced,
            total_posts=post_count,
            last_synced_at=utc_now(),
            message=f"Synced {synced} tweets via Twitter API v2.",
            ready_for_analysis=post_count >= MIN_POSTS_FOR_ANALYSIS,
            sync_path="oauth_api",
        )

    def get_status(self, db: Session, user: User) -> PlatformStatus:
        """
        Return Twitter connection status with scope-awareness.

        Reports posting readiness, read sync readiness, and missing scopes.
        """
        connection = _connection(db, user)
        scopes = list(connection.scopes or []) if connection else []
        missing_posting = missing_scopes(scopes, X_POSTING_SCOPES)
        missing_read = missing_scopes(scopes, TWITTER_READ_SCOPES)
        connected = connection is not None and connection.is_active

        return PlatformStatus(
            connected=connected,
            platform_username=connection.platform_username if connection else None,
            last_synced_at=connection.last_synced_at if connection else None,
            synced_posts=db.query(Post).filter(Post.user_id == user.id, Post.platform == "twitter").count(),
            scopes=scopes,
            posting_ready=connected and not missing_posting,
            read_sync_ready=connected and not missing_read,
            missing_posting_scopes=missing_posting,
            missing_read_scopes=missing_read,
            reconnect_required=connected and bool(missing_posting),
            message=_status_message(connected, missing_posting, missing_read),
        )

    def map_post(self, raw: dict) -> dict | None:
        """
        Map a Twitter API v2 tweet object to Post model fields.

        Expected raw tweet structure (v2):
        {
            "id": "123456",
            "text": "Hello world",
            "created_at": "2024-01-01T00:00:00.000Z",
            "public_metrics": {
                "like_count": 10,
                "retweet_count": 5,
                "reply_count": 2,
                "impression_count": 1000
            },
            "conversation_id": "123456",
            "in_reply_to_user_id": null,
            "referenced_tweets": [{"type": "replied_to", "id": "123455"}]
        }
        """
        return _map_tweet(raw)

    def detect_threads(self, tweets: list[dict]) -> dict[str, list[str]]:
        """
        Group tweets by conversation_id where the author replied to their own tweets.

        A thread is identified when:
        - Multiple tweets share the same conversation_id
        - The tweets have referenced_tweets with type "replied_to"
        - The in_reply_to_user_id matches the tweet author (self-reply)

        Returns a dict mapping conversation_id → list of tweet IDs in that thread.
        """
        return _detect_threads(tweets)

    # ── Internal methods ──────────────────────────────────────────────────────

    async def _fetch_tweets(self, access_token: str, twitter_user_id: str) -> list[dict]:
        """
        Fetch tweets from Twitter API v2 with pagination support.

        Fetches up to MAX_RESULTS tweets per page, following pagination_token
        until all available tweets are retrieved or API limit reached.
        """
        url = TWEETS_URL.format(user_id=twitter_user_id)
        headers = {"Authorization": f"Bearer {access_token}"}
        params: dict[str, Any] = {
            "tweet.fields": TWEET_FIELDS,
            "max_results": min(MAX_RESULTS, 100),
        }

        all_tweets: list[dict] = []
        next_token: str | None = None

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            while True:
                if next_token:
                    params["pagination_token"] = next_token

                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 401:
                    raise TokenRefreshError("Twitter access token is invalid or expired.")
                if response.status_code == 429:
                    logger.warning("_fetch_tweets: rate limited (429)")
                    break
                response.raise_for_status()

                data = response.json()
                tweets = data.get("data", [])
                all_tweets.extend(tweets)

                # Check pagination
                meta = data.get("meta", {})
                next_token = meta.get("next_token")
                if not next_token or len(all_tweets) >= MAX_RESULTS:
                    break

        return all_tweets[:MAX_RESULTS]

    def _sync_unavailable(self, db: Session, user: User, message: str) -> SyncResult:
        """Helper returning a SyncResult when sync is not possible."""
        post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "twitter").count()
        return SyncResult(
            synced_posts=0,
            total_posts=post_count,
            last_synced_at=utc_now(),
            message=message,
            ready_for_analysis=post_count >= MIN_POSTS_FOR_ANALYSIS,
            sync_path="unavailable",
        )


# ── Module-level singleton for easy access ────────────────────────────────────
twitter_sync_service = TwitterSyncService()


# ── Exceptions ────────────────────────────────────────────────────────────────


class TokenRefreshError(Exception):
    """Raised when token refresh fails."""

    pass


# ── Tweet mapping function ────────────────────────────────────────────────────


def _map_tweet(tweet: dict) -> dict | None:
    """
    Maps a Twitter API v2 tweet object to Post model fields.

    Stores the raw API response for debugging.
    Maps public_metrics to:
      - likes → like_count
      - shares → retweet_count
      - comments → reply_count
      - impressions → impression_count
    """
    try:
        text = tweet.get("text", "")
        if not text:
            return None

        tweet_id = tweet.get("id", "")
        if not tweet_id:
            return None

        # Parse published_at from ISO 8601 string
        created_at_str = tweet.get("created_at")
        if created_at_str:
            published_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        else:
            published_at = utc_now()

        # Extract engagement metrics from public_metrics
        metrics = tweet.get("public_metrics", {})
        likes = metrics.get("like_count", 0) or 0
        shares = metrics.get("retweet_count", 0) or 0
        comments = metrics.get("reply_count", 0) or 0
        impressions = metrics.get("impression_count", 0) or 0

        # Calculate engagement rate
        engagement_rate = round(
            (likes + shares + comments) / impressions if impressions > 0 else 0.0, 4
        )

        # Determine content type based on referenced_tweets
        content_type = "text"
        referenced_tweets = tweet.get("referenced_tweets", [])
        if referenced_tweets:
            ref_types = [ref.get("type") for ref in referenced_tweets]
            if "replied_to" in ref_types:
                # Could be part of a thread — will be updated by detect_threads
                content_type = "text"

        return {
            "platform_post_id": tweet_id,
            "platform": "twitter",
            "content": text,
            "content_type": content_type,
            "published_at": published_at,
            "impressions": impressions,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "engagement_rate": engagement_rate,
            "topics": [],
            "tone": None,
            "raw_api_response": tweet,
            "synced_at": utc_now(),
        }
    except Exception:
        logger.exception("_map_tweet: failed to parse tweet")
        return None


# ── Thread detection ──────────────────────────────────────────────────────────


def _detect_threads(tweets: list[dict]) -> dict[str, list[str]]:
    """
    Group tweets by conversation_id where the author replied to their own tweets.

    Logic:
    1. Group all tweets by conversation_id
    2. For each group, keep only tweets where the author is replying to themselves
       (in_reply_to_user_id is absent/null or matches the conversation starter)
    3. A thread requires at least 2 tweets in the same conversation

    Returns dict mapping conversation_id → list of tweet IDs in that thread.
    """
    # Group tweets by conversation_id
    conversations: dict[str, list[dict]] = {}
    for tweet in tweets:
        conv_id = tweet.get("conversation_id")
        if conv_id:
            conversations.setdefault(conv_id, []).append(tweet)

    threads: dict[str, list[str]] = {}
    for conv_id, conv_tweets in conversations.items():
        if len(conv_tweets) < 2:
            continue

        # Find the conversation starter (tweet whose id == conversation_id)
        starter_user_id: str | None = None
        for t in conv_tweets:
            if t.get("id") == conv_id:
                # This is the root tweet — the author is the thread owner
                starter_user_id = "self"
                break

        # Filter to self-replies: tweets replying to the same conversation
        # where in_reply_to_user_id is either absent (own thread) or
        # the referenced_tweets point to another tweet in the same conversation
        thread_tweet_ids: list[str] = []
        for t in conv_tweets:
            reply_to_user = t.get("in_reply_to_user_id")
            # Include the root tweet (no in_reply_to_user_id)
            if reply_to_user is None:
                thread_tweet_ids.append(t.get("id", ""))
            elif starter_user_id == "self":
                # If we found the starter in our fetched tweets,
                # include tweets that are self-replies (reply to same user)
                # Since all tweets come from the same user's timeline,
                # a reply within the same conversation is a self-reply
                thread_tweet_ids.append(t.get("id", ""))

        if len(thread_tweet_ids) >= 2:
            threads[conv_id] = thread_tweet_ids

    return threads


# ── Shared helpers ────────────────────────────────────────────────────────────


def _upsert_posts(db: Session, user: User, posts_data: list[dict]) -> int:
    """Upsert a list of post dicts into the DB. Returns count of new posts inserted."""
    synced = 0
    for item in posts_data:
        pid = item.get("platform_post_id")
        if not pid:
            continue
        post = (
            db.query(Post)
            .filter(Post.user_id == user.id, Post.platform_post_id == pid)
            .first()
        )
        if post is None:
            post = Post(user_id=user.id, **item)
            db.add(post)
            synced += 1
        else:
            # Update engagement metrics in case they changed
            for key in ("impressions", "likes", "comments", "shares", "engagement_rate", "content_type", "synced_at"):
                if key in item:
                    setattr(post, key, item[key])
    db.commit()
    return synced


def _update_last_synced(db: Session, connection: SocialConnection) -> None:
    """Update the connection's last_synced_at timestamp."""
    connection.last_synced_at = utc_now()
    db.commit()


def _update_sync_status(db: Session, connection: SocialConnection, status: str) -> None:
    """
    Update sync status in connection_metadata for progress tracking.

    Status values: "initiated", "in_progress", "completed", "failed"
    """
    meta = dict(connection.connection_metadata or {})
    meta["sync_status"] = status
    meta["sync_status_updated_at"] = utc_now().isoformat()
    connection.connection_metadata = meta
    db.commit()


def _connection(db: Session, user: User) -> SocialConnection | None:
    """Retrieve the active Twitter connection for a user."""
    return (
        db.query(SocialConnection)
        .filter(SocialConnection.user_id == user.id, SocialConnection.platform == "twitter")
        .first()
    )


async def _refresh_token(db: Session, connection: SocialConnection) -> None:
    """
    Refresh the Twitter OAuth2 token if it's about to expire.

    Reuses the same logic as _refresh_x_token_if_needed from publisher_service.py.
    """
    from app.services.publisher_service import _refresh_x_token_if_needed

    await _refresh_x_token_if_needed(db, connection)


def _status_message(
    connected: bool, missing_posting: list[str], missing_read: list[str]
) -> str | None:
    """Generate a human-readable status message based on connection state."""
    if not connected:
        return None
    if missing_posting and missing_read:
        return "Twitter/X requires reconnection to enable posting and content sync."
    if missing_posting:
        return "Twitter/X requires reconnection to enable posting."
    if missing_read:
        return "Twitter/X read permissions are missing. Reconnect to enable content sync."
    return None
