"""Permission system for organization and workspace access control.

Defines permission constants, role mappings, and helper functions
for checking access rights across the application.
"""

from enum import Enum


class Permission:
    """
    Permission constants for role-based access control.
    
    Permissions are grouped by functional area:
      - Organization: Billing, member management, settings
      - Workspace: Access and management
      - Content: Create, edit, publish, delete
      - Analytics: View, export, insights
      - AI: Predictions, generation, competitor analysis
      - Automation: Scheduling, workflows, approvals
    """
    
    # Organization permissions
    ORG_MANAGE = "org:manage"  # Full org control
    ORG_VIEW = "org:view"
    BILLING_VIEW = "billing:view"
    BILLING_MANAGE = "billing:manage"
    MEMBERS_INVITE = "members:invite"
    MEMBERS_MANAGE = "members:manage"
    
    # Workspace permissions
    WORKSPACE_CREATE = "workspace:create"
    WORKSPACE_VIEW = "workspace:view"
    WORKSPACE_EDIT = "workspace:edit"
    WORKSPACE_MANAGE = "workspace:manage"  # Full workspace control
    WORKSPACE_DELETE = "workspace:delete"
    
    # Content permissions
    CONTENT_CREATE = "content:create"
    CONTENT_EDIT = "content:edit"
    CONTENT_VIEW = "content:view"
    CONTENT_DELETE = "content:delete"
    CONTENT_PUBLISH = "content:publish"
    CONTENT_SCHEDULE = "content:schedule"
    
    # Analytics permissions
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    ANALYTICS_INSIGHTS = "analytics:insights"
    
    # AI permissions
    AI_PREDICT = "ai:predict"
    AI_GENERATE = "ai:generate"
    AI_COMPETITOR_ANALYSIS = "ai:competitor_analysis"
    AI_VIRAL_SCORE = "ai:viral_score"
    AI_TIMING_PREDICT = "ai:timing_predict"
    
    # Automation permissions
    AUTOMATION_SCHEDULE = "automation:schedule"
    AUTOMATION_APPROVE = "automation:approve"
    AUTOMATION_MANAGE_WORKFLOWS = "automation:manage_workflows"
    
    # Reporting permissions
    REPORTS_VIEW = "reports:view"
    REPORTS_CREATE = "reports:create"
    REPORTS_BRANDED = "reports:branded"
    REPORTS_WHITELABEL = "reports:whitelabel"


# Role to permissions mapping for organization-level roles
ORGANIZATION_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        Permission.ORG_MANAGE,
        Permission.ORG_VIEW,
        Permission.BILLING_VIEW,
        Permission.BILLING_MANAGE,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_MANAGE,
        Permission.WORKSPACE_CREATE,
        Permission.WORKSPACE_VIEW,
        Permission.WORKSPACE_EDIT,
        Permission.WORKSPACE_MANAGE,
        Permission.WORKSPACE_DELETE,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_PUBLISH,
        Permission.CONTENT_SCHEDULE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_INSIGHTS,
        Permission.AI_PREDICT,
        Permission.AI_GENERATE,
        Permission.AI_COMPETITOR_ANALYSIS,
        Permission.AI_VIRAL_SCORE,
        Permission.AI_TIMING_PREDICT,
        Permission.AUTOMATION_SCHEDULE,
        Permission.AUTOMATION_APPROVE,
        Permission.AUTOMATION_MANAGE_WORKFLOWS,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_CREATE,
        Permission.REPORTS_BRANDED,
        Permission.REPORTS_WHITELABEL,
    },
    "admin": {
        Permission.ORG_VIEW,
        Permission.BILLING_VIEW,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_MANAGE,
        Permission.WORKSPACE_CREATE,
        Permission.WORKSPACE_VIEW,
        Permission.WORKSPACE_EDIT,
        Permission.WORKSPACE_MANAGE,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_PUBLISH,
        Permission.CONTENT_SCHEDULE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_INSIGHTS,
        Permission.AI_PREDICT,
        Permission.AI_GENERATE,
        Permission.AI_COMPETITOR_ANALYSIS,
        Permission.AI_VIRAL_SCORE,
        Permission.AI_TIMING_PREDICT,
        Permission.AUTOMATION_SCHEDULE,
        Permission.AUTOMATION_APPROVE,
        Permission.AUTOMATION_MANAGE_WORKFLOWS,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_CREATE,
        Permission.REPORTS_BRANDED,
    },
    "manager": {
        Permission.WORKSPACE_VIEW,
        Permission.WORKSPACE_EDIT,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_PUBLISH,
        Permission.CONTENT_SCHEDULE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_INSIGHTS,
        Permission.AI_PREDICT,
        Permission.AI_GENERATE,
        Permission.AI_COMPETITOR_ANALYSIS,
        Permission.AI_VIRAL_SCORE,
        Permission.AI_TIMING_PREDICT,
        Permission.AUTOMATION_SCHEDULE,
        Permission.AUTOMATION_APPROVE,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_CREATE,
    },
    "editor": {
        Permission.WORKSPACE_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_SCHEDULE,
        Permission.ANALYTICS_VIEW,
        Permission.AI_GENERATE,
        Permission.AI_TIMING_PREDICT,
        Permission.REPORTS_VIEW,
    },
    "viewer": {
        Permission.WORKSPACE_VIEW,
        Permission.CONTENT_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.REPORTS_VIEW,
    },
}

