"""Tests for POST /api/v1/content/drafts endpoint — thread content support."""

import json


def _token(client):
    """Register and login to get an auth token."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "drafts_test@example.com", "password": "secret", "name": "Draft Tester"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "drafts_test@example.com", "password": "secret"},
    )
    return response.json()["access_token"]


def test_create_draft_plain_string(client):
    """Creating a draft with plain string content stores as-is."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/content/drafts",
        json={"platform": "linkedin", "content": "Hello from LinkedIn!"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hello from LinkedIn!"
    assert data["platform"] == "linkedin"
    assert data["status"] == "draft"


def test_create_draft_thread_as_json_array(client):
    """Creating a draft with a list of strings stores as JSON array."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    segments = ["First tweet in the thread.", "Second tweet continues here."]
    response = client.post(
        "/api/v1/content/drafts",
        json={"platform": "twitter", "content": segments},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    # Content should be stored as a JSON array string
    parsed = json.loads(data["content"])
    assert parsed == segments


def test_create_draft_thread_validates_segment_length(client):
    """Each thread segment must be within the platform character limit."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a segment that exceeds 280 chars (Twitter free tier default)
    long_segment = "x" * 281
    response = client.post(
        "/api/v1/content/drafts",
        json={"platform": "twitter", "content": ["Short tweet.", long_segment]},
        headers=headers,
    )
    assert response.status_code == 422
    assert "exceeds" in response.json()["error"]["message"].lower()


def test_create_draft_thread_empty_list_rejected(client):
    """An empty list is not valid thread content."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/content/drafts",
        json={"platform": "twitter", "content": []},
        headers=headers,
    )
    assert response.status_code == 422


def test_create_draft_thread_empty_segment_rejected(client):
    """Thread segments cannot be empty strings."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/content/drafts",
        json={"platform": "twitter", "content": ["Valid.", "  "]},
        headers=headers,
    )
    assert response.status_code == 422


def test_create_draft_single_segment_list(client):
    """A list with one segment is valid — stored as JSON array."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/content/drafts",
        json={"platform": "twitter", "content": ["Single tweet."]},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    parsed = json.loads(data["content"])
    assert parsed == ["Single tweet."]


def test_create_draft_requires_auth(client):
    """Endpoint requires authentication."""
    response = client.post(
        "/api/v1/content/drafts",
        json={"platform": "twitter", "content": "Hello"},
    )
    assert response.status_code == 401
