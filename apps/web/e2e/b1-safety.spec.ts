import { expect, test, type Page } from "@playwright/test";

import {
  MOCK_CONNECT_TOKEN,
  installMockBackend,
} from "./fixtures/mock-backend";

async function waitForHydratedButton(page: Page, label: string) {
  const button = page.getByRole("button", { name: label });
  await expect(button).toBeVisible();
  await page.waitForFunction((text) => {
    const candidate = Array.from(document.querySelectorAll("button")).find(
      (element) => element.textContent?.includes(text),
    );
    return Boolean(
      candidate &&
        Object.keys(candidate).some((key) => key.startsWith("__reactProps$")),
    );
  }, label);
  return button;
}

async function signIn(page: Page, email: string, next: string) {
  await page.goto(`/login?next=${encodeURIComponent(next)}`);
  await page.waitForFunction(() => {
    const button = Array.from(document.querySelectorAll("button")).find(
      (candidate) => candidate.textContent?.trim() === "Sign in",
    );
    return Boolean(
      button && Object.keys(button).some((key) => key.startsWith("__reactProps$")),
    );
  });
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("safe-test-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(
    new RegExp(`${next.replaceAll("/", "\\/")}$`),
    { timeout: 30_000 },
  );
  await page.waitForLoadState("networkidle");
}

test.describe("B1 frontend safety smoke", () => {
  test("uses a one-time connect token and accepts only the mocked popup completion", async ({ page }) => {
    const backend = await installMockBackend(page, { accessApproved: true });
    const browserLogs: string[] = [];
    const requestUrls: string[] = [];
    page.on("console", (message) => browserLogs.push(message.text()));
    page.on("request", (request) => requestUrls.push(request.url()));

    await signIn(page, "member@example.test", "/onboarding/persona");
    await (await waitForHydratedButton(page, "Ignite the Engine")).click();
    await expect(page.getByRole("heading", { name: "Select your sources" })).toBeVisible();

    const popupPromise = page.waitForEvent("popup");
    await (await waitForHydratedButton(page, "Connect LinkedIn")).click();
    await popupPromise;
    await expect(page.getByText("@mock-linkedin")).toBeVisible();

    expect(backend.oauthStartUrls).toHaveLength(1);
    const startUrl = new URL(backend.oauthStartUrls[0]);
    expect(startUrl.searchParams.get("ct")).toBe(MOCK_CONNECT_TOKEN);
    expect(startUrl.searchParams.has("token")).toBe(false);

    for (const accessToken of backend.accessTokens) {
      expect(requestUrls.some((url) => url.includes(accessToken))).toBe(false);
      expect(browserLogs.join("\n")).not.toContain(accessToken);
    }
  });

  test("logout and the next principal cannot inherit auth/workspace state", async ({ page }) => {
    const backend = await installMockBackend(page);

    await signIn(page, "first@example.test", "/waitlist-status");
    await expect(page.getByRole("heading", { name: /You're #4/ })).toBeVisible();

    await page.evaluate(() => {
      localStorage.setItem("currentWorkspaceId", "workspace-a");
      localStorage.setItem("iterra-product-store", "user-a product data");
      localStorage.setItem("ittera-radar-prompt", "user-a prompt");
      localStorage.setItem("ittera-theme", "dark");
      sessionStorage.setItem("skipped_onboarding", "true");
    });

    const accountButton = page.getByRole("button", { name: /F first/ });
    await expect(accountButton).toBeVisible();
    await accountButton.click();
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/$/);

    await expect
      .poll(() =>
        page.evaluate(() => ({
          product: localStorage.getItem("iterra-product-store"),
          prompt: localStorage.getItem("ittera-radar-prompt"),
          skipped: sessionStorage.getItem("skipped_onboarding"),
          theme: localStorage.getItem("ittera-theme"),
          workspace: localStorage.getItem("currentWorkspaceId"),
        })),
      )
      .toEqual({
        product: null,
        prompt: null,
        skipped: null,
        theme: "dark",
        workspace: null,
      });

    await signIn(page, "second@example.test", "/waitlist-status");
    expect(backend.authEmails).toEqual([
      "first@example.test",
      "second@example.test",
    ]);
    await expect
      .poll(() =>
        page.evaluate(() => ({
          product: localStorage.getItem("iterra-product-store"),
          workspace: localStorage.getItem("currentWorkspaceId"),
        })),
      )
      .toEqual({ product: null, workspace: null });
  });
});
