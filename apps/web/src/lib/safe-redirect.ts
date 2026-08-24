const SAFE_BASE = "https://app.local";

/** Return an app-local path or the supplied fallback; never return an external URL. */
export function safeRedirectPath(
  candidate: string | null | undefined,
  fallback: string,
): string {
  if (
    !candidate ||
    !candidate.startsWith("/") ||
    candidate.startsWith("//") ||
    candidate.includes("\\") ||
    /[\u0000-\u001F\u007F]/.test(candidate)
  ) {
    return fallback;
  }

  try {
    const parsed = new URL(candidate, SAFE_BASE);
    if (parsed.origin !== SAFE_BASE) return fallback;
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return fallback;
  }
}
