"""Add permanent context layer: user_contexts table + identity columns on users

Revision ID: 004_add_permanent_context_layer
Revises: 645e8b126c98
Create Date: 2026-05-24

Adds:
  - users.brand_name, users.bio, users.target_audience, users.content_mission
  - user_contexts table (versioned permanent context snapshots)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004_add_permanent_context_layer"
down_revision: Union[str, None] = "645e8b126c98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New identity columns on users ────────────────────────────────────────
    op.add_column("users", sa.Column("brand_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("target_audience", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("content_mission", sa.Text(), nullable=True))

    # ── Versioned permanent context snapshots ─────────────────────────────────
    op.create_table(
        "user_contexts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("brand_name", sa.String(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("content_mission", sa.Text(), nullable=True),
        sa.Column("platform_facts", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("change_source", sa.String(), nullable=False, server_default="onboarding"),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_contexts_user_id", "user_contexts", ["user_id"])
    op.create_index("ix_user_contexts_is_active", "user_contexts", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_user_contexts_is_active", table_name="user_contexts")
    op.drop_index("ix_user_contexts_user_id", table_name="user_contexts")
    op.drop_table("user_contexts")

    op.drop_column("users", "content_mission")
    op.drop_column("users", "target_audience")
    op.drop_column("users", "bio")
    op.drop_column("users", "brand_name")
