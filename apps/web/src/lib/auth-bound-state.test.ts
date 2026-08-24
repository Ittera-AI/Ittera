import { describe, expect, it, vi } from "vitest";

import {
  AUTH_BOUND_STATE_RESET_EVENT,
  registerAuthBoundStateResetter,
  resetAuthBoundState,
} from "@/lib/auth-bound-state";

const LOCAL_AUTH_KEYS = [
  "currentWorkspaceId",
  "iterra-product-store",
  "ittera-radar-prompt",
];

describe("resetAuthBoundState", () => {
  it.each(["auth", "workspace"] as const)(
    "clears %s-bound state while preserving global display preferences",
    (scope) => {
      for (const key of LOCAL_AUTH_KEYS) localStorage.setItem(key, `secret:${key}`);
      localStorage.setItem("ittera-theme", "dark");
      localStorage.setItem("ittera_sidebar_collapsed", "true");
      sessionStorage.setItem("skipped_onboarding", "true");

      const resetter = vi.fn();
      const unregister = registerAuthBoundStateResetter("test-resetter", resetter);
      const observed = vi.fn();
      window.addEventListener(AUTH_BOUND_STATE_RESET_EVENT, observed);

      resetAuthBoundState(scope);

      for (const key of LOCAL_AUTH_KEYS) expect(localStorage.getItem(key)).toBeNull();
      expect(sessionStorage.getItem("skipped_onboarding")).toBeNull();
      expect(localStorage.getItem("ittera-theme")).toBe("dark");
      expect(localStorage.getItem("ittera_sidebar_collapsed")).toBe("true");
      expect(resetter).toHaveBeenCalledOnce();
      expect(resetter).toHaveBeenCalledWith(scope);
      expect(observed).toHaveBeenCalledOnce();

      unregister();
      window.removeEventListener(AUTH_BOUND_STATE_RESET_EVENT, observed);
    },
  );
});
