"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  Sparkles,
  Clock,
  TrendingUp,
  Target,
  Zap,
  AlertCircle,
  CheckCircle,
  ChevronRight,
  Lightbulb,
} from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PredictionScore, FeatureImportanceBar, ViralPotentialBadge } from "./PredictionScore";
import { TimingHeatmap } from "./TimingHeatmap";
import { ConfidenceInterval } from "./ConfidenceInterval";

interface PredictionDashboardProps {
  prediction: {
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
    comparative_analysis?: string;
  } | null;

  viralAnalysis: {
    viral_probability: number;
    viral_score: number;
    category: "highly_viral" | "viral_potential" | "average" | "below_average" | "unlikely";
    patterns: Array<{
      pattern_type: string;
      score: number;
      detected: boolean;
      explanation: string;
      examples: string[];
    }>;
    viral_triggers: string[];
    amplification_suggestions: string[];
  } | null;

  timingPrediction: {
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
  } | null;

  isLoading: boolean;
  onRefresh: () => void;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-gray-200 rounded w-1/3" />
              <div className="h-32 bg-gray-200 rounded-full w-32 mx-auto" />
              <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto" />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

function SuggestionCard({ suggestion, index }: { suggestion: string; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="flex items-start gap-3 p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg border border-amber-100"
    >
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
        <Lightbulb className="w-4 h-4 text-amber-600" />
      </div>
      <p className="text-sm text-gray-700 leading-relaxed">{suggestion}</p>
    </motion.div>
  );
}

function PatternCard({
  pattern,
  index,
}: {
  pattern: {
    pattern_type: string;
    score: number;
    detected: boolean;
    explanation: string;
    examples: string[];
  };
  index: number;
}) {
  const patternIcons: Record<string, string> = {
    hook_strength: "🎣",
    emotional_resonance: "💝",
    shareability: "📤",
    timeliness: "⏰",
    uniqueness: "✨",
    visual_appeal: "🎨",
    authenticity: "🤝",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`p-4 rounded-xl border-2 transition-all duration-200 ${
        pattern.detected
          ? "border-emerald-200 bg-emerald-50/50"
          : "border-gray-200 bg-gray-50"
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{patternIcons[pattern.pattern_type] || "📋"}</span>
          <span className="font-medium text-gray-900 capitalize">
            {pattern.pattern_type.replace(/_/g, " ")}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${
                pattern.score > 0.6 ? "bg-emerald-500" : pattern.score > 0.4 ? "bg-amber-500" : "bg-gray-400"
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${pattern.score * 100}%` }}
              transition={{ duration: 0.8, delay: index * 0.1 }}
            />
          </div>
          <span className="text-xs font-medium text-gray-600">
            {Math.round(pattern.score * 100)}%
          </span>
        </div>
      </div>

      <p className="text-sm text-gray-600 mb-2">{pattern.explanation}</p>

      {pattern.detected && pattern.examples.length > 0 && (
        <div className="mt-3 p-2 bg-white rounded-lg border border-emerald-200">
          <p className="text-xs text-emerald-600 font-medium mb-1">Detected in your content:</p>
          <p className="text-xs text-gray-600 italic">&ldquo;{pattern.examples[0].slice(0, 100)}...&rdquo;</p>
        </div>
      )}
    </motion.div>
  );
}

