import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetchMock = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api", () => ({ apiFetch: apiFetchMock }));

import { useWorkspace } from "@/hooks/useWorkspace";
import {
  registerAuthBoundStateResetter,
  resetAuthBoundState,
} from "@/lib/auth-bound-state";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

const workspaces = [
  {
    id: "workspace-a",
    name: "Workspace A",
    slug: "workspace-a",
    organization_id: "org-a",
    is_active: true,
  },
  {
    id: "workspace-b",
    name: "Workspace B",
    slug: "workspace-b",
    organization_id: "org-a",
    is_active: true,
  },
];

beforeEach(() => {
  apiFetchMock.mockImplementation(async (path: string) => {
    if (path === "/api/v1/workspaces/my") return workspaces;
    if (path === "/api/v1/organizations/my") return [];
    throw new Error(`Unexpected API path: ${path}`);
  });
});

describe("useWorkspace", () => {
  it("uses the canonical transport, ignores legacy global selection, and resets data on switch", async () => {
    localStorage.setItem("currentWorkspaceId", "workspace-b");
    localStorage.setItem("iterra-product-store", "workspace-a private data");
    localStorage.setItem("ittera-radar-prompt", "workspace-a prompt");
    const resetter = vi.fn();
    const unregister = registerAuthBoundStateResetter("workspace-hook-test", resetter);

    const { result } = renderHook(() => useWorkspace());

    await waitFor(() => expect(result.current.currentWorkspace?.id).toBe("workspace-a"));
    expect(apiFetchMock).toHaveBeenCalledWith("/api/v1/workspaces/my");
    expect(apiFetchMock).toHaveBeenCalledWith("/api/v1/organizations/my");
    expect(localStorage.getItem("currentWorkspaceId")).toBeNull();

    act(() => result.current.switchWorkspace("workspace-b"));

    expect(result.current.currentWorkspace?.id).toBe("workspace-b");
    expect(resetter).toHaveBeenCalledWith("workspace");
    expect(localStorage.getItem("iterra-product-store")).toBeNull();
    expect(localStorage.getItem("ittera-radar-prompt")).toBeNull();
    unregister();
  });

  it("fails closed when the workspace list cannot be loaded", async () => {
    apiFetchMock.mockImplementation(async (path: string) => {
      if (path === "/api/v1/workspaces/my") throw new Error("workspace API unavailable");
      return [];
    });

    const { result } = renderHook(() => useWorkspace());

    await waitFor(() => expect(result.current.error).toBe("workspace API unavailable"));
    expect(result.current.workspaces).toEqual([]);
    expect(result.current.currentWorkspace).toBeNull();
  });

  it("ignores deferred workspace data after an auth reset", async () => {
    const workspaceResponse = deferred<typeof workspaces>();
    const organizationResponse = deferred<[]>();
    apiFetchMock.mockImplementation((path: string) => {
      if (path === "/api/v1/workspaces/my") return workspaceResponse.promise;
      if (path === "/api/v1/organizations/my") return organizationResponse.promise;
      throw new Error(`Unexpected API path: ${path}`);
    });

    const { result } = renderHook(() => useWorkspace());
    await waitFor(() => expect(apiFetchMock).toHaveBeenCalledTimes(2));

    act(() => resetAuthBoundState("auth"));
    expect(result.current.isLoading).toBe(false);

    await act(async () => {
      workspaceResponse.resolve(workspaces);
      organizationResponse.resolve([]);
      await Promise.all([workspaceResponse.promise, organizationResponse.promise]);
    });

    expect(result.current.workspaces).toEqual([]);
    expect(result.current.organizations).toEqual([]);
    expect(result.current.currentWorkspace).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("keeps the selected workspace when an older list response resolves after a switch", async () => {
    const { result } = renderHook(() => useWorkspace());
    await waitFor(() => expect(result.current.currentWorkspace?.id).toBe("workspace-a"));

    const staleWorkspaceResponse = deferred<typeof workspaces>();
    apiFetchMock.mockImplementation((path: string) => {
      if (path === "/api/v1/workspaces/my") return staleWorkspaceResponse.promise;
      if (path === "/api/v1/organizations/my") return [];
      throw new Error(`Unexpected API path: ${path}`);
    });

    let reloadPromise!: Promise<void>;
    act(() => {
      reloadPromise = result.current.loadWorkspaces();
    });
    act(() => result.current.switchWorkspace("workspace-b"));

    await act(async () => {
      staleWorkspaceResponse.resolve([workspaces[0]]);
      await reloadPromise;
    });

    expect(result.current.currentWorkspace?.id).toBe("workspace-b");
    expect(result.current.workspaces).toEqual(workspaces);
    expect(result.current.isLoading).toBe(false);
  });
});
