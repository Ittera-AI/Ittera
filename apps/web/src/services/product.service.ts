import type { components } from "@iterra/shared-types";

import { apiFetch } from "@/services/api";

type Schemas = components["schemas"];

export type BrandProfileData = Schemas["BrandProfileData"];
export type BrandProfile = Schemas["BrandProfileResponse"];
export type LinkedInStatus = Schemas["LinkedInStatusResponse"];
export type Trend = Schemas["TrendItemResponse"];
export type TrendResponse = Schemas["TrendResponse"];
export type Suggestion = Schemas["ContentSuggestion"];
export type Draft = Schemas["DraftResponse"];
export type AnalyticsPost = Schemas["PostWithAnalysis"];
export type PostAnalysis = Schemas["PostAnalysisResponse"];
export type CalendarEvent = Schemas["CalendarEventResponse"];
export type CoachResult = Schemas["CoachOutput"];
export type RadarTrendItem = Schemas["TrendItem"];
export type RadarResult = Schemas["RadarOutput"];

export const productService = {
  linkedinStatus: () => apiFetch<LinkedInStatus>("/api/v1/linkedin/status"),
  connectLinkedIn: () => apiFetch("/api/v1/linkedin/connect/mock", { method: "POST" }),
  syncLinkedIn: () => apiFetch("/api/v1/linkedin/sync", { method: "POST" }),
  getBrandProfile: () => apiFetch<BrandProfile>("/api/v1/brand-profile"),
  generateBrandProfile: () => apiFetch<BrandProfile>("/api/v1/brand-profile/generate", { method: "POST" }),
  updateBrandProfile: (profile: BrandProfileData) =>
    apiFetch<BrandProfile>("/api/v1/brand-profile", { method: "PATCH", body: JSON.stringify({ profile }) }),
  confirmBrandProfile: () => apiFetch<BrandProfile>("/api/v1/brand-profile/confirm", { method: "POST" }),
  getTrends: () => apiFetch<TrendResponse>("/api/v1/trends"),
  refreshTrends: () => apiFetch<TrendResponse>("/api/v1/trends/refresh", { method: "POST" }),
  suggest: (platform: string, topic?: string) =>
    apiFetch<{ suggestions: Suggestion[] }>("/api/v1/content/suggest", {
      method: "POST",
      body: JSON.stringify({ platform, topic }),
    }),
  generate: (platform: string, prompt: string, trend_used?: string, suggestion?: Suggestion) =>
    apiFetch<{ draft_id: string; content: string; word_count: number; within_platform_limit: boolean }>(
      "/api/v1/content/generate",
      { method: "POST", body: JSON.stringify({ platform, prompt, trend_used, suggestion }) },
    ),
  repurpose: (draft_id: string, target_platform: "instagram" | "twitter") =>
    apiFetch<{ draft_id: string; content: string; platform: string }>("/api/v1/content/repurpose", {
      method: "POST",
      body: JSON.stringify({ draft_id, target_platform }),
    }),
  drafts: () => apiFetch<Draft[]>("/api/v1/content/drafts"),
  publish: (draft_id: string) =>
    apiFetch("/api/v1/content/publish", { method: "POST", body: JSON.stringify({ draft_id }) }),
  schedule: (draft_id: string, scheduled_for: string) =>
    apiFetch("/api/v1/content/schedule", { method: "POST", body: JSON.stringify({ draft_id, scheduled_for }) }),
  cancelSchedule: (draft_id: string) => apiFetch(`/api/v1/content/schedule/${draft_id}`, { method: "DELETE" }),
  calendar: () => apiFetch<CalendarEvent[]>("/api/v1/content/calendar"),
  analyticsPosts: () => apiFetch<AnalyticsPost[]>("/api/v1/analytics/posts"),
  analyzePost: (postId: string) =>
    apiFetch<PostAnalysis>(`/api/v1/analytics/analyze/${postId}`, { method: "POST" }),
  coachAnalyze: (content: string, platform: string, goal?: string) =>
    apiFetch<CoachResult>("/api/v1/coach/analyze", {
      method: "POST",
      body: JSON.stringify({ content, platform, goal }),
    }),
  radarScan: (niche: string, platforms: string[], limit = 5) =>
    apiFetch<RadarResult>("/api/v1/radar/scan", {
      method: "POST",
      body: JSON.stringify({ niche, platforms, limit }),
    }),
};
