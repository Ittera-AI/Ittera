"""Add publishing media workflow

Revision ID: 007_publish_media
Revises: 006_repair_social_metadata
Create Date: 2026-06-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007_publish_media"
down_revision: Union[str, None] = "006_repair_social_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("auto_post_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.add_column("content_drafts", sa.Column("review_status", sa.String(), nullable=False, server_default="draft"))
    op.add_column("content_drafts", sa.Column("review_email_sent_at", sa.DateTime(), nullable=True))
    op.add_column("content_drafts", sa.Column("auto_post_enabled_snapshot", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("content_drafts", sa.Column("persona_fit_score", sa.Integer(), nullable=True))
    op.add_column("content_drafts", sa.Column("persona_fit_notes", sa.JSON(), nullable=False, server_default="[]"))

    op.create_table(
        "content_draft_media",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("draft_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("local_path", sa.Text(), nullable=False),
        sa.Column("public_path", sa.Text(), nullable=True),
        sa.Column("drive_file_id", sa.String(), nullable=True),
        sa.Column("platform_media", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(), nullable=False, server_default="ready"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["draft_id"], ["content_drafts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_content_draft_media_draft_id"), "content_draft_media", ["draft_id"], unique=False)
    op.create_index(op.f("ix_content_draft_media_user_id"), "content_draft_media", ["user_id"], unique=False)

    op.alter_column("users", "auto_post_enabled", server_default=None)
    op.alter_column("content_drafts", "review_status", server_default=None)
    op.alter_column("content_drafts", "auto_post_enabled_snapshot", server_default=None)
    op.alter_column("content_drafts", "persona_fit_notes", server_default=None)
    op.alter_column("content_draft_media", "platform_media", server_default=None)
    op.alter_column("content_draft_media", "status", server_default=None)
    op.alter_column("content_draft_media", "position", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_content_draft_media_user_id"), table_name="content_draft_media")
    op.drop_index(op.f("ix_content_draft_media_draft_id"), table_name="content_draft_media")
    op.drop_table("content_draft_media")
    op.drop_column("content_drafts", "persona_fit_notes")
    op.drop_column("content_drafts", "persona_fit_score")
    op.drop_column("content_drafts", "auto_post_enabled_snapshot")
    op.drop_column("content_drafts", "review_email_sent_at")
    op.drop_column("content_drafts", "review_status")
    op.drop_column("users", "auto_post_enabled")
