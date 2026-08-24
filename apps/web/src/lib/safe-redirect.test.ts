import { describe, expect, it } from "vitest";

import { safeRedirectPath } from "@/lib/safe-redirect";

describe("safeRedirectPath", () => {
  it("allows an application-local path with query and fragment", () => {
    expect(safeRedirectPath("/drafts?status=ready#latest", "/dashboard")).toBe(
      "/drafts?status=ready#latest",
    );
  });

  it.each([
    undefined,
    "",
    "dashboard",
    "https://evil.example/steal",
    "//evil.example/steal",
    "/\\evil.example/steal",
    "javascript:alert(1)",
  ])("falls back for unsafe destination %s", (destination) => {
    expect(safeRedirectPath(destination, "/dashboard")).toBe("/dashboard");
  });
});
