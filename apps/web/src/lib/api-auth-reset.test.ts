import { beforeEach, describe, expect, it, vi } from "vitest";

const authMocks = vi.hoisted(() => ({
  getSession: vi.fn(),
  refreshSession: vi.fn(),
  signOut: vi.fn(),
  clearStoredSupabaseSessions: vi.fn(),
}));

vi.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      getSession: authMocks.getSession,
      refreshSession: authMocks.refreshSession,
      signOut: authMocks.signOut,
    },
  },
  clearStoredSupabaseSessions: authMocks.clearStoredSupabaseSessions,
}));

import { resetAuthBoundState } from "@/lib/auth-bound-state";
import { ApiError, apiFetch } from "@/lib/api";

beforeEach(() => {
  authMocks.getSession.mockResolvedValue({ data: { session: null } });
  authMocks.refreshSession.mockResolvedValue({ data: { session: null }, error: null });
  authMocks.signOut.mockResolvedValue({ error: null });
});

describe("apiFetch terminal 401 handling", () => {
  it("clears auth-bound client state and the backend cookie session", async () => {
    localStorage.setItem("iterra-product-store", "private product data");
    localStorage.setItem("currentWorkspaceId", "workspace-a");
    localStorage.setItem("ittera-theme", "dark");
    sessionStorage.setItem("skipped_onboarding", "true");

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Expired" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch("/api/v1/private")).rejects.toEqual(
      expect.objectContaining<Partial<ApiError>>({ status: 401, message: "Expired" }),
    );

    expect(authMocks.signOut).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringMatching(/\/api\/v1\/auth\/logout$/),
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
    expect(localStorage.getItem("iterra-product-store")).toBeNull();
    expect(localStorage.getItem("currentWorkspaceId")).toBeNull();
    expect(sessionStorage.getItem("skipped_onboarding")).toBeNull();
    expect(localStorage.getItem("ittera-theme")).toBe("dark");
  });

  it("aborts an in-flight request when auth-bound state resets", async () => {
    let requestSignal: AbortSignal | undefined;
    const fetchMock = vi.fn((_url: string | URL | Request, init?: RequestInit) => {
      requestSignal = init?.signal ?? undefined;
      return new Promise<Response>((_resolve, reject) => {
        const rejectAsAborted = () =>
          reject(requestSignal?.reason ?? new DOMException("Aborted", "AbortError"));
        if (requestSignal?.aborted) {
          rejectAsAborted();
          return;
        }
        requestSignal?.addEventListener("abort", rejectAsAborted, { once: true });
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const request = apiFetch("/api/v1/private");
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());

    resetAuthBoundState("auth");

    await expect(request).rejects.toMatchObject({ name: "AbortError" });
    expect(requestSignal?.aborted).toBe(true);
  });
});
