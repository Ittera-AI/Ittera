import { clearStoredSupabaseSessions, supabase } from "@/lib/supabase";

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
  return "";
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

async function getAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  try {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  } catch {
    return null;
  }
}

async function refreshAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  try {
    const { data, error } = await supabase.auth.refreshSession();
    if (error) return null;
    return data.session?.access_token ?? null;
  } catch {
    return null;
  }
}

async function clearInvalidSession() {
  if (typeof window === "undefined") return;

  try {
    await supabase.auth.signOut();
  } catch {
    clearStoredSupabaseSessions();
  }

  try {
    await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // Keep the original API error path intact when cookie cleanup cannot complete.
  }

  window.dispatchEvent(new Event("ittera-auth-invalid"));
}

async function parseErrorMessage(response: Response): Promise<string> {
  let message = response.statusText;
  try {
    const body = await response.json();
    message = body.detail ?? message;
  } catch {
    // Keep the HTTP status text when the API did not return JSON.
  }
  return message;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  if (!headers.has("Content-Type") && init.body && !isFormData) {
    headers.set("Content-Type", "application/json");
  }

  const callerProvidedAuthorization = headers.has("Authorization");
  const accessToken = callerProvidedAuthorization ? null : await getAccessToken();
  if (accessToken && !callerProvidedAuthorization) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const url = `${API_BASE_URL}${path}`;

  const send = (requestHeaders: Headers) =>
    fetch(url, {
      ...init,
      headers: requestHeaders,
      credentials: "include",
    });

  let response: Response;
  try {
    response = await send(headers);
  } catch (err) {
    const hint =
      API_BASE_URL === ""
        ? "Same-origin proxy: ensure Next.js rewrites are configured and FastAPI is reachable from the dev server (see API_PROXY_TARGET / port 8000)."
        : `Tried ${API_BASE_URL}. Is the API running and is CORS (ALLOWED_ORIGINS) correct?`;
    const cause = err instanceof Error ? err.message : String(err);
    throw new ApiError(`Failed to reach API (${cause}). ${hint}`, 0);
  }

  if (response.status === 401 && !callerProvidedAuthorization) {
    if (accessToken) {
      const refreshedToken = await refreshAccessToken();
      if (refreshedToken) {
        const retryHeaders = new Headers(headers);
        retryHeaders.set("Authorization", `Bearer ${refreshedToken}`);
        response = await send(retryHeaders);
      }
    }

    if (response.status === 401) {
      await clearInvalidSession();
    }
  }

  if (!response.ok) {
    const message = await parseErrorMessage(response);
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
