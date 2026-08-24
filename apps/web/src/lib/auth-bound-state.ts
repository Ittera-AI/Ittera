export type AuthBoundStateScope = "auth" | "workspace";

export const AUTH_BOUND_STATE_RESET_EVENT = "ittera-auth-bound-state-reset";

const LOCAL_STORAGE_KEYS = [
  "currentWorkspaceId",
  "iterra-product-store",
  "ittera-radar-prompt",
] as const;
const SESSION_STORAGE_KEYS = ["skipped_onboarding"] as const;

const resetters = new Map<
  string,
  (scope: AuthBoundStateScope) => void
>();

/** Register in-memory state that must never survive an auth/workspace boundary. */
export function registerAuthBoundStateResetter(
  name: string,
  resetter: (scope: AuthBoundStateScope) => void,
) {
  resetters.set(name, resetter);
  return () => {
    if (resetters.get(name) === resetter) resetters.delete(name);
  };
}

/**
 * Clear all browser and registered in-memory state containing user/workspace data.
 * Global display preferences (theme/sidebar) are intentionally not touched.
 */
export function resetAuthBoundState(scope: AuthBoundStateScope = "auth") {
  if (typeof window === "undefined") return;

  try {
    for (const key of LOCAL_STORAGE_KEYS) localStorage.removeItem(key);
  } catch {
    // Storage can be unavailable in privacy modes; in-memory reset still runs.
  }

  try {
    for (const key of SESSION_STORAGE_KEYS) sessionStorage.removeItem(key);
  } catch {
    // Storage can be unavailable in privacy modes; in-memory reset still runs.
  }

  for (const resetter of resetters.values()) {
    try {
      resetter(scope);
    } catch {
      // One state container must not prevent the rest from being cleared.
    }
  }

  window.dispatchEvent(
    new CustomEvent<AuthBoundStateScope>(AUTH_BOUND_STATE_RESET_EVENT, {
      detail: scope,
    }),
  );
}
