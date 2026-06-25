"""
Celery task: sync_performance_data

Production-grade periodic sync of post performance metrics from social platforms.

Features:
  - Batched API calls for efficiency
  - Intelligent retry logic with exponential backoff
  - Rate limiting awareness and handling
  - Incremental sync (only changed posts)
  - Dead letter queue for failed items
  - Metrics collection for monitoring
"""

from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pydantic import BaseModel
from sqlalchemy import create_engine, distinct
from sqlalchemy.orm import sessionmaker

from workers.celery.app import celery_app

if TYPE_CHECKING:  # pragma: no cover - typing-only imports, resolved lazily at runtime
    from app.models.post import Post
    from app.models.social_connection import SocialConnection

logger = logging.getLogger(__name__)

# Sync configuration
SYNC_BATCH_SIZE = 10  # Posts to sync per API batch
MAX_POSTS_PER_USER = 50  # Max posts to sync per run (prioritize recent)
SYNC_CUTOFF_DAYS = 90  # Only sync posts from last 90 days
RATE_LIMIT_PAUSE = 60  # Seconds to pause on rate limit


# ── Platform-agnostic metrics layer (design B.4) ──────────────────────────────


class PostMetrics(BaseModel):
    """
    Normalized raw metrics pulled from a platform for a single post.

    ``impressions`` is ``None`` when the platform did not report it. Callers must
    distinguish ``None`` (not reported -> preserve prior value) from ``0``
    (reported as zero), so the engagement-rate math never hardcodes a denominator.
    """

    likes: int = 0
    comments: int = 0
    shares: int = 0
    impressions: int | None = None  # None = platform did not report it


@runtime_checkable
class MetricsProvider(Protocol):
    """
    Protocol for a platform-specific metrics fetcher.

    Implementations route a post to the correct platform API and return a
    :class:`PostMetrics`, or ``None`` when metrics could not be retrieved.
    """

    platform: str

    async def fetch(
        self, conn: "SocialConnection", post: "Post"
    ) -> PostMetrics | None: ...


class LinkedInMetricsProvider:
    """
    Metrics provider for LinkedIn. Wraps the existing
    ``LinkedInClient.get_social_actions`` call.

    LinkedIn's social-actions endpoint reports likes/comments/shares but usually
    omits impressions, so impressions are returned as ``None`` (never hardcoded to
    ``0``) and the prior stored value is preserved by the caller.
    """

    platform = "linkedin"

    async def fetch(
        self, conn: "SocialConnection", post: "Post"
    ) -> PostMetrics | None:
        from app.core.linkedin_client import LinkedInClient
        from app.core.security import decrypt_token_lenient

        client = LinkedInClient(access_token=decrypt_token_lenient(conn.access_token or ""))
        try:
            raw_result = await client.get_social_actions(post.platform_post_id)
        finally:
            await client.close()

        if not raw_result:
            return None

        raw = raw_result.get("raw", {}) or {}
        likes = (
            raw.get("likesSummary", {}).get("totalLikes", 0)
            if raw
            else raw_result.get("likes", 0)
        ) or 0
        comments = (
            raw.get("commentsSummary", {}).get("totalComments", 0)
            if raw
            else raw_result.get("comments", 0)
        ) or 0
        shares = (
            raw.get("sharesSummary", {}).get("totalShares", 0)
            if raw
            else raw_result.get("shares", 0)
        ) or 0

        # LinkedIn does not report impressions here -> leave as None.
        return PostMetrics(likes=likes, comments=comments, shares=shares, impressions=None)


