"use client";

import { motion } from "framer-motion";
import { Info } from "lucide-react";

interface ConfidenceIntervalProps {
  lower: number;
  upper: number;
  confidence: number;
  unit?: string;
  showTooltip?: boolean;
}

export function ConfidenceInterval({
  lower,
  upper,
  confidence,
  unit = "%",
  showTooltip = true,
}: ConfidenceIntervalProps) {
  const mid = (lower + upper) / 2;
  const range = upper - lower;
  const percentage = ((mid - lower) / range) * 100;

  return (
    <div className="inline-flex flex-col items-center">
      <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
        <span>Confidence Interval</span>
        {showTooltip && (
          <div className="group relative">
            <Info className="w-3 h-3 text-gray-400 cursor-help" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 w-48">
              <div className="bg-gray-900 text-white text-xs rounded-lg py-2 px-3 shadow-xl">
                <p className="font-medium mb-1">
                  {(confidence * 100).toFixed(0)}% Confidence Interval
                </p>
                <p className="text-gray-300 leading-relaxed">
                  Based on historical data and model uncertainty, the true value is likely
                  to fall between {lower.toFixed(1)} and {upper.toFixed(1)} {unit}.
                </p>
                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 text-sm">
        <span className="font-medium text-gray-600">
          {lower.toFixed(1)}
          {unit}
        </span>

        {/* Visual bar */}
        <div className="relative w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
          {/* Confidence range */}
          <motion.div
            className="absolute top-0 h-full bg-gradient-to-r from-indigo-300 via-indigo-500 to-indigo-300 rounded-full"
            initial={{ width: 0, left: "50%" }}
            animate={{
              width: "100%",
              left: 0,
            }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />

          {/* Center point */}
          <motion.div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-md border-2 border-indigo-500"
            initial={{ left: "50%" }}
            animate={{ left: `${percentage}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>

        <span className="font-medium text-gray-600">
          {upper.toFixed(1)}
          {unit}
        </span>
      </div>

      <span className="text-xs text-gray-400 mt-1">
        {(confidence * 100).toFixed(0)}% confidence
      </span>
    </div>
  );
}

// Prediction confidence meter
interface ConfidenceMeterProps {
  score: number; // 0-1
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function ConfidenceMeter({
  score,
  size = "md",
  showLabel = true,
}: ConfidenceMeterProps) {
  const sizeClasses = {
    sm: "w-20 h-1.5",
    md: "w-32 h-2",
    lg: "w-48 h-3",
  };

  const getConfidenceLabel = (s: number) => {
    if (s >= 0.85) return { text: "High", color: "text-emerald-600", bg: "bg-emerald-500" };
    if (s >= 0.7) return { text: "Good", color: "text-blue-600", bg: "bg-blue-500" };
    if (s >= 0.55) return { text: "Moderate", color: "text-amber-600", bg: "bg-amber-500" };
    return { text: "Low", color: "text-orange-600", bg: "bg-orange-500" };
  };

  const label = getConfidenceLabel(score);

  return (
    <div className="flex items-center gap-2">
      <div className={`relative ${sizeClasses[size]} bg-gray-200 rounded-full overflow-hidden`}>
        <motion.div
          className={`absolute top-0 left-0 h-full rounded-full ${label.bg}`}
          initial={{ width: 0 }}
          animate={{ width: `${score * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>

      {showLabel && (
        <span className={`text-sm font-medium ${label.color}`}>
          {label.text} ({Math.round(score * 100)}%)
        </span>
      )}
    </div>
  );
}
