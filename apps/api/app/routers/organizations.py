"""Organization (Agency) management API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.permissions import Permission, has_organization_permission
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.services import workspace_service

router = APIRouter(tags=["organizations"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    plan_type: str = Field(default="agency", pattern=r"^(agency|enterprise)$")
    billing_email: str | None = Field(None, max_length=255)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    billing_email: str | None = Field(None, max_length=255)
    settings: dict[str, Any] | None = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan_type: str
    billing_email: str | None
    settings: dict[str, Any]
    white_label_settings: dict[str, Any]
    created_at: str
    
    class Config:
        from_attributes = True


class MemberInvite(BaseModel):
    user_id: str
    role: str = Field(..., pattern=r"^(owner|admin|manager|editor|viewer)$")


class MemberUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(owner|admin|manager|editor|viewer)$")


class MemberResponse(BaseModel):
    id: str
    user_id: str
    role: str
    invited_by: str | None
    joined_at: str
    
    class Config:
        from_attributes = True


class MemberDetailResponse(MemberResponse):
    user_name: str | None
    user_email: str


class WhiteLabelSettingsUpdate(BaseModel):
    enabled: bool | None = None
    logo_url: str | None = None
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    favicon_url: str | None = None
    custom_domain: str | None = None
    sender_name: str | None = None
    sender_email: str | None = None
    reply_to_email: str | None = None
    custom_footer: str | None = None
    hide_powered_by: bool | None = None
    custom_disclaimer: str | None = None
    enable_client_portal: bool | None = None
    portal_access_level: str | None = Field(None, pattern=r"^(view_only|limited_edit)$")


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    client_name: str | None = Field(None, max_length=255)
    client_email: str | None = Field(None, max_length=255)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    client_name: str | None = Field(None, max_length=255)
    client_email: str | None = Field(None, max_length=255)
    brand_colors: dict[str, str] | None = None
    logo_url: str | None = None
    is_active: bool | None = None


class WorkspaceResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    slug: str
    client_name: str | None
    client_email: str | None
    is_active: bool
    brand_colors: dict[str, str] | None
    logo_url: str | None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Organization Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new organization.
    
    The creator becomes the organization owner.
    """
    org = workspace_service.create_organization(
        db=db,
        creator=current_user,
        name=data.name,
        slug=data.slug,
        plan_type=data.plan_type,
        billing_email=data.billing_email,
    )
    return org


@router.get("/my", response_model=list[OrganizationResponse])
async def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List organizations the current user is a member of."""
    orgs = workspace_service.list_user_organizations(db, current_user)
    return orgs


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get organization details."""
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check membership
    if not org.has_member(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return org


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update organization settings.
    
    Requires: org:manage permission
    """
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permission
    member = org.get_member(current_user.id)
    if not member or not has_organization_permission(member.role, Permission.ORG_MANAGE):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    updates = data.model_dump(exclude_unset=True)
    org = workspace_service.update_organization(db, org, updates)
    return org


# ---------------------------------------------------------------------------
# Member Management
# ---------------------------------------------------------------------------

@router.get("/{org_id}/members", response_model=list[MemberDetailResponse])
async def list_organization_members(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all members of an organization."""
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check membership
    if not org.has_member(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build detailed response
    members = []
    for member in org.members:
        members.append({
            "id": member.id,
            "user_id": member.user_id,
            "role": member.role,
            "invited_by": member.invited_by,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "user_name": member.user.name if member.user else None,
            "user_email": member.user.email if member.user else "unknown",
        })
    
    return members


@router.post("/{org_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_organization_member(
    org_id: str,
    data: MemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Invite a user to the organization.
    
    Requires: members:invite permission
    """
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    member = workspace_service.add_organization_member(
        db=db,
        org=org,
        invited_by=current_user,
        user_id=data.user_id,
        role=data.role,
    )
    return member


@router.patch("/{org_id}/members/{user_id}", response_model=MemberResponse)
async def update_organization_member(
    org_id: str,
    user_id: str,
    data: MemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a member's role.
    
    Requires: members:manage permission (for roles you can manage)
    """
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    member = workspace_service.update_member_role(
        db=db,
        org=org,
        updated_by=current_user,
        user_id=user_id,
        new_role=data.role,
    )
    return member


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a member from the organization.
    
    Requires: members:manage permission
    """
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    workspace_service.remove_organization_member(
        db=db,
        org=org,
        removed_by=current_user,
        user_id=user_id,
    )
    return None


# ---------------------------------------------------------------------------
# White-Label Settings
# ---------------------------------------------------------------------------

@router.get("/{org_id}/white-label", response_model=dict[str, Any])
async def get_white_label_settings(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get white-label settings for the organization."""
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check membership
    if not org.has_member(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return workspace_service.get_white_label_settings(org)


@router.patch("/{org_id}/white-label", response_model=dict[str, Any])
async def update_white_label_settings(
    org_id: str,
    data: WhiteLabelSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update white-label settings.
    
    Requires: org:manage permission
    """
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permission
    member = org.get_member(current_user.id)
    if not member or not has_organization_permission(member.role, Permission.ORG_MANAGE):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    settings = data.model_dump(exclude_unset=True)
    return workspace_service.update_white_label_settings(db, org, settings)


# ---------------------------------------------------------------------------
# Workspace Management (within organization)
# ---------------------------------------------------------------------------

@router.get("/{org_id}/workspaces", response_model=list[WorkspaceResponse])
async def list_organization_workspaces(
    org_id: str,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all workspaces in the organization."""
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check membership
    if not org.has_member(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    workspaces = workspace_service.list_organization_workspaces(
        db,
        org,
        current_user,
        include_inactive=include_inactive,
    )
    return workspaces


@router.post("/{org_id}/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    org_id: str,
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new workspace within the organization.
    
    Requires: workspace:create permission
    """
    org = workspace_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    workspace = workspace_service.create_workspace(
        db=db,
        org=org,
        created_by=current_user,
        name=data.name,
        slug=data.slug,
        client_name=data.client_name,
        client_email=data.client_email,
    )
    return workspace