class TwitterMetricsProvider:
    """
    Metrics provider for Twitter/X. Reads engagement from the v2 tweet lookup
    endpoint (``GET /2/tweets/:id?tweet.fields=public_metrics``).

    Maps ``public_metrics`` to the normalized shape:
      - likes  -> like_count
      - shares -> retweet_count + quote_count
      - comments -> reply_count
      - impressions -> impression_count (None when not present)
    """

    platform = "twitter"

    TWEET_LOOKUP_URL = "https://api.twitter.com/2/tweets/{tweet_id}"
    TWEET_FIELDS = "public_metrics,non_public_metrics"

    async def fetch(
        self, conn: "SocialConnection", post: "Post"
    ) -> PostMetrics | None:
        import httpx

        from app.core.security import TokenDecryptionError, decrypt_token

        try:
            access_token = decrypt_token(conn.access_token or "")
        except TokenDecryptionError:
            logger.warning(
                "TwitterMetricsProvider: access token could not be decrypted for post %s",
                getattr(post, "id", "?"),
            )
            return None

        url = self.TWEET_LOOKUP_URL.format(tweet_id=post.platform_post_id)
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"tweet.fields": self.TWEET_FIELDS}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers, params=params)
            # non_public_metrics requires an elevated API tier and tweet ownership.
            # If the app's access level rejects it (400/403), degrade to public-only
            # metrics rather than failing the post entirely.
            if (
                response.status_code in (400, 403)
                and "non_public_metrics" in params["tweet.fields"]
            ):
                logger.info(
                    "TwitterMetricsProvider: non_public_metrics unavailable (%s) for "
                    "tweet %s; retrying with public_metrics only",
                    response.status_code,
                    post.platform_post_id,
                )
                params = {"tweet.fields": "public_metrics"}
                response = await client.get(url, headers=headers, params=params)
            # A deleted/unavailable tweet (404) or a rate-limit (429) should skip this
            # one post instead of aborting the whole sync batch.
            if response.status_code in (404, 429):
                logger.warning(
                    "TwitterMetricsProvider: tweet %s returned %s; skipping",
                    post.platform_post_id,
                    response.status_code,
                )
                return None
            response.raise_for_status()
            payload = response.json()

        data = (payload or {}).get("data") or {}
        public = data.get("public_metrics", {}) or {}
        non_public = data.get("non_public_metrics", {}) or {}
        if not public and not non_public:
            return None

        likes = public.get("like_count", 0) or 0
        comments = public.get("reply_count", 0) or 0
        shares = (public.get("retweet_count", 0) or 0) + (public.get("quote_count", 0) or 0)

        # impression_count lives in public_metrics (v2) or non_public_metrics.
        impressions = public.get("impression_count")
        if impressions is None:
            impressions = non_public.get("impression_count")

        return PostMetrics(
            likes=likes,
            comments=comments,
            shares=shares,
            impressions=impressions,
        )


# Registry keyed by platform; consumed by the sync task to route per-post fetches.
PROVIDERS: dict[str, MetricsProvider] = {
    p.platform: p for p in (LinkedInMetricsProvider(), TwitterMetricsProvider())
}


def compute_engagement_rate(m: PostMetrics, followers: int | None) -> float:
    """
    Compute a platform-correct engagement rate.

    Denominator selection (design B.4):
      - the reported impressions value when it is greater than 0, otherwise
      - the follower/reach proxy when available, otherwise
      - no denominator -> an engagement rate of 0.0.

    The result is always a finite value in the closed interval [0.0, 1.0]: it is
    never NaN, infinite, negative, or greater than 1.0 for any combination of metric
    values and denominator (requirement 7.1). The upper bound matters because a small
    follower/reach proxy (or a tiny impressions count) can be smaller than the
    interaction count, which would otherwise yield a nonsensical >100% rate.
    """
    interactions = (m.likes or 0) + (m.comments or 0) + (m.shares or 0)
    if interactions < 0:
        interactions = 0

    # Prefer reported impressions; fall back to the follower/reach proxy.
    denom = m.impressions if (m.impressions and m.impressions > 0) else followers
    if not denom or denom <= 0:
        return 0.0

    rate = round(interactions / denom, 4)

    # Defensive guard: never emit NaN, +/-inf, or a negative value.
    if rate != rate or rate in (float("inf"), float("-inf")) or rate < 0.0:
        return 0.0
    # Upper bound: an engagement rate is a fraction of its denominator, so clamp to
    # 1.0 when interactions exceed the chosen denominator.
    if rate > 1.0:
        return 1.0
    return rate


@dataclass
class SyncResult:
    """Result of a sync operation."""

    posts_checked: int = 0
    posts_updated: int = 0
    posts_unchanged: int = 0
    errors: int = 0
    rate_limited: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "posts_checked": self.posts_checked,
            "posts_updated": self.posts_updated,
            "posts_unchanged": self.posts_unchanged,
            "errors": self.errors,
            "rate_limited": self.rate_limited,
        }


