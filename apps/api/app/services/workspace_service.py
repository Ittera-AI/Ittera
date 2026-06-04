"""Workspace and organization management service.

Provides CRUD operations for:
  - Organizations (agencies)
  - Workspaces (client containers)
  - Memberships and permissions
  - White-label settings
"""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import (
    ORGANIZATION_ROLE_PERMISSIONS,
    WORKSPACE_ROLE_PERMISSIONS,
    VALID_ORGANIZATION_ROLES,
    VALID_WORKSPACE_ROLES,
    can_manage_role,
    validate_organization_role,
    validate_workspace_role,
)
from app.models.organization import (
    ApprovalWorkflow,
    Competitor,
    ContentApproval,
    Organization,
    OrganizationMember,
    Workspace,
    WorkspaceMember,
)
from app.models.user import User


def create_organization(
    db: Session,
    creator: User,
    name: str,
    slug: str,
    plan_type: str = "agency",
    billing_email: str | None = None,
) -> Organization:
    """
    Create a new organization with the creator as owner.
    
    Args:
        db: Database session
        creator: User creating the organization
        name: Organization name
        slug: Unique organization slug
        plan_type: Subscription plan type
        billing_email: Billing contact email
        
    Returns:
        Created organization
        
    Raises:
        HTTPException: 409 if slug already exists
    """
    # Check slug uniqueness
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug already exists",
        )
    
    # Create organization
    org = Organization(
        name=name,
        slug=slug,
        plan_type=plan_type,
        billing_email=billing_email or creator.email,
    )
    db.add(org)
    db.flush()  # Get org ID
    
    # Add creator as owner
    member = OrganizationMember(
        organization_id=org.id,
        user_id=creator.id,
        role="owner",
    )
    db.add(member)
    db.commit()
    db.refresh(org)
    
    return org


def get_organization(db: Session, org_id: str) -> Organization | None:
    """Get organization by ID."""
    return db.query(Organization).filter(Organization.id == org_id).first()


def get_organization_by_slug(db: Session, slug: str) -> Organization | None:
    """Get organization by slug."""
    return db.query(Organization).filter(Organization.slug == slug).first()


def list_user_organizations(db: Session, user: User) -> list[Organization]:
    """Get all organizations the user is a member of."""
    return (
        db.query(Organization)
        .join(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .all()
    )


def update_organization(
    db: Session,
    org: Organization,
    updates: dict[str, Any],
) -> Organization:
    """
    Update organization settings.
    
    Allowed updates:
      - name
      - billing_email
      - settings
      - white_label_settings
    """
    allowed_fields = {"name", "billing_email", "settings", "white_label_settings"}
    
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(org, field, value)
    
    db.commit()
    db.refresh(org)
    return org


def add_organization_member(
    db: Session,
    org: Organization,
    invited_by: User,
    user_id: str,
    role: str,
) -> OrganizationMember:
    """
    Add a member to the organization.
    
    Args:
        db: Database session
        org: Organization to add member to
        invited_by: User sending the invitation
        user_id: User to invite
        role: Role for the new member
        
    Returns:
        Created membership
        
    Raises:
        HTTPException: 400 if invalid role
        HTTPException: 403 if inviter lacks permission
        HTTPException: 409 if user already member
    """
    # Validate role
    if not validate_organization_role(role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}",
        )
    
    # Check inviter can manage this role
    inviter_member = org.get_member(invited_by.id)
    if not inviter_member or not can_manage_role(inviter_member.role, role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot invite user with this role",
        )
    
    # Check not already member
    existing = org.get_member(user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member",
        )
    
    # Create membership
    member = OrganizationMember(
        organization_id=org.id,
        user_id=user_id,
        role=role,
        invited_by=invited_by.id,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return member


def remove_organization_member(
    db: Session,
    org: Organization,
    removed_by: User,
    user_id: str,
) -> None:
    """
    Remove a member from the organization.
    
    Raises:
        HTTPException: 403 if remover lacks permission
        HTTPException: 400 if trying to remove self as sole owner
    """
    member = org.get_member(user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    
    # Check remover can manage this role
    remover_member = org.get_member(removed_by.id)
    if not remover_member or not can_manage_role(remover_member.role, member.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove this member",
        )
    
    # Prevent removing last owner
    if member.role == "owner":
        owner_count = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.role == "owner",
            )
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner",
            )
    
    db.delete(member)
    db.commit()


