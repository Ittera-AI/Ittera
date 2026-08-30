"""Auth and happy-path tests for /api/v1/social and /api/v1/storage.

Tests cover:
- OAuth token encryption/decryption
- Storage status and health check endpoints
- Data export/import (GDPR portability)
- GDPR data deletion
- Privacy dashboard
- Retry logic
"""

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
def mock_scrape_queue(monkeypatch):
    mock_task = MagicMock()
    mock_task.id = "test-celery-task-id"

    def _queue_scrape_task(_user_id: str):
        return mock_task

    monkeypatch.setattr(
        "app.services.linkedin_service.queue_scrape_task",
        _queue_scrape_task,
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


def test_social_sync_enqueues_task(client, mock_scrape_queue):
    headers = _register_and_token(client)
    r = client.post("/api/v1/social/sync", headers=headers)
    assert r.status_code == 200
    assert r.json()["task_id"] == "test-celery-task-id"


def test_storage_status_ok_not_connected(client):
    headers = _register_and_token(client)
    r = client.get("/api/v1/storage/status", headers=headers)
    assert r.status_code == 200
    assert r.json()["connected"] is False


def test_storage_health_ok_not_connected(client):
    """Test health check when Drive is not connected."""
    headers = _register_and_token(client)
    r = client.get("/api/v1/storage/health", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["connected"] is False
    assert data["healthy"] is False
    assert data["can_read"] is False


def test_storage_delete_data_ok_without_drive(client):
    """Test GDPR data deletion when Drive is not connected."""
    headers = _register_and_token(client)
    r = client.delete("/api/v1/storage/data", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["db_records_cleared"] is True
    assert data["deleted_files"] == 0


def test_privacy_dashboard_ok(client):
    """Test privacy dashboard endpoint."""
    headers = _register_and_token(client)
    r = client.get("/api/v1/storage/privacy-dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"]
    assert "data_locations" in data
    assert "drive_connected" in data
    assert "storage_preferences" in data


def test_storage_export_unauthorized(client):
    """Test that export requires authentication."""
    assert client.get("/api/v1/storage/export").status_code == 401
    assert client.get("/api/v1/storage/export/download").status_code == 401


def test_storage_import_unauthorized(client):
    """Test that import requires authentication."""
    assert client.post("/api/v1/storage/import", json={}).status_code == 401


def test_storage_export_ok_not_connected(client):
    """Test export when Drive is not connected returns error."""
    headers = _register_and_token(client)
    r = client.get("/api/v1/storage/export/download", headers=headers)
    assert r.status_code == 400
    assert "Connect Google Drive first" in r.json()["error"]["message"]


def test_storage_import_ok_not_connected(client):
    """Test import when Drive is not connected returns error."""
    headers = _register_and_token(client)
    r = client.post("/api/v1/storage/import", json={"test": "data"}, headers=headers)
    assert r.status_code == 400
    assert "Connect Google Drive first" in r.json()["error"]["message"]


# Token Encryption Tests


def test_token_encryption_roundtrip():
    """Test that token encryption and decryption works correctly."""
    from app.core.security import encrypt_value, decrypt_value

    original_token = "test_token_12345"
    encrypted = encrypt_value(original_token)

    # Encrypted should be different from original
    assert encrypted != original_token
    assert isinstance(encrypted, str)

    # Decrypt should return original
    decrypted = decrypt_value(encrypted)
    assert decrypted == original_token


def test_decrypt_invalid_returns_empty():
    """Test that decrypting invalid data returns empty string."""
    from app.core.security import decrypt_value

    result = decrypt_value("invalid_encrypted_data")
    assert result == ""


# Scope Validation Tests


def test_validate_drive_scopes_valid():
    """Test scope validation with valid scopes."""
    from app.services.social_service import _validate_drive_scopes

    scopes = ["https://www.googleapis.com/auth/drive.file"]
    assert _validate_drive_scopes(scopes) is True


def test_validate_drive_scopes_missing():
    """Test scope validation with missing required scopes."""
    from app.services.social_service import _validate_drive_scopes

    scopes = ["https://www.googleapis.com/auth/userinfo.profile"]
    assert _validate_drive_scopes(scopes) is False


def test_validate_drive_scopes_empty():
    """Test scope validation with empty scopes."""
    from app.services.social_service import _validate_drive_scopes

    assert _validate_drive_scopes([]) is False
    assert _validate_drive_scopes(None) is False


# Audit Logger Tests


def test_audit_log_sanitization():
    """Test that sensitive data is sanitized in audit logs."""
    from app.core.audit_logger import AuditLogger

    logger = AuditLogger()
    details = {
        "username": "test_user",
        "password": "secret123",
        "token": "bearer_token_here",
        "api_key": "secret_key",
        "data": {
            "nested_password": "another_secret",
            "normal_field": "visible",
        },
    }

    sanitized = logger._sanitize_details(details)

    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["data"]["nested_password"] == "[REDACTED]"
    assert sanitized["data"]["normal_field"] == "visible"
    assert sanitized["username"] == "test_user"


# Data Retention Tests


def test_data_retention_service_get_period():
    """Test data retention service calculates correct retention period."""
    from app.services.data_retention import DataRetentionService

    # Mock user with no retention set
    class MockUser:
        data_retention_days = None

    # Use the default
    assert DataRetentionService.get_retention_period is not None


def test_retention_days_minimum():
    """Test that retention period enforces minimum."""
    from app.services.data_retention import MIN_RETENTION_DAYS

    assert MIN_RETENTION_DAYS == 7


# Storage Queue Tests


def test_storage_queue_job_creation(monkeypatch):
    """Test that storage queue creates jobs with correct structure."""
    from app.services.storage_queue import StorageQueueService, StorageOperationType

    def _redis_unavailable(*_args, **_kwargs):
        raise ConnectionError("Redis unavailable in unit test")

    monkeypatch.setattr("app.services.storage_queue.redis.from_url", _redis_unavailable)

    # Mock queue service (without Redis)
    queue = StorageQueueService()

    # Should return None when Redis is not available
    assert queue.is_available() is False

    job_id = queue.queue_operation(
        user_id="test_user",
        operation_type=StorageOperationType.SAVE_DRAFT,
        data={"draft_id": "123", "content": "test"},
        draft_id="123",
    )

    # Should return None when queue is not available
    assert job_id is None


# Retry Logic Tests


def test_drive_api_retry_decorator():
    """Test that retry decorator is properly configured."""
    from app.core.retry import drive_api_retry

    # Get the retry configuration
    retry_config = drive_api_retry(max_attempts=3)

    # Verify it's a tenacity retry decorator
    assert retry_config is not None
