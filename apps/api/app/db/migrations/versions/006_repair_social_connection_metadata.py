"""Repair social connection metadata column name.

Revision ID: 006_repair_social_metadata
Revises: 005_add_user_storage_preferences
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa


revision = "006_repair_social_metadata"
down_revision = "005_add_user_storage_preferences"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    has_metadata = _has_column("social_connections", "metadata")
    has_connection_metadata = _has_column("social_connections", "connection_metadata")

    if has_metadata and not has_connection_metadata:
        op.alter_column(
            "social_connections",
            "metadata",
            new_column_name="connection_metadata",
            existing_type=sa.JSON(),
            nullable=True,
        )
    elif not has_connection_metadata:
        op.add_column(
            "social_connections",
            sa.Column("connection_metadata", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("social_connections", "connection_metadata") and not _has_column("social_connections", "metadata"):
        op.alter_column(
            "social_connections",
            "connection_metadata",
            new_column_name="metadata",
            existing_type=sa.JSON(),
            nullable=True,
        )
