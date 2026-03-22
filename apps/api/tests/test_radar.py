def test_radar_requires_auth(client):
    response = client.post(
        "/api/v1/radar/scan",
        json={"niche": "tech", "platforms": ["twitter"]},
    )
    assert response.status_code == 401
