"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Check, RotateCcw, Sparkles, X, Zap } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const EASE = [0.16, 1, 0.3, 1] as const;

const ITEMS = [
  {
    label: "Workflow",
    before: "5+ disconnected tools for one workflow",
    after: "One unified AI strategy engine",
    impact: "5 to 1",
    detail: "Plan, create, optimize, and publish from one system instead of stitching tools together.",
  },
  {
    label: "Analytics",
    before: "Manual data analysis across platforms",
    after: "Real-time performance insights, automated",
    impact: "Live signal",
    detail: "Ittera watches every channel together, so the next move is based on current performance rather than guesswork.",
  },
  {
    label: "Timing",
    before: "Guessing optimal posting times",
    after: "AI-predicted optimal windows per platform",
    impact: "Window found",
    detail: "The engine surfaces the best publish windows for each channel instead of forcing one generic posting schedule.",
  },
  {
    label: "Repurposing",
    before: "Hours spent reformatting for each platform",
    after: "Instant repurposing in 10+ formats",
    impact: "10+ outputs",
    detail: "A single idea becomes channel-native content without burning hours on manual rewrites and formatting passes.",
  },
  {
    label: "Trends",
    before: "Reactive trend-chasing after it peaks",
    after: "Trend Radar surfaces opportunities 48h early",
    impact: "48h lead",
    detail: "You publish into momentum while a topic is still rising, not after the spike has already passed.",
  },
  {
    label: "ROI",
    before: "No clear ROI on your content effort",
    after: "Clear attribution from content to growth",
    impact: "Prove impact",
    detail: "Every post connects back to measurable growth signals so content stops feeling like a black box.",
  },
];

const STATS = [
  { value: "10+", label: "hours saved each week" },
  { value: "5 to 1", label: "tools collapsed into one" },
  { value: "3x", label: "faster publishing cycles" },
  { value: "48h", label: "earlier trend visibility" },
];

