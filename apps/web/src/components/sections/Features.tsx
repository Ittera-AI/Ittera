"use client";

import { useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { CalendarDays, Sparkles, RefreshCw, BarChart3, Globe } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const EASE = [0.16, 1, 0.3, 1] as const;

function CalendarMini({ isDark }: { isDark: boolean }) {
  const days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
  const filled = [false, true, true, false, true, true, false];
  const bg     = isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.02)";
  const border = isDark ? "#2E2922" : "#EAEAEC";
  return (
    <div className="grid grid-cols-7 gap-1 p-3 rounded-xl" style={{ background: bg, border: `1px solid ${border}` }}>
      {days.map((d, i) => (
        <div key={i} className="flex flex-col items-center gap-1">
          <span className="text-[8px]" style={{ color: isDark ? "rgba(242,237,232,0.3)" : "#a3a3a3" }}>{d}</span>
          <div className="w-5 h-5 rounded-md text-[7px] font-bold flex items-center justify-center"
            style={filled[i]
              ? { background: isDark ? "rgba(196,168,130,0.12)" : "rgba(15,23,42,0.05)", border: `1px solid ${isDark ? "rgba(196,168,130,0.2)" : "rgba(15,23,42,0.10)"}`, color: isDark ? "#C4A882" : "#737373" }
              : { background: bg, border: `1px solid ${border}`, color: isDark ? "rgba(242,237,232,0.2)" : "#D4D4D4" }}>
            {i + 10}
          </div>
        </div>
      ))}
    </div>
  );
}

function CoachMini({ isDark }: { isDark: boolean }) {
  const bg     = isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.02)";
  const border = isDark ? "#2E2922" : "#EAEAEC";
  const track  = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)";
  return (
    <div className="space-y-2 p-3 rounded-xl" style={{ background: bg, border: `1px solid ${border}` }}>
      {[{ t: "Post Tuesday 8AM → 3.2× reach", v: 82 }, { t: "Use question hooks → +67% engage", v: 67 }, { t: "Add trending #AI tag now", v: 91 }].map((item, i) => (
        <div key={i} className="space-y-0.5">
          <p className="text-[9px]" style={{ color: isDark ? "rgba(242,237,232,0.5)" : "#737373" }}>{item.t}</p>
          <div className="h-1 rounded-full overflow-hidden" style={{ background: track }}>
            <motion.div className="h-full rounded-full" style={{ background: "linear-gradient(90deg, #A38A70, #7A8B76)" }}
              initial={{ width: 0 }} whileInView={{ width: `${item.v}%` }} viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 + i * 0.12, ease: EASE }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function AnalyticsMini({ isDark }: { isDark: boolean }) {
  const bars = [45, 62, 38, 88, 55, 72, 91];
  const bg     = isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.02)";
  const border = isDark ? "#2E2922" : "#EAEAEC";
  return (
    <div className="p-3 rounded-xl" style={{ background: bg, border: `1px solid ${border}` }}>
      <div className="flex items-end gap-1 h-8 mb-2">
        {bars.map((h, i) => (
          <motion.div key={i} className="flex-1 rounded-sm"
            style={{ height: `${h}%`, transformOrigin: "bottom", background: i === 6 ? "linear-gradient(to top, rgba(163,138,112,0.8), rgba(163,138,112,0.3))" : i % 2 === 0 ? "rgba(163,138,112,0.4)" : isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.04)" }}
            initial={{ scaleY: 0 }} whileInView={{ scaleY: 1 }} viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.06, ease: EASE }} />
        ))}
      </div>
      <div className="flex justify-between text-[8px]" style={{ color: isDark ? "rgba(242,237,232,0.3)" : "#a3a3a3" }}>
        {["M","T","W","T","F","S","S"].map((d, i) => <span key={i}>{d}</span>)}
      </div>
    </div>
  );
}

function RepurposeMini({ isDark }: { isDark: boolean }) {
  const bg     = isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.02)";
  const border = isDark ? "#2E2922" : "#EAEAEC";
  const dotColor = isDark ? "rgba(242,237,232,0.2)" : "#D4D4D4";
  return (
    <div className="p-3 rounded-xl space-y-1.5" style={{ background: bg, border: `1px solid ${border}` }}>
      <div className="flex items-center gap-2 p-1.5 rounded-lg" style={{ background: "rgba(163,138,112,0.1)", border: "1px solid rgba(163,138,112,0.15)" }}>
        <div className="w-5 h-5 rounded-md flex items-center justify-center text-[8px] font-bold" style={{ background: "rgba(163,138,112,0.25)", color: "#8B6F52" }}>TW</div>
        <div className="text-[9px] flex-1 truncate" style={{ color: isDark ? "rgba(242,237,232,0.5)" : "#737373" }}>Thread: AI Productivity Tips</div>
        <span className="text-[7px] font-medium" style={{ color: isDark ? "rgba(242,237,232,0.4)" : "#737373" }}>→ 4 formats</span>
      </div>
      {["LinkedIn Post", "Instagram Caption", "Newsletter Snippet"].map((fmt) => (
        <div key={fmt} className="flex items-center gap-2 pl-2">
          <div className="w-1 h-1 rounded-full" style={{ background: dotColor }} />
          <span className="text-[8.5px]" style={{ color: isDark ? "rgba(242,237,232,0.35)" : "#a3a3a3" }}>{fmt}</span>
        </div>
      ))}
    </div>
  );
}

