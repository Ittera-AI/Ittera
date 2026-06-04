"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface PredictionScoreProps {
  score: number;
  size?: "sm" | "md" | "lg" | "xl";
  showLabel?: boolean;
  label?: string;
  confidence?: number;
}

const sizeConfig = {
  sm: { wrapper: "w-16 h-16", stroke: 2, font: "text-xs" },
  md: { wrapper: "w-24 h-24", stroke: 3, font: "text-sm" },
  lg: { wrapper: "w-32 h-32", stroke: 4, font: "text-lg" },
  xl: { wrapper: "w-40 h-40", stroke: 5, font: "text-2xl" },
};

function getScoreColor(score: number): string {
  if (score >= 75) return "#10B981"; // Emerald - excellent
  if (score >= 60) return "#3B82F6"; // Blue - good
  if (score >= 40) return "#F59E0B"; // Amber - average
  if (score >= 25) return "#F97316"; // Orange - below average
  return "#EF4444"; // Red - unlikely
}

function getScoreLabel(score: number): string {
  if (score >= 75) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Average";
  if (score >= 25) return "Below Average";
  return "Needs Work";
}

function getTrendIcon(direction: "up" | "down" | "flat") {
  switch (direction) {
    case "up":
      return <TrendingUp className="w-4 h-4 text-emerald-500" />;
    case "down":
      return <TrendingDown className="w-4 h-4 text-red-500" />;
    default:
      return <Minus className="w-4 h-4 text-gray-400" />;
  }
}

export function PredictionScore({
  score,
  size = "md",
  showLabel = true,
  label,
  confidence,
}: PredictionScoreProps) {
  const config = sizeConfig[size];
  const color = getScoreColor(score);
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className={`relative ${config.wrapper}`}>
        {/* Background circle */}
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#E5E7EB"
            strokeWidth={config.stroke}
          />
          {/* Progress circle */}
          <motion.circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={color}
            strokeWidth={config.stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className={`font-bold text-gray-900 ${config.font}`}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.3 }}
          >
            {Math.round(score)}
          </motion.span>
          {confidence && (
            <span className="text-xs text-gray-500 mt-0.5">
              {Math.round(confidence * 100)}% confidence
            </span>
          )}
        </div>

        {/* Glow effect for high scores */}
        {score >= 75 && (
          <div
            className="absolute inset-0 rounded-full blur-xl opacity-20"
            style={{ backgroundColor: color }}
          />
        )}
      </div>

      {showLabel && (
        <div className="mt-3 text-center">
          <p className="text-sm font-medium text-gray-700">
            {label || getScoreLabel(score)}
          </p>
        </div>
      )}
    </div>
  );
}

// Feature importance bar
interface FeatureBarProps {
  feature: string;
  importance: number;
  impact: "positive" | "negative" | "neutral";
  explanation: string;
}

export function FeatureImportanceBar({
  feature,
  importance,
  impact,
  explanation,
}: FeatureBarProps) {
  const width = Math.abs(importance) * 100;
  const isPositive = importance > 0;
  const color =
    impact === "positive"
      ? "bg-emerald-500"
      : impact === "negative"
        ? "bg-red-500"
        : "bg-gray-400";

  return (
    <div className="group relative py-2">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-700 capitalize">
          {feature.replace(/_/g, " ")}
        </span>
        <span
          className={`text-xs font-medium ${
            isPositive ? "text-emerald-600" : "text-red-600"
          }`}
        >
          {isPositive ? "+" : ""}
          {importance.toFixed(2)}
        </span>
      </div>

      <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
        <motion.div
          className={`absolute top-0 h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${width}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          style={{
            left: isPositive ? 0 : `${100 - width}%`,
            right: isPositive ? `${100 - width}%` : 0,
          }}
        />
      </div>

      <p className="mt-1 text-xs text-gray-500">{explanation}</p>
    </div>
  );
}

// Viral potential badge
interface ViralBadgeProps {
  category: "highly_viral" | "viral_potential" | "average" | "below_average" | "unlikely";
  probability: number;
}

const viralConfig = {
  highly_viral: {
    label: "Highly Viral Potential",
    bg: "bg-gradient-to-r from-emerald-500 to-teal-500",
    text: "text-white",
    icon: "🔥",
  },
  viral_potential: {
    label: "Viral Potential",
    bg: "bg-gradient-to-r from-blue-500 to-indigo-500",
    text: "text-white",
    icon: "⚡",
  },
  average: {
    label: "Average Potential",
    bg: "bg-gradient-to-r from-amber-400 to-orange-400",
    text: "text-white",
    icon: "📊",
  },
  below_average: {
    label: "Below Average",
    bg: "bg-gradient-to-r from-orange-400 to-red-400",
    text: "text-white",
    icon: "📉",
  },
  unlikely: {
    label: "Unlikely to Viral",
    bg: "bg-gray-200",
    text: "text-gray-600",
    icon: "💤",
  },
};

export function ViralPotentialBadge({ category, probability }: ViralBadgeProps) {
  const config = viralConfig[category];

  return (
    <motion.div
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${config.bg} ${config.text}`}
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <span className="text-lg">{config.icon}</span>
      <span className="font-semibold text-sm">{config.label}</span>
      <span className="text-xs opacity-80">
        ({(probability * 100).toFixed(0)}% probability)
      </span>
    </motion.div>
  );
}
