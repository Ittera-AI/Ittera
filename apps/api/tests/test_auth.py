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

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"
    assert me.json()["name"] == "Test User"
