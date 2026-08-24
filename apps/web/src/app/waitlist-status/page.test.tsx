import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  fetchWaitlistMemberStatus: vi.fn(),
  refreshWorkspaceAccess: vi.fn(),
  replace: vi.fn(),
  signOut: vi.fn(),
  stats: vi.fn(),
  auth: {
    user: { id: "user-a", email: "member@example.test", name: "User A", initials: "UA" } as {
      id: string;
      email: string;
      name: string;
      initials: string;
    } | null,
    sessionLoading: false,
    workspaceAccessLoading: false,
    workspaceAccessChecked: true,
    hasWorkspaceAccess: false,
    waitlistPosition: null as number | null,
  },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mocks.replace }),
}));

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    ...mocks.auth,
    refreshWorkspaceAccess: mocks.refreshWorkspaceAccess,
    signOut: mocks.signOut,
  }),
}));

vi.mock("@/lib/api", () => ({
  api: { waitlist: { stats: mocks.stats } },
}));

vi.mock("@/services/waitlist-access", () => ({
  fetchWaitlistMemberStatus: mocks.fetchWaitlistMemberStatus,
}));

vi.mock("@/components/waitlist/WaitlistStatusView", () => ({
  default: ({
    user,
    waitlistPosition,
    positionLoading,
    positionError,
  }: {
    user: { id: string; email: string };
    waitlistPosition: number | null;
    positionLoading: boolean;
    positionError?: string | null;
  }) => (
    <div>
      <span data-testid="status-principal">{user.id}</span>
      <span data-testid="status-position">{waitlistPosition ?? "none"}</span>
      <span data-testid="status-loading">{String(positionLoading)}</span>
      <span data-testid="status-error">{positionError ?? "none"}</span>
    </div>
  ),
}));

import WaitlistStatusPage from "@/app/waitlist-status/page";

beforeEach(() => {
  mocks.fetchWaitlistMemberStatus.mockReset();
  mocks.refreshWorkspaceAccess.mockReset();
  mocks.replace.mockReset();
  mocks.signOut.mockReset();
  mocks.stats.mockReset();
  Object.assign(mocks.auth, {
    user: { id: "user-a", email: "member@example.test", name: "User A", initials: "UA" },
    sessionLoading: false,
    workspaceAccessLoading: false,
    workspaceAccessChecked: true,
    hasWorkspaceAccess: false,
    waitlistPosition: null,
  });
  mocks.refreshWorkspaceAccess.mockResolvedValue(false);
  mocks.signOut.mockResolvedValue(undefined);
  mocks.stats.mockResolvedValue({
    total_joined: 10,
    total_seats: 100,
    remaining_seats: 90,
    recent_joiners: [],
  });
});

describe("WaitlistStatusPage principal containment", () => {
  it("does not expose principal A's position to a different ID with the same email", async () => {
    mocks.fetchWaitlistMemberStatus
      .mockResolvedValueOnce({
        status: {
          email: "member@example.test",
          joined: true,
          access_approved: false,
          approved_at: null,
          position: 4,
          total_joined: 10,
          total_seats: 100,
          remaining_seats: 90,
          recent_joiners: [],
        },
        error: null,
      })
      .mockResolvedValueOnce({ status: null, error: "B status unavailable" });

    const { rerender } = render(<WaitlistStatusPage />);
    await waitFor(() => expect(screen.getByTestId("status-position")).toHaveTextContent("4"));

    mocks.auth.user = {
      id: "user-b",
      email: "member@example.test",
      name: "User B",
      initials: "UB",
    };
    rerender(<WaitlistStatusPage />);

    expect(screen.getByTestId("status-principal")).toHaveTextContent("user-b");
    expect(screen.getByTestId("status-position")).toHaveTextContent("none");

    await waitFor(() =>
      expect(screen.getByTestId("status-error")).toHaveTextContent("B status unavailable"),
    );
    expect(screen.getByTestId("status-position")).toHaveTextContent("none");
    expect(mocks.fetchWaitlistMemberStatus).toHaveBeenCalledTimes(2);
  });
});
