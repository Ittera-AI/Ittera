"""Security tests for the one-time connect-token OAuth start flow.

Verifies that ``/connect/{platform}/start`` resolves the connecting user from a
single-use ``ct`` token (so the Supabase JWT never appears in the URL), and that a
missing/expired/used token is rejected. The Redis-backed store is monkeypatched so
the tests stay hermetic (no sockets).
"""

import app.routers.social_oauth as so
from app.config import settings


def test_twitter_start_uses_connect_token(client, monkeypatch):
    monkeypatch.setattr(settings, "TWITTER_CLIENT_ID", "test-client")
    monkeypatch.setattr(settings, "TWITTER_REDIRECT_URI", "https://app.example/callback")
    # One-time token resolves to a user; PKCE verifier store is bypassed.
    monkeypatch.setattr(so, "take_connect_token", lambda ct: "user-123")
    monkeypatch.setattr(so, "put_verifier", lambda state, verifier: None)

    res = client.get("/api/v1/connect/twitter/start?ct=valid", follow_redirects=False)

    assert res.status_code == 302
    assert "twitter.com/i/oauth2/authorize" in res.headers["location"]


def test_twitter_start_rejects_invalid_connect_token(client, monkeypatch):
    monkeypatch.setattr(settings, "TWITTER_CLIENT_ID", "test-client")
    monkeypatch.setattr(so, "take_connect_token", lambda ct: None)

    res = client.get("/api/v1/connect/twitter/start?ct=bad", follow_redirects=False)

    assert res.status_code == 200  # popup HTML, not a redirect
    assert "missing, expired, or already used" in res.text


def test_twitter_start_requires_a_token(client, monkeypatch):
    monkeypatch.setattr(settings, "TWITTER_CLIENT_ID", "test-client")

    res = client.get("/api/v1/connect/twitter/start", follow_redirects=False)

    assert res.status_code == 200
    assert "No connect token provided" in res.text


def test_create_connect_session_produces_versioned_contract(client, monkeypatch):
    authenticated_user = type("AuthenticatedUser", (), {"id": "user-123"})()
    client.app.dependency_overrides[so.get_current_user] = lambda: authenticated_user
    monkeypatch.setattr(so, "mint_connect_token", lambda user_id: f"ct-for-{user_id}")

    response = client.post("/api/v1/connect/session", json={})

    assert response.status_code == 200
    assert response.json() == {
        "schema_version": "connect-session.v1",
        "connect_token": "ct-for-user-123",
    }
    response_schema = client.app.openapi()["paths"]["/api/v1/connect/session"]["post"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]
    assert response_schema == {
        "$ref": "#/components/schemas/ConnectSessionResponseV1"
    }
