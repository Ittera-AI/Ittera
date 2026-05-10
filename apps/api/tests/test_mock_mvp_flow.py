from datetime import datetime, timezone, timedelta


def _token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "mvp@example.com", "password": "secret", "name": "MVP User"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "mvp@example.com", "password": "secret"},
    )
    return response.json()["access_token"]


def test_mock_first_product_loop(client):
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    onboarding = client.post(
        "/api/v1/auth/onboarding",
        json={
            "full_name": "MVP User",
            "niche": "AI content systems",
            "goals": "Build a consistent LinkedIn presence",
            "primary_platform": "linkedin",
        },
        headers=headers,
    )
    assert onboarding.status_code == 200

    assert client.post("/api/v1/linkedin/connect/mock", headers=headers).status_code == 200
    sync = client.post("/api/v1/linkedin/sync", headers=headers)
    assert sync.status_code == 200
    assert sync.json()["synced_posts"] >= 1

    brand = client.post("/api/v1/brand-profile/generate", headers=headers)
    assert brand.status_code == 200
    assert brand.json()["profile"]["core_topics"]
    confirm = client.post("/api/v1/brand-profile/confirm", headers=headers)
    assert confirm.status_code == 200
    assert confirm.json()["is_confirmed"] is True

    trends = client.get("/api/v1/trends", headers=headers)
    assert trends.status_code == 200
    assert trends.json()["trends"]

    suggest = client.post("/api/v1/content/suggest", json={"platform": "linkedin"}, headers=headers)
    assert suggest.status_code == 200
    suggestion = suggest.json()["suggestions"][0]

    generated = client.post(
        "/api/v1/content/generate",
        json={"platform": "linkedin", "prompt": "Write about AI review loops", "suggestion": suggestion},
        headers=headers,
    )
    assert generated.status_code == 200
    draft_id = generated.json()["draft_id"]

    repurpose = client.post(
        "/api/v1/content/repurpose",
        json={"draft_id": draft_id, "target_platform": "instagram"},
        headers=headers,
    )
    assert repurpose.status_code == 200

    analytics = client.get("/api/v1/analytics/posts", headers=headers)
    assert analytics.status_code == 200
    post_id = analytics.json()[0]["id"]
    analysis = client.post(f"/api/v1/analytics/analyze/{post_id}", headers=headers)
    assert analysis.status_code == 200
    assert analysis.json()["hook_score"] >= 1

    schedule_for = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    schedule = client.post(
        "/api/v1/content/schedule",
        json={"draft_id": draft_id, "scheduled_for": schedule_for},
        headers=headers,
    )
    assert schedule.status_code == 200

    calendar = client.get("/api/v1/content/calendar", headers=headers)
    assert calendar.status_code == 200
    assert calendar.json()

    publish = client.post("/api/v1/content/publish", json={"draft_id": draft_id}, headers=headers)
    assert publish.status_code == 200
    assert publish.json()["platform_post_id"].startswith("mock-published")
