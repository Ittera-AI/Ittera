"use client";

import { useState, useCallback } from "react";
import { useProductStore } from "@/stores/product.store";
import { productService, type PredictionCategory } from "@/services/product.service";

interface PredictionInput {
  content: string;
  platform: string;
  contentType: string;
  hashtags: string[];
  mentions: string[];
}

interface PredictionState {
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
  comparative_analysis?: string;
}

interface ViralAnalysis {
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

interface TimingPrediction {
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

export function usePredictions() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<PredictionState | null>(null);
  const [viralAnalysis, setViralAnalysis] = useState<ViralAnalysis | null>(null);
  const [timingPrediction, setTimingPrediction] = useState<TimingPrediction | null>(null);

  const { setPredictionsData } = useProductStore();

  const analyzeContent = useCallback(
    async (input: PredictionInput) => {
      setIsLoading(true);
      setError(null);

      try {
        // Call the all-in-one prediction endpoint
        const data = await productService.predictAll({
          content: input.content,
          platform: input.platform as "linkedin" | "twitter" | "instagram" | "facebook",
          content_type: input.contentType as "post" | "article" | "video" | "image" | "poll",
          hashtags: input.hashtags,
          mentioned_accounts: input.mentions,
        });

        // Update local state
        if (data?.performance) {
          setPrediction({
            metrics: data.performance.metrics,
            confidence: data.performance.confidence,
            feature_importance: data.performance.feature_importance || [],
            improvement_suggestions: data.performance.improvement_suggestions || [],
            comparative_analysis: data.performance.comparative_analysis ?? undefined,
          });
        }

        if (data?.viral) {
          setViralAnalysis({
            viral_probability: data.viral.viral_probability,
            viral_score: data.viral.viral_score,
            category: data.viral.category,
            patterns: data.viral.patterns || [],
            viral_triggers: data.viral.viral_triggers || [],
            amplification_suggestions: data.viral.amplification_suggestions || [],
          });
        }

        if (data?.timing) {
          setTimingPrediction({
            optimal_time: data.timing.optimal_time,
            confidence_score: data.timing.confidence_score,
            alternative_slots: data.timing.alternative_slots || [],
            detected_patterns: data.timing.detected_patterns || [],
            best_days: data.timing.best_days || [],
            best_hours: data.timing.best_hours || [],
          });
        }

        // Update store
        setPredictionsData({
          performance: data?.performance,
          viral: data?.viral,
          timing: data?.timing,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to generate predictions");
        console.error("Prediction error:", err);
      } finally {
        setIsLoading(false);
      }
    },
    [setPredictionsData]
  );

  const refreshPredictions = useCallback(() => {
    // This would re-fetch cached predictions
    // For now, just clear the error
    setError(null);
  }, []);

  return {
    prediction,
    viralAnalysis,
    timingPrediction,
    isLoading,
    error,
    analyzeContent,
    refreshPredictions,
  };
}
