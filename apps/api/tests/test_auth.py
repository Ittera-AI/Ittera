def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "iterra-api"}


def test_register_creates_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "secret", "name": "Test User"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert response.json()["name"] == "Test User"


def test_login_returns_bearer_token_and_me(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "secret", "name": "Test User"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "test@example.com"

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"
    assert me.json()["name"] == "Test User"


def test_login_sets_http_only_cookie(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "cookie@example.com", "password": "secret", "name": "Cookie User"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "cookie@example.com", "password": "secret"},
    )

    assert "ittera_token=" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]


def test_duplicate_register_returns_conflict(client):
    payload = {"email": "dupe@example.com", "password": "secret", "name": "Dupe User"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_complete_onboarding(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "onboarding@example.com", "password": "secret", "name": "New User"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "onboarding@example.com", "password": "secret"},
    ).json()

    response = client.post(
        "/api/v1/auth/onboarding",
        json={
            "full_name": "New User",
            "niche": "AI operations",
            "goals": "Build a consistent LinkedIn presence",
            "primary_platform": "linkedin",
        },
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["onboarding_complete"] is True
    assert response.json()["niche"] == "AI operations"
