#!/usr/bin/env python3
"""Seed the database with sample data for development."""

import sys
import os

# Add the api app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.post import Post
from app.models.content_plan import ContentPlan

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def seed(db: Session) -> None:
    # Check if already seeded
    if db.query(User).first():
        print("Database already seeded — skipping.")
        return

    print("Seeding database...")

    # Sample user
    user = User(
        id="00000000-0000-0000-0000-000000000001",
        email="demo@iterra.ai",
        hashed_password="$2b$12$placeholder_hash",  # not a real hash
        name="Demo User",
        is_active=True,
    )
    db.add(user)

    # Sample posts
    posts = [
        Post(
            user_id=user.id,
            platform="twitter",
            content="Thread: 10 things I learned building an AI startup 🧵",
            content_type="thread",
        ),
        Post(
            user_id=user.id,
            platform="linkedin",
            content="After 6 months of building Iterra, here are the most important lessons...",
            content_type="long-form",
        ),
    ]
    db.add_all(posts)

    # Sample content plan
    plan = ContentPlan(
        user_id=user.id,
        niche="AI & Technology",
        platforms=["twitter", "linkedin"],
        slots=[
            {"date": "2026-03-23", "platform": "twitter", "content_type": "thread", "topic": "AI tools roundup", "goal": "awareness"},
            {"date": "2026-03-25", "platform": "linkedin", "content_type": "long-form", "topic": "Building in public", "goal": "engagement"},
        ],
    )
    db.add(plan)

    db.commit()
    print(f"✅ Seeded: 1 user, {len(posts)} posts, 1 content plan")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
