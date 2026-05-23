"""Auth and happy-path tests for /api/v1/social and /api/v1/storage."""

from unittest.mock import MagicMock

import pytest


def _register_and_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "social_storage@example.com", "password": "secret", "name": "SS User"},
    )
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "social_storage@example.com", "password": "secret"},
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


def test_social_status_ok(client):
    headers = _register_and_token(client)
    r = client.get("/api/v1/social/status", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "connections" in body
    assert isinstance(body["connections"], list)


def test_social_sync_unauthorized(client):
    assert client.post("/api/v1/social/sync").status_code == 401


def test_social_sync_enqueues_task(client, mock_scrape_delay):
    headers = _register_and_token(client)
    r = client.post("/api/v1/social/sync", headers=headers)
    assert r.status_code == 200
    assert r.json()["task_id"] == "test-celery-task-id"


def test_storage_status_ok_not_connected(client):
    headers = _register_and_token(client)
    r = client.get("/api/v1/storage/status", headers=headers)
    assert r.status_code == 200
    assert r.json()["connected"] is False


def test_storage_delete_data_ok_without_drive(client):
    headers = _register_and_token(client)
    r = client.delete("/api/v1/storage/data", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["db_records_cleared"] is True
    assert data["deleted_files"] == 0
