from datetime import datetime

from sqlalchemy.orm import Session

from app.models.trend_snapshot import TrendSnapshot
from app.models.user import User
from app.services.mock_data import topics_for_niche


def get_trends_for_user(db: Session, user: User) -> dict:
    snapshot = _snapshot(db, user)
    if snapshot is None:
        return refresh_trends(db, user)
    return _response(snapshot)


def refresh_trends(db: Session, user: User) -> dict:
    trends = _mock_trends(user.niche)
    snapshot = _snapshot(db, user)
    if snapshot is None:
        snapshot = TrendSnapshot(niche=user.niche or "general")
        db.add(snapshot)
    snapshot.trends = trends
    snapshot.top_pick = trends[0] if trends else None
    snapshot.fetched_at = datetime.utcnow()
    db.commit()
    db.refresh(snapshot)
    return _response(snapshot)


def _snapshot(db: Session, user: User) -> TrendSnapshot | None:
    return db.query(TrendSnapshot).filter(TrendSnapshot.niche == (user.niche or "general")).first()


def _mock_trends(niche: str | None) -> list[dict]:
    return [
        {
            "topic": topic.title(),
            "raw_score": 92 - idx * 7,
            "niche_relevance": round(0.94 - idx * 0.06, 2),
            "related_queries": [f"{topic} examples", f"{topic} strategy", f"{topic} mistakes"],
            "content_angle": f"Show how {topic} changes the way teams plan content this month.",
        }
        for idx, topic in enumerate(topics_for_niche(niche))
    ]


def _response(snapshot: TrendSnapshot) -> dict:
    fetched_at = snapshot.fetched_at or datetime.utcnow()
    return {
        "niche": snapshot.niche,
        "trends": snapshot.trends,
        "top_pick": snapshot.top_pick,
        "fetched_at": fetched_at,
        "cache_age_minutes": int((datetime.utcnow() - fetched_at).total_seconds() // 60),
    }
