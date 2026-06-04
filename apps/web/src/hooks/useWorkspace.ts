"use client";

import { useState, useCallback, useEffect } from "react";

interface Workspace {
  id: string;
  name: string;
  slug: string;
  organization_id: string;
  organization_name?: string;
  client_name?: string;
  client_email?: string;
  is_active: boolean;
  brand_colors?: Record<string, string>;
  logo_url?: string;
  my_role?: string;
  stats?: {
    posts_count: number;
    drafts_count: number;
    content_plans_count: number;
    competitors_count: number;
    members_count: number;
  };
}

interface Organization {
  id: string;
  name: string;
  slug: string;
  plan_type: string;
  white_label_settings?: {
    enabled?: boolean;
    primary_color?: string;
    logo_url?: string;
  };
}

export function useWorkspace() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load my workspaces
  const loadWorkspaces = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/v1/workspaces/my", {
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load workspaces");
      }

      const data = await response.json();
      setWorkspaces(data);

      // Set first active workspace as current if none selected
      if (!currentWorkspace && data.length > 0) {
        const active = data.find((w: Workspace) => w.is_active) || data[0];
        setCurrentWorkspace(active);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workspaces");
    } finally {
      setIsLoading(false);
    }
  }, [currentWorkspace]);

  // Load my organizations
  const loadOrganizations = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/organizations/my", {
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load organizations");
      }

      const data = await response.json();
      setOrganizations(data);
    } catch (err) {
      console.error("Failed to load organizations:", err);
    }
  }, []);

  // Switch workspace
  const switchWorkspace = useCallback((workspaceId: string) => {
    const workspace = workspaces.find((w) => w.id === workspaceId);
    if (workspace) {
      setCurrentWorkspace(workspace);
      // Store in localStorage for persistence
      localStorage.setItem("currentWorkspaceId", workspaceId);
    }
  }, [workspaces]);

  // Create workspace
  const createWorkspace = useCallback(
    async (data: {
      organization_id: string;
      name: string;
      slug: string;
      client_name?: string;
      client_email?: string;
    }) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/v1/organizations/${data.organization_id}/workspaces`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
          }
        );

        if (!response.ok) {
          throw new Error("Failed to create workspace");
        }

        const workspace = await response.json();
        await loadWorkspaces();
        return workspace;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create workspace");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [loadWorkspaces]
  );

  // Create organization
  const createOrganization = useCallback(
    async (data: { name: string; slug: string; plan_type?: string }) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch("/api/v1/organizations", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          throw new Error("Failed to create organization");
        }

        const org = await response.json();
        await loadOrganizations();
        return org;
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to create organization"
        );
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [loadOrganizations]
  );

  // Get workspace context for API calls
  const getWorkspaceHeaders = useCallback(() => {
    if (!currentWorkspace) return {};
    return {
      "X-Workspace-ID": currentWorkspace.id,
    };
  }, [currentWorkspace]);

  // Initial load
  useEffect(() => {
    loadWorkspaces();
    loadOrganizations();

    // Restore from localStorage
    const savedId = localStorage.getItem("currentWorkspaceId");
    if (savedId) {
      const saved = workspaces.find((w) => w.id === savedId);
      if (saved) {
        setCurrentWorkspace(saved);
      }
    }
  }, []);

  return {
    workspaces,
    organizations,
    currentWorkspace,
    isLoading,
    error,
    loadWorkspaces,
    loadOrganizations,
    switchWorkspace,
    createWorkspace,
    createOrganization,
    getWorkspaceHeaders,
  };
}
