"use client";

import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const EASE = [0.16, 1, 0.3, 1] as const;

const ITEMS = [
  {
    label: "Workflow",
    before: "5+ disconnected tools for one workflow",
    after: "One unified AI strategy engine",
    impact: "5 to 1",
  },
  {
    label: "Analytics",
    before: "Manual data analysis across platforms",
    after: "Real-time performance insights, automated",
    impact: "Live signal",
  },
  {
    label: "Timing",
    before: "Guessing optimal posting times",
    after: "AI-predicted optimal windows per platform",
    impact: "Window found",
  },
  {
    label: "Repurposing",
    before: "Hours spent reformatting for each platform",
    after: "Instant repurposing in 10+ formats",
    impact: "10+ outputs",
  },
  {
    label: "Trends",
    before: "Reactive trend-chasing after it peaks",
    after: "Trend Radar surfaces opportunities 48h early",
    impact: "48h lead",
  },
  {
    label: "ROI",
    before: "No clear ROI on your content effort",
    after: "Clear attribution from content to growth",
    impact: "Prove impact",
  },
];

const STATS = [
  { value: "10+",   label: "hours saved weekly" },
  { value: "5 → 1", label: "tools collapsed" },
  { value: "3×",    label: "faster publishing" },
  { value: "48h",   label: "earlier on trends" },
];

export default function Transformation() {
  const shouldReduceMotion = useReducedMotion() ?? false;
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const sectionBg   = isDark ? "#0C0B09" : "#F9F8F6";
  const rowBorder   = isDark ? "#2E2922" : "#EAEAEC";
  const labelColor  = isDark ? "rgba(242,237,232,0.28)" : "#A3A3A3";
  const beforeColor = isDark ? "rgba(242,237,232,0.36)" : "#A3A3A3";
  const afterColor  = isDark ? "#F2EDE8" : "#171717";
  const impactBg    = isDark ? "rgba(163,138,112,0.1)" : "rgba(163,138,112,0.08)";
  const impactBdr   = isDark ? "rgba(163,138,112,0.2)" : "rgba(163,138,112,0.18)";
  const impactColor = "#8B6F52";
  const arrowColor  = isDark ? "rgba(163,138,112,0.5)" : "rgba(163,138,112,0.6)";
  const statValCol  = isDark ? "#F2EDE8" : "#171717";
  const statLblCol  = isDark ? "rgba(242,237,232,0.42)" : "#737373";
  const statDivider = isDark ? "#2E2922" : "#EAEAEC";
  const headerCol   = isDark ? "rgba(242,237,232,0.22)" : "#C5C0BB";

  return (
    <section
      id="transformation"
      className="relative overflow-hidden py-12 sm:py-24"
      style={{ background: sectionBg }}
    >
      {/* Background orb */}
      <div
        className="absolute top-0 left-0 w-[500px] h-[500px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse at top left, rgba(163,138,112,0.12) 0%, transparent 65%)" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">

        {/* Section header */}
        <div className="max-w-2xl mb-14">
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: EASE }}
            className="flex items-center gap-2 mb-6"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">The solution</span>
          </motion.div>

          <motion.h2
            initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: EASE }}
            className="text-[28px] sm:text-[42px] lg:text-[52px] font-bold tracking-[-0.03em] leading-[1.04]"
            style={{ color: isDark ? "#F2EDE8" : "#171717" }}
          >
            Your content stack,{" "}
            <span className="gradient-text">rebuilt into one unfair advantage.</span>
          </motion.h2>

          <motion.p
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.14, ease: EASE }}
            className="mt-5 text-[15px] leading-[1.8]"
            style={{ color: isDark ? "rgba(242,237,232,0.56)" : "#5F5A55" }}
          >
            Six problems creators face every day — solved in one engine.
          </motion.p>
        </div>

        {/* Column headers */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45, ease: EASE }}
          className="hidden sm:grid sm:grid-cols-[120px_1fr_36px_1fr_100px] gap-x-4 mb-3 px-5"
        >
          <div className="text-[10px] uppercase tracking-[0.22em]" style={{ color: headerCol }} />
          <div className="text-[10px] uppercase tracking-[0.22em]" style={{ color: headerCol }}>Before Ittera</div>
          <div />
          <div className="text-[10px] uppercase tracking-[0.22em]" style={{ color: headerCol }}>With Ittera</div>
          <div className="text-right text-[10px] uppercase tracking-[0.22em]" style={{ color: headerCol }}>Impact</div>
        </motion.div>

        {/* Rows */}
        <div
          className="rounded-2xl overflow-hidden"
          style={{ border: `1px solid ${rowBorder}` }}
        >
          {ITEMS.map((item, i) => (
            <motion.div
              key={item.label}
              initial={shouldReduceMotion ? false : { opacity: 0, x: -12 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-30px" }}
              transition={{ duration: 0.45, delay: shouldReduceMotion ? 0 : i * 0.07, ease: EASE }}
              className="group flex flex-col sm:grid sm:grid-cols-[120px_1fr_36px_1fr_100px] gap-3 sm:gap-x-4 items-start sm:items-center px-4 sm:px-5 py-3 sm:py-4 transition-colors duration-200"
              style={{
                borderTop: i === 0 ? "none" : `1px solid ${rowBorder}`,
                background: isDark ? "rgba(12,11,9,0)" : "rgba(255,255,255,0)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.background = isDark
                  ? "rgba(28,25,22,0.6)"
                  : "rgba(255,255,255,0.8)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.background = isDark
                  ? "rgba(12,11,9,0)"
                  : "rgba(255,255,255,0)";
              }}
            >
              {/* Label */}
              <div
                className="text-[11px] font-semibold uppercase tracking-[0.18em] shrink-0"
                style={{ color: labelColor }}
              >
                {item.label}
              </div>

              {/* Before */}
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className="text-[13px] leading-[1.5] line-through decoration-[1.5px]"
                  style={{
                    color: beforeColor,
                    textDecorationColor: isDark ? "rgba(242,237,232,0.18)" : "rgba(0,0,0,0.15)",
                  }}
                >
                  {item.before}
                </span>
              </div>

              {/* Arrow */}
              <div className="hidden sm:flex items-center justify-center">
                <ArrowRight className="w-3.5 h-3.5 shrink-0" style={{ color: arrowColor }} />
              </div>

              {/* After */}
              <div className="text-[13px] font-semibold leading-[1.5]" style={{ color: afterColor }}>
                {item.after}
              </div>

              {/* Impact badge */}
              <div className="sm:flex sm:justify-end">
                <span
                  className="inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold"
                  style={{ background: impactBg, border: `1px solid ${impactBdr}`, color: impactColor }}
                >
                  {item.impact}
                </span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Stats strip */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55, delay: 0.2, ease: EASE }}
          className="mt-10 grid grid-cols-2 sm:grid-cols-4 rounded-2xl overflow-hidden"
          style={{ border: `1px solid ${statDivider}` }}
        >
          {STATS.map((stat, i) => (
            <div
              key={stat.label}
              className="flex flex-col items-center justify-center py-4 sm:py-6 px-3 sm:px-4 text-center"
              style={{ borderLeft: i === 0 ? "none" : `1px solid ${statDivider}` }}
            >
              <motion.div
                initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: shouldReduceMotion ? 0 : 0.25 + i * 0.06, ease: EASE }}
                className="text-[26px] sm:text-[30px] font-bold tracking-[-0.04em]"
                style={{ color: statValCol }}
              >
                {stat.value}
              </motion.div>
              <div className="mt-1 text-[11px] leading-[1.4]" style={{ color: statLblCol }}>
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>

      </div>
    </section>
  );
}
