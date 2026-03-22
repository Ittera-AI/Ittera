def test_calendar_requires_auth(client):
    response = client.post(
        "/api/v1/calendar/generate",
        json={"niche": "tech", "platforms": ["twitter"], "posting_frequency": 5},
    )
    assert response.status_code == 401
