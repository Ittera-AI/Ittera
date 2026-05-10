"use client";

import { create } from "zustand";

import {
  productService,
  type AnalyticsPost,
  type BrandProfile,
  type CalendarEvent,
  type CoachResult,
  type Draft,
  type LinkedInStatus,
  type RadarResult,
  type Suggestion,
  type TrendResponse,
} from "@/services/product.service";
import type { BrandProfileData } from "@/services/product.service";

type ProductState = {
  linkedin: LinkedInStatus | null;
  brandProfile: BrandProfile | null;
  trends: TrendResponse | null;
  suggestions: Suggestion[];
  drafts: Draft[];
  analytics: AnalyticsPost[];
  calendar: CalendarEvent[];
  currentDraft: Draft | null;
  coachResult: CoachResult | null;
  radarResult: RadarResult | null;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
  loadDashboard: () => Promise<void>;
  connectLinkedIn: () => Promise<void>;
  syncLinkedIn: () => Promise<void>;
  generateBrandProfile: () => Promise<void>;
  confirmBrandProfile: () => Promise<void>;
  updateBrandProfile: (profile: BrandProfileData) => Promise<void>;
  loadTrends: () => Promise<void>;
  suggest: (platform: string, topic?: string) => Promise<void>;
  generate: (platform: string, prompt: string, trend?: string, suggestion?: Suggestion) => Promise<void>;
  repurpose: (target: "instagram" | "twitter") => Promise<void>;
  loadDrafts: () => Promise<void>;
  selectDraft: (draftId: string) => void;
  publish: (draftId: string) => Promise<void>;
  schedule: (draftId: string, scheduledFor: string) => Promise<void>;
  cancelSchedule: (draftId: string) => Promise<void>;
  loadAnalytics: () => Promise<void>;
  analyze: (postId: string) => Promise<void>;
  loadCalendar: () => Promise<void>;
  coachAnalyze: (content: string, platform: string, goal?: string) => Promise<void>;
  scanRadar: (niche: string, platforms: string[], limit?: number) => Promise<void>;
};

async function run<T>(set: (state: Partial<ProductState>) => void, task: () => Promise<T>) {
  set({ isLoading: true, error: null });
  try {
    return await task();
  } catch (error) {
    set({ error: error instanceof Error ? error.message : "Something went wrong." });
    throw error;
  } finally {
    set({ isLoading: false });
  }
}

export const useProductStore = create<ProductState>((set, get) => ({
  linkedin: null,
  brandProfile: null,
  trends: null,
  suggestions: [],
  drafts: [],
  analytics: [],
  calendar: [],
  currentDraft: null,
  coachResult: null,
  radarResult: null,
  isLoading: false,
  error: null,

  clearError: () => set({ error: null }),

  loadDashboard: () =>
    run(set, async () => {
      const [linkedin, brandProfile] = await Promise.all([
        productService.linkedinStatus(),
        productService.getBrandProfile(),
      ]);
      set({ linkedin, brandProfile });
    }),

  connectLinkedIn: () =>
    run(set, async () => {
      await productService.connectLinkedIn();
      set({ linkedin: await productService.linkedinStatus() });
    }),

  syncLinkedIn: () =>
    run(set, async () => {
      await productService.syncLinkedIn();
      const [linkedin, analytics] = await Promise.all([productService.linkedinStatus(), productService.analyticsPosts()]);
      set({ linkedin, analytics });
    }),

  generateBrandProfile: () =>
    run(set, async () => {
      set({ brandProfile: await productService.generateBrandProfile() });
    }),

  confirmBrandProfile: () =>
    run(set, async () => {
      set({ brandProfile: await productService.confirmBrandProfile() });
    }),

  updateBrandProfile: (profile) =>
    run(set, async () => {
      set({ brandProfile: await productService.updateBrandProfile(profile) });
    }),

  loadTrends: () =>
    run(set, async () => {
      set({ trends: await productService.getTrends() });
    }),

  suggest: (platform, topic) =>
    run(set, async () => {
      const result = await productService.suggest(platform, topic);
      set({ suggestions: result.suggestions });
    }),

  generate: (platform, prompt, trend, suggestion) =>
    run(set, async () => {
      await productService.generate(platform, prompt, trend, suggestion);
      const drafts = await productService.drafts();
      set({ drafts, currentDraft: drafts[0] ?? null });
    }),

  repurpose: (target) =>
    run(set, async () => {
      const draft = get().currentDraft;
      if (!draft) return;
      await productService.repurpose(draft.id, target);
      const drafts = await productService.drafts();
      set({ drafts, currentDraft: drafts.find((item) => item.id === draft.id) ?? drafts[0] ?? null });
    }),

  loadDrafts: () =>
    run(set, async () => {
      const drafts = await productService.drafts();
      set({ drafts, currentDraft: drafts[0] ?? null });
    }),

  selectDraft: (draftId) => {
    const drafts = get().drafts;
    set({ currentDraft: drafts.find((item) => item.id === draftId) ?? null });
  },

  publish: (draftId) =>
    run(set, async () => {
      await productService.publish(draftId);
      set({ drafts: await productService.drafts(), calendar: await productService.calendar() });
    }),

  schedule: (draftId, scheduledFor) =>
    run(set, async () => {
      await productService.schedule(draftId, scheduledFor);
      set({ drafts: await productService.drafts(), calendar: await productService.calendar() });
    }),

  cancelSchedule: (draftId) =>
    run(set, async () => {
      await productService.cancelSchedule(draftId);
      set({ drafts: await productService.drafts(), calendar: await productService.calendar() });
    }),

  loadAnalytics: () =>
    run(set, async () => {
      set({ analytics: await productService.analyticsPosts() });
    }),

  analyze: (postId) =>
    run(set, async () => {
      await productService.analyzePost(postId);
      set({ analytics: await productService.analyticsPosts() });
    }),

  loadCalendar: () =>
    run(set, async () => {
      set({ calendar: await productService.calendar(), drafts: await productService.drafts() });
    }),

  coachAnalyze: (content, platform, goal) =>
    run(set, async () => {
      const result = await productService.coachAnalyze(content, platform, goal);
      set({ coachResult: result });
    }),

  scanRadar: (niche, platforms, limit) =>
    run(set, async () => {
      const result = await productService.radarScan(niche, platforms, limit);
      set({ radarResult: result });
    }),
}));