export function PredictionDashboard({
  prediction,
  viralAnalysis,
  timingPrediction,
  isLoading,
  onRefresh,
}: PredictionDashboardProps) {
  const [activeTab, setActiveTab] = useState("performance");

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (!prediction && !viralAnalysis && !timingPrediction) {
    return (
      <Card className="p-12 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-indigo-100 flex items-center justify-center">
          <Sparkles className="w-8 h-8 text-indigo-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Ready to Predict</h3>
        <p className="text-gray-500 mb-6 max-w-md mx-auto">
          Enter your content above and click &ldquo;Analyze&rdquo; to get AI-powered predictions
          for performance, viral potential, and optimal timing.
        </p>
        <Button onClick={onRefresh} variant="outline">
          <Sparkles className="w-4 h-4 mr-2" />
          Get Predictions
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Tab Navigation */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">AI Predictions</h2>
          <p className="text-sm text-gray-500">Powered by Claude 3.5 Sonnet</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-gray-100/80 backdrop-blur-sm">
            <TabsTrigger value="performance" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              <span className="hidden sm:inline">Performance</span>
            </TabsTrigger>
            <TabsTrigger value="viral" className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              <span className="hidden sm:inline">Viral</span>
            </TabsTrigger>
            <TabsTrigger value="timing" className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span className="hidden sm:inline">Timing</span>
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <AnimatePresence mode="wait">
        {/* Performance Tab */}
        {activeTab === "performance" && prediction && (
          <motion.div
            key="performance"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Score Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Engagement Prediction */}
              <Card className="p-6">
                <h3 className="text-sm font-medium text-gray-500 mb-4">Predicted Engagement Rate</h3>
                <PredictionScore
                  score={prediction.metrics.engagement_rate}
                  size="lg"
                  confidence={prediction.confidence.overall_confidence}
                  label="Engagement Rate"
                />
                <div className="mt-4 text-center">
                  <ConfidenceInterval
                    lower={prediction.confidence.engagement_rate_ci.lower}
                    upper={prediction.confidence.engagement_rate_ci.upper}
                    confidence={prediction.confidence.engagement_rate_ci.confidence}
                    unit="%"
                  />
                </div>
              </Card>

              {/* Metric Predictions */}
              <Card className="p-6 md:col-span-2">
                <h3 className="text-sm font-medium text-gray-500 mb-4">Predicted Metrics</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: "Likes", value: prediction.metrics.likes, icon: "❤️" },
                    { label: "Comments", value: prediction.metrics.comments, icon: "💬" },
                    { label: "Shares", value: prediction.metrics.shares, icon: "🔄" },
                    { label: "Impressions", value: prediction.metrics.impressions, icon: "👁️" },
                  ].map((metric, i) => (
                    <motion.div
                      key={metric.label}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.1 }}
                      className="text-center p-4 bg-gray-50 rounded-xl"
                    >
                      <span className="text-2xl mb-2 block">{metric.icon}</span>
                      <p className="text-2xl font-bold text-gray-900">
                        {metric.value.toLocaleString()}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">{metric.label}</p>
                    </motion.div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Feature Importance */}
            {prediction.feature_importance.length > 0 && (
              <Card className="p-6">
                <div className="flex items-center gap-2 mb-6">
                  <Target className="w-5 h-5 text-indigo-600" />
                  <h3 className="font-semibold text-gray-900">Key Factors Affecting Performance</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
                  {prediction.feature_importance
                    .sort((a, b) => Math.abs(b.importance) - Math.abs(a.importance))
                    .slice(0, 6)
                    .map((feature, i) => (
                      <FeatureImportanceBar key={feature.feature} {...feature} />
                    ))}
                </div>
              </Card>
            )}

            {/* Improvement Suggestions */}
            {prediction.improvement_suggestions.length > 0 && (
              <Card className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="w-5 h-5 text-amber-600" />
                  <h3 className="font-semibold text-gray-900">Improvement Suggestions</h3>
                </div>
                <div className="space-y-3">
                  {prediction.improvement_suggestions.map((suggestion, i) => (
                    <SuggestionCard key={i} suggestion={suggestion} index={i} />
                  ))}
                </div>
              </Card>
            )}
          </motion.div>
        )}

        {/* Viral Tab */}
        {activeTab === "viral" && viralAnalysis && (
          <motion.div
            key="viral"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Viral Score Header */}
            <Card className="p-8 text-center bg-gradient-to-br from-gray-50 to-white">
              <ViralPotentialBadge
                category={viralAnalysis.category}
                probability={viralAnalysis.viral_probability}
              />

              <div className="mt-8 flex justify-center">
                <PredictionScore
                  score={viralAnalysis.viral_score}
                  size="xl"
                  label="Viral Score"
                />
              </div>

              {viralAnalysis.viral_triggers.length > 0 && (
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {viralAnalysis.viral_triggers.map((trigger, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium"
                    >
                      ✨ {trigger}
                    </span>
                  ))}
                </div>
              )}
            </Card>

            {/* Pattern Analysis */}
            <Card className="p-6">
              <div className="flex items-center gap-2 mb-6">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <h3 className="font-semibold text-gray-900">Viral Pattern Analysis</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {viralAnalysis.patterns.map((pattern, i) => (
                  <PatternCard key={pattern.pattern_type} pattern={pattern} index={i} />
                ))}
              </div>
            </Card>

            {/* Amplification Suggestions */}
            {viralAnalysis.amplification_suggestions.length > 0 && (
              <Card className="p-6 border-2 border-purple-100 bg-gradient-to-br from-purple-50/50 to-transparent">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="w-5 h-5 text-purple-600" />
                  <h3 className="font-semibold text-gray-900">How to Increase Viral Potential</h3>
                </div>
                <div className="space-y-3">
                  {viralAnalysis.amplification_suggestions.map((suggestion, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="flex items-start gap-3 p-3 bg-white rounded-lg border border-purple-100"
                    >
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center text-sm font-bold text-purple-600">
                        {i + 1}
                      </div>
                      <p className="text-sm text-gray-700">{suggestion}</p>
                      <ChevronRight className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
                    </motion.div>
                  ))}
                </div>
              </Card>
            )}
          </motion.div>
        )}

        {/* Timing Tab */}
        {activeTab === "timing" && timingPrediction && (
          <motion.div
            key="timing"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Optimal Time Card */}
            <Card className="p-8 bg-gradient-to-br from-indigo-50 via-white to-blue-50 border-indigo-100">
              <div className="text-center mb-6">
                <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                  <Clock className="w-4 h-4" />
                  Optimal Posting Time
                </span>
              </div>

              <div className="text-center">
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="inline-block"
                >
                  <p className="text-4xl md:text-5xl font-bold text-gray-900 mb-2">
                    {new Date(timingPrediction.optimal_time).toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "short",
                      day: "numeric",
                    })}
                  </p>
                  <p className="text-2xl md:text-3xl font-semibold text-indigo-600">
                    {new Date(timingPrediction.optimal_time).toLocaleTimeString("en-US", {
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </p>
                </motion.div>

                <div className="mt-6 flex items-center justify-center gap-2">
                  <span className="text-sm text-gray-500">Confidence:</span>
                  <span className="text-lg font-semibold text-indigo-600">
                    {Math.round(timingPrediction.confidence_score * 100)}%
                  </span>
                </div>
              </div>

              {timingPrediction.detected_patterns.length > 0 && (
                <div className="mt-8 pt-6 border-t border-indigo-100">
                  <p className="text-sm text-gray-500 mb-3">Detected Patterns:</p>
                  <div className="flex flex-wrap gap-2">
                    {timingPrediction.detected_patterns.map((pattern, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-white border border-indigo-200 rounded-full text-sm text-gray-700"
                      >
                        {pattern.description.slice(0, 60)}...
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </Card>

            {/* Timing Heatmap */}
            <Card className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Weekly Timing Heatmap</h3>
              <TimingHeatmap slots={timingPrediction.alternative_slots} />
            </Card>

            {/* Best Times Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle className="w-5 h-5 text-emerald-500" />
                  <h3 className="font-semibold text-gray-900">Best Days to Post</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {timingPrediction.best_days.map((day) => (
                    <span
                      key={day}
                      className="px-4 py-2 bg-emerald-100 text-emerald-700 rounded-lg font-medium capitalize"
                    >
                      {day}
                    </span>
                  ))}
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <AlertCircle className="w-5 h-5 text-amber-500" />
                  <h3 className="font-semibold text-gray-900">Alternative Times</h3>
                </div>
                <div className="space-y-2">
                  {timingPrediction.alternative_slots.slice(0, 3).map((slot, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                    >
                      <span className="text-sm text-gray-600 capitalize">
                        {slot.day} at {slot.hour}:00
                      </span>
                      <span className="text-sm font-medium text-indigo-600">
                        {Math.round(slot.score * 100)}% match
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
