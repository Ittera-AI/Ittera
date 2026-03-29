"use client";

import { useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { CalendarDays, Sparkles, TrendingUp, RefreshCw, BarChart3, Globe } from "lucide-react";
const EASE = [0.16, 1, 0.3, 1] as const;

function CalendarMini() {
  const days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
  const filled = [false, true, true, false, true, true, false];
  return (
    <div className="grid grid-cols-7 gap-1 p-3 rounded-xl" style={{ background: "rgba(0,0,0,0.02)", border: "1px solid #EAEAEC" }}>
      {days.map((d, i) => (
        <div key={i} className="flex flex-col items-center gap-1">
          <span className="text-[8px] text-neutral-400">{d}</span>
          <div className="w-5 h-5 rounded-md text-[7px] font-bold flex items-center justify-center"
            style={filled[i]
              ? { background: "rgba(15,23,42,0.05)", border: "1px solid rgba(15,23,42,0.10)", color: "#737373" }
              : { background: "rgba(0,0,0,0.02)", border: "1px solid #EAEAEC", color: "#D4D4D4" }}>
            {i + 10}
          </div>
        </div>
      ))}
    </div>
  );
}

function CoachMini() {
  return (
    <div className="space-y-2 p-3 rounded-xl" style={{ background: "rgba(0,0,0,0.02)", border: "1px solid #EAEAEC" }}>
      {[{ t: "Post Tuesday 8AM → 3.2× reach", v: 82 }, { t: "Use question hooks → +67% engage", v: 67 }, { t: "Add trending #AI tag now", v: 91 }].map((item, i) => (
        <div key={i} className="space-y-0.5">
          <p className="text-[9px] text-neutral-500">{item.t}</p>
          <div className="h-1 rounded-full overflow-hidden" style={{ background: "rgba(0,0,0,0.04)" }}>
            <motion.div className="h-full rounded-full" style={{ background: "linear-gradient(90deg, #A38A70, #7A8B76)" }}
              initial={{ width: 0 }} whileInView={{ width: `${item.v}%` }} viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 + i * 0.12, ease: EASE }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function TrendsMini() {
  return (
    <div className="space-y-1.5 p-3 rounded-xl" style={{ background: "rgba(0,0,0,0.02)", border: "1px solid #EAEAEC" }}>
      {[{ label: "AI Tools", pct: "+340%", hot: true }, { label: "Creator Burnout", pct: "+180%", hot: true }, { label: "Short-Form Video", pct: "+210%", hot: false }].map((item) => (
        <div key={item.label} className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] text-neutral-500">{item.label}</span>
            {item.hot && <span className="text-[7px] px-1.5 py-0.5 rounded-full font-semibold tracking-wide" style={{ background: "rgba(163,138,112,0.1)", border: "1px solid rgba(163,138,112,0.15)", color: "#8B6F52" }}>HOT</span>}
          </div>
          <span className="text-[9px] font-semibold" style={{ color: "#A38A70" }}>{item.pct}</span>
        </div>
      ))}
    </div>
  );
}

function AnalyticsMini() {
  const bars = [45, 62, 38, 88, 55, 72, 91];
  return (
    <div className="p-3 rounded-xl" style={{ background: "rgba(0,0,0,0.02)", border: "1px solid #EAEAEC" }}>
      <div className="flex items-end gap-1 h-8 mb-2">
        {bars.map((h, i) => (
          <motion.div key={i} className="flex-1 rounded-sm"
            style={{ height: `${h}%`, transformOrigin: "bottom", background: i === 6 ? "linear-gradient(to top, rgba(163,138,112,0.8), rgba(163,138,112,0.3))" : i % 2 === 0 ? "rgba(163,138,112,0.4)" : "rgba(0,0,0,0.04)" }}
            initial={{ scaleY: 0 }} whileInView={{ scaleY: 1 }} viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.06, ease: EASE }} />
        ))}
      </div>
      <div className="flex justify-between text-[8px] text-neutral-400">{["M","T","W","T","F","S","S"].map((d, i) => <span key={i}>{d}</span>)}</div>
    </div>
  );
}

function RepurposeMini() {
  return (
    <div className="p-3 rounded-xl space-y-1.5" style={{ background: "rgba(0,0,0,0.02)", border: "1px solid #EAEAEC" }}>
      <div className="flex items-center gap-2 p-1.5 rounded-lg" style={{ background: "rgba(163,138,112,0.1)", border: "1px solid rgba(163,138,112,0.15)" }}>
        <div className="w-5 h-5 rounded-md flex items-center justify-center text-[8px] font-bold" style={{ background: "rgba(163,138,112,0.25)", color: "#8B6F52" }}>TW</div>
        <div className="text-[9px] text-neutral-500 flex-1 truncate">Thread: AI Productivity Tips</div>
        <span className="text-[7px] font-medium text-neutral-500">→ 4 formats</span>
      </div>
      {["LinkedIn Post", "Instagram Caption", "Newsletter Snippet"].map((fmt) => (
        <div key={fmt} className="flex items-center gap-2 pl-2">
          <div className="w-1 h-1 rounded-full" style={{ background: "#D4D4D4" }} />
          <span className="text-[8.5px] text-neutral-400">{fmt}</span>
        </div>
      ))}
    </div>
  );
}

function PublisherMini() {
  return (
    <div className="p-3 rounded-xl space-y-1.5" style={{ background: "rgba(0,0,0,0.02)", border: "1px solid #EAEAEC" }}>
      {[{ name: "LinkedIn", color: "#0a66c2", status: "Scheduled" }, { name: "X / Twitter", color: "#0F172A", status: "Scheduled" }, { name: "Instagram", color: "#e1306c", status: "Draft" }, { name: "TikTok", color: "#010101", status: "Queued" }].map((p) => (
        <div key={p.name} className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-md" style={{ background: p.color, border: "1px solid #EAEAEC" }} />
            <span className="text-[9px] text-neutral-500">{p.name}</span>
          </div>
          <span className="text-[8px] font-medium px-1.5 py-0.5 rounded-full"
            style={p.status === "Scheduled" ? { background: "rgba(163,138,112,0.1)", color: "#8B6F52", border: "1px solid rgba(163,138,112,0.15)" }
              : p.status === "Draft" ? { background: "rgba(0,0,0,0.03)", color: "#A3A3A3", border: "1px solid #EAEAEC" }
              : { background: "rgba(163,138,112,0.1)", color: "#8B6F52", border: "1px solid rgba(163,138,112,0.15)" }}>
            {p.status}
          </span>
        </div>
      ))}
    </div>
  );
}

const FEATURES = [
  { icon: CalendarDays, title: "Smart Content Calendar", description: "Visual drag-and-drop calendar with AI-suggested publish windows based on your audience's peak activity.", Visual: CalendarMini, accent: "#A38A70", wide: true },
  { icon: Sparkles, title: "AI Engagement Coach", description: "Real-time coaching on hook strength, topic angle, and timing — personalized to your specific audience.", Visual: CoachMini, accent: "#A38A70", wide: false },
  { icon: TrendingUp, title: "Trend Radar", description: "48-hour advance warning on surging topics so you publish at peak momentum, not after it passes.", Visual: TrendsMini, accent: "#A38A70", wide: false },
  { icon: RefreshCw, title: "Content Repurposing Engine", description: "One tweet becomes a LinkedIn post, newsletter section, and Instagram caption in one click.", Visual: RepurposeMini, accent: "#A38A70", wide: false },
  { icon: BarChart3, title: "Analytics Hub", description: "Unified analytics across all platforms. See exactly what drives growth and what to double down on.", Visual: AnalyticsMini, accent: "#A38A70", wide: false },
  { icon: Globe, title: "Multi-Platform Publisher", description: "Schedule and publish to LinkedIn, X, Instagram, and TikTok from one unified queue.", Visual: PublisherMini, accent: "#A38A70", wide: false },
];

function FeatureCard({ feature, index }: { feature: typeof FEATURES[0]; index: number }) {
  const cardRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();
  const { icon: Icon, title, description, Visual, wide } = feature;

  const onMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current || !glowRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    glowRef.current.style.background = `radial-gradient(280px circle at ${x}px ${y}px, rgba(163,138,112,0.06), transparent 65%)`;
    glowRef.current.style.opacity = "1";
  };

  const onMouseLeave = () => {
    if (glowRef.current) glowRef.current.style.opacity = "0";
  };

  return (
    <motion.div ref={cardRef}
      initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, delay: index * 0.07, ease: EASE }}
      onMouseMove={onMouseMove} onMouseLeave={onMouseLeave}
      className={`relative group p-6 rounded-2xl cursor-default transition-all duration-300 ${wide ? "md:col-span-2" : ""}`}
      style={{ border: "1px solid #EAEAEC", background: "white", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
    >
      <div ref={glowRef} className="absolute inset-0 rounded-2xl pointer-events-none transition-opacity duration-200" style={{ opacity: 0 }} />
      <div className="relative z-10">
        <div className="mb-4">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: "rgba(163,138,112,0.1)", border: "1px solid rgba(163,138,112,0.15)" }}>
            <Icon className="w-4 h-4 text-[#8B6F52]" />
          </div>
        </div>
        <h3 className="text-[15px] font-semibold text-neutral-900 mb-2 tracking-tight">{title}</h3>
        <p className="text-[13px] text-neutral-500 leading-[1.7] mb-4">{description}</p>
        <Visual />
      </div>
    </motion.div>
  );
}

export default function Features() {
  const shouldReduceMotion = useReducedMotion();
  return (
    <section id="features" className="py-24 bg-[#F9F8F6] relative">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse at top right, rgba(163,138,112,0.05) 0%, transparent 60%)" }} />
      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">
        <div className="max-w-xl mb-14">
          <motion.div initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.5 }} className="flex items-center gap-2 mb-6">
            <div className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">Features</span>
          </motion.div>
          <motion.h2 initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.55, delay: 0.07 }}
            className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-neutral-900 mb-4">
            Every tool you need.{" "}<span className="gradient-text">Nothing you don&apos;t.</span>
          </motion.h2>
          <motion.p initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.5, delay: 0.14 }}
            className="text-[15px] text-neutral-500 leading-[1.75]">
            Six features, one platform. Built for creators who want results, not dashboards.
          </motion.p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {FEATURES.map((feature, i) => <FeatureCard key={feature.title} feature={feature} index={i} />)}
        </div>
      </div>
    </section>
  );
}
