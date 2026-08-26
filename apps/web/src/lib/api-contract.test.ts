import { beforeEach, describe, expect, expectTypeOf, it, vi } from "vitest";

import type {
  AuthorizationContextContract,
  ConnectSessionResponseContract,
  PlatformStatusContract,
  WaitlistMemberStatusContract,
  WaitlistRequestContract,
  WaitlistResponseContract,
  WaitlistStatsContract,
} from "@/test/fixtures/shared-contracts";
import {
  AUTHORIZATION_CONTEXT_FIXTURE,
  CONNECT_SESSION_FIXTURE,
  createWaitlistMemberStatusFixture,
  PLATFORM_STATUS_FIXTURE,
  WAITLIST_REQUEST_FIXTURE,
  WAITLIST_RESPONSE_FIXTURE,
  WAITLIST_STATS_FIXTURE,
} from "@/test/fixtures/shared-contracts";

const authMocks = vi.hoisted(() => ({
  getSession: vi.fn(),
  refreshSession: vi.fn(),
  signOut: vi.fn(),
}));

vi.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      getSession: authMocks.getSession,
      refreshSession: authMocks.refreshSession,
      signOut: authMocks.signOut,
    },
  },
  clearStoredSupabaseSessions: vi.fn(),
}));

import { api } from "@/lib/api";

beforeEach(() => {
  authMocks.getSession.mockResolvedValue({ data: { session: null } });
  authMocks.refreshSession.mockResolvedValue({ data: { session: null }, error: null });
  authMocks.signOut.mockResolvedValue({ error: null });
});

function jsonResponse(payload: unknown) {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("generated shared-contract consumer", () => {
  it("keeps public methods bound to generated schemas", () => {
    expectTypeOf<Parameters<typeof api.waitlist.join>[0]>().toEqualTypeOf<WaitlistRequestContract>();
    expectTypeOf<Awaited<ReturnType<typeof api.waitlist.join>>>().toEqualTypeOf<WaitlistResponseContract>();
    expectTypeOf<Awaited<ReturnType<typeof api.waitlist.stats>>>().toEqualTypeOf<WaitlistStatsContract>();
    expectTypeOf<Awaited<ReturnType<typeof api.waitlist.myStatus>>>().toEqualTypeOf<WaitlistMemberStatusContract>();
    expectTypeOf<Awaited<ReturnType<typeof api.connect.status>>>().toEqualTypeOf<PlatformStatusContract[]>();
    expectTypeOf<Awaited<ReturnType<typeof api.connect.createSession>>>().toEqualTypeOf<ConnectSessionResponseContract>();
    expectTypeOf<
      Awaited<ReturnType<typeof api.workspace.authorizationContext>>
    >().toEqualTypeOf<AuthorizationContextContract>();
  });

  it("accepts generated fixtures through the same API consumer used by the app", async () => {
    const memberFixture = createWaitlistMemberStatusFixture();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(WAITLIST_STATS_FIXTURE))
      .mockResolvedValueOnce(jsonResponse(memberFixture))
      .mockResolvedValueOnce(jsonResponse(WAITLIST_RESPONSE_FIXTURE))
      .mockResolvedValueOnce(jsonResponse([PLATFORM_STATUS_FIXTURE]))
      .mockResolvedValueOnce(jsonResponse(CONNECT_SESSION_FIXTURE))
      .mockResolvedValueOnce(jsonResponse(AUTHORIZATION_CONTEXT_FIXTURE));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.waitlist.stats()).resolves.toEqual(WAITLIST_STATS_FIXTURE);
    await expect(api.waitlist.myStatus()).resolves.toEqual(memberFixture);
    await expect(api.waitlist.join(WAITLIST_REQUEST_FIXTURE)).resolves.toEqual(
      WAITLIST_RESPONSE_FIXTURE,
    );
    await expect(api.connect.status()).resolves.toEqual([PLATFORM_STATUS_FIXTURE]);
    await expect(api.connect.createSession()).resolves.toEqual(CONNECT_SESSION_FIXTURE);
    await expect(
      api.workspace.authorizationContext("workspace-fixture"),
    ).resolves.toEqual(AUTHORIZATION_CONTEXT_FIXTURE);

    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      expect.stringMatching(/\/api\/v1\/waitlist$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(WAITLIST_REQUEST_FIXTURE),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      5,
      expect.stringMatching(/\/api\/v1\/connect\/session$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({}),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      6,
      expect.stringMatching(
        /\/api\/v1\/workspaces\/workspace-fixture\/authorization-context$/,
      ),
      expect.objectContaining({ method: "GET" }),
    );
  });
});
