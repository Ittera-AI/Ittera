"use client";

import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

import {
  productService,
  type AnalyticsPost,
  type AnalyticsSummary,
  type BrandProfile,
  type BrandProfileData,
  type CalendarEvent,
  type CoachResult,
  type ContentInsights,
  type Draft,
  type LinkedInStatus,
  type PublishingSettings,
  type RadarResult,
  type SocialConnectionStatus,
  type Suggestion,
  type TimeSeriesData,
  type TrendDetection,
  type TrendResponse,
} from "@/services/product.service";

type RequestStatus = "idle" | "loading" | "success" | "error";

type LoadingState = {
  dashboard: RequestStatus;
  trends: RequestStatus;
  drafts: RequestStatus;
  analytics: RequestStatus;
  calendar: RequestStatus;
  coach: RequestStatus;
  radar: RequestStatus;
  trendsData: RequestStatus;
  insights: RequestStatus;
};

type TimeSeriesFilter = {
  metric: "engagement_rate" | "likes" | "posts" | "impressions";
  periodDays: number;
  interval: "day" | "week" | "month";
};

type ProductState = {
  // Data
  linkedin: LinkedInStatus | null;
  socialConnections: SocialConnectionStatus[];
  publishingSettings: PublishingSettings | null;
  brandProfile: BrandProfile | null;
  trends: TrendResponse | null;
  suggestions: Suggestion[];
  drafts: Draft[];
  analytics: AnalyticsPost[];
  analyticsSummary: AnalyticsSummary | null;
  calendar: CalendarEvent[];
  currentDraft: Draft | null;
  coachResult: CoachResult | null;
  radarResult: RadarResult | null;
  
  // Analytics enhancements
  trendsData: TimeSeriesData[] | null;
  trendDetection: TrendDetection | null;
  contentInsights: ContentInsights | null;
  trendsFilter: TimeSeriesFilter;

  // Predictions (Agency Tier)
  predictionsData: {
    performance: unknown;
    viral: unknown;
    timing: unknown;
  } | null;
  
  // UI State
  isLoading: boolean;
  loadingStates: LoadingState;
  error: string | null;
  lastUpdated: Record<string, number>;
  
  // Actions
  clearError: () => void;
  clearCoachResult: () => void;
  selectDraft: (draftId: string) => void;
  
  // Async Actions
  loadDashboard: () => Promise<void>;
  connectLinkedIn: () => Promise<void>;
  connectTwitter: () => Promise<void>;
  syncLinkedIn: () => Promise<void>;
  disconnectLinkedIn: () => Promise<void>;
  disconnectTwitter: () => Promise<void>;
  loadPublishingSettings: () => Promise<void>;
  updatePublishingSettings: (settings: PublishingSettings) => Promise<void>;
  generateBrandProfile: () => Promise<void>;
  confirmBrandProfile: () => Promise<void>;
  updateBrandProfile: (profile: BrandProfileData) => Promise<void>;
  loadTrends: () => Promise<void>;
  suggest: (platform: string, topic?: string) => Promise<void>;
  generate: (platform: string, prompt: string, trend?: string, suggestion?: Suggestion) => Promise<void>;
  repurpose: (target: "instagram" | "twitter") => Promise<void>;
  loadDrafts: () => Promise<void>;
  updateDraft: (draftId: string, data: { content?: string; status?: string; scheduled_for?: string | null }) => Promise<void>;
  uploadDraftMedia: (draftId: string, file: File) => Promise<void>;
  deleteDraftMedia: (draftId: string, mediaId: string) => Promise<void>;
  approveDraft: (draftId: string) => Promise<void>;
  publish: (draftId: string) => Promise<void>;
  schedule: (draftId: string, scheduledFor: string) => Promise<void>;
  cancelSchedule: (draftId: string) => Promise<void>;
  loadAnalytics: () => Promise<void>;
  loadAnalyticsSummary: (period_days?: number) => Promise<void>;
  analyzePost: (postId: string) => Promise<void>;
  loadCalendar: () => Promise<void>;
  coachAnalyze: (content: string, platform: string, goal?: string) => Promise<void>;
  scanRadar: (niche: string, platforms: string[], limit?: number) => Promise<void>;
  
  // Analytics trends
  loadTrendsData: (filter?: Partial<TimeSeriesFilter>) => Promise<void>;
  loadTrendDetection: (periodDays?: number) => Promise<void>;
  loadContentInsights: (periodDays?: number) => Promise<void>;
  setTrendsFilter: (filter: Partial<TimeSeriesFilter>) => void;

  // Predictions (Agency Tier)
  setPredictionsData: (data: {
    performance: unknown;
    viral: unknown;
    timing: unknown;
  }) => void;
};

