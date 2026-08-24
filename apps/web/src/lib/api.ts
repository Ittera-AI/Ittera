/**
 * Typed API client for the Ittera FastAPI backend.
 *
 * Every request automatically attaches the current Supabase access token
 * as a Bearer header so the backend's dual-JWT auth dependency can verify it.
 *
 * Usage:
 *   import { api } from "@/lib/api";
 *   const drafts = await api.content.listDrafts();
 */

import {
  registerAuthBoundStateResetter,
  resetAuthBoundState,
} from "@/lib/auth-bound-state";
import { clearStoredSupabaseSessions, supabase } from "@/lib/supabase";

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

const BASE_URL = resolveApiBaseUrl();
const activeApiRequests = new Set<AbortController>();

registerAuthBoundStateResetter("api-fetch", () => {
  for (const controller of activeApiRequests) controller.abort();
  activeApiRequests.clear();
});

function abortError(signal: AbortSignal): Error {
  if (signal.reason instanceof Error) return signal.reason;
  const error = new Error("API request aborted");
  error.name = "AbortError";
  return error;
}

function throwIfAborted(signal: AbortSignal) {
  if (signal.aborted) throw abortError(signal);
}

// ─── Core fetch wrapper ───────────────────────────────────────────────────────

async function getToken(): Promise<string | null> {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  } catch {
    return null;
  }
}

