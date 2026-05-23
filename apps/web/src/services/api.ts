import { supabase } from "@/lib/supabase";

const isDev = process.env.NODE_ENV === "development";

/**
 * API base URL for `fetch`.
 * - In development, unset `NEXT_PUBLIC_API_URL` → same-origin `/api/v1/...` (Next.js rewrites to FastAPI). Avoids CORS and localhost vs 127.0.0.1 mismatches.
 * - Set `NEXT_PUBLIC_API_URL` to a full origin when the API is on another host (production, mobile on LAN, etc.).
 * - `NEXT_PUBLIC_API_URL=""` or `same-origin` forces proxy mode in all environments.
 */
function resolveApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL;
  if (raw === "" || raw === "same-origin") {
    return "";
  }
  if (raw !== undefined && raw.trim() !== "") {
    return raw.replace(/\/$/, "");
  }
  if (isDev) {
    return "";
  }
  return "http://localhost:8000";
}

const API_BASE_URL = resolveApiBaseUrl();

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const API_TIMEOUT_MS = 8_000;

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }

  if (typeof window !== "undefined") {
    try {
      const { data } = await supabase.auth.getSession();
      if (data.session?.access_token && !headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${data.session.access_token}`);
      }
    } catch {
      // Ignore auth errors during fetch
    }
  }

  const url = `${API_BASE_URL}${path}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers,
      credentials: "include",
      signal: controller.signal,
    });
  } catch (err) {
    const hint =
      API_BASE_URL === ""
        ? "Same-origin proxy: ensure Next.js rewrites are configured and FastAPI is reachable from the dev server (see API_PROXY_TARGET / port 8000)."
        : `Tried ${API_BASE_URL}. Is the API running and is CORS (ALLOWED_ORIGINS) correct?`;
    const cause =
      err instanceof Error && err.name === "AbortError"
        ? `timed out after ${API_TIMEOUT_MS / 1000}s`
        : err instanceof Error
          ? err.message
          : String(err);
    throw new ApiError(`Failed to reach API (${cause}). ${hint}`, 0);
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {
      // Keep the HTTP status text when the API did not return JSON.
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
