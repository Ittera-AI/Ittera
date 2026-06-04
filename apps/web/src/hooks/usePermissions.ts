"use client";

import { useCallback, useMemo, type ReactNode } from "react";

// Permission constants matching the backend
export const Permissions = {
  // Organization
  ORG_MANAGE: "org:manage",
  ORG_VIEW: "org:view",
  BILLING_VIEW: "billing:view",
  BILLING_MANAGE: "billing:manage",
  MEMBERS_INVITE: "members:invite",
  MEMBERS_MANAGE: "members:manage",

  // Workspace
  WORKSPACE_CREATE: "workspace:create",
  WORKSPACE_VIEW: "workspace:view",
  WORKSPACE_EDIT: "workspace:edit",
  WORKSPACE_MANAGE: "workspace:manage",
  WORKSPACE_DELETE: "workspace:delete",

  // Content
  CONTENT_CREATE: "content:create",
  CONTENT_EDIT: "content:edit",
  CONTENT_VIEW: "content:view",
  CONTENT_DELETE: "content:delete",
  CONTENT_PUBLISH: "content:publish",
  CONTENT_SCHEDULE: "content:schedule",

  // Analytics
  ANALYTICS_VIEW: "analytics:view",
  ANALYTICS_EXPORT: "analytics:export",
  ANALYTICS_INSIGHTS: "analytics:insights",

  // AI
  AI_PREDICT: "ai:predict",
  AI_GENERATE: "ai:generate",
  AI_COMPETITOR_ANALYSIS: "ai:competitor_analysis",
  AI_VIRAL_SCORE: "ai:viral_score",
  AI_TIMING_PREDICT: "ai:timing_predict",

  // Automation
  AUTOMATION_SCHEDULE: "automation:schedule",
  AUTOMATION_APPROVE: "automation:approve",
  AUTOMATION_MANAGE_WORKFLOWS: "automation:manage_workflows",

  // Reports
  REPORTS_VIEW: "reports:view",
  REPORTS_CREATE: "reports:create",
  REPORTS_BRANDED: "reports:branded",
  REPORTS_WHITELABEL: "reports:whitelabel",
} as const;

type Permission = (typeof Permissions)[keyof typeof Permissions];

// Role definitions
const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  owner: Object.values(Permissions),
  admin: [
    Permissions.ORG_VIEW,
    Permissions.BILLING_VIEW,
    Permissions.MEMBERS_INVITE,
    Permissions.MEMBERS_MANAGE,
    Permissions.WORKSPACE_CREATE,
    Permissions.WORKSPACE_VIEW,
    Permissions.WORKSPACE_EDIT,
    Permissions.WORKSPACE_MANAGE,
    Permissions.CONTENT_CREATE,
    Permissions.CONTENT_EDIT,
    Permissions.CONTENT_VIEW,
    Permissions.CONTENT_DELETE,
    Permissions.CONTENT_PUBLISH,
    Permissions.CONTENT_SCHEDULE,
    Permissions.ANALYTICS_VIEW,
    Permissions.ANALYTICS_EXPORT,
    Permissions.ANALYTICS_INSIGHTS,
    Permissions.AI_PREDICT,
    Permissions.AI_GENERATE,
    Permissions.AI_COMPETITOR_ANALYSIS,
    Permissions.AI_VIRAL_SCORE,
    Permissions.AI_TIMING_PREDICT,
    Permissions.AUTOMATION_SCHEDULE,
    Permissions.AUTOMATION_APPROVE,
    Permissions.AUTOMATION_MANAGE_WORKFLOWS,
    Permissions.REPORTS_VIEW,
    Permissions.REPORTS_CREATE,
    Permissions.REPORTS_BRANDED,
  ],
  manager: [
    Permissions.WORKSPACE_VIEW,
    Permissions.WORKSPACE_EDIT,
    Permissions.CONTENT_CREATE,
    Permissions.CONTENT_EDIT,
    Permissions.CONTENT_VIEW,
    Permissions.CONTENT_DELETE,
    Permissions.CONTENT_PUBLISH,
    Permissions.CONTENT_SCHEDULE,
    Permissions.ANALYTICS_VIEW,
    Permissions.ANALYTICS_EXPORT,
    Permissions.ANALYTICS_INSIGHTS,
    Permissions.AI_PREDICT,
    Permissions.AI_GENERATE,
    Permissions.AI_COMPETITOR_ANALYSIS,
    Permissions.AI_VIRAL_SCORE,
    Permissions.AI_TIMING_PREDICT,
    Permissions.AUTOMATION_SCHEDULE,
    Permissions.AUTOMATION_APPROVE,
    Permissions.REPORTS_VIEW,
    Permissions.REPORTS_CREATE,
  ],
  editor: [
    Permissions.WORKSPACE_VIEW,
    Permissions.CONTENT_CREATE,
    Permissions.CONTENT_EDIT,
    Permissions.CONTENT_VIEW,
    Permissions.CONTENT_SCHEDULE,
    Permissions.ANALYTICS_VIEW,
    Permissions.AI_GENERATE,
    Permissions.AI_TIMING_PREDICT,
    Permissions.REPORTS_VIEW,
  ],
  viewer: [
    Permissions.WORKSPACE_VIEW,
    Permissions.CONTENT_VIEW,
    Permissions.ANALYTICS_VIEW,
    Permissions.REPORTS_VIEW,
  ],
};