const initialLoadingState: LoadingState = {
  dashboard: "idle",
  trends: "idle",
  drafts: "idle",
  analytics: "idle",
  calendar: "idle",
  coach: "idle",
  radar: "idle",
  trendsData: "idle",
  insights: "idle",
};

// Cache TTL in milliseconds
const CACHE_TTL = {
  dashboard: 5 * 60 * 1000, // 5 minutes
  trends: 10 * 60 * 1000,   // 10 minutes
  drafts: 2 * 60 * 1000,    // 2 minutes
  analytics: 5 * 60 * 1000, // 5 minutes
  calendar: 2 * 60 * 1000,  // 2 minutes
};

function isCacheValid(lastUpdated: number | undefined, ttl: number): boolean {
  if (!lastUpdated) return false;
  return Date.now() - lastUpdated < ttl;
}

function handleError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "Something went wrong. Please try again.";
}

export const useProductStore = create<ProductState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial State
        linkedin: null,
        socialConnections: [],
        publishingSettings: null,
        brandProfile: null,
        trends: null,
        suggestions: [],
        drafts: [],
        analytics: [],
        analyticsSummary: null,
        calendar: [],
        currentDraft: null,
        coachResult: null,
        radarResult: null,
        
        // Analytics enhancements
        trendsData: null,
        trendDetection: null,
        contentInsights: null,
        trendsFilter: {
          metric: "engagement_rate",
          periodDays: 30,
          interval: "week",
        },

        // Predictions (Agency Tier)
        predictionsData: null,
        
        isLoading: false,
        loadingStates: initialLoadingState,
        error: null,
        lastUpdated: {},

        clearError: () => set({ error: null }),
        
        clearCoachResult: () => set({ coachResult: null }),

        selectDraft: (draftId) => {
          const drafts = get().drafts;
          const draft = drafts.find((item) => item.id === draftId) ?? null;
          set({ currentDraft: draft });
        },

        loadDashboard: async () => {
          const key = "dashboard";
          if (isCacheValid(get().lastUpdated[key], CACHE_TTL.dashboard) && get().linkedin) {
            return; // Use cached data
          }

          set({ loadingStates: { ...get().loadingStates, dashboard: "loading" } });
          try {
            const [linkedin, brandProfile, socialConnections, publishingSettings] = await Promise.all([
              productService.linkedinStatus(),
              productService.getBrandProfile(),
              productService.socialConnections(),
              productService.getPublishingSettings(),
            ]);
            set({ 
              linkedin, 
              brandProfile, 
              socialConnections,
              publishingSettings,
              loadingStates: { ...get().loadingStates, dashboard: "success" },
              lastUpdated: { ...get().lastUpdated, [key]: Date.now() },
              error: null,
            });
          } catch (error) {
            set({ 
              error: handleError(error),
              loadingStates: { ...get().loadingStates, dashboard: "error" },
            });
            throw error;
          }
        },

        connectLinkedIn: async () => {
          set({ isLoading: true, error: null });
          try {
            await productService.connectLinkedIn();
            const [linkedin, socialConnections] = await Promise.all([
              productService.linkedinStatus(),
              productService.socialConnections(),
            ]);
            set({ linkedin, socialConnections, isLoading: false, lastUpdated: { ...get().lastUpdated, dashboard: 0 } });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        syncLinkedIn: async () => {
          set({ isLoading: true, error: null });
          try {
            const result = await productService.syncLinkedIn();
            if (result.sync_path === "unavailable") {
              throw new Error(result.message);
            }
            const [linkedin, analytics] = await Promise.all([
              productService.linkedinStatus(),
              productService.analyticsPosts(),
            ]);
            set({ 
              linkedin, 
              analytics, 
              isLoading: false,
              lastUpdated: { ...get().lastUpdated, analytics: Date.now() },
            });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        connectTwitter: async () => {
          set({ isLoading: true, error: null });
          try {
            await productService.connectTwitter();
            const socialConnections = await productService.socialConnections();
            set({ socialConnections, isLoading: false, lastUpdated: { ...get().lastUpdated, dashboard: 0 } });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        disconnectLinkedIn: async () => {
          set({ isLoading: true, error: null });
          try {
            await productService.disconnectLinkedIn();
            const [linkedin, socialConnections] = await Promise.all([
              productService.linkedinStatus(),
              productService.socialConnections(),
            ]);
            set({ linkedin, socialConnections, isLoading: false, lastUpdated: { ...get().lastUpdated, dashboard: 0 } });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        disconnectTwitter: async () => {
          set({ isLoading: true, error: null });
          try {
            await productService.disconnectTwitter();
            const socialConnections = await productService.socialConnections();
            set({ socialConnections, isLoading: false, lastUpdated: { ...get().lastUpdated, dashboard: 0 } });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        loadPublishingSettings: async () => {
          try {
            const [publishingSettings, socialConnections] = await Promise.all([
              productService.getPublishingSettings(),
              productService.socialConnections(),
            ]);
            set({ publishingSettings, socialConnections, error: null });
          } catch (error) {
            set({ error: handleError(error) });
            throw error;
          }
        },

        updatePublishingSettings: async (settings) => {
          set({ isLoading: true, error: null });
          try {
            const publishingSettings = await productService.updatePublishingSettings(settings);
            set({ publishingSettings, isLoading: false });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        generateBrandProfile: async () => {
          set({ isLoading: true, error: null });
          try {
            const brandProfile = await productService.generateBrandProfile();
            set({ brandProfile, isLoading: false });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        confirmBrandProfile: async () => {
          set({ isLoading: true, error: null });
          try {
            const brandProfile = await productService.confirmBrandProfile();
            set({ brandProfile, isLoading: false });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        updateBrandProfile: async (profile) => {
          set({ isLoading: true, error: null });
          try {
            const brandProfile = await productService.updateBrandProfile(profile);
            set({ brandProfile, isLoading: false });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        loadTrends: async () => {
          const key = "trends";
          if (isCacheValid(get().lastUpdated[key], CACHE_TTL.trends)) {
            return; // Use cached data
          }

          set({ loadingStates: { ...get().loadingStates, trends: "loading" } });
          try {
            const trends = await productService.getTrends();
            set({ 
              trends, 
              loadingStates: { ...get().loadingStates, trends: "success" },
              lastUpdated: { ...get().lastUpdated, [key]: Date.now() },
              error: null,
            });
          } catch (error) {
            set({ 
              error: handleError(error),
              loadingStates: { ...get().loadingStates, trends: "error" },
            });
            throw error;
          }
        },

        suggest: async (platform, topic) => {
          set({ isLoading: true, error: null });
          try {
            const result = await productService.suggest(platform, topic);
            set({ suggestions: result.suggestions, isLoading: false, error: null });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        generate: async (platform, prompt, trend, suggestion) => {
          set({ isLoading: true, error: null });
          try {
            await productService.generate(platform, prompt, trend, suggestion);
            const drafts = await productService.drafts();
            set({ 
              drafts, 
              currentDraft: drafts[0] ?? null,
              isLoading: false,
              error: null,
            });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        repurpose: async (target) => {
          const draft = get().currentDraft;
          if (!draft) return;
          
          set({ isLoading: true, error: null });
          try {
            await productService.repurpose(draft.id, target);
            const drafts = await productService.drafts();
            const updatedDraft = drafts.find((item) => item.id === draft.id);
            set({ 
              drafts, 
              currentDraft: updatedDraft ?? drafts[0] ?? null,
              isLoading: false,
              error: null,
            });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        loadDrafts: async () => {
          const key = "drafts";
          if (isCacheValid(get().lastUpdated[key], CACHE_TTL.drafts)) {
            return; // Use cached data
          }

          set({ loadingStates: { ...get().loadingStates, drafts: "loading" } });
          try {
            const drafts = await productService.drafts();
            set({ 
              drafts, 
              currentDraft: drafts[0] ?? null,
              loadingStates: { ...get().loadingStates, drafts: "success" },
              lastUpdated: { ...get().lastUpdated, [key]: Date.now() },
              error: null,
            });
          } catch (error) {
            set({ 
              error: handleError(error),
              loadingStates: { ...get().loadingStates, drafts: "error" },
            });
            throw error;
          }
        },

        updateDraft: async (draftId, data) => {
          set({ isLoading: true, error: null });
          try {
            const updated = await productService.updateDraft(draftId, data);
            const drafts = get().drafts.map((draft) => (draft.id === draftId ? updated : draft));
            set({ drafts, currentDraft: updated, isLoading: false });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        uploadDraftMedia: async (draftId, file) => {
          set({ isLoading: true, error: null });
          try {
            await productService.uploadDraftMedia(draftId, file);
            const drafts = await productService.drafts();
            const updatedDraft = drafts.find((item) => item.id === draftId);
            set({ drafts, currentDraft: updatedDraft ?? get().currentDraft, isLoading: false });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        deleteDraftMedia: async (draftId, mediaId) => {
          set({ isLoading: true, error: null });
          try {
            await productService.deleteDraftMedia(draftId, mediaId);
            const drafts = await productService.drafts();
            const updatedDraft = drafts.find((item) => item.id === draftId);
            set({ drafts, currentDraft: updatedDraft ?? get().currentDraft, isLoading: false });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        approveDraft: async (draftId) => {
          set({ isLoading: true, error: null });
          try {
            const updated = await productService.approveDraft(draftId);
            const [drafts, calendar] = await Promise.all([
              productService.drafts(),
              productService.calendar(),
            ]);
            set({ drafts, calendar, currentDraft: updated, isLoading: false });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        publish: async (draftId) => {
          set({ isLoading: true, error: null });
          try {
            await productService.publish(draftId);
            const [drafts, calendar] = await Promise.all([
              productService.drafts(),
              productService.calendar(),
            ]);
            set({ 
              drafts, 
              calendar,
              isLoading: false,
              error: null,
            });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        schedule: async (draftId, scheduledFor) => {
          set({ isLoading: true, error: null });
          try {
            await productService.schedule(draftId, scheduledFor);
            const [drafts, calendar] = await Promise.all([
              productService.drafts(),
              productService.calendar(),
            ]);
            set({ 
              drafts, 
              calendar,
              isLoading: false,
              error: null,
            });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        cancelSchedule: async (draftId) => {
          set({ isLoading: true, error: null });
          try {
            await productService.cancelSchedule(draftId);
            const [drafts, calendar] = await Promise.all([
              productService.drafts(),
              productService.calendar(),
            ]);
            set({ 
              drafts, 
              calendar,
              isLoading: false,
              error: null,
            });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        loadAnalytics: async () => {
          const key = "analytics";
          if (isCacheValid(get().lastUpdated[key], CACHE_TTL.analytics)) {
            return; // Use cached data
          }

          set({ loadingStates: { ...get().loadingStates, analytics: "loading" } });
          try {
            const analytics = await productService.analyticsPosts();
            set({ 
              analytics,
              loadingStates: { ...get().loadingStates, analytics: "success" },
              lastUpdated: { ...get().lastUpdated, [key]: Date.now() },
              error: null,
            });
          } catch (error) {
            set({ 
              error: handleError(error),
              loadingStates: { ...get().loadingStates, analytics: "error" },
            });
            throw error;
          }
        },

        loadAnalyticsSummary: async (period_days = 30) => {
          set({ loadingStates: { ...get().loadingStates, analytics: "loading" } });
          try {
            const analyticsSummary = await productService.analyticsSummary(period_days);
            set({ 
              analyticsSummary,
              loadingStates: { ...get().loadingStates, analytics: "success" },
              error: null,
            });
          } catch (error) {
            set({ 
              error: handleError(error),
              loadingStates: { ...get().loadingStates, analytics: "error" },
            });
            throw error;
          }
        },

        analyzePost: async (postId) => {
          set({ isLoading: true, error: null });
          try {
            await productService.analyzePost(postId);
            const analytics = await productService.analyticsPosts();
            set({ 
              analytics,
              isLoading: false,
              error: null,
            });
          } catch (error) {
            set({ error: handleError(error), isLoading: false });
            throw error;
          }
        },

        loadCalendar: async () => {
          const key = "calendar";
          if (isCacheValid(get().lastUpdated[key], CACHE_TTL.calendar)) {
            return; // Use cached data
          }

          set({ loadingStates: { ...get().loadingStates, calendar: "loading" } });
          try {
            const [calendar, drafts] = await Promise.all([
              productService.calendar(),
              productService.drafts(),
            ]);
            set({ 
              calendar, 
              drafts,
              loadingStates: { ...get().loadingStates, calendar: "success" },
              lastUpdated: { ...get().lastUpdated, [key]: Date.now() },
              error: null,
            });
          } catch (error) {
            set({ 
              error: handleError(error),
              loadingStates: { ...get().loadingStates, calendar: "error" },
            });
            throw error;
          }
        },

        coachAnalyze: async (content, platform, goal) => {
          set({ loadingStates: { ...get().loadingStates, coach: "loading" } });
          try {
            const result = await productService.coachAnalyze(content, platform, goal);
            set({ 
              coachResult: result,
              loadingStates: { ...get().loadingStates, coach: "success" },
              error: null,
            });
          } catch (error) {
            set({ 
              error: handleError(error),
              loadingStates: { ...get().loadingStates, coach: "error" },
            });
            throw error;
          }
        },

        scanRadar: async (niche, platforms, limit) => {
          set({ loadingStates: { ...get().loadingStates, radar: "loading" } });
          try {
            const result = await productService.radarScan(niche, platforms, limit);
            set({
              radarResult: result,
              loadingStates: { ...get().loadingStates, radar: "success" },
              error: null,
            });
          } catch (error) {
            set({
              error: handleError(error),
              loadingStates: { ...get().loadingStates, radar: "error" },
            });
            throw error;
          }
        },
        
        // Analytics trends
        loadTrendsData: async (filter) => {
          const currentFilter = get().trendsFilter;
          const newFilter = { ...currentFilter, ...filter };
          
          set({ 
            trendsFilter: newFilter,
            loadingStates: { ...get().loadingStates, trendsData: "loading" } 
          });
          
          try {
            const data = await productService.getTrendsData(
              newFilter.metric,
              newFilter.periodDays,
              newFilter.interval
            );
            set({
              trendsData: data,
              loadingStates: { ...get().loadingStates, trendsData: "success" },
              error: null,
            });
          } catch (error) {
            set({
              error: handleError(error),
              loadingStates: { ...get().loadingStates, trendsData: "error" },
            });
            throw error;
          }
        },
        
        loadTrendDetection: async (periodDays = 30) => {
          set({ loadingStates: { ...get().loadingStates, trendsData: "loading" } });
          try {
            const result = await productService.getTrendsDetect(periodDays);
            set({
              trendDetection: result,
              loadingStates: { ...get().loadingStates, trendsData: "success" },
              error: null,
            });
          } catch (error) {
            set({
              error: handleError(error),
              loadingStates: { ...get().loadingStates, trendsData: "error" },
            });
            throw error;
          }
        },
        
        loadContentInsights: async (periodDays = 30) => {
          set({ loadingStates: { ...get().loadingStates, insights: "loading" } });
          try {
            const result = await productService.getInsights(periodDays);
            set({
              contentInsights: result,
              loadingStates: { ...get().loadingStates, insights: "success" },
              error: null,
            });
          } catch (error) {
            set({
              error: handleError(error),
              loadingStates: { ...get().loadingStates, insights: "error" },
            });
            throw error;
          }
        },
        
        setTrendsFilter: (filter) => {
          set({ trendsFilter: { ...get().trendsFilter, ...filter } });
        },

        // Predictions (Agency Tier)
        setPredictionsData: (data) => {
          set({ predictionsData: data });
        },
      }),
      {
        name: "iterra-product-store",
        partialize: (state) => ({
          // Only persist non-sensitive data
          linkedin: state.linkedin,
          socialConnections: state.socialConnections,
          publishingSettings: state.publishingSettings,
          brandProfile: state.brandProfile,
          suggestions: state.suggestions,
          drafts: state.drafts,
          currentDraft: state.currentDraft,
          lastUpdated: state.lastUpdated,
        }),
      }
    ),
    { name: "ProductStore" }
  )
);
