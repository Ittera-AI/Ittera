from datetime import datetime, timedelta

BASE_TOPICS = {
    "ai": ["agentic workflows", "prompt audits", "AI operating systems", "human review loops"],
    "saas": ["activation loops", "founder-led growth", "churn diagnosis", "pricing clarity"],
    "creator": ["content systems", "audience trust", "creative cadence", "repurposing loops"],
}


def niche_key(niche: str | None) -> str:
    text = (niche or "").lower()
    if "saas" in text or "b2b" in text:
        return "saas"
    if "creator" in text or "content" in text:
        return "creator"
    return "ai"


def topics_for_niche(niche: str | None) -> list[str]:
    return BASE_TOPICS[niche_key(niche)]


def mock_posts(niche: str | None) -> list[dict]:
    topics = topics_for_niche(niche)
    now = datetime.utcnow()
    return [
        {
            "platform_post_id": f"mock-li-{idx + 1}-{niche_key(niche)}",
            "platform": "linkedin",
            "content": (
                f"{topic.title()} are easier to trust when the system shows its work.\n\n"
                "The teams winning right now are not chasing volume. They are building repeatable loops: "
                "observe, draft, review, publish, learn."
            ),
            "content_type": "text",
            "published_at": now - timedelta(days=(idx + 1) * 4),
            "impressions": 1800 + idx * 650,
            "likes": 42 + idx * 19,
            "comments": 7 + idx * 3,
            "shares": 4 + idx,
            "engagement_rate": round(0.035 + idx * 0.008, 3),
            "topics": [topic],
            "tone": "clear, analytical, founder-led",
            "raw_api_response": {"mock": True},
            "synced_at": now,
        }
        for idx, topic in enumerate(topics)
    ]
