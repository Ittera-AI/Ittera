"""Auth and happy-path tests for /api/v1/social and /api/v1/storage."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services import social_service
from app.models.waitlist import WaitlistEntry


def _approve_access(db, email: str):
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.email == email).first()
    if entry is None:
        entry = WaitlistEntry(email=email)
        db.add(entry)
    entry.access_approved = True
    db.commit()


def _register_and_token(client, db):
    email = "social_storage@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret", "name": "SS User"},
    )
    client.post("/api/v1/waitlist", json={"email": email})
    _approve_access(db, email)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "secret"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def mock_scrape_delay(monkeypatch):
    mock_task = MagicMock()
    mock_task.id = "test-celery-task-id"

    def _delay(_user_id: str):
        return mock_task

    monkeypatch.setattr(
        "workers.celery.tasks.scraper.scrape_linkedin_posts.delay",
        _delay,
    )


def test_social_status_unauthorized(client):
    assert client.get("/api/v1/social/status").status_code == 401


def test_storage_status_unauthorized(client):
    assert client.get("/api/v1/storage/status").status_code == 401


def test_social_status_ok(client, db):
    headers = _register_and_token(client, db)
    r = client.get("/api/v1/social/status", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "connections" in body
    assert isinstance(body["connections"], list)


def test_social_sync_unauthorized(client):
    assert client.post("/api/v1/social/sync").status_code == 401


def test_social_sync_enqueues_task(client, db, mock_scrape_delay):
    headers = _register_and_token(client, db)
    r = client.post("/api/v1/social/sync", headers=headers)
    assert r.status_code == 200
    assert r.json()["task_id"] == "test-celery-task-id"


def test_storage_status_ok_not_connected(client, db):
    headers = _register_and_token(client, db)
    r = client.get("/api/v1/storage/status", headers=headers)
    assert r.status_code == 200
    assert r.json()["connected"] is False


def test_storage_delete_data_ok_without_drive(client, db):
    headers = _register_and_token(client, db)
    r = client.delete("/api/v1/storage/data", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["db_records_cleared"] is True
    assert data["deleted_files"] == 0


def test_google_drive_oauth_state_is_signed_and_user_bound():
    state = social_service._make_oauth_state("google_drive", "user-123")

    assert state != "user-123"
    assert social_service._verify_oauth_state(state, "google_drive") == "user-123"


def test_google_drive_oauth_state_rejects_wrong_purpose():
    state = social_service._make_oauth_state("google_drive", "user-123")

    with pytest.raises(HTTPException):
        social_service._verify_oauth_state(state, "linkedin_oauth")


def test_stored_secret_encryption_round_trip():
    encrypted = social_service.encrypt_stored_secret("access-token")

    assert encrypted is not None
    assert encrypted != "access-token"
    assert encrypted.startswith("fernet:")
    assert social_service.decrypt_stored_secret(encrypted) == "access-token"
    assert social_service.decrypt_stored_secret("legacy-plaintext") == "legacy-plaintext"
