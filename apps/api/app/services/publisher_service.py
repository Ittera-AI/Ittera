from __future__ import annotations

import logging
import asyncio
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.linkedin_client import LinkedInClient
from app.models.content_draft import ContentDraft, ContentDraftMedia
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.services.publishing_state import (
    LINKEDIN_POSTING_SCOPES,
    X_MEDIA_SCOPES,
    X_POSTING_SCOPES,
    missing_scopes,
)

logger = logging.getLogger(__name__)
HTTP_TIMEOUT_SECONDS = 30
MEDIA_UPLOAD_TIMEOUT_SECONDS = 45
PUBLISH_HTTP_MAX_ATTEMPTS = 3


class PublishError(Exception):
    def __init__(
        self,
        detail: str,
        code: str = "platform_error",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code
        self.status_code = status_code


async def publish_draft(db: Session, user: User, draft: ContentDraft) -> dict[str, Any]:
    conn = _connection(db, user, draft.platform)
    if not conn:
        raise PublishError(
            f"Connect {draft.platform} before publishing.",
            code="missing_connection",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if draft.platform == "linkedin":
        return await _publish_linkedin(conn, draft)
    if draft.platform == "twitter":
        return await _publish_x(db, conn, draft)
    raise PublishError(
        f"Publishing is not supported for {draft.platform}.",
        code="unsupported_platform",
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def _connection(db: Session, user: User, platform: str) -> SocialConnection | None:
    return (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user.id,
            SocialConnection.platform == platform,
            SocialConnection.is_active == True,
        )
        .first()
    )


async def _publish_linkedin(conn: SocialConnection, draft: ContentDraft) -> dict[str, Any]:
    _require_scopes(conn, LINKEDIN_POSTING_SCOPES, "LinkedIn")
    member_urn = conn.platform_user_id
    if member_urn and not member_urn.startswith("urn:"):
        member_urn = f"urn:li:person:{member_urn}"

    client = LinkedInClient(conn.access_token)
    try:
        media_assets = []
        if len(draft.media) > 1:
            raise PublishError("LinkedIn image publishing supports one image per post in this version.", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        for item in draft.media:
            asset = await _upload_linkedin_image(conn.access_token, member_urn, item)
            media_assets.append(asset)

        if not media_assets:
            data = await client.publish_post(member_urn=member_urn, text=draft.content or "")
        else:
            data = await _create_linkedin_image_post(conn.access_token, member_urn, draft.content or "", media_assets)
        return {"platform_post_id": data.get("id") or data.get("urn") or ""}
    except Exception as exc:
        if isinstance(exc, PublishError):
            raise
        raise PublishError("LinkedIn publish failed. Try again later.", code="platform_error") from exc
    finally:
        await client.close()


async def _upload_linkedin_image(access_token: str, owner_urn: str, media: ContentDraftMedia) -> str:
    path = Path(media.local_path)
    if not path.is_file():
        raise PublishError(f"Missing image file: {media.filename}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": "202605",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    body = {"initializeUploadRequest": {"owner": owner_urn}}
    async with httpx.AsyncClient(timeout=MEDIA_UPLOAD_TIMEOUT_SECONDS) as client:
        reg = await _request_with_retries(
            client,
            "POST",
            "https://api.linkedin.com/rest/images?action=initializeUpload",
            platform="linkedin",
            action="image_upload_initialization",
            headers=headers,
            json=body,
        )
        if reg.is_error:
            raise _platform_http_error("linkedin", "image_upload_initialization", reg)
        payload = reg.json().get("value", {})
        upload = payload.get("uploadUrl")
        asset = payload.get("image")
        if not upload or not asset:
            raise PublishError("LinkedIn image upload initialization did not return an upload URL.")
        put = await _request_with_retries(
            client,
            "PUT",
            upload,
            platform="linkedin",
            action="image_upload",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": media.mime_type},
            content=path.read_bytes(),
        )
        if put.is_error:
            raise _platform_http_error("linkedin", "image_upload", put)
    platform_media = dict(media.platform_media or {})
    platform_media["linkedin_image"] = asset
    media.platform_media = platform_media
    return asset


async def _create_linkedin_image_post(access_token: str, owner_urn: str, text: str, assets: list[str]) -> dict[str, Any]:
    body = {
        "author": owner_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {"media": {"id": assets[0]}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        res = await _request_with_retries(
            client,
            "POST",
            "https://api.linkedin.com/rest/posts",
            platform="linkedin",
            action="create_post",
            headers={
                "Authorization": f"Bearer {access_token}",
                "LinkedIn-Version": "202605",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json",
            },
            json=body,
        )
        if res.is_error:
            raise _platform_http_error("linkedin", "create_post", res)
            
        post_urn = res.headers.get("x-restli-id")
        if post_urn:
            return {"id": post_urn}
            
        try:
            return res.json()
        except Exception:
            return {"id": ""}


async def _publish_x(db: Session, conn: SocialConnection, draft: ContentDraft) -> dict[str, Any]:
    required = set(X_POSTING_SCOPES)
    if draft.media:
        required |= X_MEDIA_SCOPES
    _require_scopes(conn, required, "X")
    await _refresh_x_token_if_needed(db, conn)
    try:
        media_ids = []
        for item in draft.media:
            media_ids.append(await _upload_x_image(conn.access_token, item))
        body: dict[str, Any] = {"text": (draft.content or "")[:280]}
        if media_ids:
            body["media"] = {"media_ids": media_ids}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            res = await _request_with_retries(
                client,
                "POST",
                "https://api.x.com/2/tweets",
                platform="twitter",
                action="create_post",
                headers={"Authorization": f"Bearer {conn.access_token}", "Content-Type": "application/json"},
                json=body,
            )
            if res.is_error:
                raise _platform_http_error("twitter", "create_post", res)
            data = res.json()
        return {"platform_post_id": data.get("data", {}).get("id", "")}
    except Exception as exc:
        if isinstance(exc, PublishError):
            raise
        raise PublishError("X publish failed. Try again later.", code="platform_error") from exc


async def _upload_x_image(access_token: str, media: ContentDraftMedia) -> str:
    path = Path(media.local_path)
    if not path.is_file():
        raise PublishError(f"Missing image file: {media.filename}")
    async with httpx.AsyncClient(timeout=MEDIA_UPLOAD_TIMEOUT_SECONDS) as client:
        with path.open("rb") as handle:
            res = await _request_with_retries(
                client,
                "POST",
                "https://api.x.com/2/media/upload",
                platform="twitter",
                action="media_upload",
                headers={"Authorization": f"Bearer {access_token}"},
                data={"media_category": "tweet_image", "media_type": media.mime_type},
                files={"media": (media.filename, handle, media.mime_type)},
            )
        if res.is_error:
            raise _platform_http_error("twitter", "media_upload", res)
        data = res.json()
    media_id = str(data.get("data", {}).get("id") or data.get("media_id_string") or data.get("id") or "")
    if not media_id:
        raise PublishError("X media upload did not return media id.")
    platform_media = dict(media.platform_media or {})
    platform_media["x_media_id"] = media_id
    media.platform_media = platform_media
    return media_id


def _require_scopes(conn: SocialConnection, required: set[str], platform_label: str) -> None:
    missing = missing_scopes(conn.scopes, required)
    if missing:
        detail = (
            f"{platform_label} reconnect required before publishing. Missing scopes: {', '.join(missing)}."
            if platform_label == "X"
            else f"{platform_label} needs reconnect before publishing. Missing scopes: {', '.join(missing)}."
        )
        raise PublishError(
            detail,
            code="missing_scope",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


async def _refresh_x_token_if_needed(db: Session, conn: SocialConnection) -> None:
    if not conn.refresh_token or not conn.token_expires_at:
        return
    from datetime import datetime, timedelta, timezone

    expires_at = conn.token_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
        return

    data = {
        "grant_type": "refresh_token",
        "refresh_token": conn.refresh_token,
        "client_id": settings.TWITTER_CLIENT_ID,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    auth = None
    if settings.TWITTER_CLIENT_SECRET:
        auth = (settings.TWITTER_CLIENT_ID, settings.TWITTER_CLIENT_SECRET)

    async with httpx.AsyncClient(timeout=15) as client:
        res = await _request_with_retries(
            client,
            "POST",
            "https://api.twitter.com/2/oauth2/token",
            platform="twitter",
            action="token_refresh",
            data=data,
            headers=headers,
            auth=auth,
        )
    if res.is_error:
        raise PublishError("X token expired. Reconnect X before publishing.", code="token_expired", status_code=status.HTTP_401_UNAUTHORIZED)
    tokens = res.json()
    conn.access_token = tokens.get("access_token") or conn.access_token
    conn.refresh_token = tokens.get("refresh_token") or conn.refresh_token
    if tokens.get("scope"):
        conn.scopes = str(tokens["scope"]).split()
    if tokens.get("expires_in"):
        conn.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(tokens["expires_in"]))
    db.commit()


async def _request_with_retries(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    platform: str,
    action: str,
    **kwargs: Any,
) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(1, PUBLISH_HTTP_MAX_ATTEMPTS + 1):
        try:
            response = await client.request(method, url, **kwargs)
            if response.status_code < 500 or attempt == PUBLISH_HTTP_MAX_ATTEMPTS:
                return response
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_exc = exc
            if attempt == PUBLISH_HTTP_MAX_ATTEMPTS:
                raise PublishError(
                    f"{_platform_label(platform)} is temporarily unreachable. Try again later.",
                    code="network_error",
                    status_code=status.HTTP_502_BAD_GATEWAY,
                ) from exc
        await asyncio.sleep(0.25 * attempt)
    if last_exc:
        raise PublishError(
            f"{_platform_label(platform)} is temporarily unreachable. Try again later.",
            code="network_error",
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from last_exc
    raise PublishError(
        f"{_platform_label(platform)} {action.replace('_', ' ')} failed. Try again later.",
        code="platform_error",
    )


def _platform_http_error(platform: str, action: str, response: httpx.Response) -> PublishError:
    logger.error(f"Platform HTTP error: {response.status_code} on {action}. Body: {response.text}")
    if response.status_code in {401, 403}:
        code = "token_expired" if response.status_code == 401 else "missing_scope"
        return PublishError(
            f"{_platform_label(platform)} reconnect required before publishing.",
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if response.status_code == 429:
        return PublishError(
            f"{_platform_label(platform)} rate limit reached. Try again later.",
            code="rate_limited",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    if response.status_code >= 500:
        return PublishError(
            f"{_platform_label(platform)} is temporarily unavailable. Try again later.",
            code="platform_unavailable",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    return PublishError(
        f"{_platform_label(platform)} {action.replace('_', ' ')} failed. Check the draft and connection before retrying.",
        code="platform_error",
        status_code=status.HTTP_502_BAD_GATEWAY,
    )


def _platform_label(platform: str) -> str:
    return "X" if platform == "twitter" else "LinkedIn" if platform == "linkedin" else platform
