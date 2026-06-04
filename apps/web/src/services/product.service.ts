import type { components } from "@iterra/shared-types";

import { supabase } from "@/lib/supabase";
import { apiFetch } from "@/services/api";

type Schemas = components["schemas"];

export type BrandProfileData = Schemas["BrandProfileData"];
export type BrandProfile = Schemas["BrandProfileResponse"];
export type LinkedInStatus = Schemas["LinkedInStatusResponse"] & {
  scopes?: string[];
  posting_ready?: boolean;
  read_sync_ready?: boolean;
  missing_posting_scopes?: string[];
  missing_read_scopes?: string[];
  reconnect_required?: boolean;
  message?: string | null;
};
export type Trend = Schemas["TrendItemResponse"];
export type TrendResponse = Schemas["TrendResponse"];
export type Suggestion = Schemas["ContentSuggestion"];
export interface DraftMedia {
  id: string;
  filename: string;
  mime_type: string;
  preview_url?: string | null;
  drive_file_id?: string | null;
  status: string;
  position?: number;
}

export type Draft = Schemas["DraftResponse"] & {
  media?: DraftMedia[];
  review_status?: "draft" | "review_due" | "approved" | "rejected";
  status?: "draft" | "scheduled" | "publishing" | "published" | "failed" | "cancelled";
  auto_post_enabled_snapshot?: boolean;
  persona_fit_score?: number | null;
  persona_fit_notes?: string[];
};
export type AnalyticsPost = Schemas["PostWithAnalysis"];
export type PostAnalysis = Schemas["PostAnalysisResponse"];
export type CalendarEvent = Schemas["CalendarEventResponse"] & {
  media?: DraftMedia[];
  review_status?: "draft" | "review_due" | "approved" | "rejected";
  status?: "scheduled" | "publishing" | "published" | "failed" | "cancelled";
};
export type CoachResult = Schemas["CoachOutput"];
export type RadarTrendItem = Schemas["TrendItem"];
export type RadarResult = Schemas["RadarOutput"];

export interface SocialConnectionStatus {
  platform: string;
  username?: string | null;
  connected_at?: string | null;
  last_synced?: string | null;
  scopes?: string[];
  missing_scopes?: string[];
  missing_read_scopes?: string[];
  posting_ready?: boolean;
  read_sync_ready?: boolean;
  reconnect_required?: boolean;
}

export interface PublishingSettings {
  auto_post_enabled: boolean;
}

export interface LinkedInRealSyncResult {
  synced_posts: number;
  total_posts: number;
  last_synced_at: string;
  message: string;
  sync_path: "oauth_api" | "cookie_auth" | "unavailable" | "mock";
  ready_for_analysis: boolean;
}

export interface TrendMetrics {
  direction: "up" | "down" | "flat";
  percent_change?: number | null;
  absolute_change: number;
}

export interface AnalyticsSummary {
  total_posts: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_impressions: number;
  avg_engagement_rate: number;
  best_performing_post?: AnalyticsPost | null;
  posts_analyzed: number;
  analysis_coverage_percent: number;
  platform_breakdown: Record<string, number>;
  period_days: number;
  trends?: {
    posts_change: TrendMetrics;
    engagement_rate_change: TrendMetrics;
    likes_change: TrendMetrics;
  } | null;
  engagement_distribution?: {
    high: number;
    good: number;
    average: number;
    low: number;
  } | null;
  avg_analysis_scores?: {
    hook_score?: number | null;
    structure_score?: number | null;
    tone_score?: number | null;
  } | null;
}

export interface TimeSeriesData {
  date: string;
  value: number;
  posts_count: number;
  interval?: string | null;
  ma7?: number | null;
  ma30?: number | null;
}