export default function Solution() {
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [activeIndex, setActiveIndex] = useState(0);
  const [revealedRows, setRevealedRows] = useState<Set<number>>(new Set([0]));
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasPlayed, setHasPlayed] = useState(false);

  const shellRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<number[]>([]);

  const clearTimers = () => {
    timerRef.current.forEach((id) => window.clearTimeout(id));
    timerRef.current = [];
  };

  useEffect(() => () => clearTimers(), []);

  const runSequence = () => {
    if (isPlaying) return;

    if (shouldReduceMotion) {
      setActiveIndex(ITEMS.length - 1);
      setRevealedRows(new Set(ITEMS.map((_, index) => index)));
      setHasPlayed(true);
      setIsPlaying(false);
      return;
    }

    clearTimers();
    setIsPlaying(true);
    setHasPlayed(false);
    setRevealedRows(new Set());

    ITEMS.forEach((_, index) => {
      const id = window.setTimeout(() => {
        setActiveIndex(index);
        setRevealedRows((prev) => new Set(prev).add(index));

        if (index === ITEMS.length - 1) {
          const doneId = window.setTimeout(() => {
            setIsPlaying(false);
            setHasPlayed(true);
          }, 260);

          timerRef.current.push(doneId);
        }
      }, index * 220);

      timerRef.current.push(id);
    });
  };

  const resetSequence = () => {
    clearTimers();
    setIsPlaying(false);
    setHasPlayed(false);
    setActiveIndex(0);
    setRevealedRows(new Set([0]));
  };

  const onShellMove = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!shellRef.current || !glowRef.current || shouldReduceMotion) return;

    const rect = shellRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    glowRef.current.style.opacity = "1";
    glowRef.current.style.background = `radial-gradient(420px circle at ${x}px ${y}px, ${isDark ? "rgba(196,168,130,0.14)" : "rgba(163,138,112,0.12)"}, transparent 62%)`;
  };

  const onShellLeave = () => {
    if (glowRef.current) {
      glowRef.current.style.opacity = "0";
    }
  };

  const activeItem = ITEMS[activeIndex];
  const revealedCount = Math.max(revealedRows.size, activeIndex + 1);
  const progress = `${Math.round((revealedCount / ITEMS.length) * 100)}%`;

  const titleColor = isDark ? "#F2EDE8" : "#171717";
  const bodyColor = isDark ? "rgba(242,237,232,0.56)" : "#737373";
  const mutedColor = isDark ? "rgba(242,237,232,0.32)" : "#A3A3A3";
  const statSurface = isDark ? "rgba(20,18,16,0.86)" : "rgba(255,255,255,0.88)";
  const shellBg = isDark
    ? "linear-gradient(180deg, rgba(28,25,22,0.96) 0%, rgba(20,18,16,0.98) 100%)"
    : "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(249,248,246,0.98) 100%)";
  const shellBorder = isDark ? "#2E2922" : "#EAEAEC";
  const shellShadow = isDark ? "0 24px 80px rgba(0,0,0,0.4)" : "0 24px 80px rgba(15,23,42,0.08)";
  const gridLine = isDark ? "rgba(242,237,232,0.06)" : "rgba(23,23,23,0.05)";
  const beforeSurface = isDark ? "rgba(15,13,11,0.82)" : "rgba(250,250,250,0.96)";
  const afterSurface = isDark ? "rgba(23,20,17,0.95)" : "rgba(255,255,255,0.98)";
  const coreSurface = isDark ? "rgba(24,21,18,0.92)" : "rgba(247,244,240,0.96)";
  const beforeText = isDark ? "rgba(242,237,232,0.42)" : "#9A9A9A";
  const xColor = isDark ? "rgba(242,237,232,0.18)" : "#D4D4D4";
  const afterText = isDark ? "rgba(242,237,232,0.74)" : "#2B2B2B";
  const cardGlow = isDark ? "rgba(196,168,130,0.12)" : "rgba(163,138,112,0.08)";
  const accentBorder = isDark ? "rgba(196,168,130,0.22)" : "rgba(163,138,112,0.2)";

  return (
    <section id="solution" className="relative overflow-hidden py-14 sm:py-28">
      <div
        className="pointer-events-none absolute left-1/2 top-[44%] h-[680px] w-[980px] -translate-x-1/2 -translate-y-1/2"
        style={{
          background: isDark
            ? "radial-gradient(ellipse, rgba(163,138,112,0.15) 0%, transparent 70%)"
            : "radial-gradient(ellipse, rgba(163,138,112,0.1) 0%, transparent 70%)",
        }}
      />

      <div className="relative z-10 mx-auto max-w-6xl px-6 lg:px-10">
        <div className="mb-14 text-center">
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: EASE }}
            className="mb-6 flex items-center justify-center gap-2"
          >
            <div className="h-1.5 w-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">The solution</span>
            <div className="h-1.5 w-1.5 rounded-full bg-[#A38A70]/70" />
          </motion.div>

          <motion.h2
            initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.06, ease: EASE }}
            className="mx-auto mb-4 max-w-3xl text-[28px] sm:text-[42px] lg:text-[56px] font-bold leading-[1.03] tracking-[-0.04em]"
            style={{ color: titleColor }}
          >
            Your content stack, rebuilt into{" "}
            <span className="gradient-text">one unfair advantage.</span>
          </motion.h2>

          <motion.p
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.12, ease: EASE }}
            className="mx-auto max-w-2xl text-[15px] leading-[1.8]"
            style={{ color: bodyColor }}
          >
            Click any row or run the full sequence. This section shows how Ittera turns fragmented creator work into one coordinated growth engine.
          </motion.p>
        </div>

        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.18, ease: EASE }}
          className="mb-10 flex flex-wrap items-center justify-center gap-3"
        >
          {STATS.map((stat) => (
            <div
              key={stat.label}
              className="rounded-full px-4 py-3 text-center backdrop-blur-sm"
              style={{
                background: statSurface,
                border: `1px solid ${shellBorder}`,
                boxShadow: isDark ? "0 8px 24px rgba(0,0,0,0.2)" : "0 8px 24px rgba(15,23,42,0.06)",
              }}
            >
              <div className="text-[17px] font-semibold tracking-[-0.03em] gradient-text">{stat.value}</div>
              <div className="mt-0.5 text-[11px]" style={{ color: mutedColor }}>
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>

        <motion.div
          ref={shellRef}
          initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.58, delay: 0.24, ease: EASE }}
          onMouseMove={onShellMove}
          onMouseLeave={onShellLeave}
          className="relative mx-auto max-w-5xl overflow-hidden rounded-[30px] p-4 sm:p-6"
          style={{
            background: shellBg,
            border: `1px solid ${shellBorder}`,
            boxShadow: shellShadow,
          }}
        >
          <div
            ref={glowRef}
            className="pointer-events-none absolute inset-0 transition-opacity duration-200"
            style={{ opacity: 0 }}
          />
          <div
            className="pointer-events-none absolute inset-0 opacity-70"
            style={{
              backgroundImage: `linear-gradient(${gridLine} 1px, transparent 1px), linear-gradient(90deg, ${gridLine} 1px, transparent 1px)`,
              backgroundSize: "44px 44px",
              maskImage: "linear-gradient(to bottom, rgba(0,0,0,0.7), transparent 96%)",
            }}
          />

          <div className="relative z-10">
            <div className="mb-6 flex flex-col items-center gap-4 text-center">
              <div
                className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-[11px] font-medium tracking-[0.14em] uppercase"
                style={{
                  background: isDark ? "rgba(196,168,130,0.08)" : "rgba(163,138,112,0.08)",
                  border: `1px solid ${accentBorder}`,
                  color: "#A38A70",
                }}
              >
                <Sparkles className="h-3.5 w-3.5" />
                Interactive Transformation Lab
              </div>

              <div className="max-w-2xl">
                <p className="text-[15px] font-medium" style={{ color: titleColor }}>
                  Watch each pain point get rewritten into a system-level advantage.
                </p>
                <p className="mt-1 text-[13px] leading-[1.7]" style={{ color: bodyColor }}>
                  Hover or tap a row to inspect it. Run the full sequence to show the entire transformation in motion.
                </p>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-3">
                <button
                  type="button"
                  onClick={runSequence}
                  disabled={isPlaying}
                  className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-[13px] font-semibold transition-all duration-300 hover:-translate-y-px active:scale-[0.985] disabled:cursor-not-allowed disabled:opacity-55"
                  style={{
                    background: isDark ? "linear-gradient(135deg, #D1B089 0%, #A38A70 100%)" : "#0F172A",
                    color: isDark ? "#0C0B09" : "#FFFFFF",
                    boxShadow: isDark ? "0 14px 28px rgba(196,168,130,0.18)" : "0 14px 28px rgba(15,23,42,0.14)",
                  }}
                >
                  <Zap className="h-3.5 w-3.5" />
                  {isPlaying ? "Transforming..." : "Run full transformation"}
                </button>

                <button
                  type="button"
                  onClick={resetSequence}
                  className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-[13px] font-medium transition-all duration-300 hover:-translate-y-px active:scale-[0.985]"
                  style={{
                    background: isDark ? "rgba(28,25,22,0.92)" : "rgba(255,255,255,0.92)",
                    border: `1px solid ${shellBorder}`,
                    color: bodyColor,
                  }}
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  {hasPlayed ? "Reset demo" : "Reset focus"}
                </button>
              </div>
            </div>

            <div
              className="mb-6 overflow-hidden rounded-full"
              style={{
                background: isDark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.06)",
                border: `1px solid ${isDark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.05)"}`,
              }}
            >
              <motion.div
                className="h-2 rounded-full"
                animate={{ width: progress }}
                transition={{ duration: shouldReduceMotion ? 0 : 0.35, ease: EASE }}
                style={{ background: "linear-gradient(90deg, #A38A70 0%, #D1B089 100%)" }}
              />
            </div>

            <div className="mb-3 grid grid-cols-[minmax(0,1fr)_64px_minmax(0,1fr)] items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.14em]">
              <div className="rounded-full px-4 py-2 text-center" style={{ background: beforeSurface, color: mutedColor, border: `1px solid ${shellBorder}` }}>
                Before Ittera
              </div>
              <div className="text-center" style={{ color: mutedColor }}>
                Core
              </div>
              <div className="rounded-full px-4 py-2 text-center" style={{ background: afterSurface, color: "#A38A70", border: `1px solid ${accentBorder}` }}>
                With Ittera
              </div>
            </div>

            <div className="space-y-3">
              {ITEMS.map((item, index) => {
                const isActive = activeIndex === index;
                const isRevealed = revealedRows.has(index);

                return (
                  <motion.button
                    key={item.label}
                    type="button"
                    onClick={() => setActiveIndex(index)}
                    onMouseEnter={() => setActiveIndex(index)}
                    onFocus={() => setActiveIndex(index)}
                    aria-pressed={isActive}
                    className="grid w-full grid-cols-[minmax(0,1fr)_64px_minmax(0,1fr)] items-stretch gap-3 rounded-[24px] p-2 text-left transition-all duration-300"
                    style={{
                      background: isActive ? cardGlow : "transparent",
                      border: `1px solid ${isActive ? accentBorder : "transparent"}`,
                    }}
                    whileHover={shouldReduceMotion ? undefined : { y: -2 }}
                    transition={{ duration: 0.2, ease: EASE }}
                  >
                    <motion.div
                      className="relative overflow-hidden rounded-[20px] px-4 py-4 sm:px-5"
                      animate={{ opacity: isActive ? 0.55 : 1 }}
                      transition={{ duration: 0.22 }}
                      style={{
                        background: beforeSurface,
                        border: `1px solid ${shellBorder}`,
                      }}
                    >
                      <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: mutedColor }}>
                        <X className="h-3 w-3" style={{ color: xColor }} />
                        {item.label}
                      </div>
                      <div className="relative pr-2 text-[13px] leading-[1.7]" style={{ color: beforeText }}>
                        {item.before}
                        <AnimatePresence>
                          {isActive && (
                            <motion.div
                              initial={{ scaleX: 0, opacity: 0 }}
                              animate={{ scaleX: 1, opacity: 1 }}
                              exit={{ scaleX: 0, opacity: 0 }}
                              transition={{ duration: 0.24, ease: EASE }}
                              className="pointer-events-none absolute left-0 top-1/2 h-px w-full origin-left"
                              style={{ background: isDark ? "rgba(242,237,232,0.22)" : "rgba(23,23,23,0.18)" }}
                            />
                          )}
                        </AnimatePresence>
                      </div>
                    </motion.div>

                    <div
                      className="flex flex-col items-center justify-center rounded-[20px] px-2 py-4"
                      style={{
                        background: coreSurface,
                        border: `1px solid ${shellBorder}`,
                      }}
                    >
                      <motion.div
                        animate={{
                          scale: isActive ? 1.08 : 1,
                          boxShadow: isActive
                            ? isDark
                              ? "0 0 0 10px rgba(196,168,130,0.08)"
                              : "0 0 0 10px rgba(163,138,112,0.08)"
                            : "0 0 0 0 rgba(0,0,0,0)",
                        }}
                        transition={{ duration: 0.25, ease: EASE }}
                        className="flex h-11 w-11 items-center justify-center rounded-full"
                        style={{
                          background: isRevealed
                            ? "linear-gradient(135deg, rgba(209,176,137,0.22) 0%, rgba(163,138,112,0.2) 100%)"
                            : isDark
                              ? "rgba(255,255,255,0.04)"
                              : "rgba(15,23,42,0.04)",
                          border: `1px solid ${isRevealed ? accentBorder : shellBorder}`,
                        }}
                      >
                        <motion.div
                          animate={{
                            x: isActive ? 2 : 0,
                            rotate: isPlaying && isActive ? 6 : 0,
                          }}
                          transition={{ duration: 0.22, ease: EASE }}
                        >
                          <ArrowRight className="h-4 w-4" style={{ color: isRevealed ? "#A38A70" : mutedColor }} />
                        </motion.div>
                      </motion.div>
                      <div className="mt-2 text-center text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: isRevealed ? "#A38A70" : mutedColor }}>
                        {index + 1}/{ITEMS.length}
                      </div>
                    </div>

                    <motion.div
                      className="relative overflow-hidden rounded-[20px] px-4 py-4 sm:px-5"
                      animate={{
                        backgroundColor: isActive
                          ? isDark
                            ? "rgba(32,27,23,0.98)"
                            : "rgba(255,255,255,1)"
                          : afterSurface,
                      }}
                      transition={{ duration: 0.22 }}
                      style={{
                        border: `1px solid ${isActive ? accentBorder : shellBorder}`,
                      }}
                    >
                      <AnimatePresence>
                        {isActive && (
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="pointer-events-none absolute inset-0"
                            style={{
                              background: isDark
                                ? "radial-gradient(circle at left center, rgba(196,168,130,0.12) 0%, transparent 64%)"
                                : "radial-gradient(circle at left center, rgba(163,138,112,0.1) 0%, transparent 64%)",
                            }}
                          />
                        )}
                      </AnimatePresence>

                      <div className="relative z-10">
                        <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: "#A38A70" }}>
                          <Check className="h-3 w-3" />
                          {item.impact}
                        </div>
                        <motion.div
                          className="pr-2 text-[13px] leading-[1.7]"
                          animate={{ color: isActive ? titleColor : afterText }}
                          transition={{ duration: 0.22 }}
                        >
                          {item.after}
                        </motion.div>
                      </div>
                    </motion.div>
                  </motion.button>
                );
              })}
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeItem.label}
                  initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.24, ease: EASE }}
                  className="rounded-[24px] p-5 text-left"
                  style={{
                    background: isDark ? "rgba(17,15,13,0.95)" : "rgba(255,255,255,0.96)",
                    border: `1px solid ${shellBorder}`,
                  }}
                >
                  <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.14em]" style={{ color: "#A38A70" }}>
                    <Sparkles className="h-3.5 w-3.5" />
                    Active insight
                  </div>
                  <h3 className="mb-2 text-[22px] font-semibold tracking-[-0.03em]" style={{ color: titleColor }}>
                    {activeItem.after}
                  </h3>
                  <p className="max-w-2xl text-[14px] leading-[1.8]" style={{ color: bodyColor }}>
                    {activeItem.detail}
                  </p>
                </motion.div>
              </AnimatePresence>

              <div
                className="rounded-[24px] p-5"
                style={{
                  background: isDark ? "rgba(24,21,18,0.92)" : "rgba(247,244,240,0.96)",
                  border: `1px solid ${shellBorder}`,
                }}
              >
                <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em]" style={{ color: mutedColor }}>
                  System state
                </div>
                <div className="mb-2 text-[34px] font-semibold tracking-[-0.04em] gradient-text">{progress}</div>
                <p className="text-[13px] leading-[1.7]" style={{ color: bodyColor }}>
                  {revealedCount} of {ITEMS.length} transformation layers are active. The section stays centered, but each row is still individually explorable.
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