def update_member_role(
    db: Session,
    org: Organization,
    updated_by: User,
    user_id: str,
    new_role: str,
) -> OrganizationMember:
    """
    Update a member's role in the organization.
    
    Raises:
        HTTPException: 400 if invalid role
        HTTPException: 403 if updater lacks permission
    """
    # Validate role
    if not validate_organization_role(new_role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {new_role}",
        )
    
    member = org.get_member(user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    
    # Check updater can manage both old and new roles
    updater_member = org.get_member(updated_by.id)
    if not updater_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an organization member",
        )
    
    if not can_manage_role(updater_member.role, member.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify this member's role",
        )
    
    if not can_manage_role(updater_member.role, new_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign this role",
        )
    
    # Prevent demoting last owner
    if member.role == "owner" and new_role != "owner":
        owner_count = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.role == "owner",
            )
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last owner",
            )
    
    member.role = new_role
    db.commit()
    db.refresh(member)
    
    return member


# ---------------------------------------------------------------------------
# Workspace Management
# ---------------------------------------------------------------------------

def create_workspace(
    db: Session,
    org: Organization,
    created_by: User,
    name: str,
    slug: str,
    client_name: str | None = None,
    client_email: str | None = None,
    settings: dict | None = None,
) -> Workspace:
    """
    Create a new workspace within an organization.
    
    Args:
        db: Database session
        org: Parent organization
        created_by: User creating the workspace
        name: Workspace name
        slug: Unique slug within organization
        client_name: External client name (optional)
        client_email: External client contact (optional)
        settings: Workspace settings dict
        
    Returns:
        Created workspace
        
    Raises:
        HTTPException: 403 if creator lacks permission
        HTTPException: 409 if slug exists in org
    """
    # Check creator has workspace create permission
    member = org.get_member(created_by.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an organization member",
        )
    
    from app.core.permissions import Permission, has_organization_permission
    if not has_organization_permission(member.role, Permission.WORKSPACE_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create workspaces",
        )
    
    # Check slug uniqueness within org
    existing = (
        db.query(Workspace)
        .filter(Workspace.organization_id == org.id, Workspace.slug == slug)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workspace slug already exists in this organization",
        )
    
    # Create workspace
    workspace = Workspace(
        organization_id=org.id,
        name=name,
        slug=slug,
        client_name=client_name,
        client_email=client_email,
        settings=settings or {},
    )
    db.add(workspace)
    db.flush()  # Get workspace ID
    
    # Add creator as manager
    ws_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=created_by.id,
        role="manager",
        added_by=created_by.id,
    )
    db.add(ws_member)
    db.commit()
    db.refresh(workspace)
    
    return workspace


def get_workspace(db: Session, workspace_id: str) -> Workspace | None:
    """Get workspace by ID."""
    return db.query(Workspace).filter(Workspace.id == workspace_id).first()


def get_workspace_by_slug(db: Session, org_id: str, slug: str) -> Workspace | None:
    """Get workspace by organization and slug."""
    return (
        db.query(Workspace)
        .filter(Workspace.organization_id == org_id, Workspace.slug == slug)
        .first()
    )


def list_organization_workspaces(
    db: Session,
    org: Organization,
    include_inactive: bool = False,
) -> list[Workspace]:
    """Get all workspaces in an organization."""
    query = db.query(Workspace).filter(Workspace.organization_id == org.id)
    
    if not include_inactive:
        query = query.filter(Workspace.is_active == True)
    
    return query.all()


def list_user_workspaces(
    db: Session,
    user: User,
    org_id: str | None = None,
) -> list[Workspace]:
    """
    Get all workspaces the user has access to.
    
    Includes workspaces where user is:
      - Direct workspace member
      - Organization admin (can access all workspaces in org)
    """
    # Direct workspace memberships
    direct_access = (
        db.query(Workspace)
        .join(WorkspaceMember)
        .filter(
            WorkspaceMember.user_id == user.id,
            Workspace.is_active == True,
        )
    )
    
    if org_id:
        direct_access = direct_access.filter(Workspace.organization_id == org_id)
    
    workspaces = set(direct_access.all())
    
    # Organization-level access (admins can see all workspaces)
    org_memberships = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .all()
    )
    
    for org_member in org_memberships:
        # Admins and owners get access to all workspaces
        if org_member.role in ("owner", "admin"):
            org_workspaces = (
                db.query(Workspace)
                .filter(
                    Workspace.organization_id == org_member.organization_id,
                    Workspace.is_active == True,
                )
                .all()
            )
            workspaces.update(org_workspaces)
    
    return list(workspaces)