function PublisherMini({ isDark }: { isDark: boolean }) {
  const bg     = isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.02)";
  const border = isDark ? "#2E2922" : "#EAEAEC";
  return (
    <div className="p-3 rounded-xl space-y-1.5" style={{ background: bg, border: `1px solid ${border}` }}>
      {[{ name: "LinkedIn", color: "#0a66c2", status: "Scheduled" }, { name: "X / Twitter", color: "#0F172A", status: "Scheduled" }, { name: "Instagram", color: "#e1306c", status: "Draft" }, { name: "TikTok", color: "#010101", status: "Queued" }].map((p) => (
        <div key={p.name} className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-md" style={{ background: p.color, border: `1px solid ${border}` }} />
            <span className="text-[9px]" style={{ color: isDark ? "rgba(242,237,232,0.5)" : "#737373" }}>{p.name}</span>
          </div>
          <span className="text-[8px] font-medium px-1.5 py-0.5 rounded-full"
            style={p.status === "Scheduled" || p.status === "Queued"
              ? { background: "rgba(163,138,112,0.1)", color: "#8B6F52", border: "1px solid rgba(163,138,112,0.15)" }
              : { background: isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.03)", color: isDark ? "rgba(242,237,232,0.4)" : "#A3A3A3", border: `1px solid ${border}` }}>
            {p.status}
          </span>
        </div>
      ))}
    </div>
  );
}