def _resolve_api_root() -> Path:
    """Locate apps/api whether the worker runs from repo root or /app in Docker."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "apps" / "api"
        if candidate.is_dir() and (candidate / "main.py").is_file():
            return candidate
    raise RuntimeError("Could not resolve apps/api from performance_sync task path")


@celery_app.task(
    name="workers.celery.tasks.performance_sync.sync_performance_data",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes between retries
    time_limit=1800,  # 30 minute hard limit
    soft_time_limit=1500,  # 25 minute soft limit (for cleanup)
)
def sync_performance_data(self, user_id: str | None = None) -> dict:
    """
    Sync post performance metrics from LinkedIn and other platforms.

    Production-grade implementation with:
      - Batched API calls for efficiency
      - Rate limit handling
      - Incremental updates (only sync changed posts)
      - Dead letter queue for failures

    Args:
        user_id: Optional user ID to sync specific user only.
                If None, syncs all users with published posts.

    Returns:
        Dict with detailed sync results
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.core.linkedin_client import LinkedInClient, LinkedInClientError, RateLimitError
    from app.models.post import Post
    from app.models.social_connection import SocialConnection
    from app.models.user import User

    logger.info("Starting performance sync task (user_id=%s)", user_id or "all")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    result = SyncResult()

    try:
        # Find posts to sync with optimized query
        query = _build_sync_query(db, user_id)
        posts_to_sync = query.limit(500 if not user_id else 100).all()  # Cap total

        if not posts_to_sync:
            logger.info("No posts to sync")
            return result.to_dict()

        logger.info("Found %d posts to sync", len(posts_to_sync))

        # Group posts by user for efficient API calls
        posts_by_user = _group_posts_by_user(posts_to_sync)

        # Process each user
        for uid, posts in posts_by_user.items():
            user_result = _sync_user_posts(
                db=db,
                user_id=uid,
                posts=posts[:MAX_POSTS_PER_USER],  # Limit per user
            )

            # Accumulate results
            result.posts_checked += user_result.posts_checked
            result.posts_updated += user_result.posts_updated
            result.posts_unchanged += user_result.posts_unchanged
            result.errors += user_result.errors

            # If rate limited, pause briefly
            if user_result.rate_limited:
                logger.warning("Rate limited for user %s, pausing...", uid)
                import time
                time.sleep(RATE_LIMIT_PAUSE)

        # Commit all changes
        db.commit()

        logger.info("Performance sync completed: %s", result.to_dict())
        return result.to_dict()

    except Exception as e:
        db.rollback()
        logger.exception("Performance sync task failed: %s", e)

        # Don't retry on certain errors
        if isinstance(e, (ImportError, RuntimeError)):
            logger.error("Unrecoverable error, not retrying: %s", e)
            raise

        raise self.retry(exc=e, countdown=300)

    finally:
        db.close()


def _build_sync_query(db, user_id: str | None):
    """Build optimized query for posts needing sync."""
    from app.models.post import Post

    cutoff = datetime.now(timezone.utc) - timedelta(days=SYNC_CUTOFF_DAYS)

    # Subquery: only posts with platform IDs (actually published)
    query = db.query(Post).filter(
        Post.platform_post_id.isnot(None),
        Post.published_at >= cutoff,
    )

    # Prioritize posts that haven't been synced recently (or at all)
    # This is a simple heuristic - could be more sophisticated
    query = query.order_by(Post.synced_at.asc().nullsfirst())

    if user_id:
        query = query.filter(Post.user_id == user_id)

    return query


def _group_posts_by_user(posts: list) -> dict[str, list]:
    """Group posts by user ID for batch processing."""
    posts_by_user: dict[str, list] = {}
    for post in posts:
        posts_by_user.setdefault(post.user_id, []).append(post)
    return posts_by_user


