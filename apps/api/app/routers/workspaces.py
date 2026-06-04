"""Workspace management API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.dependencies.workspace import get_current_workspace
from app.models.organization import Workspace
from app.models.user import User
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    client_name: str | None = Field(None, max_length=255)
    client_email: str | None = Field(None, max_length=255)
    brand_colors: dict[str, str] | None = None
    logo_url: str | None = None
    is_active: bool | None = None


class WorkspaceMember(BaseModel):
    id: str
    user_id: str
    role: str
    added_by: str | None
    added_at: str


class AddWorkspaceMember(BaseModel):
    user_id: str
    role: str = Field(..., pattern=r"^(manager|editor|viewer|client)$")


class UpdateWorkspaceMember(BaseModel):
    role: str = Field(..., pattern=r"^(manager|editor|viewer|client)$")


class WorkspaceStats(BaseModel):
    posts_count: int
    drafts_count: int
    content_plans_count: int
    competitors_count: int
    members_count: int


class WorkspaceDetail(BaseModel):
    id: str
    organization_id: str
    name: str
    slug: str
    client_name: str | None
    client_email: str | None
    is_active: bool
    brand_colors: dict[str, str] | None
    logo_url: str | None
    settings: dict[str, Any]
    created_at: str
    updated_at: str
    stats: WorkspaceStats | None = None
    my_role: str | None = None
    organization_name: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/my", response_model=list[WorkspaceDetail])
async def list_my_workspaces(
    org_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all workspaces the current user has access to.
    
    Includes direct workspace memberships and organization-level access.
    """
    workspaces = workspace_service.list_user_workspaces(
        db, current_user, org_id=org_id
    )
    
    # Enhance with stats and role info
    result = []
    for ws in workspaces:
        # Get user's role
        member = ws.get_member(current_user.id)
        org_member = ws.organization.get_member(current_user.id)
        role = member.role if member else (org_member.role if org_member else None)
        
        # Get stats
        stats = WorkspaceStats(
            posts_count=len(ws.posts),
            drafts_count=len(ws.content_drafts),
            content_plans_count=len(ws.content_plans),
            competitors_count=len(ws.competitors),
            members_count=len(ws.members),
        )
        
        result.append({
            "id": ws.id,
            "organization_id": ws.organization_id,
            "name": ws.name,
            "slug": ws.slug,
            "client_name": ws.client_name,
            "client_email": ws.client_email,
            "is_active": ws.is_active,
            "brand_colors": ws.brand_colors,
            "logo_url": ws.logo_url,
            "settings": ws.settings or {},
            "created_at": ws.created_at.isoformat() if ws.created_at else None,
            "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
            "stats": stats,
            "my_role": role,
            "organization_name": ws.organization.name if ws.organization else None,
        })
    
    return result


@router.get("/{workspace_id}", response_model=WorkspaceDetail)
async def get_workspace(
    workspace: Workspace | None = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
):
    """Get detailed workspace information."""
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get user's role
    member = workspace.get_member(current_user.id)
    org_member = workspace.organization.get_member(current_user.id)
    role = member.role if member else (org_member.role if org_member else None)
    
    # Get stats
    stats = WorkspaceStats(
        posts_count=len(workspace.posts),
        drafts_count=len(workspace.content_drafts),
        content_plans_count=len(workspace.content_plans),
        competitors_count=len(workspace.competitors),
        members_count=len(workspace.members),
    )
    
    return {
        "id": workspace.id,
        "organization_id": workspace.organization_id,
        "name": workspace.name,
        "slug": workspace.slug,
        "client_name": workspace.client_name,
        "client_email": workspace.client_email,
        "is_active": workspace.is_active,
        "brand_colors": workspace.brand_colors,
        "logo_url": workspace.logo_url,
        "settings": workspace.settings or {},
        "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
        "updated_at": workspace.updated_at.isoformat() if workspace.updated_at else None,
        "stats": stats,
        "my_role": role,
        "organization_name": workspace.organization.name if workspace.organization else None,
    }