export interface ContentInsights {
  period_days: number;
  analyzed_posts_count: number;
  top_performer_avg_scores: {
    hook_score: number;
    structure_score: number;
    tone_score: number;
  };
  identified_strengths: string[];
  hook_patterns?: {
    distribution: Record<string, number>;
    dominant_pattern: string;
    dominant_percentage: number;
    insights: string[];
  };
  length_patterns?: {
    top_performer_avg_chars: number;
    bottom_performer_avg_chars: number;
    difference: number;
    insight: string;
    optimal_range: { min: number; max: number; ideal: number };
  };
  quality_engagement_correlation?: {
    correlation: number;
    strength: "strong" | "moderate" | "weak";
    insight: string;
  };
  recommendations: string[];
  message?: string | null;
}

export interface TrendDetection {
  has_enough_data: boolean;
  period_days?: number | null;
  message?: string | null;
  engagement_rate?: Record<string, unknown> | null;
  post_volume?: Record<string, unknown> | null;
  anomalies: Array<Record<string, unknown>>;
  recommendations: string[];
}

export type PredictionCategory = "highly_viral" | "viral_potential" | "average" | "below_average" | "unlikely";

export interface PerformancePredictionResponse {
  prediction_id?: string;
  metrics: {
    likes: number;
    comments: number;
    shares: number;
    impressions: number;
    engagement_rate: number;
  };
  confidence: {
    overall_confidence: number;
    engagement_rate_ci: {
      lower: number;
      upper: number;
      confidence: number;
    };
  };
  feature_importance: Array<{
    feature: string;
    importance: number;
    impact: "positive" | "negative" | "neutral";
    explanation: string;
  }>;
  improvement_suggestions: string[];
  comparative_analysis?: string | null;
}

export interface ViralPredictionResponse {
  prediction_id?: string;
  viral_probability: number;
  viral_score: number;
  category: PredictionCategory;
  patterns: Array<{
    pattern_type: string;
    score: number;
    detected: boolean;
    explanation: string;
    examples: string[];
  }>;
  viral_triggers: string[];
  amplification_suggestions: string[];
}

export interface TimingPredictionResponse {
  prediction_id?: string;
  optimal_time: string;
  confidence_score: number;
  alternative_slots: Array<{
    day: string;
    hour: number;
    score: number;
    predicted_engagement_rate: number;
    reasoning: string;
  }>;
  detected_patterns: Array<{
    pattern_type: string;
    description: string;
    confidence: number;
  }>;
  best_days: string[];
  best_hours: number[];
}

export interface PredictionAllResponse {
  performance?: PerformancePredictionResponse;
  viral?: ViralPredictionResponse;
  timing?: TimingPredictionResponse;
}

export interface CompetitorResponse {
  id: string;
  name: string;
  platform: string;
  handle: string;
  profile_url?: string | null;
  follower_count?: number | null;
  niche_tags?: string[];
  is_active: boolean;
  last_synced_at?: string | null;
  recent_posts_count?: number;
}

export interface CompetitorAnalysisResponse {
  analysis_id: string;
  analysis_type: string;
  competitor_id?: string | null;
  created_at: string;
  findings_summary: Record<string, unknown>;
}

export interface ContentGapResponse extends CompetitorAnalysisResponse {
  gap_topics: Array<{
    topic: string;
    opportunity_score: number;
    why_valuable: string;
    difficulty: string;
  }>;
  high_impact_opportunities: Array<{
    opportunity: string;
    rationale: string;
    effort_required: string;
    priority: number;
  }>;
  quick_wins: string[];
  format_gaps: Array<{
    format: string;
    competitor_usage: string;
    your_opportunity: string;
    implementation_effort: string;
  }>;
}

async function getAccessToken(): Promise<string> {
  const { data, error } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (error || !token) {
    throw new Error("You need to be signed in.");
  }
  return token;
}