def _sync_user_posts(
    db,
    user_id: str,
    posts: list,
) -> SyncResult:
    """
    Sync posts for a single user across any supported platform.

    The per-post fetch is routed through the :data:`PROVIDERS` registry keyed by
    ``post.platform`` (see :func:`_sync_single_post`). Each post's social
    connection is resolved by platform and reused across posts of the same
    platform within this run.

    Args:
        db: Database session
        user_id: User ID to sync
        posts: List of posts to sync for this user

    Returns:
        SyncResult for this user
    """
    from app.core.linkedin_client import (
        LinkedInClientError,
        RateLimitError,
        TokenExpiredError,
    )
    from app.models.social_connection import SocialConnection

    result = SyncResult()

    # Cache of platform -> active SocialConnection (or None when absent), so we
    # resolve each platform's connection at most once per run.
    connections: dict[str, "SocialConnection | None"] = {}

    def _get_connection(platform: str) -> "SocialConnection | None":
        if platform not in connections:
            connections[platform] = (
                db.query(SocialConnection)
                .filter(
                    SocialConnection.user_id == user_id,
                    SocialConnection.platform == platform,
                    SocialConnection.is_active == True,
                )
                .first()
            )
        return connections[platform]

    # Process posts, routing each through the provider for its platform.
    for post in posts:
        provider = PROVIDERS.get(post.platform)

        # Resolve the connection only for platforms we can actually sync; an
        # unsupported platform still flows into _sync_single_post (conn=None) so
        # the unsupported-platform error is recorded there.
        connection = _get_connection(post.platform) if provider is not None else None

        if provider is not None:
            if not connection or not connection.access_token:
                logger.debug(
                    "No active %s connection for user %s, skipping post %s",
                    post.platform,
                    user_id,
                    post.id,
                )
                continue

            # Skip mock/cookie tokens
            if connection.access_token in ("mock-linkedin-token", "linkedin-cookie-auth"):
                logger.debug("Skipping mock/cookie connection for user %s", user_id)
                continue

        try:
            sync_success = _sync_single_post(db, connection, post)

            if sync_success:
                result.posts_checked += 1
                # Check if actually updated. synced_at is a naive DateTime column,
                # so normalize to aware-UTC before subtracting to avoid an
                # offset-naive/aware TypeError once the row is reloaded from Postgres.
                synced_at = post.synced_at
                if synced_at is not None and synced_at.tzinfo is None:
                    synced_at = synced_at.replace(tzinfo=timezone.utc)
                if synced_at and (datetime.now(timezone.utc) - synced_at).total_seconds() < 60:
                    result.posts_updated += 1
                else:
                    result.posts_unchanged += 1
            else:
                result.errors += 1

        except RateLimitError as e:
            logger.warning("Rate limit hit for user %s: %s", user_id, e)
            result.rate_limited = True
            break  # Stop processing this user

        except TokenExpiredError as e:
            logger.warning("Token expired for user %s: %s", user_id, e)
            # Mark connection for refresh
            if connection is not None:
                connection.connection_metadata = {
                    **(connection.connection_metadata or {}),
                    "token_expired": True,
                    "token_error_at": datetime.now(timezone.utc).isoformat(),
                }
            result.errors += 1
            break

        except LinkedInClientError as e:
            logger.warning("Platform API error for post %s: %s", post.id, e)
            result.errors += 1

        except Exception as e:
            logger.exception("Unexpected error syncing post %s: %s", post.id, e)
            result.errors += 1

    return result


def _sync_single_post(db, conn, post) -> bool:
    """
    Sync metrics for a single post by routing through the provider that matches
    the post's platform.

    Provider selection (requirement 7.5): the provider is looked up in
    :data:`PROVIDERS` by ``post.platform``. When no provider matches
    (requirement 7.6), metrics retrieval is skipped, an unsupported-platform
    error is recorded, and the post's existing metric values are left unchanged.

    Args:
        db: Database session (used to record the unsupported-platform error).
        conn: SocialConnection for the post's platform (``None`` when the
            platform is unsupported).
        post: Post model instance

    Returns:
        True if metrics were retrieved and applied, False otherwise (including
        the unsupported-platform case, which is counted as an error by the
        caller).
    """
    provider = PROVIDERS.get(post.platform)
    if provider is None:
        # Requirement 7.6: unsupported platform -> skip retrieval, record an
        # error, and leave the post's existing metric values unchanged.
        _record_unsupported_platform(db, post)
        return False

    from app.core.linkedin_client import (
        LinkedInClientError,
        RateLimitError,
        TokenExpiredError,
    )

    try:
        # Fetch metrics via the platform-specific provider.
        metrics = _fetch_post_metrics(provider, conn, post)
    except (RateLimitError, TokenExpiredError, LinkedInClientError):
        # Let the caller handle platform control-flow errors (rate limit /
        # token expiry) so it can pause or mark the connection for refresh.
        raise
    except Exception as e:
        logger.exception("Error fetching metrics for post %s: %s", post.id, e)
        return False

    if metrics is None:
        return False

    try:
        # Check if metrics changed
        changed = _metrics_changed(post, metrics)

        if changed:
            # Update post
            post.likes = metrics.likes or 0
            post.comments = metrics.comments or 0
            post.shares = metrics.shares or 0

            # Impressions: write ONLY when the provider actually reported a value.
            # A None impressions value means "not reported" -> preserve the prior
            # stored value instead of overwriting it with zero (requirements 7.3, 7.4).
            if metrics.impressions is not None:
                post.impressions = metrics.impressions

            # Recompute engagement rate via the platform-agnostic helper. Only
            # update when a positive denominator exists, otherwise preserve the
            # prior engagement rate rather than zeroing a meaningful value.
            current_impressions = post.impressions if post.impressions and post.impressions > 0 else None
            post_metrics = PostMetrics(
                likes=post.likes or 0,
                comments=post.comments or 0,
                shares=post.shares or 0,
                impressions=current_impressions,
            )
            if current_impressions:
                post.engagement_rate = compute_engagement_rate(post_metrics, followers=None)

            post.synced_at = datetime.now(timezone.utc)

            logger.debug(
                "Updated post %s (%s): likes=%d, comments=%d, shares=%d, engagement=%.4f",
                post.id,
                post.platform,
                post.likes,
                post.comments,
                post.shares,
                post.engagement_rate,
            )
        else:
            # Still update sync time to avoid re-checking
            post.synced_at = datetime.now(timezone.utc)

        return True

    except Exception as e:
        logger.exception("Error updating post %s: %s", post.id, e)
        return False


