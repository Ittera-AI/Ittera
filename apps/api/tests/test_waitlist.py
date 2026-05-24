def test_waitlist_stats_are_empty_initially(client):
    response = client.get("/api/v1/waitlist")

    assert response.status_code == 200
    assert response.json() == {
        "total_joined": 0,
        "total_seats": 100,
        "remaining_seats": 100,
        "recent_joiners": [],
    }


def test_waitlist_join_returns_position_and_updates_stats(client):
    response = client.post("/api/v1/waitlist", json={"email": "hello@example.com"})

    assert response.status_code == 201
    assert response.json() == {
        "message": "You're on the list!",
        "position": 1,
        "already_joined": False,
        "total_joined": 1,
        "total_seats": 100,
        "remaining_seats": 99,
        "recent_joiners": ["HE"],
    }

    stats = client.get("/api/v1/waitlist")
    assert stats.status_code == 200
    assert stats.json()["total_joined"] == 1
    assert stats.json()["remaining_seats"] == 99
    assert stats.json()["recent_joiners"] == ["HE"]


def test_waitlist_duplicate_returns_existing_position(client):
    client.post("/api/v1/waitlist", json={"email": "hello@example.com"})
    client.post("/api/v1/waitlist", json={"email": "second@example.com"})

    duplicate = client.post("/api/v1/waitlist", json={"email": "HELLO@example.com"})

    assert duplicate.status_code == 200
    assert duplicate.json() == {
        "message": "You're already on the waitlist!",
        "position": 1,
        "already_joined": True,
        "total_joined": 2,
        "total_seats": 100,
        "remaining_seats": 98,
        "recent_joiners": ["HE", "SE"],
    }


def test_waitlist_me_returns_signed_in_member_status(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "member@example.com", "password": "secret", "name": "Member User"},
    )
    client.post("/api/v1/waitlist", json={"email": "member@example.com"})
    login = client.post("/api/v1/auth/login", json={"email": "member@example.com", "password": "secret"})

    response = client.get(
        "/api/v1/waitlist/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "member@example.com"
    assert body["joined"] is True
    assert body["access_approved"] is False
    assert body["approved_at"] is None
    assert body["position"] == body["total_joined"]
    assert body["total_seats"] == 100
    assert body["remaining_seats"] == 100 - body["total_joined"]


def test_waitlist_admin_approve_and_revoke(client, monkeypatch):
    monkeypatch.setattr("app.routers.waitlist.settings.ADMIN_EMAILS", "admin@example.com")

    client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "secret", "name": "Admin User"},
    )
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "secret"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    client.post("/api/v1/waitlist", json={"email": "member@example.com"})

    entries = client.get("/api/v1/waitlist/admin/entries", headers=admin_headers)
    assert entries.status_code == 200
    member_entries = [e for e in entries.json()["entries"] if e["email"] == "member@example.com"]
    assert len(member_entries) == 1

    approve = client.post(
        "/api/v1/waitlist/admin/approve",
        json={"email": "member@example.com"},
        headers=admin_headers,
    )
    assert approve.status_code == 200

    client.post(
        "/api/v1/auth/register",
        json={"email": "member@example.com", "password": "secret", "name": "Member User"},
    )
    member_login = client.post(
        "/api/v1/auth/login",
        json={"email": "member@example.com", "password": "secret"},
    )
    member_headers = {"Authorization": f"Bearer {member_login.json()['access_token']}"}

    me = client.get("/api/v1/waitlist/me", headers=member_headers)
    assert me.status_code == 200
    assert me.json()["access_approved"] is True
    assert me.json()["approved_at"] is not None

    revoke = client.post(
        "/api/v1/waitlist/admin/revoke",
        json={"email": "member@example.com"},
        headers=admin_headers,
    )
    assert revoke.status_code == 200

    me_after = client.get("/api/v1/waitlist/me", headers=member_headers)
    assert me_after.json()["access_approved"] is False
