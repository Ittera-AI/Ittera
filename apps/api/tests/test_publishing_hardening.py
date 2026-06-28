from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.content_draft import ContentDraft
from app.models.content_draft import ContentDraftMedia
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.services.publisher_service import PublishError


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _register(client, email: str) -> tuple[dict[str, str], str]:
    client.post("/api/v1/auth/register", json={"email": email, "password": "secret", "name": "Test User"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "secret"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    return headers, user_id


def _draft(db, user_id: str, **overrides) -> ContentDraft:
    draft = ContentDraft(
        user_id=user_id,
        platform=overrides.pop("platform", "linkedin"),
        content=overrides.pop("content", "A real post body"),
        status=overrides.pop("status", "draft"),
        review_status=overrides.pop("review_status", "draft"),
        scheduled_for=overrides.pop("scheduled_for", None),
        auto_post_enabled_snapshot=overrides.pop("auto_post_enabled_snapshot", False),
        **overrides,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def _connection(db, user_id: str, platform: str = "linkedin", scopes: list[str] | None = None) -> SocialConnection:
    conn = SocialConnection(
        user_id=user_id,
        platform=platform,
        platform_user_id="urn:li:person:test" if platform == "linkedin" else "x-user-id",
        platform_username=f"{platform}-user",
        access_token="token",
        refresh_token="refresh",
        scopes=scopes or ["openid", "profile", "email", "w_member_social"],
        is_active=True,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def _add_media(db, draft: ContentDraft, user_id: str, count: int = 1) -> list[ContentDraftMedia]:
    media_items = []
    for idx in range(count):
        media = ContentDraftMedia(
            draft_id=draft.id,
            user_id=user_id,
            filename=f"{idx}.png",
            mime_type="image/png",
            local_path=__file__,
            public_path=f"/api/v1/content/media-file/test-{idx}",
            status="ready",
            position=idx,
        )
        db.add(media)
        media_items.append(media)
    db.commit()
    for media in media_items:
        db.refresh(media)
    return media_items


def test_media_file_requires_owner_auth(client, db):
    owner_headers, owner_id = _register(client, f"owner-{uuid4()}@example.com")
    other_headers, _ = _register(client, f"other-{uuid4()}@example.com")
    draft = _draft(db, owner_id)

    upload = client.post(
        f"/api/v1/content/drafts/{draft.id}/media",
        headers=owner_headers,
        files={"file": ("ok.png", PNG_BYTES, "image/png")},
    )
    assert upload.status_code == 200
    media_id = upload.json()["id"]

    client.cookies.clear()
    assert client.get(f"/api/v1/content/media-file/{media_id}").status_code == 401
    assert client.get(f"/api/v1/content/media-file/{media_id}", headers=other_headers).status_code == 404
    assert client.get(f"/api/v1/content/media-file/{media_id}", headers=owner_headers).status_code == 200


def test_owner_auth_denies_cross_user_delete_publish_and_calendar(client, db):
    owner_headers, owner_id = _register(client, f"owner-flow-{uuid4()}@example.com")
    other_headers, _ = _register(client, f"other-flow-{uuid4()}@example.com")
    draft = _draft(db, owner_id)
    upload = client.post(
        f"/api/v1/content/drafts/{draft.id}/media",
        headers=owner_headers,
        files={"file": ("ok.png", PNG_BYTES, "image/png")},
    )
    media_id = upload.json()["id"]

    assert client.delete(f"/api/v1/content/drafts/{draft.id}/media/{media_id}", headers=other_headers).status_code == 404
    assert client.post(f"/api/v1/content/drafts/{draft.id}/publish-now", headers=other_headers).status_code == 404
    client.cookies.clear()
    assert client.get("/api/v1/content/calendar").status_code == 401


def test_media_validation_rejects_bad_signature_and_more_than_four(client, db):
    headers, user_id = _register(client, f"media-{uuid4()}@example.com")
    draft = _draft(db, user_id)

    bad = client.post(
        f"/api/v1/content/drafts/{draft.id}/media",
        headers=headers,
        files={"file": ("bad.png", b"not-a-png", "image/png")},
    )
    assert bad.status_code == 415

    for idx in range(4):
        ok = client.post(
            f"/api/v1/content/drafts/{draft.id}/media",
            headers=headers,
            files={"file": (f"{idx}.png", PNG_BYTES, "image/png")},
        )
        assert ok.status_code == 200

    fifth = client.post(
        f"/api/v1/content/drafts/{draft.id}/media",
        headers=headers,
        files={"file": ("fifth.png", PNG_BYTES, "image/png")},
    )
    assert fifth.status_code == 422


def test_linkedin_multi_image_blocks_schedule_and_publish_now(client, db):
    headers, user_id = _register(client, f"li-media-{uuid4()}@example.com")
    draft = _draft(db, user_id, platform="linkedin")
    for idx in range(2):
        upload = client.post(
            f"/api/v1/content/drafts/{draft.id}/media",
            headers=headers,
            files={"file": (f"{idx}.png", PNG_BYTES, "image/png")},
        )
        assert upload.status_code == 200

    scheduled_for = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=12).isoformat()
    schedule = client.post("/api/v1/content/schedule", headers=headers, json={"draft_id": draft.id, "scheduled_for": scheduled_for})
    assert schedule.status_code == 422
    assert "LinkedIn publishing currently supports 1 image" in schedule.json()["error"]["message"]

    publish = client.post(f"/api/v1/content/drafts/{draft.id}/publish-now", headers=headers)
    assert publish.status_code == 422
    assert "LinkedIn publishing currently supports 1 image" in publish.json()["error"]["message"]


def test_publish_now_is_idempotent_after_success(client, db, monkeypatch):
    headers, user_id = _register(client, f"publish-{uuid4()}@example.com")
    draft = _draft(db, user_id)
    calls = {"count": 0}

    async def fake_publish(_db, _user, _draft):
        calls["count"] += 1
        return {"platform_post_id": "real-post-123"}

    monkeypatch.setattr("app.services.content_service.publish_draft", fake_publish)

    first = client.post(f"/api/v1/content/drafts/{draft.id}/publish-now", headers=headers)
    assert first.status_code == 200
    assert first.json()["platform_post_id"] == "real-post-123"

    second = client.post(f"/api/v1/content/drafts/{draft.id}/publish-now", headers=headers)
    assert second.status_code == 200
    assert second.json()["platform_post_id"] == "real-post-123"
    assert calls["count"] == 1


def test_publish_failure_marks_draft_failed(client, db, monkeypatch):
    headers, user_id = _register(client, f"fail-{uuid4()}@example.com")
    draft = _draft(db, user_id)

    async def fake_publish(_db, _user, _draft):
        raise PublishError("Platform said no.", code="platform_error")

    monkeypatch.setattr("app.services.content_service.publish_draft", fake_publish)

    response = client.post(f"/api/v1/content/drafts/{draft.id}/publish-now", headers=headers)
    assert response.status_code == 502

    db.refresh(draft)
    assert draft.status == "failed"
    assert draft.publish_error == "Platform said no."


def test_publish_failure_can_retry_without_duplicate_records(client, db, monkeypatch):
    headers, user_id = _register(client, f"retry-{uuid4()}@example.com")
    draft = _draft(db, user_id, platform="twitter")
    _add_media(db, draft, user_id, count=1)
    calls = {"count": 0}

    async def fake_publish(_db, _user, _draft):
        calls["count"] += 1
        if calls["count"] == 1:
            raise PublishError("Temporary platform failure.", code="platform_error")
        return {"platform_post_id": "x-post-retry"}

    monkeypatch.setattr("app.services.content_service.publish_draft", fake_publish)

    failed = client.post(f"/api/v1/content/drafts/{draft.id}/publish-now", headers=headers)
    assert failed.status_code == 502
    db.refresh(draft)
    assert draft.status == "failed"
    assert draft.publish_error == "Temporary platform failure."

    retried = client.post(f"/api/v1/content/drafts/{draft.id}/publish-now", headers=headers)
    assert retried.status_code == 200
    db.refresh(draft)
    assert draft.status == "published"
    assert draft.platform_post_id == "x-post-retry"
    assert calls["count"] == 2
    assert db.query(ContentDraft).filter(ContentDraft.id == draft.id).count() == 1
    assert db.query(ContentDraftMedia).filter(ContentDraftMedia.draft_id == draft.id).count() == 1


def test_cancel_sets_cancelled_and_edit_resets_approval(client, db):
    headers, user_id = _register(client, f"review-{uuid4()}@example.com")
    scheduled = datetime.now(timezone.utc) + timedelta(days=2)
    draft = _draft(db, user_id, status="scheduled", review_status="approved", scheduled_for=scheduled)

    edit = client.patch(f"/api/v1/content/drafts/{draft.id}", headers=headers, json={"content": "Edited body"})
    assert edit.status_code == 200
    body = edit.json()
    assert body["review_status"] == "draft"

    cancel = client.delete(f"/api/v1/content/schedule/{draft.id}", headers=headers)
    assert cancel.status_code == 200
    db.refresh(draft)
    assert draft.status == "cancelled"


def test_published_drafts_reject_edits(client, db):
    headers, user_id = _register(client, f"immutable-{uuid4()}@example.com")
    draft = _draft(db, user_id, status="published", review_status="approved")

    edit = client.patch(f"/api/v1/content/drafts/{draft.id}", headers=headers, json={"content": "Edited body"})
    assert edit.status_code == 409
    assert "cannot be edited" in edit.json()["error"]["message"]


def test_connection_status_reports_scope_readiness(client, db):
    headers, user_id = _register(client, f"scope-{uuid4()}@example.com")
    conn = SocialConnection(
        user_id=user_id,
        platform="linkedin",
        platform_user_id="urn:li:person:test",
        platform_username="scope-user",
        access_token="token",
        scopes=["openid", "profile", "email", "w_member_social"],
        is_active=True,
    )
    db.add(conn)
    db.commit()

    response = client.get("/api/v1/connect/status", headers=headers)
    assert response.status_code == 200
    linkedin = next(item for item in response.json() if item["platform"] == "linkedin")
    assert linkedin["posting_ready"] is True
    assert linkedin["read_sync_ready"] is False
    assert linkedin["missing_read_scopes"] == ["r_member_social"]


def test_x_old_scopes_show_reconnect_and_publish_fails_before_platform(client, db):
    headers, user_id = _register(client, f"x-scope-{uuid4()}@example.com")
    _connection(db, user_id, platform="twitter", scopes=["tweet.read", "users.read"])
    draft = _draft(db, user_id, platform="twitter")

    status_response = client.get("/api/v1/connect/status", headers=headers)
    assert status_response.status_code == 200
    twitter = next(item for item in status_response.json() if item["platform"] == "twitter")
    assert twitter["posting_ready"] is False
    assert twitter["reconnect_required"] is True
    assert set(twitter["missing_scopes"]) == {"media.write", "offline.access", "tweet.write"}

    publish = client.post(f"/api/v1/content/drafts/{draft.id}/publish-now", headers=headers)
    assert publish.status_code == 400
    assert "X reconnect required before publishing" in publish.json()["error"]["message"]


def test_mocked_queue_publish_is_idempotent(client, db, monkeypatch):
    _headers, user_id = _register(client, f"queue-{uuid4()}@example.com")
    _connection(db, user_id, platform="twitter", scopes=["tweet.read", "tweet.write", "users.read", "offline.access", "media.write"])
    draft = _draft(
        db,
        user_id,
        platform="twitter",
        status="scheduled",
        review_status="approved",
        scheduled_for=datetime.now(timezone.utc) - timedelta(minutes=5),
        auto_post_enabled_snapshot=True,
    )
    draft_id = draft.id
    _add_media(db, draft, user_id, count=1)
    calls = {"count": 0}

    async def fake_publish(_db, _user, _draft):
        calls["count"] += 1
        return {"platform_post_id": "x-queued-post"}

    import workers.celery.tasks.publisher as publisher_task

    monkeypatch.setattr("app.services.publisher_service.publish_draft", fake_publish)
    monkeypatch.setattr(publisher_task, "_session", lambda: db)

    first = publisher_task.process_publishing_queue.run()
    draft_after_first = db.query(ContentDraft).filter(ContentDraft.id == draft_id).first()
    assert first["published"] == 1
    assert draft_after_first.status == "published"
    assert draft_after_first.platform_post_id == "x-queued-post"
    assert calls["count"] == 1

    second = publisher_task.process_publishing_queue.run()
    draft_after_second = db.query(ContentDraft).filter(ContentDraft.id == draft_id).first()
    assert second["published"] == 0
    assert draft_after_second.status == "published"
    assert calls["count"] == 1
