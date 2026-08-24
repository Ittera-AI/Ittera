import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { Session } from "@supabase/supabase-js";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  authStateHandler: null as ((event: string, session: Session | null) => void) | null,
  apiLogout: vi.fn(),
  getSession: vi.fn(),
  myStatus: vi.fn(),
  signOut: vi.fn(),
  unsubscribe: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  api: {
    auth: { logout: mocks.apiLogout },
    waitlist: { myStatus: mocks.myStatus },
  },
}));

vi.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      getSession: mocks.getSession,
      onAuthStateChange: vi.fn((handler) => {
        mocks.authStateHandler = handler;
        return { data: { subscription: { unsubscribe: mocks.unsubscribe } } };
      }),
      signOut: mocks.signOut,
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signInWithOAuth: vi.fn(),
      resetPasswordForEmail: vi.fn(),
    },
  },
  clearStoredSupabaseSessions: vi.fn(),
}));

import { AuthProvider, useAuth } from "@/context/AuthContext";
import { registerAuthBoundStateResetter } from "@/lib/auth-bound-state";

function AuthHarness() {
  const {
    hasWorkspaceAccess,
    refreshWorkspaceAccess,
    sessionLoading,
    signOut,
    user,
    waitlistPosition,
    workspaceAccessChecked,
    workspaceAccessLoading,
  } = useAuth();
  return (
    <div>
      <span data-testid="principal">{sessionLoading ? "loading" : user?.email ?? "signed-out"}</span>
      <span data-testid="access-approved">{String(hasWorkspaceAccess)}</span>
      <span data-testid="access-checked">{String(workspaceAccessChecked)}</span>
      <span data-testid="access-loading">{String(workspaceAccessLoading)}</span>
      <span data-testid="waitlist-position">{waitlistPosition ?? "none"}</span>
      <button onClick={() => void refreshWorkspaceAccess()}>Refresh access</button>
      <button onClick={() => void signOut()}>Sign out</button>
    </div>
  );
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function sessionFor(id: string, email: string): Session {
  return {
    access_token: "test-access-token",
    refresh_token: "test-refresh-token",
    expires_in: 3600,
    token_type: "bearer",
    user: {
      id,
      aud: "authenticated",
      role: "authenticated",
      email,
      app_metadata: {},
      user_metadata: { full_name: email.split("@")[0] },
      created_at: new Date(0).toISOString(),
    },
  } as Session;
}

beforeEach(() => {
  mocks.authStateHandler = null;
  mocks.getSession.mockReset();
  mocks.signOut.mockReset();
  mocks.apiLogout.mockReset();
  mocks.myStatus.mockReset();
  mocks.getSession.mockResolvedValue({ data: { session: null } });
  mocks.signOut.mockResolvedValue({ error: null });
  mocks.apiLogout.mockResolvedValue(undefined);
  mocks.myStatus.mockResolvedValue({ access_approved: false, position: 1 });
});

describe("AuthProvider state containment", () => {
  it("logs out both sessions and clears auth-bound state without clearing theme", async () => {
    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );
    await screen.findByText("signed-out");

    localStorage.setItem("iterra-product-store", "private product data");
    localStorage.setItem("currentWorkspaceId", "workspace-a");
    localStorage.setItem("ittera-theme", "dark");
    sessionStorage.setItem("skipped_onboarding", "true");

    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));

    await waitFor(() => expect(mocks.signOut).toHaveBeenCalledOnce());
    expect(mocks.apiLogout).toHaveBeenCalledOnce();
    expect(localStorage.getItem("iterra-product-store")).toBeNull();
    expect(localStorage.getItem("currentWorkspaceId")).toBeNull();
    expect(sessionStorage.getItem("skipped_onboarding")).toBeNull();
    expect(localStorage.getItem("ittera-theme")).toBe("dark");
  });

  it("resets client state before replacing one signed-in principal with another", async () => {
    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );
    await screen.findByText("signed-out");
    expect(mocks.authStateHandler).not.toBeNull();

    act(() => mocks.authStateHandler?.("SIGNED_IN", sessionFor("user-a", "a@example.test")));
    await screen.findByText("a@example.test");

    localStorage.setItem("iterra-product-store", "user-a data");
    localStorage.setItem("currentWorkspaceId", "workspace-a");
    const resetter = vi.fn();
    const unregister = registerAuthBoundStateResetter("principal-switch-test", resetter);

    act(() => mocks.authStateHandler?.("SIGNED_IN", sessionFor("user-b", "b@example.test")));
    await screen.findByText("b@example.test");

    expect(resetter).toHaveBeenCalledWith("auth");
    expect(localStorage.getItem("iterra-product-store")).toBeNull();
    expect(localStorage.getItem("currentWorkspaceId")).toBeNull();
    unregister();
  });

  it("clears an approved principal before exposing a replacement principal", async () => {
    mocks.myStatus.mockResolvedValueOnce({ access_approved: true, position: 4 });

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );
    await screen.findByText("signed-out");

    act(() => mocks.authStateHandler?.("SIGNED_IN", sessionFor("user-a", "a@example.test")));
    await screen.findByText("a@example.test");
    await waitFor(() => expect(screen.getByTestId("access-approved")).toHaveTextContent("true"));

    const pendingB = deferred<{ access_approved: boolean; position: number | null }>();
    mocks.myStatus.mockReturnValueOnce(pendingB.promise);

    act(() => mocks.authStateHandler?.("SIGNED_IN", sessionFor("user-b", "b@example.test")));
    await screen.findByText("b@example.test");

    expect(screen.getByTestId("access-approved")).toHaveTextContent("false");
    expect(screen.getByTestId("access-checked")).toHaveTextContent("false");
    expect(screen.getByTestId("waitlist-position")).toHaveTextContent("none");

    await act(async () => {
      pendingB.resolve({ access_approved: false, position: 12 });
      await pendingB.promise;
    });
    await waitFor(() => expect(screen.getByTestId("access-checked")).toHaveTextContent("true"));
    expect(screen.getByTestId("access-approved")).toHaveTextContent("false");
    expect(screen.getByTestId("waitlist-position")).toHaveTextContent("12");
  });

  it("ignores an older principal's access response when it resolves last", async () => {
    mocks.myStatus.mockResolvedValueOnce({ access_approved: true, position: 3 });

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );
    await screen.findByText("signed-out");

    act(() => mocks.authStateHandler?.("SIGNED_IN", sessionFor("user-a", "a@example.test")));
    await waitFor(() => expect(screen.getByTestId("access-approved")).toHaveTextContent("true"));

    const staleA = deferred<{ access_approved: boolean; position: number | null }>();
    const currentB = deferred<{ access_approved: boolean; position: number | null }>();
    mocks.myStatus
      .mockReturnValueOnce(staleA.promise)
      .mockReturnValueOnce(currentB.promise);

    fireEvent.click(screen.getByRole("button", { name: "Refresh access" }));
    await waitFor(() => expect(mocks.myStatus).toHaveBeenCalledTimes(2));

    act(() => mocks.authStateHandler?.("SIGNED_IN", sessionFor("user-b", "b@example.test")));
    await screen.findByText("b@example.test");
    await waitFor(() => expect(mocks.myStatus).toHaveBeenCalledTimes(3));

    await act(async () => {
      currentB.resolve({ access_approved: false, position: 9 });
      await currentB.promise;
    });
    await waitFor(() => expect(screen.getByTestId("access-loading")).toHaveTextContent("false"));

    await act(async () => {
      staleA.resolve({ access_approved: true, position: 3 });
      await staleA.promise;
    });

    expect(screen.getByTestId("access-approved")).toHaveTextContent("false");
    expect(screen.getByTestId("access-checked")).toHaveTextContent("true");
    expect(screen.getByTestId("access-loading")).toHaveTextContent("false");
    expect(screen.getByTestId("waitlist-position")).toHaveTextContent("9");
  });
});