# Role to permissions mapping for workspace-level roles
WORKSPACE_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "manager": {
        Permission.WORKSPACE_VIEW,
        Permission.WORKSPACE_EDIT,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_PUBLISH,
        Permission.CONTENT_SCHEDULE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_INSIGHTS,
        Permission.AI_PREDICT,
        Permission.AI_GENERATE,
        Permission.AI_COMPETITOR_ANALYSIS,
        Permission.AI_VIRAL_SCORE,
        Permission.AI_TIMING_PREDICT,
        Permission.AUTOMATION_SCHEDULE,
        Permission.AUTOMATION_APPROVE,
        Permission.AUTOMATION_MANAGE_WORKFLOWS,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_CREATE,
    },
    "editor": {
        Permission.WORKSPACE_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_SCHEDULE,
        Permission.ANALYTICS_VIEW,
        Permission.AI_GENERATE,
        Permission.AI_TIMING_PREDICT,
        Permission.REPORTS_VIEW,
    },
    "viewer": {
        Permission.WORKSPACE_VIEW,
        Permission.CONTENT_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.REPORTS_VIEW,
    },
    "client": {
        # External client access - view only
        Permission.WORKSPACE_VIEW,
        Permission.CONTENT_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.REPORTS_VIEW,
    },
}


def get_organization_role_permissions(role: str) -> set[str]:
    """Get all permissions for an organization role."""
    return ORGANIZATION_ROLE_PERMISSIONS.get(role, set())


def get_workspace_role_permissions(role: str) -> set[str]:
    """Get all permissions for a workspace role."""
    return WORKSPACE_ROLE_PERMISSIONS.get(role, set())


def has_organization_permission(user_role: str, permission: str) -> bool:
    """Check if an organization role has a specific permission."""
    return permission in get_organization_role_permissions(user_role)


def has_workspace_permission(user_role: str, permission: str) -> bool:
    """Check if a workspace role has a specific permission."""
    return permission in get_workspace_role_permissions(user_role)


def get_role_hierarchy(role: str) -> int:
    """
    Get numeric hierarchy level for a role.
    Higher numbers = more permissions.
    """
    hierarchy = {
        "owner": 100,
        "admin": 90,
        "manager": 70,
        "editor": 50,
        "viewer": 30,
        "client": 20,
    }
    return hierarchy.get(role, 0)


def can_manage_role(manager_role: str, target_role: str, is_org_level: bool = True) -> bool:
    """
    Check if a user with manager_role can manage (invite/edit/remove) 
    a user with target_role.
    """
    manager_level = get_role_hierarchy(manager_role)
    target_level = get_role_hierarchy(target_role)
    
    # Can only manage roles below your own
    return manager_level > target_level


# Valid organization roles
VALID_ORGANIZATION_ROLES = set(ORGANIZATION_ROLE_PERMISSIONS.keys())

# Valid workspace roles
VALID_WORKSPACE_ROLES = set(WORKSPACE_ROLE_PERMISSIONS.keys())


def validate_organization_role(role: str) -> bool:
    """Validate if a string is a valid organization role."""
    return role in VALID_ORGANIZATION_ROLES


def validate_workspace_role(role: str) -> bool:
    """Validate if a string is a valid workspace role."""
    return role in VALID_WORKSPACE_ROLES