function openConnectPopup(url: string, platform: "linkedin" | "twitter"): Promise<void> {
  return new Promise((resolve, reject) => {
    const popup = window.open(url, `ittera-${platform}-connect`, "width=520,height=720");
    if (!popup) {
      reject(new Error("Popup was blocked. Allow popups and try again."));
      return;
    }

    const cleanup = () => {
      window.removeEventListener("message", onMessage);
      window.clearInterval(checkClosed);
      window.clearTimeout(timeout);
    };

    const onMessage = (event: MessageEvent) => {
      const payload = event.data;
      if (!payload || payload.type !== "ittera_oauth" || payload.platform !== platform) return;
      cleanup();
      if (payload.status === "connected") {
        resolve();
      } else {
        reject(new Error(payload.error || `${platform} connection failed.`));
      }
    };

    const checkClosed = window.setInterval(() => {
      if (popup.closed) {
        cleanup();
        reject(new Error(`${platform} connection was cancelled.`));
      }
    }, 500);

    const timeout = window.setTimeout(() => {
      cleanup();
      try {
        popup.close();
      } catch {
        // Ignore popup cleanup failures.
      }
      reject(new Error(`${platform} connection timed out.`));
    }, 120000);

    window.addEventListener("message", onMessage);
  });
}

function mediaApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL;
  if (raw === "" || raw === "same-origin") return "";
  if (raw !== undefined && raw.trim() !== "") return raw.replace(/\/$/, "");
  return "";
}

