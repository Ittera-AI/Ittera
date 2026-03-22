def test_repurpose_requires_auth(client):
    response = client.post(
        "/api/v1/repurpose/",
        json={"original_content": "Hello", "source_platform": "twitter", "target_platforms": ["linkedin"]},
    )
    assert response.status_code == 401
