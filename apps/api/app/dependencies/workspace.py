"""Workspace context and permission dependencies for FastAPI.

Provides dependency functions to:
  - Extract and validate workspace context from requests
  - Check user permissions for workspace access
  - Enforce role-based access control
"""

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.permissions import Permission, has_workspace_permission
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.organization import Workspace, WorkspaceMember
from app.models.user import User


async def get_current_workspace(
    request: Request,
    x_workspace_id: str | None = Header(None, alias="X-Workspace-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace | None:
    """
    Extract and validate workspace context from request.
    
    Reads X-Workspace-ID header and validates:
      1. Workspace exists
      2. User has access to workspace
      3. Workspace is active
    
    If no workspace_id provided, returns None (personal/single-user mode).
    
    Args:
        request: FastAPI request object
        workspace_id: Workspace ID from X-Workspace-ID header
        current_user: Authenticated user from auth dependency
        db: Database session
        
    Returns:
        Workspace object or None (for personal mode)
        
    Raises:
        HTTPException: 404 if workspace not found
        HTTPException: 403 if user lacks access
    """
    # No workspace header - personal mode
    if not x_workspace_id:
        return None
    
    # Validate workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == x_workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    
    # Check if workspace is active
    if not workspace.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace is inactive",
        )
    
    # Check workspace membership
    member = workspace.get_member(current_user.id)
    if not member:
        # Check if user is org member (for admin access)
        org_member = workspace.organization.get_member(current_user.id)
        if not org_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace",
            )
        
        # Org admins can access all workspaces
        if not has_workspace_permission(org_member.role, Permission.WORKSPACE_MANAGE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace",
            )
    
    # Store in request state for downstream use
    request.state.workspace = workspace
    if member:
        request.state.workspace_role = member.role
        request.state.workspace_member = member
    else:
        # Org-level access
        request.state.workspace_role = org_member.role
        request.state.workspace_member = None
    
    return workspace


async def require_workspace_permission(
    permission: str,
    workspace: Workspace | None = Depends(get_current_workspace),
    request: Request = None,
) -> Workspace | None:
    """
    Dependency factory to require specific permission.
    
    Usage:
        @router.post("/posts")
        async def create_post(
            workspace: Workspace = Depends(require_workspace_permission(Permission.CONTENT_CREATE))
        ):
            ...
    
    Args:
        permission: Required permission constant
        workspace: Workspace from get_current_workspace
        request: FastAPI request
        
    Returns:
        Workspace if permission granted
        
    Raises:
        HTTPException: 403 if permission denied
    """
    # Personal mode - allow all permissions
    if workspace is None:
        return None
    
    # Get role from request state
    role = getattr(request.state, "workspace_role", None)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace context required",
        )
    
    # Check permission
    if not has_workspace_permission(role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission}",
        )
    
    return workspace


class PermissionChecker:
    """
    Reusable permission checker for route dependencies.
    
    Usage:
        require_create = PermissionChecker(Permission.CONTENT_CREATE)
        require_publish = PermissionChecker(Permission.CONTENT_PUBLISH)
        
        @router.post("/drafts")
        async def create_draft(
            workspace: Workspace = Depends(require_create)
        ):
            ...
    """
    
    def __init__(self, permission: str):
        self.permission = permission
    
    async def __call__(
        self,
        workspace: Workspace | None = Depends(get_current_workspace),
        request: Request = None,
    ) -> Workspace | None:
        return await require_workspace_permission(self.permission, workspace, request)


# Predefined permission checkers for common operations
can_create_content = PermissionChecker(Permission.CONTENT_CREATE)
can_edit_content = PermissionChecker(Permission.CONTENT_EDIT)
can_publish_content = PermissionChecker(Permission.CONTENT_PUBLISH)
can_delete_content = PermissionChecker(Permission.CONTENT_DELETE)
can_view_analytics = PermissionChecker(Permission.ANALYTICS_VIEW)
can_export_analytics = PermissionChecker(Permission.ANALYTICS_EXPORT)
can_use_ai_predict = PermissionChecker(Permission.AI_PREDICT)
can_use_ai_generate = PermissionChecker(Permission.AI_GENERATE)
can_manage_workspace = PermissionChecker(Permission.WORKSPACE_MANAGE)
can_view_competitors = PermissionChecker(Permission.AI_COMPETITOR_ANALYSIS)
can_create_reports = PermissionChecker(Permission.REPORTS_CREATE)
can_use_whitelabel = PermissionChecker(Permission.REPORTS_WHITELABEL)


def get_workspace_id_header(
    workspace_id: str | None = Header(None, alias="X-Workspace-ID")
) -> str | None:
    """
    Simple dependency to extract workspace ID from header.
    
    Use when you just need the ID without full validation.
    """
    return workspace_id


async def get_workspace_context(
    request: Request,
    workspace_id: str | None = Depends(get_workspace_id_header),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get full workspace context including membership details.
    
    Returns a dictionary with:
      - workspace: Workspace object or None
      - member: WorkspaceMember or None
      - role: User's role in workspace
      - permissions: List of granted permissions
      
    Useful for endpoints that need detailed context.
    """
    if not workspace_id:
        return {
            "workspace": None,
            "member": None,
            "role": None,
            "permissions": list(Permission.__dict__.values()),  # All permissions in personal mode
            "is_personal": True,
        }
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    
    member = workspace.get_member(current_user.id)
    org_member = workspace.organization.get_member(current_user.id)
    
    if not member and not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to workspace",
        )
    
    # Determine effective role and permissions
    if member:
        role = member.role
        permissions = member.get_permissions()
    else:
        # Org-level access
        role = org_member.role
        # Org admins get workspace manage permissions
        from app.core.permissions import get_organization_role_permissions
        permissions = get_organization_role_permissions(role)
    
    return {
        "workspace": workspace,
        "member": member,
        "organization_member": org_member,
        "role": role,
        "permissions": permissions,
        "is_personal": False,
    }
