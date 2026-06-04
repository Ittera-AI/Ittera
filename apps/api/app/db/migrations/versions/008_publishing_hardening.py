"""Publishing workflow hardening

Revision ID: 008_publishing_hardening
Revises: 007_publish_media
Create Date: 2026-06-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "008_publishing_hardening"
down_revision: Union[str, None] = "007_publish_media"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_content_drafts_publish_queue",
        "content_drafts",
        ["status", "scheduled_for", "review_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_content_drafts_publish_queue", table_name="content_drafts")
