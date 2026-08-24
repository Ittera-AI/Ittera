import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  ensureWaitlistEntry: vi.fn(),
  fetchWaitlistMemberStatus: vi.fn(),
  fetchWaitlistStats: vi.fn(),
  openAuth: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({ user: null, openAuth: mocks.openAuth }),
}));

vi.mock("@/context/ThemeContext", () => ({
  useTheme: () => ({ theme: "light" }),
}));

vi.mock("@/services/waitlist-access", () => ({
  ensureWaitlistEntry: mocks.ensureWaitlistEntry,
  fetchWaitlistMemberStatus: mocks.fetchWaitlistMemberStatus,
  fetchWaitlistStats: mocks.fetchWaitlistStats,
}));

import Waitlist from "@/components/sections/Waitlist";

beforeEach(() => {
  mocks.ensureWaitlistEntry.mockReset();
  mocks.fetchWaitlistMemberStatus.mockReset();
  mocks.fetchWaitlistStats.mockReset();
  mocks.openAuth.mockReset();
  mocks.fetchWaitlistMemberStatus.mockResolvedValue({ status: null, error: null });
});

describe("Waitlist aggregate failure containment", () => {
  it("shows an unavailable retry state instead of fabricated zero/100 stats", async () => {
    mocks.fetchWaitlistStats.mockRejectedValue(new Error("stats unavailable"));

    render(<Waitlist />);

    expect(
      await screen.findByRole("button", { name: "Retry live cohort stats" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Live cohort count unavailable.")).toBeInTheDocument();
    expect(screen.queryByText("0 joined")).not.toBeInTheDocument();
    expect(screen.queryByText("100 seats remaining")).not.toBeInTheDocument();
    expect(screen.queryByText("0 people joined")).not.toBeInTheDocument();
  });

  it("keeps a committed enrollment successful when the follow-up stats read fails", async () => {
    mocks.fetchWaitlistStats.mockRejectedValue(new Error("stats unavailable"));
    mocks.ensureWaitlistEntry.mockResolvedValue({
      position: 7,
      joined: true,
      alreadyJoined: false,
    });

    render(<Waitlist />);
    await screen.findByRole("button", { name: "Retry live cohort stats" });

    fireEvent.change(screen.getByPlaceholderText("your@email.com"), {
      target: { value: " Creator@Example.Test " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Claim my seat" }));

    expect(await screen.findByText("You're #7 on the list.")).toBeInTheDocument();
    expect(mocks.ensureWaitlistEntry).toHaveBeenCalledWith(
      "creator@example.test",
      "",
      "",
    );
    await waitFor(() => expect(mocks.fetchWaitlistStats).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Network error. Please try again.")).not.toBeInTheDocument();
  });
});