export const productService = {
  linkedinStatus: () => apiFetch<LinkedInStatus>("/api/v1/linkedin/status"),
  socialConnections: () => apiFetch<SocialConnectionStatus[]>("/api/v1/connect/status"),
  connectLinkedIn: async () => {
    const token = await getAccessToken();
    await openConnectPopup(`/api/v1/connect/linkedin/start?token=${encodeURIComponent(token)}`, "linkedin");
  },
  connectTwitter: async () => {
    const token = await getAccessToken();
    await openConnectPopup(`/api/v1/connect/twitter/start?token=${encodeURIComponent(token)}`, "twitter");
  },
  syncLinkedIn: () => apiFetch<LinkedInRealSyncResult>("/api/v1/linkedin/sync/real", { method: "POST" }),
  disconnectLinkedIn: () => apiFetch("/api/v1/connect/linkedin", { method: "DELETE" }),
  disconnectTwitter: () => apiFetch("/api/v1/connect/twitter", { method: "DELETE" }),
  getPublishingSettings: () => apiFetch<PublishingSettings>("/api/v1/users/me/publishing-settings"),
  updatePublishingSettings: (settings: PublishingSettings) =>
    apiFetch<PublishingSettings>("/api/v1/users/me/publishing-settings", {
      method: "PATCH",
      body: JSON.stringify(settings),
    }),
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
  updateDraft: (draft_id: string, data: { content?: string; status?: string; scheduled_for?: string | null }) =>
    apiFetch<Draft>(`/api/v1/content/drafts/${draft_id}`, { method: "PATCH", body: JSON.stringify(data) }),
  uploadDraftMedia: (draft_id: string, file: File) => {
    const body = new FormData();
    body.append("file", file);
    return apiFetch<DraftMedia>(`/api/v1/content/drafts/${draft_id}/media`, { method: "POST", body });
  },
  mediaPreviewUrl: async (media_id: string) => {
    const token = await getAccessToken();
    const response = await fetch(`${mediaApiBaseUrl()}/api/v1/content/media-file/${encodeURIComponent(media_id)}`, {
      credentials: "include",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      throw new Error("Could not load image preview.");
    }
    return URL.createObjectURL(await response.blob());
  },
  deleteDraftMedia: (draft_id: string, media_id: string) =>
    apiFetch(`/api/v1/content/drafts/${draft_id}/media/${media_id}`, { method: "DELETE" }),
  approveDraft: (draft_id: string) =>
    apiFetch<Draft>(`/api/v1/content/drafts/${draft_id}/approve`, { method: "POST" }),
  publish: (draft_id: string) =>
    apiFetch("/api/v1/content/drafts/" + encodeURIComponent(draft_id) + "/publish-now", { method: "POST" }),
  schedule: (draft_id: string, scheduled_for: string) =>
    apiFetch("/api/v1/content/schedule", { method: "POST", body: JSON.stringify({ draft_id, scheduled_for }) }),
  cancelSchedule: (draft_id: string) => apiFetch(`/api/v1/content/schedule/${draft_id}`, { method: "DELETE" }),
  calendar: () => apiFetch<CalendarEvent[]>("/api/v1/content/calendar"),
  analyticsSummary: (period_days = 30) =>
    apiFetch<AnalyticsSummary>(`/api/v1/analytics/summary?period_days=${period_days}`),
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
  // Analytics trends
  getTrendsData: (metric: string, period_days = 30, interval: "day" | "week" | "month" = "week") =>
    apiFetch<TimeSeriesData[]>(`/api/v1/analytics/trends?metric=${metric}&period_days=${period_days}&interval=${interval}`),
  getTrendsDetect: (period_days = 30) =>
    apiFetch<TrendDetection>(`/api/v1/analytics/trends/detect?period_days=${period_days}`),
  getInsights: (period_days = 30) =>
    apiFetch<ContentInsights>(`/api/v1/analytics/insights?period_days=${period_days}`),

  // Predictions
  predictPerformance: (data: {
    content: string;
    platform: "linkedin" | "twitter" | "instagram" | "facebook";
    content_type?: "post" | "article" | "video" | "image" | "poll";
    hashtags?: string[];
    mentioned_accounts?: string[];
  }) =>
    apiFetch<PerformancePredictionResponse>("/api/v1/predictions/performance", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  predictViral: (data: {
    content: string;
    platform?: "linkedin" | "twitter" | "instagram" | "facebook";
  }) =>
    apiFetch<ViralPredictionResponse>("/api/v1/predictions/viral", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  predictTiming: (data: {
    content: string;
    platform?: "linkedin" | "twitter" | "instagram" | "facebook";
    timezone?: string;
    allowed_days?: string[];
  }) =>
    apiFetch<TimingPredictionResponse>("/api/v1/predictions/timing", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  predictAll: (data: {
    content: string;
    platform: "linkedin" | "twitter" | "instagram" | "facebook";
    content_type?: "post" | "article" | "video" | "image" | "poll";
    hashtags?: string[];
    mentioned_accounts?: string[];
  }) => {
    const params = new URLSearchParams({
      content: data.content,
      platform: data.platform,
    });
    return apiFetch<PredictionAllResponse>(`/api/v1/predictions/all?${params}`, { method: "POST" });
  },

  // Competitors
  getCompetitors: () => apiFetch<CompetitorResponse[]>("/api/v1/competitors"),
  addCompetitor: (data: {
    name: string;
    platform: string;
    handle: string;
    profile_url?: string;
    niche_tags?: string[];
  }) =>
    apiFetch<CompetitorResponse>("/api/v1/competitors", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  analyzeCompetitorStrategy: (competitorId: string) =>
    apiFetch<CompetitorAnalysisResponse>(`/api/v1/competitors/${competitorId}/analyze/strategy`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  analyzeContentGaps: () =>
    apiFetch<ContentGapResponse>("/api/v1/competitors/analyze/gaps", {
      method: "POST",
      body: JSON.stringify({}),
    }),
  benchmarkTrend: (trendTopic: string) =>
    apiFetch("/api/v1/competitors/analyze/trend", {
      method: "POST",
      body: JSON.stringify({ trend_topic: trendTopic }),
    }),

  // Reports
  generateAnalyticsReport: (data: { period_days?: number; include_charts?: boolean }) =>
    apiFetch("/api/v1/reports/analytics", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  generateCompetitiveReport: (data?: { analysis_id?: string }) =>
    apiFetch("/api/v1/reports/competitive", {
      method: "POST",
      body: JSON.stringify(data || {}),
    }),
  downloadReport: (reportId: string) =>
    apiFetch(`/api/v1/reports/download/${reportId}`),
};
