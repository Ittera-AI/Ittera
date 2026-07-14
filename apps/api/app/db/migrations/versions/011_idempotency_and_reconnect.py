"""Additive fields for publish idempotency and reconnect-required state

Adds:
  - content_drafts.publish_idempotency_key (nullable String, unique per draft)
  - social_connections.requires_reconnect (Boolean, default false)

Revision ID: 011_idempotency_reconnect
Revises: 010_self_learning_loop
Create Date: 2026-06-08 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "011_idempotency_reconnect"
down_revision: Union[str, None] = "010_self_learning_loop"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- R8.5: stable idempotency key on drafts, unique per draft ---
    op.add_column(
        "content_drafts",
        sa.Column("publish_idempotency_key", sa.String(), nullable=True),
    )
    # Unique index (works natively on SQLite and Postgres without batch ALTER).
    op.create_index(
        "uq_content_drafts_publish_idempotency_key",
        "content_drafts",
        ["publish_idempotency_key"],
        unique=True,
    )

    # --- R4.3: connection requires re-authorization flag ---
    op.add_column(
        "social_connections",
        sa.Column(
            "requires_reconnect",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    # --- R4.3 ---
    op.drop_column("social_connections", "requires_reconnect")

    # --- R8.5 (reverse order) ---
    op.drop_index(
        "uq_content_drafts_publish_idempotency_key",
        table_name="content_drafts",
    )
    op.drop_column("content_drafts", "publish_idempotency_key")
