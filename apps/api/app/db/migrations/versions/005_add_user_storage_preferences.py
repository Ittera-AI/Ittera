"""Add granular user storage preferences.

Revision ID: 005_add_user_storage_preferences
Revises: 004_add_permanent_context_layer, 65130da7c837
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa


revision = "005_add_user_storage_preferences"
down_revision = ("004_add_permanent_context_layer", "65130da7c837")
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column("users", "storage_preferences"):
        op.add_column(
            "users",
            sa.Column("storage_preferences", sa.JSON(), nullable=True),
        )
        op.execute(
            """
            UPDATE users
            SET storage_preferences = json_build_object(
                'default',
                COALESCE(storage_preference, 'google_drive')
            )
            WHERE storage_preferences IS NULL
            """
        )
        op.alter_column("users", "storage_preferences", nullable=False)

    if not _has_column("users", "data_retention_days"):
        op.add_column(
            "users",
            sa.Column("data_retention_days", sa.Integer(), nullable=True),
        )
        op.execute("UPDATE users SET data_retention_days = 365 WHERE data_retention_days IS NULL")


def downgrade() -> None:
    if _has_column("users", "data_retention_days"):
        op.drop_column("users", "data_retention_days")

    if _has_column("users", "storage_preferences"):
        op.drop_column("users", "storage_preferences")
