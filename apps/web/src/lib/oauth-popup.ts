import { api } from "@/lib/api";

export type OAuthPlatform = "linkedin" | "twitter" | "instagram";

export type OAuthPopupResult = {
  platform: OAuthPlatform;
  username?: string;
};

type OAuthPopupDependencies = {
  createSession?: typeof api.connect.createSession;
  buildStartUrl?: (platform: string, connectToken: string) => string;
  openWindow?: (
    url?: string | URL,
    target?: string,
    features?: string,
  ) => Window | null;
  pollIntervalMs?: number;
  timeoutMs?: number;
};

type OAuthMessage = {
  type: "ittera_oauth";
  platform: OAuthPlatform;
  status: "connected" | "error";
  username?: string;
  error?: string;
};

function isOAuthMessage(value: unknown): value is OAuthMessage {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<OAuthMessage>;
  return (
    candidate.type === "ittera_oauth" &&
    (candidate.platform === "linkedin" ||
      candidate.platform === "twitter" ||
      candidate.platform === "instagram") &&
    (candidate.status === "connected" || candidate.status === "error") &&
    (candidate.username === undefined || typeof candidate.username === "string") &&
    (candidate.error === undefined || typeof candidate.error === "string")
  );
}

function popupFeatures() {
  const width = 520;
  const height = 720;
  const left = Math.max(0, window.screenX + (window.outerWidth - width) / 2);
  const top = Math.max(0, window.screenY + (window.outerHeight - height) / 2);
  return `width=${width},height=${height},left=${left},top=${top},toolbar=0,menubar=0`;
}

/**
 * Open a social OAuth popup without ever placing a bearer/provider token in its URL.
 * Completion is accepted once, and only from the exact popup and callback origin.
 */
export function connectWithOAuthPopup(
  platform: OAuthPlatform,
  dependencies: OAuthPopupDependencies = {},
): Promise<OAuthPopupResult> {
  const openWindow = dependencies.openWindow ?? window.open.bind(window);
  const createSession = dependencies.createSession ?? api.connect.createSession;
  const buildStartUrl = dependencies.buildStartUrl ?? api.connect.startUrl;
  const pollIntervalMs = dependencies.pollIntervalMs ?? 500;
  const timeoutMs = dependencies.timeoutMs ?? 120_000;

  // This must happen before the first await so browsers recognize the user gesture.
  const popup = openWindow(
    "about:blank",
    `ittera-${platform}-connect`,
    popupFeatures(),
  );
  if (!popup) {
    return Promise.reject(new Error("Popup was blocked. Allow popups and try again."));
  }

  return new Promise<OAuthPopupResult>((resolve, reject) => {
    let callbackOrigin: string | null = null;
    let settled = false;

    const cleanup = () => {
      window.removeEventListener("message", onMessage);
      window.clearInterval(closedTimer);
      window.clearTimeout(timeoutTimer);
    };

    const finish = (
      outcome:
        | { ok: true; value: OAuthPopupResult }
        | { ok: false; error: Error; closePopup?: boolean },
    ) => {
      if (settled) return;
      settled = true;
      cleanup();
      if (!outcome.ok && outcome.closePopup) {
        try {
          popup.close();
        } catch {
          // The popup may already have closed or become cross-origin.
        }
      }
      if (outcome.ok) resolve(outcome.value);
      else reject(outcome.error);
    };

    const onMessage = (event: MessageEvent) => {
      if (!callbackOrigin || event.origin !== callbackOrigin || event.source !== popup) return;
      if (!isOAuthMessage(event.data) || event.data.platform !== platform) return;

      if (event.data.status === "connected") {
        finish({
          ok: true,
          value: { platform, username: event.data.username },
        });
        return;
      }

      finish({
        ok: false,
        error: new Error(event.data.error || `${platform} connection failed.`),
      });
    };

    const closedTimer = window.setInterval(() => {
      try {
        if (popup.closed) {
          finish({
            ok: false,
            error: new Error(`${platform} connection was cancelled.`),
          });
        }
      } catch {
        // Cross-origin popup access can transiently throw; wait for timeout/message.
      }
    }, pollIntervalMs);

    const timeoutTimer = window.setTimeout(() => {
      finish({
        ok: false,
        error: new Error(`${platform} connection timed out.`),
        closePopup: true,
      });
    }, timeoutMs);

    window.addEventListener("message", onMessage);

    void Promise.resolve()
      .then(createSession)
      .then(({ connect_token }) => {
        if (settled) return;
        if (!connect_token) throw new Error("Could not create a connection session.");
        const startUrl = buildStartUrl(platform, connect_token);
        callbackOrigin = new URL(startUrl, window.location.href).origin;
        popup.location.href = startUrl;
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : "Could not start the connection.";
        finish({ ok: false, error: new Error(message), closePopup: true });
      });
  });
}
