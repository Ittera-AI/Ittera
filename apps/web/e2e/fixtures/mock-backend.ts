import type { Page } from "@playwright/test";

export const MOCK_SUPABASE_ORIGIN = "https://supabase.e2e.test";
export const MOCK_CONNECT_TOKEN = "ct-e2e-single-use";

export type MockBackendState = {
  accessTokens: string[];
  authEmails: string[];
  oauthStartUrls: string[];
};

function base64Url(value: object) {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function authResponse(email: string) {
  const userId = email.startsWith("second") ? "user-b" : "user-a";
  const now = Math.floor(Date.now() / 1_000);
  const accessToken = [
    base64Url({ alg: "HS256", typ: "JWT" }),
    base64Url({
      aud: "authenticated",
      email,
      exp: now + 3_600,
      iat: now,
      role: "authenticated",
      sub: userId,
      user_metadata: { full_name: email.split("@")[0] },
    }),
    "e2e-signature",
  ].join(".");
  const timestamp = new Date(now * 1_000).toISOString();
  const user = {
    id: userId,
    aud: "authenticated",
    role: "authenticated",
    email,
    email_confirmed_at: timestamp,
    last_sign_in_at: timestamp,
    app_metadata: { provider: "email", providers: ["email"] },
    user_metadata: { full_name: email.split("@")[0] },
    identities: [],
    created_at: timestamp,
    updated_at: timestamp,
  };

  return {
    accessToken,
    body: {
      access_token: accessToken,
      token_type: "bearer",
      expires_in: 3_600,
      expires_at: now + 3_600,
      refresh_token: `refresh-${userId}`,
      user,
    },
  };
}

export async function installMockBackend(
  page: Page,
  { accessApproved = false }: { accessApproved?: boolean } = {},
): Promise<MockBackendState> {
  const state: MockBackendState = {
    accessTokens: [],
    authEmails: [],
    oauthStartUrls: [],
  };

  await page.route(`${MOCK_SUPABASE_ORIGIN}/auth/v1/token**`, async (route) => {
    const payload = route.request().postDataJSON() as { email?: string } | null;
    const email = payload?.email?.trim().toLowerCase() || "member@example.test";
    const response = authResponse(email);
    state.authEmails.push(email);
    state.accessTokens.push(response.accessToken);
    await route.fulfill({ status: 200, json: response.body });
  });

  await page.route(`${MOCK_SUPABASE_ORIGIN}/auth/v1/logout**`, async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });

  await page.route("**/api/v1/auth/logout", async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });

  await page.route("**/api/v1/waitlist/me", async (route) => {
    await route.fulfill({
      status: 200,
      json: {
        email: state.authEmails.at(-1) || "member@example.test",
        joined: true,
        access_approved: accessApproved,
        approved_at: accessApproved ? new Date(0).toISOString() : null,
        position: 4,
        total_joined: 42,
        total_seats: 100,
        remaining_seats: 58,
        recent_joiners: [],
      },
    });
  });

  await page.route("**/api/v1/waitlist", async (route) => {
    await route.fulfill({
      status: 200,
      json: {
        total_joined: 42,
        total_seats: 100,
        remaining_seats: 58,
        recent_joiners: [],
      },
    });
  });

  await page.route("**/api/v1/connect/status", async (route) => {
    await route.fulfill({ status: 200, json: [] });
  });

  await page.route("**/api/v1/connect/session", async (route) => {
    await route.fulfill({
      status: 200,
      json: { connect_token: MOCK_CONNECT_TOKEN },
    });
  });

  await page.context().route("**/api/v1/connect/*/start?**", async (route) => {
    const requestUrl = route.request().url();
    state.oauthStartUrls.push(requestUrl);
    const platform = new URL(requestUrl).pathname.split("/").at(-2) || "linkedin";
    const payload = JSON.stringify({
      type: "ittera_oauth",
      platform,
      status: "connected",
      username: `mock-${platform}`,
    });
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: `<!doctype html><script>
        window.opener.postMessage(${payload}, window.location.origin);
        window.setTimeout(() => window.close(), 0);
      </script>`,
    });
  });

  return state;
}
