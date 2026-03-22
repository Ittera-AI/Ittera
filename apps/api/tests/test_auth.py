def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "iterra-api"}


def test_register_not_implemented(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "secret", "name": "Test User"},
    )
    assert response.status_code == 501


def test_login_not_implemented(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "secret"},
    )
    assert response.status_code == 501
