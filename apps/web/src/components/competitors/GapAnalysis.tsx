"use client";

import { motion } from "framer-motion";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle,
  Lightbulb,
  Target,
  TrendingUp,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/Button";

interface GapTopic {
  topic: string;
  competitor_performance?: string;
  opportunity_score: number;
  why_valuable: string;
  difficulty: string;
}

interface Opportunity {
  opportunity: string;
  rationale: string;
  effort_required: string;
  priority: number;
}

interface GapAnalysisData {
  gap_topics: GapTopic[];
  high_impact_opportunities: Opportunity[];
  quick_wins: string[];
  format_gaps: Array<{
    format: string;
    competitor_usage: string;
    your_opportunity: string;
    implementation_effort: string;
  }>;
}

interface GapAnalysisProps {
  data: GapAnalysisData;
  onCreateContent: (topic: string) => void;
}

function DifficultyBadge({ difficulty }: { difficulty: string }) {
  const colors = {
    easy: "bg-emerald-100 text-emerald-700",
    medium: "bg-amber-100 text-amber-700",
    hard: "bg-red-100 text-red-700",
  };

  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium ${
        colors[difficulty as keyof typeof colors] || colors.medium
      }`}
    >
      {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
    </span>
  );
}

function OpportunityScore({ score }: { score: number }) {
  const percentage = Math.round(score * 100);

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden w-24">
        <motion.div
          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, delay: 0.2 }}
        />
      </div>
      <span className="text-sm font-semibold text-gray-700">{percentage}%</span>
    </div>
  );
}

export function GapAnalysis({ data, onCreateContent }: GapAnalysisProps) {
  return (
    <div className="space-y-6">
      {/* High Impact Opportunities */}
      {data.high_impact_opportunities.length > 0 && (
        <Card className="p-6 border-2 border-indigo-100 bg-gradient-to-br from-indigo-50/50 to-transparent">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
              <Target className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">High-Impact Opportunities</h3>
              <p className="text-sm text-gray-500">
                Prioritized gaps based on opportunity score and effort required
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {data.high_impact_opportunities.slice(0, 3).map((opp, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-4 p-4 bg-white rounded-xl border border-indigo-100"
              >
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm">
                  {opp.priority}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 mb-1">{opp.opportunity}</h4>
                  <p className="text-sm text-gray-600 mb-2">{opp.rationale}</p>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      {opp.effort_required}
                    </span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onCreateContent(opp.opportunity)}
                >
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </motion.div>
            ))}
          </div>
        </Card>
      )}

      {/* Gap Topics */}
      {data.gap_topics.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <AlertCircle className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Content Gaps</h3>
              <p className="text-sm text-gray-500">
                Topics competitors cover that you don&apos;t
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.gap_topics.slice(0, 6).map((gap, index) => (
              <motion.div
                key={gap.topic}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{gap.topic}</h4>
                  <DifficultyBadge difficulty={gap.difficulty} />
                </div>
                <p className="text-sm text-gray-600 mb-3">{gap.why_valuable}</p>
                <div className="flex items-center justify-between">
                  <OpportunityScore score={gap.opportunity_score} />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onCreateContent(gap.topic)}
                    className="text-indigo-600"
                  >
                    Create
                  </Button>
                </div>
              </motion.div>
            ))}
          </div>
        </Card>
      )}

      {/* Quick Wins */}
      {data.quick_wins.length > 0 && (
        <Card className="p-6 border-2 border-emerald-100 bg-gradient-to-br from-emerald-50/50 to-transparent">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Quick Wins</h3>
              <p className="text-sm text-gray-500">
                Easy opportunities to pursue for immediate impact
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {data.quick_wins.map((win, index) => (
              <motion.button
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                whileHover={{ scale: 1.02 }}
                onClick={() => onCreateContent(win)}
                className="px-4 py-2 bg-white border border-emerald-200 rounded-full text-sm font-medium text-emerald-700 hover:bg-emerald-50 transition-colors"
              >
                <Lightbulb className="w-3 h-3 inline mr-1" />
                {win}
              </motion.button>
            ))}
          </div>
        </Card>
      )}

      {/* Format Gaps */}
      {data.format_gaps.length > 0 && (
        <Card className="p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Format Opportunities</h3>
          <div className="space-y-3">
            {data.format_gaps.slice(0, 3).map((gap, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex-shrink-0 w-8 h-8 rounded bg-purple-100 flex items-center justify-center">
                  <span className="text-lg">📐</span>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{gap.format}</h4>
                  <p className="text-sm text-gray-600">{gap.your_opportunity}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Effort: {gap.implementation_effort}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
