"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Sparkles, BarChart3, Zap, Clock } from "lucide-react";

import { Card } from "@/components/ui/card";
import { PredictionInput } from "@/components/predictions/PredictionInput";
import { PredictionDashboard } from "@/components/predictions/PredictionDashboard";
import { usePredictions } from "@/hooks/usePredictions";

export default function PredictionsPage() {
  const [hasAnalyzed, setHasAnalyzed] = useState(false);

  const {
    prediction,
    viralAnalysis,
    timingPrediction,
    isLoading,
    error,
    analyzeContent,
    refreshPredictions,
  } = usePredictions();

  const handleAnalyze = useCallback(
    async (input: {
      content: string;
      platform: string;
      contentType: string;
      hashtags: string[];
      mentions: string[];
    }) => {
      setHasAnalyzed(true);
      await analyzeContent(input);
    },
    [analyzeContent]
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-indigo-50/30">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                AI Predictions
              </h1>
              <p className="mt-1 text-gray-500">
                Predict performance, viral potential, and optimal timing before you post
              </p>
            </div>

            {/* Feature badges */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-full text-sm font-medium">
                <BarChart3 className="w-4 h-4" />
                Performance
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-full text-sm font-medium">
                <Zap className="w-4 h-4" />
                Viral Score
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium">
                <Clock className="w-4 h-4" />
                Timing
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Section */}
          <div className="lg:col-span-1">
            <Card className="p-6 sticky top-6">
              <div className="mb-6">
                <h2 className="font-semibold text-gray-900 mb-1">Content Input</h2>
                <p className="text-sm text-gray-500">
                  Enter your content to get AI-powered predictions
                </p>
              </div>

              <PredictionInput onAnalyze={handleAnalyze} isLoading={isLoading} />

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 p-4 bg-red-50 border border-red-100 rounded-lg"
                >
                  <p className="text-sm text-red-600">{error}</p>
                </motion.div>
              )}
            </Card>

            {/* Info Card */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="mt-6 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-100"
            >
              <h3 className="font-medium text-indigo-900 mb-2 flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                How it works
              </h3>
              <ul className="space-y-2 text-sm text-indigo-700">
                <li className="flex items-start gap-2">
                  <span className="font-bold">1.</span>
                  Paste your content and select platform
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">2.</span>
                  AI analyzes engagement, viral potential, and timing
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">3.</span>
                  Get actionable suggestions to improve performance
                </li>
              </ul>
            </motion.div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2">
            <PredictionDashboard
              prediction={prediction}
              viralAnalysis={viralAnalysis}
              timingPrediction={timingPrediction}
              isLoading={isLoading}
              onRefresh={refreshPredictions}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
