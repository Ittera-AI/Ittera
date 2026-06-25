"""
LinkedInService — fetches and persists a user's LinkedIn posts.

Two sync paths are supported and auto-selected at runtime:

  PATH A  — LinkedIn OAuth API (preferred)
            Requires the access_token stored during OAuth (openid/w_member_social scopes)
            AND the r_member_social scope granted on your LinkedIn Developer App.
            Uses: GET https://api.linkedin.com/v2/ugcPosts

  PATH B  — Cookie-based scraper (fallback)
            Uses the linkedin-api library with credentials stored encrypted in
            SocialConnection.connection_metadata (set via store_linkedin_credentials).
            Activated when PATH A returns 403 (scope not granted) or when
            access_token == "linkedin-cookie-auth".

  MOCK    — Development stub
            Activated when access_token == "mock-linkedin-token" or no connection exists.
            Returns predictable fake data so the rest of the pipeline can be exercised.

The correct path is logged so developers can see which one fired.

This module implements the ContentSyncProvider protocol for LinkedIn,
providing a consistent interface alongside the Twitter provider.

Sync progress tracking:
  The sync status is stored in connection_metadata under the "sync_progress" key:
    {
      "sync_status": "initiated" | "in_progress" | "completed" | "failed",
      "sync_started_at": "ISO datetime",
      "sync_completed_at": "ISO datetime" | null,
      "sync_error": "error message" | null,
      "sync_posts_fetched": int,
      "reconnect_required": bool
    }
  This allows the frontend to poll for real-time progress (requirement 1.8).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from celery import Celery
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.linkedin_client import (
    LinkedInClient,
    LinkedInClientError,
    LinkedInCookieClient,
    ScopeMissingError,
    TokenExpiredError,
)
from app.core.security import decrypt_token_lenient, decrypt_value
from app.db.datetime_helpers import utc_now
from app.models.post import Post
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.services.content_sync_provider import PlatformStatus, SyncResult
from app.services.mock_data import mock_posts
from app.services.publishing_state import LINKEDIN_POSTING_SCOPES, LINKEDIN_READ_SCOPES, missing_scopes
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

# ── Minimum posts before BrandProfileEngine is triggered ─────────────────────
MIN_POSTS_FOR_ANALYSIS = 5
SCRAPE_LINKEDIN_TASK = "workers.celery.tasks.scraper.scrape_linkedin_posts"
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


def queue_scrape_task(user_id: str):
    return _get_celery_client().send_task(SCRAPE_LINKEDIN_TASK, args=[str(user_id)])


def get_scrape_task_result(task_id: str):
    return _get_celery_client().AsyncResult(task_id)


# ── LinkedInSyncService — ContentSyncProvider implementation ──────────────────


# ── Sync progress state constants ─────────────────────────────────────────────
SYNC_STATUS_INITIATED = "initiated"
SYNC_STATUS_IN_PROGRESS = "in_progress"
SYNC_STATUS_COMPLETED = "completed"
SYNC_STATUS_FAILED = "failed"


class LinkedInSyncService:
    """
    Implements the ContentSyncProvider protocol for LinkedIn.

    Provides:
      - sync_posts: fetch and upsert LinkedIn posts via OAuth API, cookie fallback, or mock
      - get_status: return PlatformStatus with scope-awareness (detect missing r_member_social)
      - map_post: map a LinkedIn UGC Post API response to Post model fields
    """

    platform: str = "linkedin"

    async def sync_posts(self, db: Session, user: User) -> SyncResult:
        """
        Fetch and upsert LinkedIn posts. Returns SyncResult matching the protocol.

        Delegates to the best available auth path (OAuth API → cookie → unavailable).
        Tracks sync progress in connection_metadata for real-time status updates.
        """
        connection = _connection(db, user)
        if connection is None:
            logger.warning("sync_posts: no LinkedIn connection for user_id=%s", user.id)
            return self._sync_unavailable(db, user, "No real LinkedIn connection is configured.")
        if not connection.is_active:
            logger.warning("sync_posts: LinkedIn connection is disconnected user_id=%s", user.id)
            return self._sync_unavailable(db, user, "LinkedIn is disconnected. Reconnect before syncing.")

        token = decrypt_token_lenient(connection.access_token or "")

        if token == "mock-linkedin-token":
            logger.warning("sync_posts: mock token cannot be used for real sync user_id=%s", user.id)
            return self._sync_unavailable(db, user, "Reconnect LinkedIn with a real account before syncing.")

        if "r_member_social" not in (connection.scopes or []):
            return self._sync_unavailable(
                db,
                user,
                "LinkedIn read permission is not active for this OAuth connection. "
                "Posting can work, but historical sync requires r_member_social approval and reconnect.",
            )

        # Mark sync as initiated
        _update_sync_progress(db, connection, SYNC_STATUS_INITIATED)

        if token == "linkedin-cookie-auth":
            logger.info("sync_posts: cookie-auth mode user_id=%s", user.id)
            return await self._sync_via_cookie(db, user, connection)

        # Attempt OAuth API first
        logger.info("sync_posts: trying OAuth API path user_id=%s", user.id)
        # Mark sync as in-progress
        _update_sync_progress(db, connection, SYNC_STATUS_IN_PROGRESS)
        try:
            result = await self._sync_via_oauth_api(db, user, connection)
            if result is not None:
                return result
        except ScopeMissingError:
            logger.warning(
                "sync_posts: r_member_social scope missing user_id=%s",
                user.id,
            )
            _update_sync_progress(
                db, connection, SYNC_STATUS_FAILED,
                error="r_member_social scope missing. Reconnect LinkedIn.",
            )

        return self._sync_unavailable(
            db,
            user,
            "LinkedIn read permission is not active for this OAuth connection. "
            "Enable r_member_social for the LinkedIn app, then disconnect and reconnect LinkedIn.",
        )

    def get_status(self, db: Session, user: User) -> PlatformStatus:
        """
        Return LinkedIn connection status with scope-awareness.

        Detects missing `r_member_social` scope and reports it clearly
        via missing_read_scopes and message fields.
        Includes sync progress info from connection_metadata (requirement 1.8).
        """
        connection = _connection(db, user)
        scopes = list(connection.scopes or []) if connection else []
        missing_posting = missing_scopes(scopes, LINKEDIN_POSTING_SCOPES)
        missing_read = missing_scopes(scopes, LINKEDIN_READ_SCOPES)
        connected = connection is not None and connection.is_active

        # Extract sync progress from connection_metadata
        sync_progress = _get_sync_progress(connection) if connection else {}
        sync_status = sync_progress.get("sync_status")
        sync_error = sync_progress.get("sync_error")
        sync_started_at_str = sync_progress.get("sync_started_at")
        sync_started_at = (
            datetime.fromisoformat(sync_started_at_str)
            if sync_started_at_str
            else None
        )
        reconnect_from_sync = sync_progress.get("reconnect_required", False)

        return PlatformStatus(
            connected=connected,
            platform_username=connection.platform_username if connection else None,
            last_synced_at=connection.last_synced_at if connection else None,
            synced_posts=db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count(),
            scopes=scopes,
            posting_ready=connected and not missing_posting,
            read_sync_ready=connected and not missing_read,
            missing_posting_scopes=missing_posting,
            missing_read_scopes=missing_read,
            reconnect_required=(connected and bool(missing_posting)) or reconnect_from_sync,
            message=(
                "LinkedIn posting is ready. Historical read sync is pending approval "
                "and separate from posting."
                if connected and not missing_posting and missing_read
                else None
            ),
            sync_status=sync_status,
            sync_error=sync_error,
            sync_started_at=sync_started_at,
        )

    def map_post(self, raw: dict) -> dict | None:
        """
        Map a LinkedIn UGC Post API response to Post model fields.

        This is the protocol-conforming wrapper around the internal _map_ugc_post logic.
        Stores the raw API response for debugging (requirement 1.3).
        """
        return _map_ugc_post(raw)

    # ── Internal sync paths ───────────────────────────────────────────────────

    async def _sync_via_oauth_api(
        self,
        db: Session,
        user: User,
        connection: SocialConnection,
    ) -> SyncResult | None:
        """
        Calls the LinkedIn UGC Posts API to fetch the user's own posts.
        Requires r_member_social scope. Raises ScopeMissingError on 403.
        Returns None if the member_urn cannot be resolved.

        On token expiry: preserves any already-fetched data and marks
        reconnect_required in sync progress (requirement 1.2).
        """
        token = decrypt_token_lenient(connection.access_token or "")
        member_urn = connection.platform_user_id

        # Normalise the member URN
        if member_urn and not member_urn.startswith("urn:"):
            member_urn = f"urn:li:person:{member_urn}"

        if not member_urn:
            logger.warning("_sync_via_oauth_api: no member_urn for user_id=%s", user.id)
            _update_sync_progress(
                db, connection, SYNC_STATUS_FAILED,
                error="No member URN available. Reconnect LinkedIn.",
            )
            return None

        client = LinkedInClient(access_token=token)

        try:
            elements = await client.get_posts(
                member_urn=member_urn,
                count=50,
                start=0,
            )
        except ScopeMissingError:
            _update_sync_progress(
                db, connection, SYNC_STATUS_FAILED,
                error="r_member_social scope missing. Reconnect LinkedIn.",
            )
            raise
        except TokenExpiredError:
            logger.warning("_sync_via_oauth_api: token expired/invalid user_id=%s", user.id)
            # Token expired during retrieval — preserve any previously fetched data
            # and mark reconnect_required so the frontend can prompt the user.
            _update_sync_progress(
                db, connection, SYNC_STATUS_FAILED,
                error="LinkedIn token expired. Please reconnect to continue syncing.",
                reconnect_required=True,
            )
            post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count()
            return SyncResult(
                synced_posts=0,
                total_posts=post_count,
                last_synced_at=utc_now(),
                message="LinkedIn token expired. Previously fetched data preserved. Please reconnect.",
                ready_for_analysis=post_count >= MIN_POSTS_FOR_ANALYSIS,
                sync_path="oauth_api",
            )

        posts_data = [_map_ugc_post(el) for el in elements if el]
        posts_data = [p for p in posts_data if p]  # drop None entries

        synced = _upsert_posts(db, user, posts_data)
        _update_last_synced(db, connection)

        # Save to Google Drive if connected
        try:
            _save_scraped_posts_to_drive_if_connected(db, user, posts_data)
        except Exception as e:
            logger.warning("Failed to save scraped posts to Drive: %s", e)

        post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count()

        # Mark sync as completed with post count (requirement 1.9)
        _update_sync_progress(
            db, connection, SYNC_STATUS_COMPLETED,
            posts_fetched=synced,
        )

        logger.info(
            "_sync_via_oauth_api: synced %d new posts (total %d) user_id=%s",
            synced,
            post_count,
            user.id,
        )
        return SyncResult(
            synced_posts=synced,
            total_posts=post_count,
            last_synced_at=utc_now(),
            message=f"Synced {synced} LinkedIn posts via OAuth API.",
            ready_for_analysis=post_count >= MIN_POSTS_FOR_ANALYSIS,
            sync_path="oauth_api",
        )

    async def _sync_via_cookie(
        self,
        db: Session,
        user: User,
        connection: SocialConnection,
    ) -> SyncResult:
        """
        Uses the linkedin-api library (cookie/session auth) to fetch posts.
        Credentials must have been stored via social_service.store_linkedin_credentials().
        Falls back to unavailable if credentials are missing or the library is not installed.
        Tracks sync progress in connection_metadata.
        """
        meta: dict = connection.connection_metadata or {}
        enc_username = meta.get("encrypted_username")
        enc_password = meta.get("encrypted_password")

        if not enc_username or not enc_password:
            logger.warning(
                "_sync_via_cookie: no encrypted credentials found user_id=%s",
                user.id,
            )
            _update_sync_progress(
                db, connection, SYNC_STATUS_FAILED,
                error="No credentials found for cookie-auth sync.",
            )
            return self._sync_unavailable(
                db,
                user,
                "LinkedIn read permission is not active for this OAuth connection. "
                "Enable r_member_social for the LinkedIn app, then disconnect and reconnect LinkedIn.",
            )

        # Mark sync as in-progress
        _update_sync_progress(db, connection, SYNC_STATUS_IN_PROGRESS)

        username = decrypt_value(enc_username)
        password = decrypt_value(enc_password)

        try:
            client = LinkedInCookieClient(username=username, password=password)
            own_profile = client.get_profile()
            public_id = own_profile.get("publicIdentifier", username.split("@")[0])

            raw_posts = client.get_posts(public_id=public_id, count=50)
            posts_data = [_map_cookie_post(p) for p in (raw_posts or [])]
            posts_data = [p for p in posts_data if p]

            synced = _upsert_posts(db, user, posts_data)
            _update_last_synced(db, connection)

            # Save to Google Drive if connected
            try:
                _save_scraped_posts_to_drive_if_connected(db, user, posts_data)
            except Exception as e:
                logger.warning("Failed to save scraped posts to Drive: %s", e)

            post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count()

            # Mark sync as completed
            _update_sync_progress(
                db, connection, SYNC_STATUS_COMPLETED,
                posts_fetched=synced,
            )

            logger.info(
                "_sync_via_cookie: synced %d new posts (total %d) user_id=%s",
                synced,
                post_count,
                user.id,
            )
            return SyncResult(
                synced_posts=synced,
                total_posts=post_count,
                last_synced_at=utc_now(),
                message=f"Synced {synced} LinkedIn posts via cookie auth.",
                ready_for_analysis=post_count >= MIN_POSTS_FOR_ANALYSIS,
                sync_path="cookie_auth",
            )
        except LinkedInClientError as e:
            logger.warning("_sync_via_cookie: client error %s user_id=%s", e, user.id)
            _update_sync_progress(
                db, connection, SYNC_STATUS_FAILED,
                error=f"LinkedIn scraper failed: {e}",
            )
            return self._sync_unavailable(db, user, f"LinkedIn scraper failed: {e}")
        except Exception:
            logger.exception("_sync_via_cookie: failed user_id=%s", user.id)
            _update_sync_progress(
                db, connection, SYNC_STATUS_FAILED,
                error="LinkedIn scraper failed unexpectedly.",
            )
            return self._sync_unavailable(db, user, "LinkedIn scraper failed.")

    def _sync_unavailable(self, db: Session, user: User, message: str) -> SyncResult:
        """Helper returning a SyncResult when sync is not possible."""
        post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count()
        return SyncResult(
            synced_posts=0,
            total_posts=post_count,
            last_synced_at=utc_now(),
            message=message,
            ready_for_analysis=post_count >= MIN_POSTS_FOR_ANALYSIS,
            sync_path="unavailable",
        )


# ── Module-level singleton for easy access ────────────────────────────────────
linkedin_sync_service = LinkedInSyncService()


# ── Backward-compatible public API (delegates to class methods) ───────────────


def get_status(db: Session, user: User) -> dict:
    """
    Backward-compatible function returning status as a dict.

    New code should use `linkedin_sync_service.get_status()` which returns PlatformStatus.
    """
    status = linkedin_sync_service.get_status(db, user)
    return {
        "connected": status.connected,
        "platform_username": status.platform_username,
        "last_synced_at": status.last_synced_at,
        "synced_posts": status.synced_posts,
        "scopes": status.scopes,
        "posting_ready": status.posting_ready,
        "read_sync_ready": status.read_sync_ready,
        "missing_posting_scopes": status.missing_posting_scopes,
        "missing_read_scopes": status.missing_read_scopes,
        "reconnect_required": status.reconnect_required,
        "message": status.message,
        "sync_status": status.sync_status,
        "sync_error": status.sync_error,
        "sync_started_at": status.sync_started_at,
    }


async def sync_real_posts(db: Session, user: User) -> dict:
    """
    Backward-compatible function returning sync result as a dict.

    New code should use `linkedin_sync_service.sync_posts()` which returns SyncResult.
    """
    result = await linkedin_sync_service.sync_posts(db, user)
    return {
        "synced_posts": result.synced_posts,
        "total_posts": result.total_posts,
        "last_synced_at": result.last_synced_at,
        "message": result.message,
        "ready_for_analysis": result.ready_for_analysis,
        "sync_path": result.sync_path,
    }


# ── Legacy mock connect (kept for dev convenience) ────────────────────────────

def connect_mock(db: Session, user: User) -> dict:
    connection = _connection(db, user)
    if connection is None:
        connection = SocialConnection(
            user_id=user.id,
            platform="linkedin",
            platform_user_id=f"mock-{user.id}",
            platform_username=user.full_name or user.name,
            access_token="mock-linkedin-token",
            scopes=["openid", "profile", "email", "w_member_social"],
        )
        db.add(connection)
    else:
        connection.is_active = True
        connection.platform_username = user.full_name or user.name
    db.commit()
    return {
        "connected": True,
        "platform_username": connection.platform_username,
        "message": "Mock LinkedIn connection is active.",
    }


# ── Post mapping functions ────────────────────────────────────────────────────


def _map_ugc_post(el: dict) -> dict | None:
    """Maps a LinkedIn UGC Post element to our Post model fields.

    Stores the raw API response for debugging (requirement 1.3).
    """
    try:
        share = (
            el.get("specificContent", {})
            .get("com.linkedin.ugc.ShareContent", {})
        )
        text = (
            share.get("shareCommentary", {}).get("text", "")
            or el.get("commentary", "")
        )
        if not text:
            return None

        created_ts = el.get("created", {}).get("time", 0)
        published_at = (
            datetime.fromtimestamp(created_ts / 1000, tz=timezone.utc)
            if created_ts
            else utc_now()
        )

        # Social stats — available on the full socialDetail endpoint;
        # not present in basic ugcPosts response, so we default to 0.
        stats: dict = el.get("socialDetail", {})
        likes = stats.get("totalSocialActivityCounts", {}).get("numLikes", 0)
        comments = stats.get("totalSocialActivityCounts", {}).get("numComments", 0)
        impressions = stats.get("totalSocialActivityCounts", {}).get("numImpressions", 0)
        engagement_rate = round(
            (likes + comments) / impressions if impressions > 0 else 0.0, 4
        )

        content_type = "text"
        media = share.get("media", [])
        if media:
            mime = (media[0].get("originalUrl") or "")
            content_type = "image" if any(ext in mime for ext in (".jpg", ".png", ".jpeg")) else "article"

        return {
            "platform_post_id": el.get("id", ""),
            "platform": "linkedin",
            "content": text,
            "content_type": content_type,
            "published_at": published_at,
            "impressions": impressions,
            "likes": likes,
            "comments": comments,
            "shares": 0,
            "engagement_rate": engagement_rate,
            "topics": [],
            "tone": None,
            "raw_api_response": el,
            "synced_at": utc_now(),
        }
    except Exception:
        logger.exception("_map_ugc_post: failed to parse element")
        return None


def _map_cookie_post(raw: dict) -> dict | None:
    """Maps a linkedin-api post dict to our Post model fields.

    Stores the raw API response for debugging (requirement 1.3).
    """
    try:
        # linkedin-api returns actor/commentary structure
        commentary = (
            raw.get("commentary", {}).get("text", {}).get("text", "")
            or raw.get("actor", {}).get("description", {}).get("text", "")
        )
        if not commentary:
            return None

        created = raw.get("created", {})
        ts = created.get("time", 0) if isinstance(created, dict) else 0
        published_at = (
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc) if ts else utc_now()
        )

        social = raw.get("socialDetail", {}).get("totalSocialActivityCounts", {})
        likes = social.get("numLikes", 0)
        comments = social.get("numComments", 0)
        impressions = social.get("numImpressions", 0)

        platform_post_id = raw.get("entityUrn", raw.get("urn", ""))

        return {
            "platform_post_id": platform_post_id,
            "platform": "linkedin",
            "content": commentary,
            "content_type": "text",
            "published_at": published_at,
            "impressions": impressions,
            "likes": likes,
            "comments": comments,
            "shares": social.get("numShares", 0),
            "engagement_rate": round(
                (likes + comments) / impressions if impressions > 0 else 0.0, 4
            ),
            "topics": [],
            "tone": None,
            "raw_api_response": raw,
            "synced_at": utc_now(),
        }
    except Exception:
        logger.exception("_map_cookie_post: failed to parse element")
        return None


# ── MOCK FALLBACK ─────────────────────────────────────────────────────────────

def _real_sync_unavailable(db: Session, user: User, message: str) -> dict:
    """Legacy dict-returning helper for backward compatibility."""
    post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count()
    return {
        "synced_posts": 0,
        "total_posts": post_count,
        "last_synced_at": utc_now(),
        "message": message,
        "ready_for_analysis": post_count >= MIN_POSTS_FOR_ANALYSIS,
        "sync_path": "unavailable",
    }


def _sync_mock_posts_fallback(db: Session, user: User) -> dict:
    """
    Inserts deterministic mock posts. Used in development or when no real
    credentials are available. Previously named sync_mock_posts().
    """
    connection = _connection(db, user)
    if connection is None:
        connect_mock(db, user)
        connection = _connection(db, user)

    synced = 0
    for item in mock_posts(user.niche):
        post = (
            db.query(Post)
            .filter(Post.user_id == user.id, Post.platform_post_id == item["platform_post_id"])
            .first()
        )
        if post is None:
            post = Post(user_id=user.id, **item)
            db.add(post)
            synced += 1
        else:
            for key, value in item.items():
                setattr(post, key, value)

    now = utc_now()
    connection.last_synced_at = now
    db.commit()

    post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count()

    return {
        "synced_posts": synced or len(mock_posts(user.niche)),
        "total_posts": post_count,
        "last_synced_at": now,
        "message": "Mock LinkedIn posts synced (no real credentials configured).",
        "ready_for_analysis": post_count >= MIN_POSTS_FOR_ANALYSIS,
        "sync_path": "mock",
    }


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
            for key in ("impressions", "likes", "comments", "shares", "engagement_rate", "synced_at"):
                if key in item:
                    setattr(post, key, item[key])
    db.commit()
    return synced


def _update_last_synced(db: Session, connection: SocialConnection) -> None:
    connection.last_synced_at = utc_now()
    db.commit()


def _connection(db: Session, user: User) -> SocialConnection | None:
    return (
        db.query(SocialConnection)
        .filter(SocialConnection.user_id == user.id, SocialConnection.platform == "linkedin")
        .first()
    )


# ── Sync progress tracking helpers ───────────────────────────────────────────


def _update_sync_progress(
    db: Session,
    connection: SocialConnection,
    status: str,
    *,
    error: str | None = None,
    posts_fetched: int | None = None,
    reconnect_required: bool = False,
) -> None:
    """
    Update sync progress in connection_metadata.

    Stores sync state under the "sync_progress" key so the frontend can
    poll for real-time status (requirement 1.8).
    """
    meta = dict(connection.connection_metadata or {})
    now = utc_now()

    progress = meta.get("sync_progress", {})
    progress["sync_status"] = status

    if status == SYNC_STATUS_INITIATED:
        progress["sync_started_at"] = now.isoformat()
        progress["sync_completed_at"] = None
        progress["sync_error"] = None
        progress["sync_posts_fetched"] = None
        progress["reconnect_required"] = False
    elif status == SYNC_STATUS_IN_PROGRESS:
        # Keep sync_started_at from initiated phase
        progress["sync_error"] = None
        progress["reconnect_required"] = False
    elif status == SYNC_STATUS_COMPLETED:
        progress["sync_completed_at"] = now.isoformat()
        progress["sync_error"] = None
        progress["reconnect_required"] = False
        if posts_fetched is not None:
            progress["sync_posts_fetched"] = posts_fetched
    elif status == SYNC_STATUS_FAILED:
        progress["sync_completed_at"] = now.isoformat()
        progress["sync_error"] = error
        progress["reconnect_required"] = reconnect_required

    meta["sync_progress"] = progress
    connection.connection_metadata = meta
    flag_modified(connection, "connection_metadata")
    db.commit()


def _get_sync_progress(connection: SocialConnection | None) -> dict:
    """
    Read current sync progress from connection_metadata.

    Returns an empty dict if no progress has been recorded.
    """
    if connection is None:
        return {}
    meta = connection.connection_metadata or {}
    return meta.get("sync_progress", {})


def _save_scraped_posts_to_drive_if_connected(
    db: Session, user: User, posts: list[dict]
) -> str | None:
    """
    Save scraped posts to Google Drive if user has Drive connected.
    Updates LinkedIn connection metadata with drive_posts_file_id.

    Returns the Drive file ID or None if not saved.
    """
    # Check storage preference
    if user.storage_preference != "google_drive":
        return None

    # Get Google Drive connection
    drive_connection = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user.id,
            SocialConnection.platform == "google_drive",
            SocialConnection.is_active == True,
        )
        .first()
    )

    if not drive_connection:
        logger.debug("User %s has no Google Drive connection, skipping Drive save", user.id)
        return None

    # Get folder ID from metadata
    meta = drive_connection.connection_metadata or {}
    iterra_folder_id = meta.get("iterra_folder_id")

    if not iterra_folder_id:
        logger.warning("User %s has Drive connection but no Iterra folder ID", user.id)
        return None

    # Get LinkedIn connection to store posts file ID
    linkedin_connection = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user.id,
            SocialConnection.platform == "linkedin",
            SocialConnection.is_active == True,
        )
        .first()
    )

    # Prepare posts data for Drive
    posts_data = {
        "synced_at": utc_now().isoformat(),
        "posts_count": len(posts),
        "posts": posts,
    }

    # Save to Drive
    storage = StorageService(
        access_token=drive_connection.access_token,
        refresh_token=drive_connection.refresh_token,
    )

    # Use existing file ID if available (update), else create new
    existing_file_id = None
    if linkedin_connection and linkedin_connection.connection_metadata:
        existing_file_id = linkedin_connection.connection_metadata.get("drive_posts_file_id")

    file_id = storage.save_scraped_posts(
        folder_id=iterra_folder_id,
        posts_data=posts_data,
        existing_file_id=existing_file_id,
    )

    # Update LinkedIn connection metadata with file ID
    if linkedin_connection:
        linkedin_meta = dict(linkedin_connection.connection_metadata or {})
        linkedin_meta["drive_posts_file_id"] = file_id
        linkedin_connection.connection_metadata = linkedin_meta
        db.commit()

    logger.info("Saved %d scraped posts to Drive with file ID %s", len(posts), file_id)
    return file_id