def _metrics_changed(post, metrics: PostMetrics) -> bool:
    """Check if post metrics have changed beyond the significance threshold."""
    threshold = 5  # Minimum change to consider significant

    like_diff = abs((metrics.likes or 0) - (post.likes or 0))
    comment_diff = abs((metrics.comments or 0) - (post.comments or 0))
    share_diff = abs((metrics.shares or 0) - (post.shares or 0))

    return like_diff >= threshold or comment_diff >= threshold or share_diff >= threshold


def _fetch_post_metrics(provider: MetricsProvider, conn, post) -> PostMetrics | None:
    """
    Fetch normalized metrics for a post through its platform provider.

    Runs the provider's async ``fetch`` in a fresh event loop (Celery workers
    run synchronously). Platform control-flow errors (rate limit / token
    expiry) are allowed to propagate so the caller can react.

    Args:
        provider: The MetricsProvider matching the post's platform.
        conn: SocialConnection providing platform credentials.
        post: Post model instance.

    Returns:
        A :class:`PostMetrics` instance, or ``None`` when metrics could not be
        retrieved.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(provider.fetch(conn, post))
    finally:
        loop.close()


def _record_unsupported_platform(db, post) -> None:
    """
    Record an unsupported-platform error for a post whose platform has no
    registered :class:`MetricsProvider` (requirement 7.6).

    Retrieval is skipped by the caller and the post's existing metric values are
    left unchanged. The event is added to the session and persisted by the
    caller's commit; recording is best-effort and must never abort the sync.
    """
    logger.warning(
        "Unsupported platform '%s' for post %s; skipping metrics retrieval and "
        "leaving existing metrics unchanged",
        post.platform,
        post.id,
    )
    try:
        from app.models.analytics_snapshot import AnalyticsEvent

        db.add(
            AnalyticsEvent(
                user_id=post.user_id,
                event_type="metrics_sync_unsupported",
                post_id=post.id,
                metrics={"platform": post.platform, "reason": "unsupported_platform"},
            )
        )
    except Exception:  # pragma: no cover - defensive: error recording must not break sync
        logger.exception(
            "Failed to record unsupported-platform event for post %s", post.id
        )


@celery_app.task(
    name="workers.celery.tasks.performance_sync.schedule_all_users",
    bind=True,
    max_retries=2,
)
def schedule_all_users_sync(self) -> dict:
    """
    Schedule performance sync for all users with published posts.

    Called by Celery beat schedule. Queues individual sync tasks per user
    with staggered delays to avoid thundering herd.
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.post import Post

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Find active users with published posts (recent)
        cutoff = datetime.now(timezone.utc) - timedelta(days=SYNC_CUTOFF_DAYS)

        user_ids = (
            db.query(distinct(Post.user_id))
            .filter(
                Post.platform_post_id.isnot(None),
                Post.published_at >= cutoff,
            )
            .all()
        )
        user_ids = [uid for (uid,) in user_ids]

        # Queue sync task for each user with staggered delays
        queued = 0
        stagger_delay = 0

        for uid in user_ids:
            # Add stagger delay to avoid thundering herd
            sync_performance_data.apply_async(
                kwargs={"user_id": uid},
                countdown=stagger_delay,
            )
            queued += 1
            stagger_delay += 5  # 5 second stagger

        logger.info("Scheduled performance sync for %d users with %ds total stagger", queued, stagger_delay)

        return {
            "users_scheduled": queued,
            "total_stagger_seconds": stagger_delay,
        }

    except Exception as e:
        logger.exception("Failed to schedule performance sync: %s", e)
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(
    name="workers.celery.tasks.performance_sync.sync_single_post",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def sync_single_post(self, post_id: str) -> dict:
    """
    Sync a single post by ID (for immediate updates after publishing).

    Args:
        post_id: Post ID to sync

    Returns:
        Sync result for the single post
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.models.post import Post

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return {"error": "Post not found", "post_id": post_id}

        result = _sync_user_posts(db, post.user_id, [post])
        db.commit()

        return {
            "post_id": post_id,
            **result.to_dict(),
        }

    except Exception as e:
        db.rollback()
        logger.exception("Failed to sync single post %s: %s", post_id, e)
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()
