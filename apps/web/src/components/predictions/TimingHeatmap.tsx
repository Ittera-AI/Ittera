"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

interface TimeSlot {
  day: string;
  hour: number;
  score: number;
  predicted_engagement_rate: number;
  reasoning: string;
}

interface TimingHeatmapProps {
  slots: TimeSlot[];
}

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
const HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20];

function getScoreColor(score: number): string {
  if (score >= 0.8) return "bg-emerald-500";
  if (score >= 0.6) return "bg-emerald-400";
  if (score >= 0.5) return "bg-amber-400";
  if (score >= 0.4) return "bg-amber-300";
  if (score >= 0.3) return "bg-orange-300";
  return "bg-gray-200";
}

function getScoreIntensity(score: number): string {
  if (score >= 0.8) return "shadow-emerald-500/50";
  if (score >= 0.6) return "shadow-emerald-400/40";
  if (score >= 0.5) return "shadow-amber-400/30";
  return "";
}

export function TimingHeatmap({ slots }: TimingHeatmapProps) {
  // Create a lookup map for quick access
  const slotMap = useMemo(() => {
    const map = new Map<string, TimeSlot>();
    slots.forEach((slot) => {
      map.set(`${slot.day}-${slot.hour}`, slot);
    });
    return map;
  }, [slots]);

  // Get day label
  const getDayLabel = (day: string) => {
    return day.charAt(0).toUpperCase() + day.slice(1, 3);
  };

  // Get hour label
  const getHourLabel = (hour: number) => {
    if (hour === 0) return "12am";
    if (hour === 12) return "12pm";
    if (hour < 12) return `${hour}am`;
    return `${hour - 12}pm`;
  };

  // Filter slots to relevant hours
  const relevantSlots = slots.filter((s) => HOURS.includes(s.hour));

  // Find best slot
  const bestSlot = relevantSlots.reduce((best, current) => {
    return current.score > best.score ? current : best;
  }, relevantSlots[0] || { day: "", hour: 0, score: 0 });

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Poor</span>
        <div className="flex gap-1">
          <div className="w-4 h-4 bg-gray-200 rounded" />
          <div className="w-4 h-4 bg-orange-300 rounded" />
          <div className="w-4 h-4 bg-amber-300 rounded" />
          <div className="w-4 h-4 bg-amber-400 rounded" />
          <div className="w-4 h-4 bg-emerald-400 rounded" />
          <div className="w-4 h-4 bg-emerald-500 rounded" />
        </div>
        <span>Excellent</span>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto">
        <div className="min-w-[600px]">
          {/* Header row with day labels */}
          <div className="grid grid-cols-8 gap-1 mb-2">
            <div className="text-xs text-gray-400 font-medium">Time</div>
            {DAYS.map((day) => (
              <div
                key={day}
                className={`text-xs font-medium text-center ${
                  bestSlot.day === day ? "text-emerald-600 font-bold" : "text-gray-500"
                }`}
              >
                {getDayLabel(day)}
                {bestSlot.day === day && (
                  <span className="ml-1 text-emerald-500">★</span>
                )}
              </div>
            ))}
          </div>

          {/* Grid rows */}
          <div className="space-y-1">
            {HOURS.map((hour, hourIndex) => (
              <motion.div
                key={hour}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: hourIndex * 0.03 }}
                className="grid grid-cols-8 gap-1"
              >
                {/* Hour label */}
                <div
                  className={`text-xs text-gray-400 flex items-center ${
                    bestSlot.hour === hour ? "text-emerald-600 font-bold" : ""
                  }`}
                >
                  {getHourLabel(hour)}
                  {bestSlot.hour === hour && (
                    <span className="ml-1 text-emerald-500">★</span>
                  )}
                </div>

                {/* Day cells */}
                {DAYS.map((day) => {
                  const slot = slotMap.get(`${day}-${hour}`);
                  const score = slot?.score || 0;
                  const isBest = day === bestSlot.day && hour === bestSlot.hour;

                  return (
                    <motion.div
                      key={`${day}-${hour}`}
                      className={`
                        relative h-10 rounded-md cursor-pointer group
                        ${getScoreColor(score)}
                        ${isBest ? `ring-2 ring-emerald-500 ring-offset-2 ${getScoreIntensity(score)} shadow-lg` : ""}
                        transition-all duration-200 hover:scale-105 hover:z-10
                      `}
                      whileHover={{ scale: 1.1, zIndex: 10 }}
                      title={`${day} ${hour}:00 - Score: ${Math.round(score * 100)}%`}
                    >
                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50">
                        <div className="bg-gray-900 text-white text-xs rounded-lg py-2 px-3 shadow-xl whitespace-nowrap">
                          <p className="font-semibold capitalize">
                            {day} {hour}:00
                          </p>
                          <p className="text-gray-300">
                            Score: {Math.round(score * 100)}%
                          </p>
                          {slot?.predicted_engagement_rate && (
                            <p className="text-emerald-300">
                              Est. Engagement: {slot.predicted_engagement_rate.toFixed(1)}%
                            </p>
                          )}
                          {slot?.reasoning && (
                            <p className="text-gray-400 mt-1 max-w-xs line-clamp-2">
                              {slot.reasoning}
                            </p>
                          )}
                          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
                        </div>
                      </div>

                      {/* Score indicator */}
                      {score >= 0.6 && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-[10px] font-bold text-white/80">
                            {Math.round(score * 100)}
                          </span>
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Best time highlight */}
      {bestSlot.score > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 p-4 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl border border-emerald-100"
        >
          <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
            <span className="text-lg">⭐</span>
          </div>
          <div>
            <p className="font-semibold text-emerald-900">
              Best Time: {getDayLabel(bestSlot.day)} at {bestSlot.hour}:00
            </p>
            <p className="text-sm text-emerald-600">
              Match Score: {Math.round(bestSlot.score * 100)}%
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
}
