"""Add waitlist platform access approval fields.

Revision ID: 003_add_waitlist_access_approval
Revises: 002_add_drive_pipeline_fields
Create Date: 2026-05-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_add_waitlist_access_approval"
down_revision: str | None = "002_add_drive_pipeline_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade() -> None:
    if not _has_column("waitlist", "access_approved"):
        op.add_column(
            "waitlist",
            sa.Column("access_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if not _has_column("waitlist", "approved_at"):
        op.add_column("waitlist", sa.Column("approved_at", sa.DateTime(), nullable=True))
    if not _has_column("waitlist", "approved_by"):
        op.add_column("waitlist", sa.Column("approved_by", sa.String(), nullable=True))


def downgrade() -> None:
    if _has_column("waitlist", "approved_by"):
        op.drop_column("waitlist", "approved_by")
    if _has_column("waitlist", "approved_at"):
        op.drop_column("waitlist", "approved_at")
    if _has_column("waitlist", "access_approved"):
        op.drop_column("waitlist", "access_approved")
