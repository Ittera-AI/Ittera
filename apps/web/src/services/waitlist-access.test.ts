import { beforeEach, describe, expect, it, vi } from "vitest";

const waitlistMocks = vi.hoisted(() => ({
  join: vi.fn(),
  myStatus: vi.fn(),
  stats: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {
    constructor(message: string, public status: number) {
      super(message);
    }
  },
  api: { waitlist: waitlistMocks },
}));

vi.mock("@/services/api", () => ({
  ApiError: class ApiError extends Error {},
  apiFetch: vi.fn(() => {
    throw new Error("legacy waitlist transport used");
  }),
}));

import {
  ensureWaitlistEntry,
  fetchWaitlistMemberStatus,
} from "@/services/waitlist-access";

beforeEach(() => {
  waitlistMocks.join.mockReset();
  waitlistMocks.myStatus.mockReset();
  waitlistMocks.stats.mockReset();
});

describe("waitlist API boundary", () => {
  it("normalizes enrollment and preserves the API's idempotent already-joined result", async () => {
    waitlistMocks.join.mockResolvedValue({ position: 7, already_joined: true });

    await expect(ensureWaitlistEntry("  MEMBER@Example.COM ", "  Member  ")).resolves.toEqual({
      position: 7,
      joined: true,
      alreadyJoined: true,
    });
    expect(waitlistMocks.join).toHaveBeenCalledWith({
      email: "member@example.com",
      name: "Member",
    });
  });

  it("surfaces a failed enrollment and permits an explicit retry", async () => {
    waitlistMocks.join
      .mockRejectedValueOnce(new Error("Waitlist temporarily unavailable"))
      .mockResolvedValueOnce({ position: 8, already_joined: false });

    await expect(ensureWaitlistEntry("member@example.com")).rejects.toThrow(
      "Waitlist temporarily unavailable",
    );
    await expect(ensureWaitlistEntry("member@example.com")).resolves.toEqual({
      position: 8,
      joined: true,
      alreadyJoined: false,
    });
    expect(waitlistMocks.join).toHaveBeenCalledTimes(2);
  });

  it("returns an explicit fail-closed member-status error", async () => {
    waitlistMocks.myStatus.mockRejectedValue(new Error("offline"));

    await expect(fetchWaitlistMemberStatus()).resolves.toEqual({
      status: null,
      error: "Could not load your queue position. Is the API running?",
    });
  });
});
