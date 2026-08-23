"""Workspace context and permission dependencies for FastAPI.

Provides dependency functions to:
  - Extract and validate workspace context from requests
  - Check user permissions for workspace access
  - Enforce role-based access control
"""

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.permissions import Permission, get_all_permissions
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.organization import Workspace
from app.models.user import User


async def get_current_workspace(
    request: Request,
    x_workspace_id: str | None = Header(None, alias="X-Workspace-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace | None:
    """Resolve one authoritative workspace and validate the user's access.

    Path-scoped endpoints use ``{workspace_id}`` as their authoritative context.
    Header-scoped endpoints use ``X-Workspace-ID``. When both are present they
    must match; silently selecting one would allow a confused-deputy request.
    Endpoints with neither identifier retain the legacy personal-mode result.
    """
    path_workspace_id = request.path_params.get("workspace_id")
    if path_workspace_id is not None:
        path_workspace_id = str(path_workspace_id)

    if (
        path_workspace_id
        and x_workspace_id
        and path_workspace_id != x_workspace_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context does not match request path",
        )

    workspace_id = path_workspace_id or x_workspace_id
    if not workspace_id:
        request.state.workspace = None
        request.state.workspace_member = None
        request.state.organization_member = None
        request.state.workspace_role = None
        request.state.workspace_permissions = get_all_permissions()
        return None

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    if not workspace.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace is inactive",
        )

    member = workspace.get_member(current_user.id)
    org_member = workspace.organization.get_member(current_user.id)

    if member:
        role = member.role
        permissions = member.get_permissions()
    else:
        # Organization owners/admins inherit workspace access through the
        # organization permission map. Workspace-role permissions must never be
        # applied to an organization role with the same textual name.
        if not org_member or not org_member.has_permission(Permission.WORKSPACE_MANAGE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace",
            )
        role = org_member.role
        permissions = org_member.get_permissions()

    # Membership alone is not sufficient when an explicit deny revokes the
    # baseline view permission. This gate also protects routes that only resolve
    # context and do not ask for a more specific action permission.
    if Permission.WORKSPACE_VIEW not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to workspace",
        )

    request.state.workspace = workspace
    request.state.workspace_member = member
    request.state.organization_member = org_member
    request.state.workspace_role = role
    request.state.workspace_permissions = permissions
    return workspace


async def get_required_current_workspace(
    request: Request,
    x_workspace_id: str = Header(..., alias="X-Workspace-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    """Resolve a header-scoped workspace for routes without personal mode."""
    workspace = await get_current_workspace(
        request=request,
        x_workspace_id=x_workspace_id,
        current_user=current_user,
        db=db,
    )
    if workspace is None:  # Defensive: the required header makes this unreachable.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    return workspace


async def require_workspace_permission(
    permission: str,
    workspace: Workspace | None = Depends(get_current_workspace),
    request: Request = None,
) -> Workspace | None:
    """Require a permission in workspace mode; preserve legacy personal mode."""
    if workspace is None:
        return None

    permissions = getattr(request.state, "workspace_permissions", set())
    if permission not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission}",
        )

    return workspace


class PermissionChecker:
    """Reusable permission checker that permits legacy personal mode."""

    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(
        self,
        workspace: Workspace | None = Depends(get_current_workspace),
        request: Request = None,
    ) -> Workspace | None:
        return await require_workspace_permission(self.permission, workspace, request)


class RequiredWorkspacePermissionChecker:
    """Permission checker for header-scoped routes that require a workspace."""

    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(
        self,
        workspace: Workspace = Depends(get_required_current_workspace),
        request: Request = None,
    ) -> Workspace:
        resolved = await require_workspace_permission(
            self.permission,
            workspace,
            request,
        )
        if resolved is None:  # Defensive: required workspace cannot be personal.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workspace context required",
            )
        return resolved


# Predefined permission checkers for common operations
can_create_content = PermissionChecker(Permission.CONTENT_CREATE)
can_edit_content = PermissionChecker(Permission.CONTENT_EDIT)
can_publish_content = PermissionChecker(Permission.CONTENT_PUBLISH)
can_delete_content = PermissionChecker(Permission.CONTENT_DELETE)
can_view_analytics = PermissionChecker(Permission.ANALYTICS_VIEW)
can_export_analytics = PermissionChecker(Permission.ANALYTICS_EXPORT)
can_use_ai_predict = PermissionChecker(Permission.AI_PREDICT)
can_use_ai_predict_required = RequiredWorkspacePermissionChecker(
    Permission.AI_PREDICT
)
can_use_ai_generate = PermissionChecker(Permission.AI_GENERATE)
can_manage_workspace = RequiredWorkspacePermissionChecker(Permission.WORKSPACE_MANAGE)
can_view_competitors = RequiredWorkspacePermissionChecker(
    Permission.AI_COMPETITOR_ANALYSIS
)
can_create_reports = PermissionChecker(Permission.REPORTS_CREATE)
can_create_reports_required = RequiredWorkspacePermissionChecker(
    Permission.REPORTS_CREATE
)
can_use_whitelabel = RequiredWorkspacePermissionChecker(
    Permission.REPORTS_WHITELABEL
)


def get_workspace_id_header(
    workspace_id: str | None = Header(None, alias="X-Workspace-ID")
) -> str | None:
    """Extract an optional workspace identifier without resolving access."""
    return workspace_id


async def get_workspace_context(
    request: Request,
    workspace_id: str | None = Depends(get_workspace_id_header),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return workspace membership details or an explicit personal context."""
    workspace = await get_current_workspace(
        request=request,
        x_workspace_id=workspace_id,
        current_user=current_user,
        db=db,
    )
    if workspace is None:
        return {
            "workspace": None,
            "member": None,
            "organization_member": None,
            "role": None,
            "permissions": sorted(get_all_permissions()),
            "is_personal": True,
        }

    return {
        "workspace": workspace,
        "member": getattr(request.state, "workspace_member", None),
        "organization_member": getattr(
            request.state,
            "organization_member",
            None,
        ),
        "role": getattr(request.state, "workspace_role", None),
        "permissions": sorted(
            getattr(request.state, "workspace_permissions", set())
        ),
        "is_personal": False,
    }
