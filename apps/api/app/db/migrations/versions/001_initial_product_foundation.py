"""Initial product foundation schema.

Revision ID: 001_initial_product_foundation
Revises:
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial_product_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("niche", sa.String(), nullable=True),
        sa.Column("goals", sa.Text(), nullable=True),
        sa.Column("primary_platform", sa.String(), nullable=False),
        sa.Column("onboarding_complete", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "waitlist",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("profession", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_waitlist_email"), "waitlist", ["email"], unique=True)

    op.create_table(
        "content_plans",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("niche", sa.String(), nullable=False),
        sa.Column("platforms", sa.JSON(), nullable=False),
        sa.Column("slots", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "posts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("platform_post_id", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Integer(), nullable=False),
        sa.Column("shares", sa.Integer(), nullable=False),
        sa.Column("engagement_rate", sa.Float(), nullable=False),
        sa.Column("topics", sa.JSON(), nullable=False),
        sa.Column("tone", sa.String(), nullable=True),
        sa.Column("raw_api_response", sa.JSON(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_posts_platform_post_id"), "posts", ["platform_post_id"], unique=False)

    op.create_table(
        "social_connections",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("platform_user_id", sa.String(), nullable=False),
        sa.Column("platform_username", sa.String(), nullable=True),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_social_connections_platform"), "social_connections", ["platform"], unique=False)
    op.create_index(op.f("ix_social_connections_user_id"), "social_connections", ["user_id"], unique=False)

    op.create_table(
        "brand_profiles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("profile", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("ai_confidence_score", sa.Float(), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        sa.Column("analysis_based_on_posts", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "content_drafts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("repurposed_versions", sa.JSON(), nullable=False),
        sa.Column("prompt_used", sa.Text(), nullable=True),
        sa.Column("trend_used", sa.String(), nullable=True),
        sa.Column("generation_model", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("celery_task_id", sa.String(), nullable=True),
        sa.Column("platform_post_id", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("publish_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_content_drafts_user_id"), "content_drafts", ["user_id"], unique=False)

    op.create_table(
        "trend_snapshots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("niche", sa.String(), nullable=False),
        sa.Column("trends", sa.JSON(), nullable=False),
        sa.Column("top_pick", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("niche", name="uq_trend_snapshots_niche"),
    )

    op.create_table(
        "post_analyses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("post_id", sa.String(), nullable=False),
        sa.Column("hook_score", sa.Integer(), nullable=False),
        sa.Column("tone_match_score", sa.Integer(), nullable=False),
        sa.Column("structure_score", sa.Integer(), nullable=False),
        sa.Column("cta_effectiveness", sa.String(), nullable=False),
        sa.Column("coach_feedback", sa.JSON(), nullable=False),
        sa.Column("rewrite_suggestion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id"),
    )


def downgrade() -> None:
    op.drop_table("post_analyses")
    op.drop_table("trend_snapshots")
    op.drop_index(op.f("ix_content_drafts_user_id"), table_name="content_drafts")
    op.drop_table("content_drafts")
    op.drop_table("brand_profiles")
    op.drop_index(op.f("ix_social_connections_user_id"), table_name="social_connections")
    op.drop_index(op.f("ix_social_connections_platform"), table_name="social_connections")
    op.drop_table("social_connections")
    op.drop_index(op.f("ix_posts_platform_post_id"), table_name="posts")
    op.drop_table("posts")
    op.drop_table("content_plans")
    op.drop_index(op.f("ix_waitlist_email"), table_name="waitlist")
    op.drop_table("waitlist")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
