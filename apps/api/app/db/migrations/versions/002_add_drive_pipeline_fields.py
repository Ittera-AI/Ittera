"""Add Drive pipeline fields to support privacy-first storage.

Adds:
  - social_connections.metadata (JSON) — Drive folder IDs + encrypted LinkedIn creds
  - brand_profiles.drive_analysis_file_id (String) — Drive file ID for full AI analysis
  - content_drafts.drive_file_id (String) — Drive file ID for draft content
  - content_drafts.content nullable=True — Drive-backed drafts don't store inline text
  - users.storage_preference (String) — "google_drive" | "local" | "iterra"

Revision ID: 002_add_drive_pipeline_fields
Revises: 001_initial_product_foundation
Create Date: 2026-04-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_add_drive_pipeline_fields"
down_revision: str | None = "001_initial_product_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade() -> None:
    # social_connections: add metadata JSON column for Drive folder IDs + encrypted creds
    if not _has_column("social_connections", "metadata"):
        op.add_column(
            "social_connections",
            sa.Column("metadata", sa.JSON(), nullable=True),
        )

    # brand_profiles: add Drive file ID for full AI analysis
    if not _has_column("brand_profiles", "drive_analysis_file_id"):
        op.add_column(
            "brand_profiles",
            sa.Column("drive_analysis_file_id", sa.String(), nullable=True),
        )

    # content_drafts: add Drive file ID + make content nullable
    if not _has_column("content_drafts", "drive_file_id"):
        op.add_column(
            "content_drafts",
            sa.Column("drive_file_id", sa.String(), nullable=True),
        )
    # SQLite doesn't support ALTER COLUMN nullability directly; batch mode recreates table safely.
    with op.batch_alter_table("content_drafts") as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.Text(),
            nullable=True,
        )

    # users: add storage preference
    if not _has_column("users", "storage_preference"):
        op.add_column(
            "users",
            sa.Column(
                "storage_preference",
                sa.String(),
                nullable=True,
                server_default="google_drive",
            ),
        )


def downgrade() -> None:
    # Ensure rollback does not fail when nullable rows were created after upgrade.
    op.execute("UPDATE content_drafts SET content = '' WHERE content IS NULL")
    with op.batch_alter_table("content_drafts") as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.Text(),
            nullable=False,
        )
    if _has_column("content_drafts", "drive_file_id"):
        op.drop_column("content_drafts", "drive_file_id")
    if _has_column("brand_profiles", "drive_analysis_file_id"):
        op.drop_column("brand_profiles", "drive_analysis_file_id")
    if _has_column("social_connections", "metadata"):
        op.drop_column("social_connections", "metadata")
    if _has_column("users", "storage_preference"):
        op.drop_column("users", "storage_preference")
