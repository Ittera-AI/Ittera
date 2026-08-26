import { describe, expect, it, vi } from "vitest";

import { connectWithOAuthPopup, type OAuthPlatform } from "@/lib/oauth-popup";

type FakePopup = Window & {
  closed: boolean;
  location: Location & { href: string };
  close: ReturnType<typeof vi.fn>;
};

function createPopup(): FakePopup {
  return {
    closed: false,
    location: { href: "about:blank" },
    close: vi.fn(),
  } as unknown as FakePopup;
}

function dispatchOAuthMessage(
  source: Window,
  origin: string,
  data: Record<string, unknown>,
) {
  const event = new MessageEvent("message", { data, origin });
  Object.defineProperty(event, "source", { value: source });
  window.dispatchEvent(event);
}

function startConnection(platform: OAuthPlatform, popup = createPopup()) {
  const openWindow = vi.fn(() => popup);
  const createSession = vi.fn(async () => ({
    schema_version: "connect-session.v1" as const,
    connect_token: "one-time-connect-token",
  }));
  const buildStartUrl = vi.fn(
    (selectedPlatform: string, token: string) =>
      `https://api.example.test/api/v1/connect/${selectedPlatform}/start?ct=${encodeURIComponent(token)}`,
  );
  const promise = connectWithOAuthPopup(platform, {
    openWindow,
    createSession,
    buildStartUrl,
    pollIntervalMs: 25,
    timeoutMs: 1_000,
  });
  return { buildStartUrl, createSession, openWindow, popup, promise };
}

describe("connectWithOAuthPopup", () => {
  it("opens synchronously and puts only the one-time connect token in the start URL", async () => {
    const { buildStartUrl, openWindow, popup, promise } = startConnection("linkedin");

    expect(openWindow).toHaveBeenCalledOnce();
    expect(openWindow).toHaveBeenCalledWith(
      "about:blank",
      "ittera-linkedin-connect",
      expect.stringContaining("width=520"),
    );

    await vi.waitFor(() => expect(popup.location.href).toContain("/connect/linkedin/start"));
    const startUrl = new URL(popup.location.href);
    expect(startUrl.searchParams.get("ct")).toBe("one-time-connect-token");
    expect(startUrl.searchParams.has("token")).toBe(false);
    expect(startUrl.href).not.toContain("access-token");
    expect(buildStartUrl).toHaveBeenCalledWith("linkedin", "one-time-connect-token");

    dispatchOAuthMessage(popup, startUrl.origin, {
      type: "ittera_oauth",
      platform: "linkedin",
      status: "connected",
      username: "safe-user",
    });
    await expect(promise).resolves.toEqual({ platform: "linkedin", username: "safe-user" });
  });

  it("ignores messages from the wrong origin, popup, or platform", async () => {
    const otherPopup = createPopup();
    const { popup, promise } = startConnection("twitter");
    await vi.waitFor(() => expect(popup.location.href).toContain("/connect/twitter/start"));

    let settled = false;
    void promise.finally(() => {
      settled = true;
    });

    const payload = { type: "ittera_oauth", platform: "twitter", status: "connected" };
    dispatchOAuthMessage(popup, "https://evil.example", payload);
    dispatchOAuthMessage(otherPopup, "https://api.example.test", payload);
    dispatchOAuthMessage(popup, "https://api.example.test", { ...payload, platform: "linkedin" });
    await Promise.resolve();
    expect(settled).toBe(false);

    dispatchOAuthMessage(popup, "https://api.example.test", payload);
    await expect(promise).resolves.toEqual({ platform: "twitter", username: undefined });
  });

  it("settles once and removes the message listener so replay is inert", async () => {
    const removeListener = vi.spyOn(window, "removeEventListener");
    const { popup, promise } = startConnection("linkedin");
    await vi.waitFor(() => expect(popup.location.href).toContain("/connect/linkedin/start"));

    const success = {
      type: "ittera_oauth",
      platform: "linkedin",
      status: "connected",
      username: "first",
    };
    dispatchOAuthMessage(popup, "https://api.example.test", success);
    await expect(promise).resolves.toEqual({ platform: "linkedin", username: "first" });

    dispatchOAuthMessage(popup, "https://api.example.test", {
      ...success,
      status: "error",
      error: "replayed failure",
    });
    expect(removeListener).toHaveBeenCalledWith("message", expect.any(Function));
  });

  it("rejects blocked, closed, failed-to-start, and timed-out popups with cleanup", async () => {
    await expect(
      connectWithOAuthPopup("linkedin", { openWindow: () => null }),
    ).rejects.toThrow("Popup was blocked");

    vi.useFakeTimers();
    const closed = createPopup();
    const closedAttempt = startConnection("linkedin", closed);
    const closedExpectation = expect(closedAttempt.promise).rejects.toThrow("cancelled");
    await vi.advanceTimersByTimeAsync(0);
    closed.closed = true;
    await vi.advanceTimersByTimeAsync(25);
    await closedExpectation;

    const failed = createPopup();
    const failedPromise = connectWithOAuthPopup("twitter", {
      openWindow: () => failed,
      createSession: async () => {
        throw new Error("session unavailable");
      },
    });
    const failedExpectation = expect(failedPromise).rejects.toThrow("session unavailable");
    await vi.runAllTicks();
    await failedExpectation;
    expect(failed.close).toHaveBeenCalledOnce();

    const timedOut = createPopup();
    const timedOutAttempt = startConnection("twitter", timedOut);
    const timeoutExpectation = expect(timedOutAttempt.promise).rejects.toThrow("timed out");
    await vi.advanceTimersByTimeAsync(1_000);
    await timeoutExpectation;
    expect(timedOut.close).toHaveBeenCalledOnce();
  });
});
