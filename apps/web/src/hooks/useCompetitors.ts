"use client";

import { useState, useCallback, useEffect } from "react";
import {
  productService,
  type CompetitorAnalysisResponse,
  type CompetitorResponse,
  type ContentGapResponse,
} from "@/services/product.service";

type Competitor = CompetitorResponse;
type CompetitorAnalysis = CompetitorAnalysisResponse;
type GapAnalysisData = ContentGapResponse;

export function useCompetitors() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysisData | null>(null);
  const [analyses, setAnalyses] = useState<CompetitorAnalysis[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load competitors
  const loadCompetitors = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const competitors = await productService.getCompetitors();
      setCompetitors(competitors);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load competitors");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Add competitor
  const addCompetitor = useCallback(
    async (data: {
      name: string;
      platform: string;
      handle: string;
      profile_url?: string;
      niche_tags?: string[];
    }) => {
      setIsLoading(true);
      setError(null);

      try {
        const competitor = await productService.addCompetitor(data);
        // Refresh list
        await loadCompetitors();
        return competitor;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to add competitor");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [loadCompetitors]
  );

  // Analyze competitor strategy
  const analyzeStrategy = useCallback(async (competitorId: string) => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const analysis = await productService.analyzeCompetitorStrategy(competitorId);
      // Refresh analyses
      await loadAnalyses();
      return analysis;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze competitor");
      throw err;
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  // Analyze content gaps
  const analyzeGaps = useCallback(async () => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const analysis = await productService.analyzeContentGaps();
      setGapAnalysis(analysis);
      return analysis;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze gaps");
      throw err;
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  // Load analyses
  const loadAnalyses = useCallback(async () => {
    // TODO: Add endpoint for listing analyses
    // For now, this is a placeholder
  }, []);

  // Initial load
  useEffect(() => {
    loadCompetitors();
  }, [loadCompetitors]);

  return {
    competitors,
    gapAnalysis,
    analyses,
    isLoading,
    isAnalyzing,
    error,
    loadCompetitors,
    addCompetitor,
    analyzeStrategy,
    analyzeGaps,
  };
}
