"use client";

import { Lightbulb, TrendingUp, TrendingDown, Minus, AlertCircle } from "lucide-react";

type HookPattern = {
  distribution: Record<string, number>;
  dominant_pattern: string;
  dominant_percentage: number;
  insights: string[];
};

type LengthPattern = {
  top_performer_avg_chars: number;
  bottom_performer_avg_chars: number;
  difference: number;
  insight: string;
  optimal_range: { min: number; max: number; ideal: number };
};

type QualityEngagement = {
  correlation: number;
  strength: "strong" | "moderate" | "weak";
  insight: string;
};

type ContentInsights = {
  period_days: number;
  analyzed_posts_count: number;
  top_performer_avg_scores: {
    hook_score: number;
    tone_score: number;
    structure_score: number;
  };
  identified_strengths: string[];
  hook_patterns?: HookPattern;
  length_patterns?: LengthPattern;
  quality_engagement_correlation?: QualityEngagement;
  recommendations: string[];
  message?: string | null;
};

type InsightsFeedProps = {
  insights: ContentInsights | null;
  loading?: boolean;
};

export function InsightsFeed({ insights, loading }: InsightsFeedProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-20 animate-pulse rounded-lg bg-muted"
          />
        ))}
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="rounded-lg border bg-card p-4 text-center">
        <p className="text-sm text-muted-foreground">
          Run AI analysis on your posts to generate insights
        </p>
      </div>
    );
  }

  if (insights.message) {
    return (
      <div className="rounded-lg border bg-card p-4">
        <div className="flex items-start gap-3">
          <AlertCircle size={18} className="mt-0.5 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">{insights.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          Based on {insights.analyzed_posts_count} analyzed posts
        </p>
        <span className="text-xs text-muted-foreground">
          Last {insights.period_days} days
        </span>
      </div>

      {/* Strengths */}
      {insights.identified_strengths.length > 0 && (
        <div className="rounded-lg border bg-card p-4">
          <div className="mb-3 flex items-center gap-2">
            <TrendingUp size={16} className="text-olive" />
            <h3 className="text-sm font-semibold">Your Strengths</h3>
          </div>
          <ul className="space-y-2">
            {insights.identified_strengths.map((strength, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-muted-foreground"
              >
                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-olive" />
                {strength}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Hook Pattern Analysis */}
      {insights.hook_patterns && insights.hook_patterns.dominant_pattern && (
        <div className="rounded-lg border bg-card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Hook Pattern Analysis</h3>
            <PatternBadge pattern={insights.hook_patterns.dominant_pattern} />
          </div>
          
          {/* Distribution */}
          <div className="mb-3 flex flex-wrap gap-1">
            {Object.entries(insights.hook_patterns.distribution).map(
              ([pattern, count]) =>
                count > 0 && (
                  <div
                    key={pattern}
                    className={`rounded-md px-2 py-1 text-xs ${
                      pattern === insights.hook_patterns?.dominant_pattern
                        ? "bg-bronze/20 text-bronze font-medium"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {pattern}: {count}
                  </div>
                )
            )}
          </div>

          {/* Insights */}
          {insights.hook_patterns.insights.length > 0 && (
            <div className="space-y-2">
              {insights.hook_patterns.insights.map((insight, idx) => (
                <p
                  key={idx}
                  className="text-sm text-muted-foreground flex items-start gap-2"
                >
                  <Lightbulb size={14} className="mt-1 shrink-0 text-bronze" />
                  {insight}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Length Pattern Analysis */}
      {insights.length_patterns && (
        <div className="rounded-lg border bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold">Content Length Analysis</h3>
          
          <div className="mb-3 grid grid-cols-2 gap-3">
            <div className="rounded-md bg-muted p-3">
              <p className="text-xs text-muted-foreground">Top Posts</p>
              <p className="text-lg font-semibold">
                {insights.length_patterns.top_performer_avg_chars.toFixed(0)} chars
              </p>
            </div>
            <div className="rounded-md bg-muted p-3">
              <p className="text-xs text-muted-foreground">Bottom Posts</p>
              <p className="text-lg font-semibold">
                {insights.length_patterns.bottom_performer_avg_chars.toFixed(0)} chars
              </p>
            </div>
          </div>

          <p className="mb-2 text-sm text-muted-foreground">
            {insights.length_patterns.insight}
          </p>

          {insights.length_patterns.optimal_range && (
            <div className="rounded-md bg-olive/10 p-2">
              <p className="text-xs text-olive">
                Suggested range: {insights.length_patterns.optimal_range.min.toFixed(0)} - {insights.length_patterns.optimal_range.max.toFixed(0)} chars
                (ideal: {insights.length_patterns.optimal_range.ideal.toFixed(0)})
              </p>
            </div>
          )}
        </div>
      )}

      {/* Quality vs Engagement */}
      {insights.quality_engagement_correlation && (
        <div className="rounded-lg border bg-card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Quality vs Engagement</h3>
            <CorrelationBadge correlation={insights.quality_engagement_correlation} />
          </div>
          <p className="text-sm text-muted-foreground">
            {insights.quality_engagement_correlation.insight}
          </p>
        </div>
      )}

      {/* Recommendations */}
      {insights.recommendations.length > 0 && (
        <div className="rounded-lg border-l-4 border-l-bronze bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold">Actionable Recommendations</h3>
          <ul className="space-y-3">
            {insights.recommendations.map((rec, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-muted-foreground"
              >
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-bronze/20 text-xs font-medium text-bronze">
                  {idx + 1}
                </span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PatternBadge({ pattern }: { pattern: string }) {
  const colors: Record<string, string> = {
    question: "bg-blue-100 text-blue-700",
    statement: "bg-gray-100 text-gray-700",
    story: "bg-purple-100 text-purple-700",
    number: "bg-green-100 text-green-700",
    contrarian: "bg-red-100 text-red-700",
    other: "bg-muted text-muted-foreground",
  };

  const labels: Record<string, string> = {
    question: "Question Hooks",
    statement: "Statements",
    story: "Personal Stories",
    number: "Number/Lists",
    contrarian: "Contrarian Takes",
    other: "Mixed Patterns",
  };

  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
        colors[pattern] || colors.other
      }`}
    >
      {labels[pattern] || pattern}
    </span>
  );
}

function CorrelationBadge({ correlation }: { correlation: QualityEngagement }) {
  const colors = {
    strong: "bg-olive/20 text-olive",
    moderate: "bg-bronze/20 text-bronze",
    weak: "bg-muted text-muted-foreground",
  };

  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
        colors[correlation.strength]
      }`}
    >
      {correlation.strength === "strong" && <TrendingUp size={12} className="mr-1 inline" />}
      {correlation.strength === "weak" && <TrendingDown size={12} className="mr-1 inline" />}
      {correlation.strength === "moderate" && <Minus size={12} className="mr-1 inline" />}
      {correlation.strength} correlation
    </span>
  );
}

export default InsightsFeed;
