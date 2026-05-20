from sqlalchemy.orm import Session

from app.db.datetime_helpers import utc_now

from app.models.post import Post
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.services.mock_data import mock_posts


def get_status(db: Session, user: User) -> dict:
    connection = _connection(db, user)
    return {
        "connected": connection is not None and connection.is_active,
        "platform_username": connection.platform_username if connection else None,
        "last_synced_at": connection.last_synced_at if connection else None,
        "synced_posts": db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").count(),
    }


def connect_mock(db: Session, user: User) -> dict:
    connection = _connection(db, user)
    if connection is None:
        connection = SocialConnection(
            user_id=user.id,
            platform="linkedin",
            platform_user_id=f"mock-{user.id}",
            platform_username=user.full_name or user.name,
            access_token="mock-linkedin-token",
            scopes=["openid", "profile", "email", "w_member_social"],
        )
        db.add(connection)
    else:
        connection.is_active = True
        connection.platform_username = user.full_name or user.name
    db.commit()
    return {
        "connected": True,
        "platform_username": connection.platform_username,
        "message": "Mock LinkedIn connection is active.",
    }


def sync_mock_posts(db: Session, user: User) -> dict:
    connection = _connection(db, user)
    if connection is None:
        connect_mock(db, user)
        connection = _connection(db, user)

    synced = 0
    for item in mock_posts(user.niche):
        post = (
            db.query(Post)
            .filter(Post.user_id == user.id, Post.platform_post_id == item["platform_post_id"])
            .first()
        )
        if post is None:
            post = Post(user_id=user.id, **item)
            db.add(post)
            synced += 1
        else:
            for key, value in item.items():
                setattr(post, key, value)
    now = utc_now()
    connection.last_synced_at = now
    db.commit()
    return {
        "synced_posts": synced or len(mock_posts(user.niche)),
        "last_synced_at": now,
        "message": "Mock LinkedIn posts synced.",
    }


def _connection(db: Session, user: User) -> SocialConnection | None:
    return (
        db.query(SocialConnection)
        .filter(SocialConnection.user_id == user.id, SocialConnection.platform == "linkedin")
        .first()
    )
