def test_coach_requires_auth(client):
    response = client.post(
        "/api/v1/coach/analyze",
        json={"content": "Hello world", "platform": "twitter"},
    )
    assert response.status_code == 401
