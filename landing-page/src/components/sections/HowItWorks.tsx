"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { BarChart3, Brain, CalendarDays, ChevronRight, Clock3, Link, Rocket, Sparkles } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const EASE = [0.16, 1, 0.3, 1] as const;

const STEPS = [
  {
    num: "01",
    stepLabel: "Connect",
    icon: Link,
    title: "Connect your platforms",
    description:
      "Link LinkedIn, X, Instagram, and analytics in under two minutes. Ittera syncs your history immediately.",
    chips: ["1-click auth", "Historical sync", "Cross-platform view"],
    leadLabel: "Sources",
    leadValue: "4",
    headerLabel: "Sync",
    headerValue: "Ready",
    statLabel: "Setup time",
    statValue: "< 2 min",
  },
  {
    num: "02",
    stepLabel: "Analyze",
    icon: Brain,
    title: "AI analyzes your audience",
    description:
      "The engine maps engagement patterns, peak windows, and the formats that resonate with your audience.",
    chips: ["Peak windows", "Format scoring", "Audience signals"],
    leadLabel: "Patterns",
    leadValue: "84",
    headerLabel: "Signals",
    headerValue: "mapped",
    statLabel: "Best window",
    statValue: "Thu 8AM",
  },
  {
    num: "03",
    stepLabel: "Execute",
    icon: Rocket,
    title: "Execute with confidence",
    description:
      "Your calendar fills with AI recommendations. You review, adjust, and publish while strategy keeps compounding.",
    chips: ["Ready-to-post plan", "Approval flow", "Autopilot rhythm"],
    leadLabel: "Autopilot",
    leadValue: "On",
    headerLabel: "Queue",
    headerValue: "12",
    statLabel: "Content queued",
    statValue: "12",
  },
] as const;

type StepIndex = 0 | 1 | 2;

