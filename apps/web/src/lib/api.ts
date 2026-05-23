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

import { supabase } from "@/lib/supabase";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Core fetch wrapper ───────────────────────────────────────────────────────

async function getToken(): Promise<string | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function request<T>(
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    credentials: "include", // also sends the legacy ittera_token cookie if present
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const json = await res.json();
      detail = json.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

const get  = <T>(path: string)              => request<T>("GET",    path);
const post = <T>(path: string, body: unknown) => request<T>("POST",   path, body);

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

export interface WaitlistMemberStatus extends WaitlistStats {
  email: string;
  joined: boolean;
  position: number | null;
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

// ─── API Namespaces ───────────────────────────────────────────────────────────

const auth = {
  me: ()                                      => get<ApiUser>("/api/v1/auth/me"),
  logout: ()                                  => post("/api/v1/auth/logout", {}),
  onboarding: (payload: {
    full_name?: string;
    niche?: string;
    goals?: string;
    primary_platform: string;
  })                                          => post<ApiUser>("/api/v1/auth/onboarding", payload),
};

const waitlist = {
  stats: ()                                   => get<WaitlistStats>("/api/v1/waitlist"),
  myStatus: ()                                => get<WaitlistMemberStatus>("/api/v1/waitlist/me"),
  join: (payload: { email: string; name?: string; profession?: string }) =>
    post("/api/v1/waitlist", payload),
};

const content = {
  listDrafts: (status?: string) =>
    get<ContentDraft[]>("/api/v1/content/drafts" + (status ? `?status=${status}` : "")),
  getDraft: (id: string)                      => get<ContentDraft>(`/api/v1/content/drafts/${id}`),
  suggest: (payload: { topic?: string })      => post("/api/v1/content/suggest", payload),
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

const trends = {
  list: ()                                   => get("/api/v1/trends"),
  refresh: ()                                => post("/api/v1/trends/refresh", {}),
};

export interface PersonaProfile {
  id: string;
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
  sources?: PersonaSource[];
}

export interface PersonaSource {
  id: string;
  source_type: string;
  url: string | null;
  manual_text: string | null;
  status: string;
  error_message: string | null;
}

const persona = {
  startOnboarding: () => post<PersonaProfile>("/api/v1/persona/onboarding/start", {}),
  addSource: (payload: { source_type: string; url?: string; manual_text?: string }) => post<PersonaSource>("/api/v1/persona/sources", payload),
  listSources: () => get<PersonaSource[]>("/api/v1/persona/sources"),
  scrape: () => post<{status: string, results: any[]}>("/api/v1/persona/scrape", {}),
  analyze: () => post<PersonaProfile>("/api/v1/persona/analyze", {}),
  get: () => get<PersonaProfile>("/api/v1/persona"),
  update: (payload: Partial<PersonaProfile>) => request<PersonaProfile>("PATCH", "/api/v1/persona", payload),
  confirm: () => post<PersonaProfile>("/api/v1/persona/confirm", {}),
};

export interface SocialConnectionStatus {
  platform: string;
  username: string;
  connected_at: string;
  last_synced: string | null;
}

const connect = {
  status: () => get<SocialConnectionStatus[]>("/api/v1/connect/status"),
  disconnect: (platform: string) => request<{ disconnected: string }>("DELETE", `/api/v1/connect/${platform}`),
  // Returns the URL to open in a popup — the popup handles the OAuth redirect
  startUrl: (platform: "twitter" | "linkedin" | "instagram", token: string) =>
    `${BASE_URL}/api/v1/connect/${platform}/start?token=${encodeURIComponent(token)}`,
};

export const api = {
  auth,
  waitlist,
  content,
  calendar,
  coach,
  radar,
  repurpose,
  brandProfile,
  analytics,
  trends,
  persona,
  connect,
};

export { ApiError };