interface UsePermissionsProps {
  role: string | null | undefined;
  customPermissions?: Permission[];
}

export function usePermissions({ role, customPermissions = [] }: UsePermissionsProps) {
  // Get all permissions for the role
  const rolePermissions = useMemo(() => {
    if (!role) return [];
    return ROLE_PERMISSIONS[role] || [];
  }, [role]);

  // Combined permissions (role + custom)
  const allPermissions = useMemo(() => {
    return new Set([...rolePermissions, ...customPermissions]);
  }, [rolePermissions, customPermissions]);

  // Check if has permission
  const hasPermission = useCallback(
    (permission: Permission) => {
      return allPermissions.has(permission);
    },
    [allPermissions]
  );

  // Check multiple permissions (all must match)
  const hasAllPermissions = useCallback(
    (permissions: Permission[]) => {
      return permissions.every((p) => allPermissions.has(p));
    },
    [allPermissions]
  );

  // Check multiple permissions (any can match)
  const hasAnyPermission = useCallback(
    (permissions: Permission[]) => {
      return permissions.some((p) => allPermissions.has(p));
    },
    [allPermissions]
  );

  // Feature check helpers
  const canManageOrganization = useCallback(
    () => hasPermission(Permissions.ORG_MANAGE),
    [hasPermission]
  );

  const canManageWorkspace = useCallback(
    () => hasPermission(Permissions.WORKSPACE_MANAGE),
    [hasPermission]
  );

  const canPublishContent = useCallback(
    () => hasPermission(Permissions.CONTENT_PUBLISH),
    [hasPermission]
  );

  const canCreateContent = useCallback(
    () => hasPermission(Permissions.CONTENT_CREATE),
    [hasPermission]
  );

  const canViewAnalytics = useCallback(
    () => hasPermission(Permissions.ANALYTICS_VIEW),
    [hasPermission]
  );

  const canExportAnalytics = useCallback(
    () => hasPermission(Permissions.ANALYTICS_EXPORT),
    [hasPermission]
  );

  const canUseAIPredictions = useCallback(
    () => hasPermission(Permissions.AI_PREDICT),
    [hasPermission]
  );

  const canUseAIGeneration = useCallback(
    () => hasPermission(Permissions.AI_GENERATE),
    [hasPermission]
  );

  const canUseCompetitorAnalysis = useCallback(
    () => hasPermission(Permissions.AI_COMPETITOR_ANALYSIS),
    [hasPermission]
  );

  const canCreateReports = useCallback(
    () => hasPermission(Permissions.REPORTS_CREATE),
    [hasPermission]
  );

  const canUseWhiteLabel = useCallback(
    () => hasPermission(Permissions.REPORTS_WHITELABEL),
    [hasPermission]
  );

  const canManageWorkflows = useCallback(
    () => hasPermission(Permissions.AUTOMATION_MANAGE_WORKFLOWS),
    [hasPermission]
  );

  return {
    // Direct permission check
    hasPermission,
    hasAllPermissions,
    hasAnyPermission,

    // Permission list
    permissions: Array.from(allPermissions),

    // Feature helpers
    canManageOrganization,
    canManageWorkspace,
    canPublishContent,
    canCreateContent,
    canViewAnalytics,
    canExportAnalytics,
    canUseAIPredictions,
    canUseAIGeneration,
    canUseCompetitorAnalysis,
    canCreateReports,
    canUseWhiteLabel,
    canManageWorkflows,

    // Role info
    role,
    isOwner: role === "owner",
    isAdmin: role === "admin" || role === "owner",
    isManager: role === "manager" || role === "admin" || role === "owner",
    isEditor: role === "editor" || role === "manager" || role === "admin" || role === "owner",
  };
}

// Component wrapper for permission-based rendering
interface PermissionGateProps {
  permission: Permission;
  permissions?: Permission[];
  requireAll?: boolean;
  role?: string;
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGate({
  permission,
  permissions = [],
  requireAll = false,
  role,
  children,
  fallback = null,
}: PermissionGateProps) {
  const perms = useMemo(() => {
    if (permission) return [permission];
    return permissions;
  }, [permission, permissions]);

  const { hasAllPermissions, hasAnyPermission } = usePermissions({ role });

  const hasAccess = requireAll
    ? hasAllPermissions(perms)
    : hasAnyPermission(perms);

  if (!hasAccess) {
    return fallback;
  }

  return children;
}