def update_workspace(
    db: Session,
    workspace: Workspace,
    updates: dict[str, Any],
) -> Workspace:
    """
    Update workspace settings.
    
    Allowed updates:
      - name
      - client_name
      - client_email
      - settings
      - brand_colors
      - logo_url
      - is_active
    """
    allowed_fields = {
        "name",
        "client_name",
        "client_email",
        "settings",
        "brand_colors",
        "logo_url",
        "is_active",
    }
    
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(workspace, field, value)
    
    db.commit()
    db.refresh(workspace)
    return workspace


def add_workspace_member(
    db: Session,
    workspace: Workspace,
    added_by: User,
    user_id: str,
    role: str,
) -> WorkspaceMember:
    """
    Add a member to a workspace.
    
    Args:
        db: Database session
        workspace: Target workspace
        added_by: User adding the member
        user_id: User to add
        role: Workspace role (manager, editor, viewer, client)
        
    Returns:
        Created workspace membership
    """
    # Validate role
    if not validate_workspace_role(role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}",
        )
    
    # Check adder has manage permission
    adder = workspace.get_member(added_by.id)
    if not adder:
        # Check org-level permission
        org_member = workspace.organization.get_member(added_by.id)
        if not org_member or org_member.role not in ("owner", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add members to this workspace",
            )
    else:
        # Check adder has manage permission
        from app.core.permissions import Permission
        if not adder.has_permission(Permission.WORKSPACE_MANAGE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add members to this workspace",
            )
        
        # Check adder can manage this role
        if not can_manage_role(adder.role, role, is_org_level=False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add member with this role",
            )
    
    # Check not already member
    existing = workspace.get_member(user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a workspace member",
        )
    
    # Create membership
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user_id,
        role=role,
        added_by=added_by.id,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return member


def remove_workspace_member(
    db: Session,
    workspace: Workspace,
    removed_by: User,
    user_id: str,
) -> None:
    """Remove a member from a workspace."""
    member = workspace.get_member(user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    
    # Check remover has permission
    remover = workspace.get_member(removed_by.id)
    if not remover:
        org_member = workspace.organization.get_member(removed_by.id)
        if not org_member or org_member.role not in ("owner", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove members",
            )
    else:
        from app.core.permissions import Permission
        if not remover.has_permission(Permission.WORKSPACE_MANAGE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove members",
            )
    
    db.delete(member)
    db.commit()


# ---------------------------------------------------------------------------
# White-Label Settings
# ---------------------------------------------------------------------------

def update_white_label_settings(
    db: Session,
    org: Organization,
    settings: dict[str, Any],
) -> dict[str, Any]:
    """
    Update white-label settings for an organization.
    
    Settings:
      - enabled: bool
      - logo_url: str
      - primary_color: str (hex)
      - secondary_color: str (hex)
      - favicon_url: str
      - custom_domain: str
      - sender_name: str
      - sender_email: str
      - reply_to_email: str
      - custom_footer: str
      - hide_powered_by: bool
      - custom_disclaimer: str
      - enable_client_portal: bool
      - portal_access_level: str
    """
    current = org.white_label_settings or {}
    
    allowed_fields = {
        "enabled",
        "logo_url",
        "primary_color",
        "secondary_color",
        "favicon_url",
        "custom_domain",
        "sender_name",
        "sender_email",
        "reply_to_email",
        "custom_footer",
        "hide_powered_by",
        "custom_disclaimer",
        "enable_client_portal",
        "portal_access_level",
    }
    
    for field, value in settings.items():
        if field in allowed_fields:
            current[field] = value
    
    org.white_label_settings = current
    db.commit()
    db.refresh(org)
    
    return current


def get_white_label_settings(org: Organization) -> dict[str, Any]:
    """Get white-label settings with defaults."""
    defaults = {
        "enabled": False,
        "primary_color": "#6366F1",
        "secondary_color": "#A5B4FC",
        "sender_name": "Iterra Reports",
        "sender_email": "reports@iterra.io",
        "hide_powered_by": False,
        "enable_client_portal": False,
        "portal_access_level": "view_only",
    }
    
    current = org.white_label_settings or {}
    return {**defaults, **current}
