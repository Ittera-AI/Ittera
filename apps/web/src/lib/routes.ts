/** Central route targets for auth / waitlist flows. */
export const ROUTES = {
  home: "/",
  dashboard: "/dashboard",
  waitlistStatus: "/waitlist-status",
  login: "/login",
  authCallback: "/auth/callback",
  demo: "/demo",
} as const;

/** Public marketing routes signed-in users should never stay on. Demo is allowed while waitlisted. */
export const MARKETING_PATHS = [ROUTES.home, ROUTES.login] as const;

export function waitlistDestination(hasAccess: boolean) {
  return hasAccess ? ROUTES.dashboard : ROUTES.waitlistStatus;
}

/** Hard navigation — avoids marketing page flash during client-side route transitions. */
export function redirectAfterSignIn() {
  window.location.replace(ROUTES.dashboard);
}
