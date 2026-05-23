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
        "access_approved": False,
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
        "access_approved": False,
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


def test_waitlist_me_auto_enrolls_signed_in_user_without_prior_join(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "auto@example.com", "password": "secret", "name": "Auto User"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "auto@example.com", "password": "secret"})

    response = client.get(
        "/api/v1/waitlist/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "auto@example.com"
    assert body["joined"] is True
    assert body["position"] == 1
    assert body["total_joined"] == 1


def test_workspace_access_pending_until_waitlist_approval(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "pending@example.com", "password": "secret", "name": "Pending User"},
    )
    client.post("/api/v1/waitlist", json={"email": "pending@example.com"})
    login = client.post("/api/v1/auth/login", json={"email": "pending@example.com", "password": "secret"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    access = client.get("/api/v1/auth/workspace-access", headers=headers)
    assert access.status_code == 200
    assert access.json()["has_access"] is False
    assert access.json()["waitlisted"] is True
    assert access.json()["reason"] == "pending_approval"

    workspace = client.get("/api/v1/linkedin/status", headers=headers)
    assert workspace.status_code == 403