function FeatureCard({ feature, index, isDark }: { feature: ReturnType<typeof buildFeatures>[0]; index: number; isDark: boolean }) {
  const cardRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);
  const rectRef = useRef<DOMRect | null>(null);
  const shouldReduceMotion = useReducedMotion();
  const { icon: Icon, title, description, Visual, wide } = feature;

  const cardBg    = isDark ? "#141210" : "white";
  const cardBorder= isDark ? "#2E2922" : "#EAEAEC";
  const titleColor= isDark ? "#F2EDE8" : "#171717";
  const descColor = isDark ? "rgba(242,237,232,0.5)" : "#737373";
  const iconBg    = isDark ? "rgba(196,168,130,0.1)" : "rgba(163,138,112,0.1)";
  const iconBorder= isDark ? "rgba(196,168,130,0.2)" : "rgba(163,138,112,0.15)";

  const onMouseEnter = () => {
    if (cardRef.current) rectRef.current = cardRef.current.getBoundingClientRect();
  };

  const onMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!rectRef.current || !glowRef.current) return;
    const rect = rectRef.current;
    glowRef.current.style.background = `radial-gradient(280px circle at ${e.clientX - rect.left}px ${e.clientY - rect.top}px, rgba(163,138,112,${isDark ? "0.14" : "0.08"}), transparent 65%)`;
    glowRef.current.style.opacity = "1";
  };

  const onMouseLeave = () => { if (glowRef.current) glowRef.current.style.opacity = "0"; };

  return (
    <motion.div ref={cardRef}
      initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, delay: index * 0.07, ease: EASE }}
      onMouseEnter={onMouseEnter} onMouseMove={onMouseMove} onMouseLeave={onMouseLeave}
      className={`relative group p-6 rounded-2xl cursor-default transition-[border-color,box-shadow] duration-300 ${wide ? "md:col-span-2" : ""}`}
      style={{ border: `1px solid ${cardBorder}`, background: cardBg, boxShadow: isDark ? "0 1px 3px rgba(0,0,0,0.3)" : "0 1px 3px rgba(0,0,0,0.06)" }}
    >
      <div ref={glowRef} className="absolute inset-0 rounded-2xl pointer-events-none transition-opacity duration-200" style={{ opacity: 0 }} />
      <div className="relative z-10">
        <div className="mb-4">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: iconBg, border: `1px solid ${iconBorder}` }}>
            <Icon className="w-4 h-4 text-[#8B6F52]" />
          </div>
        </div>
        <h3 className="text-[15px] font-semibold mb-2 tracking-tight" style={{ color: titleColor }}>{title}</h3>
        <p className="text-[13px] leading-[1.7] mb-4" style={{ color: descColor }}>{description}</p>
        <Visual isDark={isDark} />
      </div>
    </motion.div>
  );
}

function buildFeatures() {
  return [
    { icon: CalendarDays, title: "Smart Content Calendar", description: "Visual drag-and-drop calendar with AI-suggested publish windows based on your audience's peak activity.", Visual: CalendarMini, wide: true },
    { icon: Sparkles,     title: "AI Engagement Coach",      description: "Real-time coaching on hook strength, topic angle, and timing — personalized to your specific audience.", Visual: CoachMini, wide: false },
    { icon: RefreshCw,    title: "Content Repurposing Engine", description: "One tweet becomes a LinkedIn post, newsletter section, and Instagram caption in one click.", Visual: RepurposeMini, wide: false },
    { icon: BarChart3,    title: "Analytics Hub",             description: "Unified analytics across all platforms. See exactly what drives growth and what to double down on.", Visual: AnalyticsMini, wide: false },
    { icon: Globe,        title: "Multi-Platform Publisher",  description: "Schedule and publish to LinkedIn, X, Instagram, and TikTok from one unified queue.", Visual: PublisherMini, wide: false },
  ];
}

export default function Features() {
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const FEATURES = buildFeatures();

  return (
    <section id="features" className="py-12 sm:py-24 bg-[#F9F8F6] relative">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse at top right, rgba(163,138,112,0.12) 0%, transparent 65%)" }} />
      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">
        <div className="max-w-xl mb-14">
          <motion.div initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.5 }} className="flex items-center gap-2 mb-6">
            <div className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">Features</span>
          </motion.div>
          <motion.h2 initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.55, delay: 0.07 }}
            className="text-[28px] sm:text-[42px] lg:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-neutral-900 mb-4">
            Every tool you need.{" "}<span className="gradient-text">Nothing you don&apos;t.</span>
          </motion.h2>
          <motion.p initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.5, delay: 0.14 }}
            className="text-[15px] text-neutral-500 leading-[1.75]">
            Five features, one platform. Built for creators who want results, not dashboards.
          </motion.p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {FEATURES.map((feature, i) => (
            <FeatureCard key={feature.title} feature={feature} index={i} isDark={isDark} />
          ))}
        </div>
      </div>
    </section>
  );
}
