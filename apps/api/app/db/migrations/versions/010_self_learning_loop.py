"""Self-learning content loop: learned_insights table, draft->post link, post source

Revision ID: 010_self_learning_loop
Revises: 009_encrypt_social_tokens
Create Date: 2026-06-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "010_self_learning_loop"
down_revision: Union[str, None] = "009_encrypt_social_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Gap 3: NEW learned_insights table (the summarized memory) ---
    op.create_table(
        "learned_insights",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("why_wins", sa.JSON(), nullable=False),
        sa.Column("why_losses", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("candidate_facts", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("based_on_posts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("based_on_analyses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("is_mock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_learned_insights_user_id", "learned_insights", ["user_id"], unique=False)
    op.create_index("ix_learned_insights_platform", "learned_insights", ["platform"], unique=False)
    op.create_unique_constraint(
        "uq_learned_insight_user_platform", "learned_insights", ["user_id", "platform"]
    )

    # --- Gap 1: draft -> post link ---
    op.add_column("content_drafts", sa.Column("post_id", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_content_drafts_post_id",
        "content_drafts",
        "posts",
        ["post_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_content_drafts_post_id", "content_drafts", ["post_id"], unique=False)

    # --- Gaps 1 & 7: post provenance ---
    op.add_column(
        "posts",
        sa.Column("source", sa.String(), nullable=False, server_default="imported"),
    )
    op.create_index("ix_posts_source", "posts", ["source"], unique=False)


def downgrade() -> None:
    # --- Gaps 1 & 7: post provenance (reverse order) ---
    op.drop_index("ix_posts_source", table_name="posts")
    op.drop_column("posts", "source")

    # --- Gap 1: draft -> post link ---
    op.drop_index("ix_content_drafts_post_id", table_name="content_drafts")
    op.drop_constraint("fk_content_drafts_post_id", "content_drafts", type_="foreignkey")
    op.drop_column("content_drafts", "post_id")

    # --- Gap 3: drop learned_insights table ---
    op.drop_constraint("uq_learned_insight_user_platform", "learned_insights", type_="unique")
    op.drop_index("ix_learned_insights_platform", table_name="learned_insights")
    op.drop_index("ix_learned_insights_user_id", table_name="learned_insights")
    op.drop_table("learned_insights")