function PreviewContent({
  activeStep,
  isDark,
  shouldReduceMotion,
}: {
  activeStep: StepIndex;
  isDark: boolean;
  shouldReduceMotion: boolean;
}) {
  const panelBg = isDark ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.82)";
  const panelBorder = isDark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.06)";
  const muted = isDark ? "rgba(242,237,232,0.48)" : "#5F5A55";
  const text = isDark ? "#F2EDE8" : "#171717";

  if (activeStep === 0) {
    const platforms = [
      ["LinkedIn", "Synced", "#0A66C2"],
      ["X", "Imported", isDark ? "#F2EDE8" : "#171717"],
      ["Instagram", "Ready", "#E1306C"],
      ["Analytics", "Connected", "#7A8B76"],
    ] as const;

    return (
      <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="rounded-[24px] p-4" style={{ background: panelBg, border: `1px solid ${panelBorder}` }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.24em] text-[#A38A70]">Connected stack</div>
              <div className="text-sm font-semibold mt-1" style={{ color: text }}>All sources in one stream</div>
            </div>
            <div className="rounded-full px-3 py-1 text-[11px] font-medium text-[#7A8B76]" style={{ background: "rgba(122,139,118,0.12)" }}>
              Sync active
            </div>
          </div>
          <div className="space-y-2.5">
            {platforms.map(([name, status, color], index) => (
              <motion.div
                key={name}
                initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: shouldReduceMotion ? 0 : index * 0.08, ease: EASE }}
                className="flex items-center justify-between rounded-2xl px-3.5 py-3"
                style={{ background: isDark ? "rgba(12,11,9,0.38)" : "rgba(15,23,42,0.03)" }}
              >
                <div>
                  <div className="text-[13px] font-medium" style={{ color: text }}>{name}</div>
                  <div className="text-[11px]" style={{ color: muted }}>Historical data pulled</div>
                </div>
                <div className="flex items-center gap-1.5 text-[11px] font-medium" style={{ color }}>
                  <span className="h-2 w-2 rounded-full" style={{ background: color }} />
                  {status}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          <div className="rounded-[24px] p-4" style={{ background: panelBg, border: `1px solid ${panelBorder}` }}>
            <div className="text-[12px] font-semibold mb-3" style={{ color: text }}>Import timeline</div>
            <div className="space-y-2.5">
              {[
                "Authenticating workspace",
                "Backfilling posts and comments",
                "Grouping audience signals",
              ].map((item, index) => (
                <motion.div
                  key={item}
                  initial={shouldReduceMotion ? false : { opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: shouldReduceMotion ? 0 : 0.12 + index * 0.08, ease: EASE }}
                  className="rounded-2xl px-3.5 py-3 text-[12px]"
                  style={{ background: isDark ? "rgba(12,11,9,0.38)" : "rgba(15,23,42,0.03)", color: muted }}
                >
                  {item}
                </motion.div>
              ))}
            </div>
          </div>
          <div className="rounded-[24px] p-4" style={{ background: "linear-gradient(135deg, rgba(163,138,112,0.12), rgba(122,139,118,0.08))", border: "1px solid rgba(163,138,112,0.18)" }}>
            <div className="flex items-end justify-between">
              <div>
                <div className="text-[11px] uppercase tracking-[0.24em] text-[#8B6F52]">Immediate payoff</div>
                <div className="text-[22px] font-semibold mt-1" style={{ color: text }}>Unified audience picture</div>
              </div>
              <div className="text-right">
                <div className="text-[30px] font-bold tracking-[-0.05em]" style={{ color: text }}>2m</div>
                <div className="text-[11px]" style={{ color: muted }}>to full sync</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (activeStep === 1) {
    const bars = [34, 52, 46, 78, 64, 90, 72];
    const formats = [["Carousels", 92], ["Threads", 81], ["Founder POV", 88]] as const;

    return (
      <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-[24px] p-4" style={{ background: panelBg, border: `1px solid ${panelBorder}` }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.24em] text-[#A38A70]">Audience map</div>
              <div className="text-sm font-semibold mt-1" style={{ color: text }}>Engagement pattern analysis</div>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-[#7A8B76]">
              <Sparkles className="h-3.5 w-3.5" />
              AI processing
            </div>
          </div>
          <div className="rounded-[22px] p-4" style={{ background: isDark ? "rgba(12,11,9,0.4)" : "rgba(15,23,42,0.03)" }}>
            <div className="flex items-end gap-2 h-40">
              {bars.map((bar, index) => (
                <div key={index} className="flex-1 h-full flex items-end">
                  <motion.div
                    className="w-full rounded-t-[14px]"
                    style={{ background: index === 5 ? "linear-gradient(180deg, rgba(163,138,112,0.96), rgba(122,139,118,0.76))" : isDark ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.08)" }}
                    initial={shouldReduceMotion ? false : { height: 0 }}
                    animate={{ height: `${bar}%` }}
                    transition={{ duration: 0.5, delay: shouldReduceMotion ? 0 : index * 0.06, ease: EASE }}
                  />
                </div>
              ))}
            </div>
            <div className="grid grid-cols-7 mt-3 text-[10px]" style={{ color: isDark ? "rgba(242,237,232,0.32)" : "#A3A3A3" }}>
              {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => <div key={day} className="text-center">{day}</div>)}
            </div>
          </div>
        </div>
        <div className="space-y-3">
          <div className="rounded-[24px] p-4" style={{ background: panelBg, border: `1px solid ${panelBorder}` }}>
            <div className="flex items-center gap-2">
              <Clock3 className="h-4 w-4 text-[#A38A70]" />
              <div className="text-[12px] font-semibold" style={{ color: text }}>Best posting window</div>
            </div>
            <div className="mt-4 rounded-[22px] p-4" style={{ background: "rgba(163,138,112,0.08)" }}>
              <div className="text-[30px] font-bold tracking-[-0.05em]" style={{ color: text }}>Thu 8:00 AM</div>
              <p className="mt-2 text-[12px] leading-relaxed" style={{ color: muted }}>
                2.8x expected reach based on recency, saves, and comment velocity.
              </p>
            </div>
          </div>
          <div className="rounded-[24px] p-4" style={{ background: panelBg, border: `1px solid ${panelBorder}` }}>
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="h-4 w-4 text-[#7A8B76]" />
              <div className="text-[12px] font-semibold" style={{ color: text }}>Format resonance</div>
            </div>
            <div className="space-y-3">
              {formats.map(([name, score], index) => (
                <div key={name}>
                  <div className="flex items-center justify-between mb-1.5 text-[11px]">
                    <span style={{ color: muted }}>{name}</span>
                    <span className="font-semibold" style={{ color: text }}>{score}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full" style={{ background: isDark ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.06)" }}>
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: "linear-gradient(90deg, #A38A70, #7A8B76)" }}
                      initial={shouldReduceMotion ? false : { width: 0 }}
                      animate={{ width: `${score}%` }}
                      transition={{ duration: 0.55, delay: shouldReduceMotion ? 0 : 0.16 + index * 0.08, ease: EASE }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const queue = [
    ["Mon", "Founder POV", "8:00 AM"],
    ["Wed", "Carousel", "11:30 AM"],
    ["Thu", "Thread", "8:00 AM"],
    ["Sat", "Recap", "9:00 AM"],
  ] as const;

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
      <div className="rounded-[24px] p-4" style={{ background: panelBg, border: `1px solid ${panelBorder}` }}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-[11px] uppercase tracking-[0.24em] text-[#A38A70]">AI calendar</div>
            <div className="text-sm font-semibold mt-1" style={{ color: text }}>Recommended posts, already queued</div>
          </div>
          <CalendarDays className="h-4 w-4 text-[#7A8B76]" />
        </div>
        <div className="grid grid-cols-1 xs:grid-cols-2 gap-3">
          {queue.map(([day, label, time], index) => (
            <motion.div
              key={day}
              initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: shouldReduceMotion ? 0 : index * 0.08, ease: EASE }}
              className="rounded-[22px] p-3.5"
              style={{ background: index === 2 ? "rgba(163,138,112,0.16)" : isDark ? "rgba(12,11,9,0.38)" : "rgba(15,23,42,0.03)" }}
            >
              <div className="text-[10px] uppercase tracking-[0.18em]" style={{ color: isDark ? "rgba(242,237,232,0.32)" : "#A3A3A3" }}>{day}</div>
              <div className="mt-2 text-[14px] font-semibold" style={{ color: text }}>{label}</div>
              <div className="mt-1 text-[11px]" style={{ color: muted }}>Publish at {time}</div>
            </motion.div>
          ))}
        </div>
      </div>
      <div className="space-y-3">
        <div className="rounded-[24px] p-4" style={{ background: panelBg, border: `1px solid ${panelBorder}` }}>
          <div className="flex items-center justify-between mb-3">
            <div className="text-[12px] font-semibold" style={{ color: text }}>Approval queue</div>
            <div className="rounded-full px-2.5 py-1 text-[10px] font-medium text-[#8B6F52]" style={{ background: "rgba(163,138,112,0.1)" }}>
              3 awaiting review
            </div>
          </div>
          <div className="space-y-2.5">
            {[
              "Thursday 8:00 AM selected for max reach",
              "Caption tuned for comment-first engagement",
              "Variants generated for X and LinkedIn",
            ].map((item, index) => (
              <motion.div
                key={item}
                initial={shouldReduceMotion ? false : { opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: shouldReduceMotion ? 0 : 0.12 + index * 0.08, ease: EASE }}
                className="rounded-2xl px-3.5 py-3 text-[12px]"
                style={{ background: isDark ? "rgba(12,11,9,0.38)" : "rgba(15,23,42,0.03)", color: muted }}
              >
                {item}
              </motion.div>
            ))}
          </div>
        </div>
        <div className="rounded-[24px] p-4" style={{ background: "linear-gradient(135deg, rgba(15,23,42,0.92), rgba(163,138,112,0.82))", border: "1px solid rgba(163,138,112,0.18)" }}>
          <div className="flex items-end justify-between">
            <div>
              <div className="text-[11px] uppercase tracking-[0.24em] text-white/70">Execution confidence</div>
              <div className="text-[24px] font-semibold mt-1 text-white">Strategy running on cadence</div>
            </div>
            <div className="text-right text-white">
              <div className="text-[30px] font-bold tracking-[-0.04em]">94%</div>
              <div className="text-[11px] text-white/70">calendar coverage</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HowItWorks() {
  const shouldReduceMotion = useReducedMotion() ?? false;
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [activeStep, setActiveStep] = useState<StepIndex>(0);
  const [hasInteracted, setHasInteracted] = useState(false);

  useEffect(() => {
    if (shouldReduceMotion || hasInteracted) return;
    const interval = window.setInterval(() => setActiveStep((value) => ((value + 1) % STEPS.length) as StepIndex), 3600);
    return () => window.clearInterval(interval);
  }, [hasInteracted, shouldReduceMotion]);

  return (
    <section id="how-it-works" className="relative overflow-hidden bg-[#F9F8F6] py-10 sm:py-20">
      <div className="absolute left-[-8%] top-20 h-72 w-72 rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(163,138,112,0.09) 0%, rgba(163,138,112,0) 72%)", filter: "blur(14px)" }} />
      <div className="absolute right-[-6%] bottom-10 h-80 w-80 rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(122,139,118,0.08) 0%, rgba(122,139,118,0) 72%)", filter: "blur(20px)" }} />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">
        <div className="mb-12 max-w-2xl">
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: EASE }}
            className="flex items-center gap-2 mb-6"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">How it works</span>
          </motion.div>

          <motion.h2
            initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: EASE }}
            className="text-[28px] sm:text-[42px] lg:text-[52px] font-bold tracking-[-0.03em] leading-[1.04] text-neutral-900"
          >
            From connection to <span className="gradient-text">compounding growth</span>
          </motion.h2>

          <motion.p
            initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.12, ease: EASE }}
            className="mt-5 max-w-xl text-[15px] leading-[1.8]"
            style={{ color: isDark ? "rgba(242,237,232,0.56)" : "#5F5A55" }}
          >
            Explore each phase to see how Ittera turns scattered channels into a live strategy system.
          </motion.p>
        </div>

        <div className="grid items-stretch gap-6 lg:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)] xl:gap-8">
          <div className="space-y-3">
            {STEPS.map((step, index) => {
              const isActive = activeStep === index;
              const Icon = step.icon;

              return (
                <motion.button
                  key={step.num}
                  type="button"
                  initial={shouldReduceMotion ? false : { opacity: 0, y: 18 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-40px" }}
                  transition={{ duration: 0.45, delay: shouldReduceMotion ? 0 : index * 0.08, ease: EASE }}
                  onMouseEnter={() => { setHasInteracted(true); setActiveStep(index as StepIndex); }}
                  onFocus={() => { setHasInteracted(true); setActiveStep(index as StepIndex); }}
                  onClick={() => { setHasInteracted(true); setActiveStep(index as StepIndex); }}
                  className="group relative flex w-full overflow-hidden rounded-[28px] p-5 text-left transition-transform duration-300 hover:-translate-y-0.5"
                  style={{
                    background: isActive ? (isDark ? "linear-gradient(180deg, rgba(28,25,22,0.98), rgba(20,18,16,0.98))" : "linear-gradient(180deg, rgba(255,255,255,0.98), rgba(249,248,246,0.98))") : (isDark ? "rgba(20,18,16,0.7)" : "rgba(255,255,255,0.7)"),
                    border: `1px solid ${isActive ? "rgba(163,138,112,0.26)" : isDark ? "#2E2922" : "rgba(15,23,42,0.08)"}`,
                    boxShadow: isActive ? (isDark ? "0 20px 45px rgba(0,0,0,0.26)" : "0 18px 40px rgba(15,23,42,0.06)") : "none",
                  }}
                >
                  {isActive && <motion.div layoutId="how-it-works-active-glow" className="pointer-events-none absolute inset-0" style={{ background: "radial-gradient(circle at top right, rgba(163,138,112,0.12), rgba(163,138,112,0) 45%)" }} />}

                  <div className="relative z-10 flex min-h-full w-full flex-col">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div className="h-12 w-12 rounded-2xl flex items-center justify-center" style={{ background: isActive ? "rgba(163,138,112,0.14)" : isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.04)", border: `1px solid ${isActive ? "rgba(163,138,112,0.2)" : isDark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.06)"}` }}>
                          <Icon className="h-5 w-5" style={{ color: isActive ? "#A38A70" : isDark ? "rgba(242,237,232,0.45)" : "#737373" }} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-1.5">
                            {/* number + step-label pair — always aligned as a unit */}
                            <div className="flex items-center gap-1.5">
                              <div
                                className="rounded-[10px] px-2.5 py-1 text-[11px] font-mono tracking-[0.22em]"
                                style={{
                                  color: isActive ? "#A38A70" : isDark ? "rgba(242,237,232,0.25)" : "#A3A3A3",
                                  background: isActive ? "rgba(163,138,112,0.12)" : isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.03)",
                                  border: `1px solid ${isActive ? "rgba(163,138,112,0.16)" : isDark ? "rgba(255,255,255,0.05)" : "rgba(15,23,42,0.05)"}`,
                                }}
                              >
                                {step.num}
                              </div>
                              <div
                                className="rounded-[10px] px-2.5 py-1 text-[11px] font-medium tracking-[0.06em]"
                                style={{
                                  color: isActive ? (isDark ? "#F2EDE8" : "#3D3530") : isDark ? "rgba(242,237,232,0.32)" : "#8A8580",
                                  background: isActive ? (isDark ? "rgba(163,138,112,0.1)" : "rgba(61,53,48,0.06)") : isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.03)",
                                  border: `1px solid ${isActive ? "rgba(163,138,112,0.14)" : isDark ? "rgba(255,255,255,0.05)" : "rgba(15,23,42,0.05)"}`,
                                }}
                              >
                                {step.stepLabel}
                              </div>
                            </div>
                            {/* data pills */}
                            <div
                              className="rounded-[10px] px-2.5 py-1 text-[11px] leading-none"
                              style={{
                                background: isActive ? "rgba(163,138,112,0.1)" : isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.03)",
                                border: `1px solid ${isActive ? "rgba(163,138,112,0.16)" : isDark ? "rgba(255,255,255,0.05)" : "rgba(15,23,42,0.05)"}`,
                                color: isActive ? (isDark ? "rgba(242,237,232,0.8)" : "#6F5D4A") : isDark ? "rgba(242,237,232,0.42)" : "#737373",
                              }}
                            >
                              <span className="mr-1 uppercase tracking-[0.16em] text-[9px]">{step.leadLabel}</span>
                              <span className="font-semibold text-[11px]">{step.leadValue}</span>
                            </div>
                            <div
                              className="rounded-[10px] px-2.5 py-1 text-[11px] leading-none"
                              style={{
                                background: isActive ? "rgba(122,139,118,0.12)" : isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.03)",
                                border: `1px solid ${isActive ? "rgba(122,139,118,0.16)" : isDark ? "rgba(255,255,255,0.05)" : "rgba(15,23,42,0.05)"}`,
                                color: isActive ? (isDark ? "rgba(242,237,232,0.8)" : "#3F4A3C") : isDark ? "rgba(242,237,232,0.42)" : "#737373",
                              }}
                            >
                              <span className="mr-1 uppercase tracking-[0.16em] text-[9px]">{step.headerLabel}</span>
                              <span className="font-semibold text-[11px]">{step.headerValue}</span>
                            </div>
                          </div>
                          <h3 className="text-[18px] font-semibold tracking-tight mt-1" style={{ color: isDark ? "#F2EDE8" : "#171717" }}>{step.title}</h3>
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-0.5" style={{ color: isActive ? "#A38A70" : isDark ? "rgba(242,237,232,0.28)" : "#A3A3A3" }} />
                    </div>

                    <p className="mt-3.5 text-[14px] leading-[1.75]" style={{ color: isDark ? "rgba(242,237,232,0.56)" : "#5F5A55" }}>{step.description}</p>

                    <div className="mt-3.5 flex flex-wrap content-start gap-2">
                      {step.chips.map((chip) => (
                        <span key={chip} className="rounded-full px-3 py-1.5 text-[11px] font-medium" style={{ background: isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.04)", color: isDark ? "rgba(242,237,232,0.62)" : "#525252", border: `1px solid ${isDark ? "rgba(255,255,255,0.05)" : "rgba(15,23,42,0.05)"}` }}>
                          {chip}
                        </span>
                      ))}
                    </div>

                    <div className="mt-auto flex items-center justify-between rounded-[20px] px-4 py-3" style={{ background: isDark ? "rgba(12,11,9,0.38)" : "rgba(15,23,42,0.03)" }}>
                      <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: isDark ? "rgba(242,237,232,0.28)" : "#A3A3A3" }}>{step.statLabel}</div>
                      <div className="text-[20px] font-semibold tracking-[-0.03em]" style={{ color: isDark ? "#F2EDE8" : "#171717" }}>{step.statValue}</div>
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </div>

          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.55, delay: 0.12, ease: EASE }}
            className="relative overflow-hidden rounded-[32px] p-4 sm:p-5"
            style={{
              background: isDark ? "linear-gradient(180deg, rgba(20,18,16,0.96), rgba(28,25,22,0.96))" : "linear-gradient(180deg, rgba(255,255,255,0.96), rgba(249,248,246,0.96))",
              border: `1px solid ${isDark ? "#2E2922" : "rgba(15,23,42,0.08)"}`,
              boxShadow: isDark ? "0 24px 60px rgba(0,0,0,0.35)" : "0 24px 60px rgba(15,23,42,0.08)",
            }}
          >
            <div className="pointer-events-none absolute -top-16 right-0 h-48 w-48 rounded-full" style={{ background: "radial-gradient(circle, rgba(163,138,112,0.16) 0%, rgba(163,138,112,0) 72%)", filter: "blur(10px)" }} />
            <div className="relative z-10">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <div className="h-2.5 w-2.5 rounded-full bg-[#FF5F57]/80" />
                    <div className="h-2.5 w-2.5 rounded-full bg-[#FEBC2E]/80" />
                    <div className="h-2.5 w-2.5 rounded-full bg-[#28C840]/80" />
                  </div>
                  <div className="rounded-full px-3 py-1 text-[11px]" style={{ background: isDark ? "rgba(255,255,255,0.05)" : "rgba(15,23,42,0.04)", color: isDark ? "rgba(242,237,232,0.42)" : "#737373" }}>
                    app.ittera.ai / onboarding
                  </div>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-[#7A8B76]">
                  <span className="h-2 w-2 rounded-full bg-[#7A8B76] animate-pulse" />
                  Interactive preview
                </div>
              </div>

              <div className="mb-4 grid grid-cols-3 gap-2">
                {STEPS.map((step, index) => (
                  <div key={step.num} className="rounded-full px-3 py-2 text-[11px] font-medium text-center" style={{ background: index === activeStep ? "linear-gradient(135deg, rgba(163,138,112,0.18), rgba(122,139,118,0.12))" : isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.04)", color: index === activeStep ? (isDark ? "#F2EDE8" : "#171717") : isDark ? "rgba(242,237,232,0.42)" : "#737373", border: `1px solid ${index === activeStep ? "rgba(163,138,112,0.24)" : isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.05)"}` }}>
                    {step.num}
                  </div>
                ))}
              </div>

              <div className="overflow-hidden">
                <AnimatePresence initial={false} mode="wait">
                <motion.div
                  key={activeStep}
                  initial={shouldReduceMotion ? false : { opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={shouldReduceMotion ? undefined : { opacity: 0, y: -8 }}
                  transition={{ duration: 0.45, ease: EASE }}
                >
                  <PreviewContent activeStep={activeStep} isDark={isDark} shouldReduceMotion={shouldReduceMotion} />
                </motion.div>
                </AnimatePresence>
              </div>

              {/* Persistent AI insight summary — always visible below the preview */}
              <div
                className="mt-4 rounded-[22px] p-4"
                style={{
                  background: isDark ? "rgba(12,11,9,0.5)" : "rgba(15,23,42,0.03)",
                  border: `1px solid ${isDark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.07)"}`,
                }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="text-[11px] uppercase tracking-[0.22em] text-[#A38A70]">AI insight snapshot</div>
                  <div className="flex items-center gap-1.5 text-[10px]" style={{ color: isDark ? "rgba(242,237,232,0.36)" : "#A3A3A3" }}>
                    <Sparkles className="h-3 w-3 text-[#7A8B76]" />
                    Live analysis
                  </div>
                </div>

                <div className="grid grid-cols-[auto_1fr] gap-x-5 gap-y-1 items-center mb-3">
                  <div className="text-[11px] uppercase tracking-[0.16em]" style={{ color: isDark ? "rgba(242,237,232,0.32)" : "#A3A3A3" }}>Best window</div>
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-semibold tracking-[-0.02em]" style={{ color: isDark ? "#F2EDE8" : "#171717" }}>Thu 8:00 AM</span>
                    <span className="rounded-full px-2 py-0.5 text-[10px] font-medium text-[#7A8B76]" style={{ background: "rgba(122,139,118,0.12)" }}>2.8× reach</span>
                  </div>
                  <div className="text-[11px] uppercase tracking-[0.16em]" style={{ color: isDark ? "rgba(242,237,232,0.32)" : "#A3A3A3" }}>Top formats</div>
                  <div className="flex items-center gap-1.5">
                    {([["Carousels", 92], ["Threads", 81], ["Founder POV", 88]] as const).map(([label, score]) => (
                      <span
                        key={label}
                        className="rounded-[8px] px-2 py-1 text-[10px] font-medium"
                        style={{
                          background: isDark ? "rgba(255,255,255,0.05)" : "rgba(15,23,42,0.04)",
                          border: `1px solid ${isDark ? "rgba(255,255,255,0.07)" : "rgba(15,23,42,0.06)"}`,
                          color: isDark ? "rgba(242,237,232,0.7)" : "#525252",
                        }}
                      >
                        {label} <span className="font-semibold" style={{ color: isDark ? "#F2EDE8" : "#171717" }}>{score}</span>
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5">
                  {([["Carousels", 92], ["Threads", 81], ["Founder POV", 88]] as const).map(([label, score], i) => (
                    <div key={label} className="flex items-center gap-3">
                      <div className="w-[72px] text-[10px] shrink-0" style={{ color: isDark ? "rgba(242,237,232,0.38)" : "#8A8580" }}>{label}</div>
                      <div className="relative flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: isDark ? "rgba(255,255,255,0.07)" : "rgba(15,23,42,0.06)" }}>
                        <motion.div
                          className="absolute inset-y-0 left-0 rounded-full"
                          style={{ background: i === 0 ? "linear-gradient(90deg,#A38A70,#C4A882)" : i === 2 ? "linear-gradient(90deg,#7A8B76,#9AAD96)" : "linear-gradient(90deg,#A38A70,#7A8B76)" }}
                          initial={shouldReduceMotion ? false : { width: 0 }}
                          whileInView={{ width: `${score}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.6, delay: i * 0.07, ease: EASE }}
                        />
                      </div>
                      <div className="w-6 text-right text-[10px] font-semibold shrink-0" style={{ color: isDark ? "rgba(242,237,232,0.55)" : "#525252" }}>{score}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
