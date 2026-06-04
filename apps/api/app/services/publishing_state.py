from __future__ import annotations

from collections.abc import Iterable

from fastapi import status


DRAFT_STATUS_DRAFT = "draft"
DRAFT_STATUS_SCHEDULED = "scheduled"
DRAFT_STATUS_PUBLISHING = "publishing"
DRAFT_STATUS_PUBLISHED = "published"
DRAFT_STATUS_FAILED = "failed"
DRAFT_STATUS_CANCELLED = "cancelled"

REVIEW_STATUS_DRAFT = "draft"
REVIEW_STATUS_REVIEW_DUE = "review_due"
REVIEW_STATUS_APPROVED = "approved"
REVIEW_STATUS_REJECTED = "rejected"

TERMINAL_PUBLISH_STATUSES = {
    DRAFT_STATUS_PUBLISHED,
    DRAFT_STATUS_PUBLISHING,
    DRAFT_STATUS_CANCELLED,
}

LINKEDIN_POSTING_SCOPES = {"openid", "profile", "email", "w_member_social"}
LINKEDIN_READ_SCOPES = {"r_member_social"}
X_POSTING_SCOPES = {"tweet.read", "tweet.write", "users.read", "offline.access"}
X_MEDIA_SCOPES = {"media.write"}
LINKEDIN_MAX_IMAGES = 1
X_MAX_IMAGES = 4


def normalize_scopes(scopes: Iterable[str] | None) -> set[str]:
    return {str(scope).strip() for scope in (scopes or []) if str(scope).strip()}


def missing_scopes(scopes: Iterable[str] | None, required: Iterable[str]) -> list[str]:
    granted = normalize_scopes(scopes)
    return sorted(set(required) - granted)


class PublishingValidationError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def validate_platform_media(platform: str, media_count: int) -> None:
    if platform == "linkedin" and media_count > LINKEDIN_MAX_IMAGES:
        raise PublishingValidationError("LinkedIn publishing currently supports 1 image per post. Remove extra images before scheduling or publishing.")
    if platform == "twitter" and media_count > X_MAX_IMAGES:
        raise PublishingValidationError("X publishing supports up to 4 images per post.")
