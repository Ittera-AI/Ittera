"""Organization and workspace models for agency multi-client support."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, Numeric
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.datetime_helpers import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class Organization(Base):
    """
    Represents an agency or organization that manages multiple client workspaces.
    
    The top-level entity for agency/team functionality. Organizations can have
    multiple members (staff) and multiple workspaces (clients).
    """
    
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Billing and plan
    plan_type = Column(String(50), default="agency", nullable=False)
    billing_email = Column(String(255), nullable=True)
    billing_status = Column(String(50), default="active", nullable=False)
    
    # Settings
    settings = Column(JSON, default=dict, nullable=False)
    white_label_settings = Column(JSON, default=dict, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    workspaces = relationship(
        "Workspace",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def get_member(self, user_id: str) -> "OrganizationMember | None":
        """Get organization member by user ID."""
        for member in self.members:
            if member.user_id == user_id:
                return member
        return None

    def has_member(self, user_id: str) -> bool:
        """Check if user is a member of this organization."""
        return any(m.user_id == user_id for m in self.members)


class OrganizationMember(Base):
    """
    Links users to organizations with specific roles.
    
    Roles:
      - owner: Full control, can delete organization
      - admin: Manage billing, invite members, manage workspaces
      - manager: Manage workspaces and content
      - editor: Create and edit content
      - viewer: View-only access
    """
    
    __tablename__ = "organization_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    role = Column(String(50), nullable=False)
    permissions = Column(JSON, default=dict, nullable=False)
    
    invited_by = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    joined_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="organization_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])

    def get_permissions(self) -> set[str]:
        """Resolve effective organization permissions from the central policy."""
        from app.core.permissions import get_effective_organization_permissions

        return get_effective_organization_permissions(self.role, self.permissions)

    def has_permission(self, permission: str) -> bool:
        """Check a permission using the central organization policy."""
        return permission in self.get_permissions()


class Workspace(Base):
    """
    Represents a client workspace within an organization.
    
    Each workspace is isolated and contains its own:
      - Posts and analytics
      - Content drafts and plans
      - Social connections
      - Brand profiles
      - Competitors being tracked
    
    Workspaces allow agencies to manage multiple clients
    with complete data separation.
    """
    
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Identity
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    
    # Client information (optional external client details)
    client_name = Column(String(255), nullable=True)
    client_email = Column(String(255), nullable=True)
    
    # Configuration
    settings = Column(JSON, default=dict, nullable=False)
    brand_colors = Column(JSON, nullable=True)
    logo_url = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    organization = relationship("Organization", back_populates="workspaces")
    members = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
    # Content relationships
    posts = relationship("Post", back_populates="workspace", cascade="all, delete-orphan")
    content_drafts = relationship("ContentDraft", back_populates="workspace", cascade="all, delete-orphan")
    content_plans = relationship("ContentPlan", back_populates="workspace", cascade="all, delete-orphan")
    social_connections = relationship("SocialConnection", back_populates="workspace", cascade="all, delete-orphan")
    brand_profiles = relationship("BrandProfile", back_populates="workspace", cascade="all, delete-orphan")
    analytics_snapshots = relationship(
        "DailyAnalyticsSnapshot",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
    # Agency features
    competitors = relationship("Competitor", back_populates="workspace", cascade="all, delete-orphan")
    competitor_analyses = relationship("CompetitorAnalysis", back_populates="workspace", cascade="all, delete-orphan")
    approval_workflows = relationship("ApprovalWorkflow", back_populates="workspace", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="workspace", cascade="all, delete-orphan")

    def get_member(self, user_id: str) -> "WorkspaceMember | None":
        """Get workspace member by user ID."""
        for member in self.members:
            if member.user_id == user_id:
                return member
        return None

    def has_member(self, user_id: str) -> bool:
        """Check if user has access to this workspace."""
        return any(m.user_id == user_id for m in self.members)

    __table_args__ = (
        # Unique constraint on organization + slug
        {"sqlite_autoincrement": True},
    )


class WorkspaceMember(Base):
    """
    Links users to workspaces with specific roles.
    
    Workspace roles are scoped to a single client/workspace:
      - manager: Full workspace control, manage members
      - editor: Create and edit content, view analytics
      - viewer: View-only access to content and analytics
      - client: External client access (if enabled)
    """
    
    __tablename__ = "workspace_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    role = Column(String(50), nullable=False)
    permissions = Column(JSON, default=dict, nullable=False)
    
    added_by = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    added_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="workspace_memberships")
    adder = relationship("User", foreign_keys=[added_by])

    def get_permissions(self) -> set[str]:
        """Resolve effective workspace permissions from the central policy."""
        from app.core.permissions import get_effective_workspace_permissions

        return get_effective_workspace_permissions(self.role, self.permissions)

    def has_permission(self, permission: str) -> bool:
        """Check a permission using the central workspace policy."""
        return permission in self.get_permissions()


class Competitor(Base):
    """
    Represents a competitor being tracked for a workspace.
    
    Agencies can track competitors for their clients to:
      - Monitor competitor content strategy
      - Identify content gaps and opportunities
      - Benchmark performance
      - Track industry trends
    """
    
    __tablename__ = "competitors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Identity
    name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    handle = Column(String(255), nullable=False)
    profile_url = Column(Text, nullable=True)
    
    # Metrics
    follower_count = Column(Integer, nullable=True)
    niche_tags = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    workspace = relationship("Workspace", back_populates="competitors")
    posts = relationship("CompetitorPost", back_populates="competitor", cascade="all, delete-orphan")
    analyses = relationship("CompetitorAnalysis", back_populates="competitor", cascade="all, delete-orphan")


class CompetitorPost(Base):
    """
    Cached posts from tracked competitors.
    
    Stores competitor content and engagement metrics
    for analysis and comparison.
    """
    
    __tablename__ = "competitor_posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    competitor_id = Column(
        String,
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    platform_post_id = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Engagement metrics
    likes = Column(Integer, default=0, nullable=False)
    comments = Column(Integer, default=0, nullable=False)
    shares = Column(Integer, default=0, nullable=False)
    engagement_rate = Column(Numeric(8, 6), nullable=True)
    
    topics = Column(JSON, nullable=True)
    raw_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    competitor = relationship("Competitor", back_populates="posts")


class CompetitorAnalysis(Base):
    """
    AI-generated analysis of competitor strategy.
    
    Cached results from competitive intelligence AI
    to avoid repeated LLM calls.
    """
    
    __tablename__ = "competitor_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competitor_id = Column(
        String,
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    analysis_type = Column(String(50), nullable=False)
    findings = Column(JSON, nullable=True)
    ai_model_used = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    workspace = relationship("Workspace", back_populates="competitor_analyses")
    competitor = relationship("Competitor", back_populates="analyses")


class ApprovalWorkflow(Base):
    """
    Defines approval workflows for content within a workspace.
    
    Workflows define multi-step approval processes with:
      - Ordered approval steps
      - Required approvers
      - Auto-approval rules
      - Deadline settings
    """
    
    __tablename__ = "approval_workflows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    name = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)  # 'post', 'content_plan', etc.
    steps = Column(JSON, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    workspace = relationship("Workspace", back_populates="approval_workflows")


class ContentApproval(Base):
    """
    Tracks approval status for specific content items.
    
    Links content to workflows and tracks the approval
    process through all steps.
    """
    
    __tablename__ = "content_approvals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    content_type = Column(String(50), nullable=False)
    content_id = Column(String, nullable=False, index=True)
    workflow_id = Column(
        String,
        ForeignKey("approval_workflows.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    current_step = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    
    requested_by = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    requested_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace")
    workflow = relationship("ApprovalWorkflow")
    requester = relationship("User", foreign_keys=[requested_by])
    decisions = relationship("ApprovalDecision", back_populates="approval", cascade="all, delete-orphan")


class ApprovalDecision(Base):
    """
    Records individual approval/rejection decisions.
    
    Tracks who made what decision and when, with comments.
    """
    
    __tablename__ = "approval_decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    approval_id = Column(
        String,
        ForeignKey("content_approvals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    step_number = Column(Integer, nullable=False)
    approver_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    decision = Column(String(50), nullable=False)  # approved, rejected, requested_changes
    comments = Column(Text, nullable=True)
    
    decided_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    approval = relationship("ContentApproval", back_populates="decisions")
    approver = relationship("User")


class Prediction(Base):
    """
    Caches AI predictions to avoid redundant LLM calls.
    
    Stores predictions with input hashes for cache lookups,
    confidence scores, and accuracy feedback.
    """
    
    __tablename__ = "predictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    content_type = Column(String(50), nullable=False)
    content_id = Column(String, nullable=True)
    prediction_type = Column(String(50), nullable=False)  # performance, viral, timing
    
    # Cache key
    input_hash = Column(String(64), nullable=False)
    
    # Prediction data
    prediction_data = Column(JSON, nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    
    # AI tracking
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    estimated_cost = Column(Numeric(10, 6), nullable=True)
    
    # Feedback
    was_accurate = Column(Boolean, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    workspace = relationship("Workspace", back_populates="predictions")

    __table_args__ = (
        # Index for cache lookups
        {"sqlite_autoincrement": True},
    )