async function refreshToken(): Promise<string | null> {
  try {
    const {
      data: { session },
      error,
    } = await supabase.auth.refreshSession();
    if (error) return null;
    return session?.access_token ?? null;
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
    await fetch(`${BASE_URL}/api/v1/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // Preserve the original API error path if cookie cleanup cannot complete.
  }

  resetAuthBoundState("auth");
  window.dispatchEvent(new Event("ittera-auth-invalid"));
}

/**
 * Canonical API error for the whole web app.
 *
 * Exposes `message`/`detail` (same string) and `status` so both calling
 * conventions used across the codebase keep working:
 *   - `err.message` (low-level `apiFetch` callers)
 *   - `err.detail`  (typed `api.*` namespace callers)
 */
export class ApiError extends Error {
  detail: string;
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
    this.detail = message;
  }
}

async function parseErrorMessage(response: Response): Promise<string> {
  let message = response.statusText || `HTTP ${response.status}`;
  try {
    const body = await response.json();
    message = body.detail ?? message;
  } catch {
    // Keep the HTTP status text when the API did not return JSON.
  }
  return message;
}

/**
 * Single low-level transport for the app. The typed `api.*` namespace and the
 * raw `apiFetch` consumers (product/waitlist services) both route through here,
 * so token attachment, 401 refresh, and error shaping live in exactly one place.
 *
 * Callers pass an absolute API path (e.g. `/api/v1/...`). A caller-provided
 * `Authorization` header bypasses the automatic Supabase bearer token.
 */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const callerSignal = init.signal;
  const abortFromCaller = () => controller.abort(callerSignal?.reason);

  if (callerSignal?.aborted) {
    abortFromCaller();
  } else {
    callerSignal?.addEventListener("abort", abortFromCaller, { once: true });
  }
  activeApiRequests.add(controller);

  try {
    throwIfAborted(controller.signal);

    const headers = new Headers(init.headers);
    const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
    if (!headers.has("Content-Type") && init.body && !isFormData) {
      headers.set("Content-Type", "application/json");
    }

    const callerProvidedAuthorization = headers.has("Authorization");
    const accessToken = callerProvidedAuthorization ? null : await getToken();
    throwIfAborted(controller.signal);

    if (accessToken && !callerProvidedAuthorization) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }

    const url = `${BASE_URL}${path}`;
    const send = async (requestHeaders: Headers) => {
      try {
        throwIfAborted(controller.signal);
        const response = await fetch(url, {
          ...init,
          headers: requestHeaders,
          credentials: "include",
          signal: controller.signal,
        });
        throwIfAborted(controller.signal);
        return response;
      } catch (error) {
        if (controller.signal.aborted) throw abortError(controller.signal);

        const hint =
          BASE_URL === ""
            ? "Same-origin proxy: ensure Next.js rewrites are configured and FastAPI is reachable from the dev server (see API_PROXY_TARGET / port 8000)."
            : `Tried ${BASE_URL}. Is the API running and is CORS (ALLOWED_ORIGINS) correct?`;
        const cause = error instanceof Error ? error.message : String(error);
        throw new ApiError(`Failed to reach API (${cause}). ${hint}`, 0);
      }
    };

    let response = await send(headers);

    if (response.status === 401 && !callerProvidedAuthorization) {
      if (accessToken) {
        const refreshedToken = await refreshToken();
        throwIfAborted(controller.signal);
        if (refreshedToken) {
          const retryHeaders = new Headers(headers);
          retryHeaders.set("Authorization", `Bearer ${refreshedToken}`);
          response = await send(retryHeaders);
        }
      }

      if (response.status === 401) {
        // Keep this response readable while the auth reset aborts every other
        // request that began under the invalid principal.
        activeApiRequests.delete(controller);
        await clearInvalidSession();
      }
    }

    if (!response.ok) {
      const message = await parseErrorMessage(response);
      throwIfAborted(controller.signal);
      throw new ApiError(message, response.status);
    }

    if (response.status === 204) {
      throwIfAborted(controller.signal);
      return undefined as T;
    }

    const payload = (await response.json()) as T;
    throwIfAborted(controller.signal);
    return payload;
  } finally {
    activeApiRequests.delete(controller);
    callerSignal?.removeEventListener("abort", abortFromCaller);
  }
}

function request<T>(
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
): Promise<T> {
  return apiFetch<T>(path, {
    method,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

const get    = <T>(path: string)               => request<T>("GET",    path);
const post   = <T>(path: string, body: unknown) => request<T>("POST",   path, body);
const patch  = <T>(path: string, body: unknown) => request<T>("PATCH",  path, body);
const del    = <T>(path: string)               => request<T>("DELETE", path);

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ApiUser {
  id: string;
  email: string;
  name: string;
  full_name: string | null;
  niche: string | null;
  goals: string | null;
  primary_platform: string;
  onboarding_complete: boolean;
  created_at: string;
}

export interface WaitlistStats {
  total_joined: number;
  total_seats: number;
  remaining_seats: number;
  recent_joiners: string[];
}

export interface WaitlistJoinResult {
  position: number;
  already_joined: boolean;
}

export interface WaitlistMemberStatus extends WaitlistStats {
  email: string;
  joined: boolean;
  access_approved: boolean;
  approved_at: string | null;
  position: number | null;
}

export interface SocialConnectionStatus {
  platform: string;
  username: string;
  connected_at: string;
  last_synced: string | null;
}

export interface PersonaSource {
  id: string;
  persona_profile_id: string;
  source_type: string;
  url: string | null;
  manual_text: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface PersonaProfile {
  id: string;
  user_id: string;
  status: string;
  niche: string | null;
  target_audience: string | null;
  goals: string[];
  persona_summary: string | null;
  voice_tone: string | null;
  positioning: string | null;
  content_pillars: string[];
  audience_pain_points: string[];
  credibility_signals: string[];
  content_opportunities: string[];
  avoid_topics: string[];
  raw_ai_output: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  sources: PersonaSource[];
}

export interface ContentDraft {
  id: string;
  platform: string;
  content: string;
  status: string;
  scheduled_for: string | null;
  published_at: string | null;
  created_at: string;
}

export interface CalendarInput {
  niche: string;
  platforms: string[];
  weeks?: number;
}

export interface CalendarOutput {
  id: string;
  plan: unknown;
  created_at: string;
}

export interface BrandProfile {
  id: string;
  niche: string;
  tone: string | null;
  audience: string | null;
  confirmed: boolean;
}

// ─── Permanent context (Step 1 onboarding questionnaire) ──────────────────────

export interface PlatformFactEntry {
  best_post_times: string[];
  best_formats: string[];
  avoid: string[];
  confirmed_at: string | null;
}

export interface PermanentContext {
  brand_name: string | null;
  bio: string | null;
  target_audience: string | null;
  content_mission: string | null;
  niche: string | null;
  primary_platform: string;
  platform_facts: Record<string, PlatformFactEntry>;
  context_version: number;
}

export interface PersonaContext {
  voice_tone: string | null;
  sentence_style: string | null;
  hook_patterns: string[];
  content_pillars: string[];
  hashtag_style: string | null;
  emoji_usage: string | null;
  avg_post_length: number | null;
  analysis_based_on_posts: number;
  confidence_score: number;
}

export interface ReportContext {
  top_performing_topics: string[];
  avg_engagement_rate: number | null;
  best_hook_last_cycle: string | null;
  content_gaps: string[];
  posts_analysed: number;
  period_days: number;
  learned_summary: string | null;
  why_wins: string[];
  recommendations: string[];
  avg_hook_score: number | null;
  recurring_improvement: string | null;
}

export interface AssembledContext {
  system_prompt: string;
  permanent: PermanentContext;
  persona: PersonaContext;
  report: ReportContext;
  platform: string;
  missing_layers: string[];
}

export interface UpdatePermanentContextRequest {
  brand_name?: string | null;
  bio?: string | null;
  target_audience?: string | null;
  content_mission?: string | null;
  niche?: string | null;
  primary_platform?: string | null;
}

export interface UpdateContextResult {
  message: string;
  context_version: number;
  missing_layers: string[];
}

// ─── API Namespaces ───────────────────────────────────────────────────────────

const auth = {
  me: ()                                      => get<ApiUser>("/api/v1/auth/me"),
  logout: ()                                  => post("/api/v1/auth/logout", {}),
  onboarding: (payload: {
    full_name: string;
    niche: string;
    goals?: string;
    primary_platform: string;
  })                                          => post<ApiUser>("/api/v1/auth/onboarding", payload),
};

const waitlist = {
  stats: ()                                   => get<WaitlistStats>("/api/v1/waitlist"),
  myStatus: ()                                => get<WaitlistMemberStatus>("/api/v1/waitlist/me"),
  join: (payload: { email: string; name?: string; profession?: string }) =>
    post<WaitlistJoinResult>("/api/v1/waitlist", payload),
};

const connect = {
  status: ()                                  => get<SocialConnectionStatus[]>("/api/v1/connect/status"),
  // Mint a single-use connect token (Bearer auth) so the JWT never enters the start URL.
  createSession: ()                           => post<{ connect_token: string }>("/api/v1/connect/session", {}),
  // Build the OAuth start URL from a single-use connect token (not the raw JWT).
  startUrl: (platform: string, connectToken: string) =>
    `${BASE_URL}/api/v1/connect/${platform}/start?ct=${encodeURIComponent(connectToken)}`,
  disconnect: (platform: string)              => del<{ disconnected: string }>(`/api/v1/connect/${platform}`),
};

const persona = {
  startOnboarding: ()                         => post<PersonaProfile>("/api/v1/persona/onboarding/start", {}),
  addSource: (payload: { source_type: string; url?: string; manual_text?: string }) =>
    post<PersonaSource>("/api/v1/persona/sources", payload),
  listSources: ()                             => get<PersonaSource[]>("/api/v1/persona/sources"),
  scrape: ()                                  => post<{ status: string; results: unknown[] }>("/api/v1/persona/scrape", {}),
  analyze: ()                                 => post<PersonaProfile>("/api/v1/persona/analyze", {}),
  get: ()                                     => get<PersonaProfile>("/api/v1/persona"),
  update: (payload: Partial<PersonaProfile>)  => patch<PersonaProfile>("/api/v1/persona", payload),
  confirm: ()                                 => post<PersonaProfile>("/api/v1/persona/confirm", {}),
};

const content = {
  listDrafts: (status?: string) =>
    get<ContentDraft[]>("/api/v1/content/drafts" + (status ? `?status=${status}` : "")),
  getDraft: (id: string)                      => get<ContentDraft>(`/api/v1/content/drafts/${id}`),
  suggest: (payload: { topic?: string; platform?: string }) =>
    post("/api/v1/content/suggest", payload),
  generate: (payload: unknown)                => post("/api/v1/content/generate", payload),
  repurpose: (payload: unknown)               => post("/api/v1/content/repurpose", payload),
  publishNow: (draftId: string)               => post(`/api/v1/content/drafts/${draftId}/publish`, {}),
  schedule: (payload: unknown)                => post("/api/v1/content/schedule", payload),
  calendarEvents: ()                          => get("/api/v1/content/calendar"),
};

const calendar = {
  generate: (payload: CalendarInput)          => post<CalendarOutput>("/api/v1/calendar/generate", payload),
  list: ()                                    => get<CalendarOutput[]>("/api/v1/calendar/"),
};

const coach = {
  analyze: (payload: unknown)                 => post("/api/v1/coach/analyze", payload),
};

const radar = {
  scan: (payload: unknown)                    => post("/api/v1/radar/scan", payload),
};

const repurpose = {
  generate: (payload: unknown)               => post("/api/v1/repurpose/generate", payload),
};

const brandProfile = {
  get: ()                                    => get<BrandProfile>("/api/v1/brand-profile"),
  upsert: (payload: unknown)                 => post<BrandProfile>("/api/v1/brand-profile", payload),
};

const analytics = {
  summary: ()                                => get("/api/v1/analytics/summary"),
};

const context = {
  get: (platform = "linkedin")               =>
    get<AssembledContext>(`/api/v1/context/?platform=${encodeURIComponent(platform)}`),
  updatePermanent: (payload: UpdatePermanentContextRequest) =>
    patch<UpdateContextResult>("/api/v1/context/", payload),
  prompt: (platform = "linkedin")            =>
    get<{ system_prompt: string; missing_layers: string[]; context_version: number }>(
      `/api/v1/context/prompt?platform=${encodeURIComponent(platform)}`,
    ),
};

const trends = {
  list: ()                                   => get("/api/v1/trends"),
  refresh: ()                                => post("/api/v1/trends/refresh", {}),
};

export const api = {
  auth,
  waitlist,
  connect,
  persona,
  content,
  calendar,
  coach,
  radar,
  repurpose,
  brandProfile,
  analytics,
  context,
  trends,
};