@router.patch("/{workspace_id}", response_model=WorkspaceDetail)
async def update_workspace(
    data: WorkspaceUpdate,
    workspace: Workspace | None = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update workspace settings.
    
    Requires: workspace:edit permission
    """
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check permission
    member = workspace.get_member(current_user.id)
    org_member = workspace.organization.get_member(current_user.id)
    
    can_edit = False
    if member and member.has_permission(Permission.WORKSPACE_EDIT):
        can_edit = True
    elif org_member and org_member.has_permission(Permission.WORKSPACE_EDIT):
        can_edit = True
    
    if not can_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    updates = data.model_dump(exclude_unset=True)
    workspace = workspace_service.update_workspace(db, workspace, updates)
    
    # Return updated workspace (re-use get_workspace logic)
    stats = WorkspaceStats(
        posts_count=len(workspace.posts),
        drafts_count=len(workspace.content_drafts),
        content_plans_count=len(workspace.content_plans),
        competitors_count=len(workspace.competitors),
        members_count=len(workspace.members),
    )
    
    role = member.role if member else (org_member.role if org_member else None)
    
    return {
        "id": workspace.id,
        "organization_id": workspace.organization_id,
        "name": workspace.name,
        "slug": workspace.slug,
        "client_name": workspace.client_name,
        "client_email": workspace.client_email,
        "is_active": workspace.is_active,
        "brand_colors": workspace.brand_colors,
        "logo_url": workspace.logo_url,
        "settings": workspace.settings or {},
        "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
        "updated_at": workspace.updated_at.isoformat() if workspace.updated_at else None,
        "stats": stats,
        "my_role": role,
        "organization_name": workspace.organization.name if workspace.organization else None,
    }


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace: Workspace | None = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soft-delete a workspace (sets is_active = False).
    
    Requires: workspace:delete permission
    """
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check permission
    member = workspace.get_member(current_user.id)
    org_member = workspace.organization.get_member(current_user.id)
    
    can_delete = False
    if member and member.has_permission(Permission.WORKSPACE_DELETE):
        can_delete = True
    elif org_member and org_member.has_permission(Permission.WORKSPACE_DELETE):
        can_delete = True
    
    if not can_delete:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Soft delete
    workspace.is_active = False
    db.commit()
    
    return None


# ---------------------------------------------------------------------------
# Member Management
# ---------------------------------------------------------------------------

@router.get("/{workspace_id}/members", response_model=list[WorkspaceMember])
async def list_workspace_members(
    workspace: Workspace | None = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
):
    """List all members of a workspace."""
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check access (any member can view)
    if not workspace.has_member(current_user.id):
        # Check org-level access
        org_member = workspace.organization.get_member(current_user.id)
        if not org_member or org_member.role not in ("owner", "admin"):
            raise HTTPException(status_code=403, detail="Access denied")
    
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "role": m.role,
            "added_by": m.added_by,
            "added_at": m.added_at.isoformat() if m.added_at else None,
        }
        for m in workspace.members
    ]


@router.post("/{workspace_id}/members", response_model=WorkspaceMember, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    data: AddWorkspaceMember,
    workspace: Workspace | None = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a member to the workspace.
    
    Requires: workspace:manage permission
    """
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    member = workspace_service.add_workspace_member(
        db=db,
        workspace=workspace,
        added_by=current_user,
        user_id=data.user_id,
        role=data.role,
    )
    
    return {
        "id": member.id,
        "user_id": member.user_id,
        "role": member.role,
        "added_by": member.added_by,
        "added_at": member.added_at.isoformat() if member.added_at else None,
    }


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMember)
async def update_workspace_member(
    user_id: str,
    data: UpdateWorkspaceMember,
    workspace: Workspace | None = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a workspace member's role.
    
    Requires: workspace:manage permission
    """
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get member
    member = workspace.get_member(user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check permission
    current_member = workspace.get_member(current_user.id)
    if not current_member or not current_member.has_permission(Permission.WORKSPACE_MANAGE):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Update role
    member.role = data.role
    db.commit()
    db.refresh(member)
    
    return {
        "id": member.id,
        "user_id": member.user_id,
        "role": member.role,
        "added_by": member.added_by,
        "added_at": member.added_at.isoformat() if member.added_at else None,
    }


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    user_id: str,
    workspace: Workspace | None = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a member from the workspace.
    
    Requires: workspace:manage permission
    """
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    workspace_service.remove_workspace_member(
        db=db,
        workspace=workspace,
        removed_by=current_user,
        user_id=user_id,
    )
    
    return None


# ---------------------------------------------------------------------------
# Context Endpoint
# ---------------------------------------------------------------------------

@router.get("/{workspace_id}/context")
async def get_workspace_context(
    workspace: Workspace | None = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current user's context within a workspace.
    
    Returns role, permissions, and settings.
    """
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get role
    member = workspace.get_member(current_user.id)
    org_member = workspace.organization.get_member(current_user.id)
    
    role = None
    permissions = []
    
    if member:
        role = member.role
        permissions = member.get_permissions()
    elif org_member:
        role = org_member.role
        from app.core.permissions import get_organization_role_permissions
        permissions = list(get_organization_role_permissions(org_member.role))
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get white-label settings (filtered for client users)
    wl_settings = workspace_service.get_white_label_settings(workspace.organization)
    if role == "client":
        # Clients see limited white-label info
        wl_settings = {
            "enabled": wl_settings.get("enabled"),
            "logo_url": wl_settings.get("logo_url"),
            "primary_color": wl_settings.get("primary_color"),
            "sender_name": wl_settings.get("sender_name"),
        }
    
    return {
        "workspace_id": workspace.id,
        "workspace_name": workspace.name,
        "organization_id": workspace.organization_id,
        "organization_name": workspace.organization.name,
        "role": role,
        "permissions": permissions,
        "white_label": wl_settings,
        "brand_colors": workspace.brand_colors,
        "logo_url": workspace.logo_url,
    }
