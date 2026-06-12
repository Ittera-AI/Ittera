"""Debug the failing sync progress tests."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.services.linkedin_service import (
    SYNC_STATUS_COMPLETED,
    SYNC_STATUS_FAILED,
    _get_sync_progress,
    _update_sync_progress,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./debug_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

db = TestingSessionLocal()

# Create user
u = User(
    id="debug-user",
    email="debug@example.com",
    name="Debug User",
    hashed_password="fakehash",
)
db.merge(u)
db.commit()

# Create connection
conn = SocialConnection(
    id="debug-conn",
    user_id=u.id,
    platform="linkedin",
    platform_user_id="urn:li:person:abc123",
    platform_username="Debug User",
    access_token="valid-token",
    scopes=["openid", "profile", "email", "w_member_social", "r_member_social"],
    is_active=True,
    connection_metadata={},
)
db.merge(conn)
db.commit()

print(f"After merge+commit, conn.connection_metadata = {conn.connection_metadata}")

# Now update sync progress
_update_sync_progress(db, conn, SYNC_STATUS_COMPLETED, posts_fetched=10)

print(f"After _update_sync_progress, conn.connection_metadata = {conn.connection_metadata}")

# Re-query from db
conn2 = db.query(SocialConnection).filter(SocialConnection.id == "debug-conn").first()
print(f"Re-queried conn2.connection_metadata = {conn2.connection_metadata}")
print(f"conn2 is conn: {conn2 is conn}")

progress = _get_sync_progress(conn2)
print(f"progress = {progress}")

if progress.get("sync_status") == "completed":
    print("SUCCESS")
else:
    print("FAILED - sync_status not found or wrong value")

db.close()

import os
try:
    os.unlink("debug_test.db")
except:
    pass
