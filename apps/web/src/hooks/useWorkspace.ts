"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  AUTH_BOUND_STATE_RESET_EVENT,
  resetAuthBoundState,
  type AuthBoundStateScope,
} from "@/lib/auth-bound-state";
import { apiFetch } from "@/lib/api";

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

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function staleWorkspaceRequest() {
  const error = new Error("Workspace request crossed an auth or workspace boundary");
  error.name = "AbortError";
  return error;
}

export function useWorkspace() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestGenerationRef = useRef(0);

  const loadWorkspaces = useCallback(async () => {
    const requestGeneration = requestGenerationRef.current;
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiFetch<Workspace[]>("/api/v1/workspaces/my");
      if (requestGeneration !== requestGenerationRef.current) return;

      setWorkspaces(data);
      setCurrentWorkspace((selected) => {
        if (selected) {
          const stillAuthorized = data.find((workspace) => workspace.id === selected.id);
          if (stillAuthorized) return stillAuthorized;
        }
        return data.find((workspace) => workspace.is_active) ?? data[0] ?? null;
      });
    } catch (loadError) {
      if (requestGeneration !== requestGenerationRef.current) return;

      setWorkspaces([]);
      setCurrentWorkspace(null);
      setError(errorMessage(loadError, "Failed to load workspaces"));
    } finally {
      if (requestGeneration === requestGenerationRef.current) setIsLoading(false);
    }
  }, []);

  const loadOrganizations = useCallback(async () => {
    const requestGeneration = requestGenerationRef.current;

    try {
      const data = await apiFetch<Organization[]>("/api/v1/organizations/my");
      if (requestGeneration !== requestGenerationRef.current) return;
      setOrganizations(data);
    } catch (loadError) {
      if (requestGeneration !== requestGenerationRef.current) return;
      setOrganizations([]);
      setError((current) => current ?? errorMessage(loadError, "Failed to load organizations"));
    }
  }, []);

  const switchWorkspace = useCallback(
    (workspaceId: string) => {
      const workspace = workspaces.find((candidate) => candidate.id === workspaceId);
      if (!workspace || workspace.id === currentWorkspace?.id) return;

      // B1 containment: invalidate every user/workspace-derived cache before exposing
      // the newly selected workspace. Shared workspace tenancy is implemented in B2.
      resetAuthBoundState("workspace");
      setCurrentWorkspace(workspace);
    },
    [currentWorkspace?.id, workspaces],
  );

  const createWorkspace = useCallback(
    async (data: {
      organization_id: string;
      name: string;
      slug: string;
      client_name?: string;
      client_email?: string;
    }) => {
      const requestGeneration = requestGenerationRef.current;
      setIsLoading(true);
      setError(null);

      try {
        const workspace = await apiFetch<Workspace>(
          `/api/v1/organizations/${encodeURIComponent(data.organization_id)}/workspaces`,
          {
            method: "POST",
            body: JSON.stringify(data),
          },
        );
        if (requestGeneration !== requestGenerationRef.current) {
          throw staleWorkspaceRequest();
        }

        await loadWorkspaces();
        if (requestGeneration !== requestGenerationRef.current) {
          throw staleWorkspaceRequest();
        }
        return workspace;
      } catch (createError) {
        if (requestGeneration === requestGenerationRef.current) {
          setError(errorMessage(createError, "Failed to create workspace"));
        }
        throw createError;
      } finally {
        if (requestGeneration === requestGenerationRef.current) setIsLoading(false);
      }
    },
    [loadWorkspaces],
  );

  const createOrganization = useCallback(
    async (data: { name: string; slug: string; plan_type?: string }) => {
      const requestGeneration = requestGenerationRef.current;
      setIsLoading(true);
      setError(null);

      try {
        const organization = await apiFetch<Organization>("/api/v1/organizations", {
          method: "POST",
          body: JSON.stringify(data),
        });
        if (requestGeneration !== requestGenerationRef.current) {
          throw staleWorkspaceRequest();
        }

        await loadOrganizations();
        if (requestGeneration !== requestGenerationRef.current) {
          throw staleWorkspaceRequest();
        }
        return organization;
      } catch (createError) {
        if (requestGeneration === requestGenerationRef.current) {
          setError(errorMessage(createError, "Failed to create organization"));
        }
        throw createError;
      } finally {
        if (requestGeneration === requestGenerationRef.current) setIsLoading(false);
      }
    },
    [loadOrganizations],
  );

  const getWorkspaceHeaders = useCallback(() => {
    if (!currentWorkspace) return {};
    return { "X-Workspace-ID": currentWorkspace.id };
  }, [currentWorkspace]);

  useEffect(() => {
    const handleReset = (event: Event) => {
      const scope = (event as CustomEvent<AuthBoundStateScope>).detail;
      requestGenerationRef.current += 1;
      setIsLoading(false);
      setError(null);

      if (scope === "auth") {
        setWorkspaces([]);
        setOrganizations([]);
        setCurrentWorkspace(null);
      }
    };

    window.addEventListener(AUTH_BOUND_STATE_RESET_EVENT, handleReset);

    // Remove the legacy global selector. B1 keeps selection in memory until B2 can
    // scope it to a verified principal/workspace contract.
    localStorage.removeItem("currentWorkspaceId");
    void loadWorkspaces();
    void loadOrganizations();

    return () => {
      requestGenerationRef.current += 1;
      window.removeEventListener(AUTH_BOUND_STATE_RESET_EVENT, handleReset);
    };
  }, [loadOrganizations, loadWorkspaces]);

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
