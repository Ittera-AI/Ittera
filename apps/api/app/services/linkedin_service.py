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
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.security import decrypt_value
from app.db.datetime_helpers import utc_now
from app.models.post import Post
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.services.mock_data import mock_posts

logger = logging.getLogger(__name__)

# ── Minimum posts before BrandProfileEngine is triggered ─────────────────────
MIN_POSTS_FOR_ANALYSIS = 5


# ── Public API ────────────────────────────────────────────────────────────────

def get_status(db: Session, user: User) -> dict:
    connection = _connection(db, user)
    return {
        "connected": connection is not None and connection.is_active,
        "platform_username": connection.platform_username if connection else None,
        "last_synced_at": connection.last_synced_at if connection else None,
        "synced_posts": db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count(),
    }


async def sync_real_posts(db: Session, user: User) -> dict:
    """
    Syncs LinkedIn posts using the best available auth path.
    Returns a dict with synced_posts, last_synced_at, message, and ready_for_analysis.
    """
    connection = _connection(db, user)
    if connection is None:
        logger.warning("sync_real_posts: no LinkedIn connection for user_id=%s — using mock", user.id)
        return _sync_mock_posts_fallback(db, user)

    token = connection.access_token or ""

    if token == "mock-linkedin-token":
        logger.info("sync_real_posts: mock token detected — using mock fallback user_id=%s", user.id)
        return _sync_mock_posts_fallback(db, user)

    if token == "linkedin-cookie-auth":
        logger.info("sync_real_posts: cookie-auth mode user_id=%s", user.id)
        return await _sync_via_cookie(db, user, connection)

    # Attempt OAuth API first
    logger.info("sync_real_posts: trying OAuth API path user_id=%s", user.id)
    try:
        result = await _sync_via_oauth_api(db, user, connection)
        if result is not None:
            return result
    except _ScopeMissingError:
        logger.warning(
            "sync_real_posts: r_member_social scope missing — falling back to cookie path user_id=%s",
            user.id,
        )

    # OAuth API failed due to missing scope — try cookie path
    return await _sync_via_cookie(db, user, connection)


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


# ── PATH A: LinkedIn OAuth API ────────────────────────────────────────────────

class _ScopeMissingError(Exception):
    """Raised when the OAuth token lacks r_member_social scope."""


async def _sync_via_oauth_api(
    db: Session,
    user: User,
    connection: SocialConnection,
) -> dict | None:
    """
    Calls the LinkedIn UGC Posts API to fetch the user's own posts.
    Requires r_member_social scope. Raises _ScopeMissingError on 403.
    Returns None if the member_urn cannot be resolved.
    """
    token = connection.access_token
    member_urn = connection.platform_user_id  # stored as "urn:li:person:{sub}" or plain sub

    # Normalise the member URN
    if member_urn and not member_urn.startswith("urn:"):
        member_urn = f"urn:li:person:{member_urn}"

    if not member_urn:
        logger.warning("sync_via_oauth_api: no member_urn for user_id=%s", user.id)
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": "202404",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            params={
                "q": "authors",
                "authors": f"List({member_urn})",
                "count": 50,
                "start": 0,
            },
        )

    if resp.status_code == 403:
        raise _ScopeMissingError("r_member_social scope not granted")

    if resp.status_code == 401:
        logger.warning("sync_via_oauth_api: token expired/invalid user_id=%s", user.id)
        return None

    resp.raise_for_status()
    data = resp.json()
    elements: list[dict] = data.get("elements", [])

    posts_data = [_map_ugc_post(el) for el in elements if el]
    posts_data = [p for p in posts_data if p]  # drop None entries

    synced = _upsert_posts(db, user, posts_data)
    _update_last_synced(db, connection)

    post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count()

    logger.info(
        "sync_via_oauth_api: synced %d new posts (total %d) user_id=%s",
        synced,
        post_count,
        user.id,
    )
    return {
        "synced_posts": synced,
        "total_posts": post_count,
        "last_synced_at": utc_now(),
        "message": f"Synced {synced} LinkedIn posts via OAuth API.",
        "ready_for_analysis": post_count >= MIN_POSTS_FOR_ANALYSIS,
        "sync_path": "oauth_api",
    }


def _map_ugc_post(el: dict) -> dict | None:
    """Maps a LinkedIn UGC Post element to our Post model fields."""
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


# ── PATH B: Cookie-based scraper ──────────────────────────────────────────────

async def _sync_via_cookie(
    db: Session,
    user: User,
    connection: SocialConnection,
) -> dict:
    """
    Uses the linkedin-api library (cookie/session auth) to fetch posts.
    Credentials must have been stored via social_service.store_linkedin_credentials().
    Falls back to mock if credentials are missing or the library is not installed.
    """
    meta: dict = connection.connection_metadata or {}
    enc_username = meta.get("encrypted_username")
    enc_password = meta.get("encrypted_password")

    if not enc_username or not enc_password:
        logger.warning(
            "sync_via_cookie: no encrypted credentials found — using mock user_id=%s",
            user.id,
        )
        return _sync_mock_posts_fallback(db, user)

    try:
        from linkedin_api import Linkedin  # type: ignore[import]
    except ImportError:
        logger.warning("sync_via_cookie: linkedin-api not installed — using mock user_id=%s", user.id)
        return _sync_mock_posts_fallback(db, user)

    username = decrypt_value(enc_username)
    password = decrypt_value(enc_password)

    try:
        client = Linkedin(username, password)
        # Get own profile to resolve public_id
        own_profile = client.get_profile(urn_id=None)
        public_id = own_profile.get("publicIdentifier", username.split("@")[0])

        raw_posts = client.get_profile_posts(public_id=public_id, post_count=50)
        posts_data = [_map_cookie_post(p) for p in (raw_posts or [])]
        posts_data = [p for p in posts_data if p]

        synced = _upsert_posts(db, user, posts_data)
        _update_last_synced(db, connection)

        post_count = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count()

        logger.info(
            "sync_via_cookie: synced %d new posts (total %d) user_id=%s",
            synced,
            post_count,
            user.id,
        )
        return {
            "synced_posts": synced,
            "total_posts": post_count,
            "last_synced_at": utc_now(),
            "message": f"Synced {synced} LinkedIn posts via cookie auth.",
            "ready_for_analysis": post_count >= MIN_POSTS_FOR_ANALYSIS,
            "sync_path": "cookie_auth",
        }
    except Exception:
        logger.exception("sync_via_cookie: failed — using mock user_id=%s", user.id)
        return _sync_mock_posts_fallback(db, user)


def _map_cookie_post(raw: dict) -> dict | None:
    """Maps a linkedin-api post dict to our Post model fields."""
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
