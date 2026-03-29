"use client";

import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { CalendarDays, BarChart3, TrendingUp, Sparkles, Check, Bookmark } from "lucide-react";
const EASE = [0.16, 1, 0.3, 1] as const;

const TABS = [
  { id: "calendar", label: "Content Calendar", icon: CalendarDays },
  { id: "coach", label: "AI Coach", icon: Sparkles },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "trends", label: "Trend Radar", icon: TrendingUp },
];

function CalendarTab() {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const [events, setEvents] = useState([
    { day: 0, title: "LinkedIn Post", color: "bg-[#A38A70]/10 border-[#A38A70]/20 text-[#8B6F52]" },
    { day: 1, title: "X Thread", color: "bg-[#A38A70]/10 border-[#A38A70]/20 text-[#8B6F52]" },
    { day: 1, title: "Newsletter", color: "bg-[#A38A70]/10 border-[#A38A70]/20 text-[#8B6F52]" },
    { day: 3, title: "YouTube", color: "bg-[#A38A70]/10 border-[#A38A70]/20 text-[#8B6F52]" },
    { day: 4, title: "TikTok", color: "bg-[#A38A70]/10 border-[#A38A70]/20 text-[#8B6F52]" },
    { day: 5, title: "X Thread", color: "bg-[#A38A70]/10 border-[#A38A70]/20 text-[#8B6F52]" },
  ]);
  const [addingDay, setAddingDay] = useState<number | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const addEvent = (day: number) => {
    if (!newTitle.trim()) { setAddingDay(null); return; }
    setEvents((prev) => [...prev, { day, title: newTitle.trim(), color: "bg-[#A38A70]/10 border-[#A38A70]/20 text-[#8B6F52]" }]);
    setNewTitle(""); setAddingDay(null);
  };
  return (
    <div className="p-5 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div><div className="text-[13px] font-semibold text-neutral-700">March 2026</div><div className="text-[11px] text-neutral-400 mt-0.5">{events.length} posts scheduled</div></div>
        <div className="flex items-center gap-1.5 text-[11px] text-neutral-500"><span className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70 animate-pulse" /> AI suggestions active</div>
      </div>
      <div className="grid grid-cols-7 gap-1.5 mb-1.5">{days.map((d) => <div key={d} className="text-center text-[10px] text-neutral-400 font-medium py-1">{d}</div>)}</div>
      <div className="grid grid-cols-7 gap-1.5 flex-1">
        {Array.from({ length: 7 }).map((_, dayIdx) => {
          const dayEvents = events.filter((e) => e.day === dayIdx);
          const isAdding = addingDay === dayIdx;
          return (
            <div key={dayIdx} className="min-h-[80px] rounded-xl p-1.5 cursor-pointer group transition-colors"
              style={{ background: "rgba(0,0,0,0.02)", border: "1px solid #EAEAEC" }}
              onClick={() => { if (!isAdding) { setAddingDay(dayIdx); setNewTitle(""); } }}>
              <div className="text-[10px] text-neutral-400 mb-1">{dayIdx + 10}</div>
              <div className="space-y-1">
                {dayEvents.map((event, i) => (<motion.div key={i} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className={`border rounded-md px-1.5 py-0.5 text-[8.5px] font-medium truncate ${event.color}`}>{event.title}</motion.div>))}
                {isAdding ? (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} onClick={(e) => e.stopPropagation()}>
                    <input autoFocus value={newTitle} onChange={(e) => setNewTitle(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") addEvent(dayIdx); if (e.key === "Escape") setAddingDay(null); }}
                      placeholder="Post title..." className="w-full text-[8.5px] rounded-md px-1.5 py-0.5 text-neutral-700 placeholder-neutral-400 outline-none"
                      style={{ background: "rgba(163,138,112,0.08)", border: "1px solid rgba(163,138,112,0.25)" }} />
                    <div className="flex gap-0.5 mt-0.5">
                      <button onClick={() => addEvent(dayIdx)} className="flex-1 text-[7px] rounded py-0.5" style={{ background: "rgba(163,138,112,0.2)", color: "#8B6F52" }}>✓</button>
                      <button onClick={() => setAddingDay(null)} className="flex-1 text-[7px] rounded py-0.5" style={{ background: "rgba(0,0,0,0.04)", color: "#A3A3A3" }}>✕</button>
                    </div>
                  </motion.div>
                ) : (<div className="opacity-0 group-hover:opacity-100 transition-opacity text-[8px] text-neutral-400 text-center">+ add</div>)}
              </div>
            </div>
          );
        })}
      </div>
      <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="mt-3 flex items-start gap-2.5 p-3 rounded-xl" style={{ background: "rgba(163,138,112,0.06)", border: "1px solid rgba(163,138,112,0.12)" }}>
        <div className="w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: "rgba(163,138,112,0.15)" }}><svg width="8" height="8" viewBox="0 0 10 10" fill="none"><path d="M5 1L6.2 3.8L9 4.4L7 6.3L7.5 9L5 7.6L2.5 9L3 6.3L1 4.4L3.8 3.8L5 1Z" fill="#A38A70" /></svg></div>
        <p className="text-[11px] text-neutral-500 leading-relaxed"><span className="font-medium text-[#8B6F52]">AI Coach · </span>Thursday 8AM is your peak window. Click any day to add a post — 2.8× expected reach.</p>
      </motion.div>
    </div>
  );
}

const PLATFORMS = ["LinkedIn", "X / Twitter", "Instagram", "TikTok"];
const AI_RESPONSES: Record<string, { text: string; scores: { label: string; score: number }[] }> = {
  "LinkedIn": { text: "Strong professional angle. Lead with the insight, not the story. Posts under 200 words see 40% more engagement on LinkedIn. Add a single CTA question at the end to drive comments.", scores: [{ label: "Hook Strength", score: 82 }, { label: "Timing Score", score: 91 }, { label: "Virality Index", score: 74 }] },
  "X / Twitter": { text: "Great hook potential. Break this into a 5-tweet thread — first tweet should be your boldest claim. Use numbered list format for max saves and retweets.", scores: [{ label: "Hook Strength", score: 94 }, { label: "Thread Potential", score: 88 }, { label: "Virality Index", score: 86 }] },
  "Instagram": { text: "Caption feels too long for Instagram. Cut to 80 words max. Use 3–5 highly relevant hashtags. The hook (first line) is what drives tap-to-read — make it a bold statement.", scores: [{ label: "Visual Fit", score: 68 }, { label: "Caption Score", score: 55 }, { label: "Hashtag Power", score: 79 }] },
  "TikTok": { text: "Start the video with the payoff, not the setup. 'Here's what I learned after X...' style hooks see 3× completion rate. Add text overlay for the first 3 seconds.", scores: [{ label: "Hook Strength", score: 77 }, { label: "Completion Rate", score: 83 }, { label: "Share Potential", score: 91 }] },
};

function getGrade(avg: number) {
  if (avg >= 90) return { grade: "A+", color: "#A38A70" };
  if (avg >= 80) return { grade: "A", color: "#A38A70" };
  if (avg >= 70) return { grade: "B+", color: "#7A8B76" };
  return { grade: "B", color: "#737373" };
}

function CoachTab() {
  const [platform, setPlatform] = useState("LinkedIn");
  const [content, setContent] = useState("");
  const [response, setResponse] = useState<typeof AI_RESPONSES["LinkedIn"] | null>(null);
  const [loading, setLoading] = useState(false);
  const [typed, setTyped] = useState("");
  const analyze = () => {
    if (!content.trim()) return;
    setLoading(true); setResponse(null); setTyped("");
    setTimeout(() => {
      setLoading(false);
      const full = AI_RESPONSES[platform] ?? AI_RESPONSES["LinkedIn"];
      setResponse(full);
      let i = 0;
      const iv = setInterval(() => { i++; setTyped(full.text.slice(0, i)); if (i >= full.text.length) clearInterval(iv); }, 16);
    }, 1000);
  };
  return (
    <div className="p-5 h-full flex flex-col gap-3">
      <div className="flex gap-1.5 flex-wrap">
        {PLATFORMS.map((p) => (<button key={p} onClick={() => { setPlatform(p); setResponse(null); setTyped(""); }} className="px-3 py-1.5 rounded-lg text-[11.5px] font-medium transition-all duration-200"
          style={platform === p ? { background: "rgba(15,23,42,0.08)", border: "1px solid rgba(15,23,42,0.15)", color: "#171717" } : { background: "#F5F5F4", border: "1px solid #EAEAEC", color: "#525252" }}>{p}</button>))}
      </div>
      <div className="flex-1 flex flex-col gap-3">
        <div className="relative">
          <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder={`Paste your ${platform} content here for AI analysis...`}
            className="w-full h-24 rounded-xl p-3 text-[12px] text-neutral-700 placeholder-neutral-400 resize-none outline-none font-mono leading-relaxed transition-all duration-200"
            style={{ background: "#F9F8F6", border: "1px solid #EAEAEC" }}
            onFocus={(e) => { e.currentTarget.style.border = "1px solid rgba(163,138,112,0.5)"; }}
            onBlur={(e) => { e.currentTarget.style.border = "1px solid #EAEAEC"; }} />
          <div className="absolute bottom-2 right-2 text-[9px] text-neutral-400">{content.length} chars</div>
        </div>
        <button onClick={analyze} disabled={!content.trim() || loading} className="w-full py-2.5 rounded-xl text-[12.5px] font-semibold transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ background: !content.trim() || loading ? "rgba(15,23,42,0.06)" : "#0F172A", color: !content.trim() || loading ? "#A3A3A3" : "white" }}>
          {loading ? "Analyzing..." : `Analyze for ${platform}`}
        </button>
        <AnimatePresence>
          {(loading || response) && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} className="rounded-xl overflow-hidden" style={{ border: "1px solid rgba(163,138,112,0.15)" }}>
              <div className="flex items-center gap-2 px-3.5 pt-3.5 pb-2.5" style={{ background: "rgba(163,138,112,0.06)" }}>
                <div className="w-4 h-4 rounded-md flex items-center justify-center" style={{ background: "rgba(163,138,112,0.2)" }}><svg width="8" height="8" viewBox="0 0 10 10" fill="none"><path d="M5 1L6.2 3.8L9 4.4L7 6.3L7.5 9L5 7.6L2.5 9L3 6.3L1 4.4L3.8 3.8L5 1Z" fill="#A38A70" /></svg></div>
                <span className="text-[11px] font-semibold text-[#8B6F52]">AI Coach</span>
                {loading && <span className="text-[10px] text-neutral-400 animate-pulse ml-1">analyzing...</span>}
                {response && (() => { const avg = Math.round(response.scores.reduce((s, sc) => s + sc.score, 0) / response.scores.length); const { grade, color } = getGrade(avg); return <div className="ml-auto flex items-center gap-1.5"><span className="text-[10px] text-neutral-400">Overall</span><span className="text-[16px] font-bold" style={{ color }}>{grade}</span></div>; })()}
              </div>
              <div className="px-3.5 py-3 space-y-2" style={{ background: "rgba(163,138,112,0.02)" }}>
                {loading ? [80,60,72].map((w, i) => <div key={i} className="h-2 rounded-full animate-pulse" style={{ width: `${w}%`, background: "#EAEAEC" }} />) :
                  response?.scores.map((sc) => (
                    <div key={sc.label}>
                      <div className="flex justify-between text-[10px] mb-0.5"><span className="text-neutral-700">{sc.label}</span><span className="font-semibold text-neutral-900">{sc.score}/100</span></div>
                      <div className="h-1 rounded-full overflow-hidden" style={{ background: "#F5F5F4" }}>
                        <motion.div className="h-full rounded-full" style={{ background: "linear-gradient(90deg, #A38A70, #7A8B76)" }} initial={{ width: 0 }} animate={{ width: `${sc.score}%` }} transition={{ duration: 0.7, ease: EASE }} />
                      </div>
                    </div>
                  ))}
              </div>
              {!loading && response && (<div className="px-3.5 pb-3.5 pt-2" style={{ background: "rgba(163,138,112,0.02)" }}><p className="text-[12px] text-neutral-500 leading-relaxed">{typed}<span className="cursor-blink">|</span></p></div>)}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function AnalyticsTab() {
  const [hoveredBar, setHoveredBar] = useState<number | null>(null);
  const platforms = [{ name: "LinkedIn", value: 68, engagement: "+42%", color: "#0a66c2" }, { name: "Twitter / X", value: 45, engagement: "+28%", color: "#A38A70" }, { name: "Instagram", value: 82, engagement: "+65%", color: "#e1306c" }, { name: "TikTok", value: 91, engagement: "+120%", color: "#7A8B76" }];
  const weekData = [30, 45, 38, 70, 55, 85, 60];
  const weekLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  return (
    <div className="p-5 h-full flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3">
        {[{ label: "Total Reach", value: "142K", change: "+23%" }, { label: "Avg. Engagement", value: "8.4%", change: "+340%" }].map((stat) => (
          <div key={stat.label} className="rounded-xl p-4" style={{ background: "white", border: "1px solid #EAEAEC" }}>
            <div className="text-[22px] font-bold text-neutral-900 tracking-tight">{stat.value}</div>
            <div className="text-[11px] text-neutral-400 mt-0.5">{stat.label}</div>
            <div className="text-[11px] font-medium mt-1 text-[#7A8B76]">↑ {stat.change}</div>
          </div>
        ))}
      </div>
      <div className="space-y-2.5">
        {platforms.map((p, i) => (
          <motion.div key={p.name} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 + i * 0.08 }}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full" style={{ background: p.color }} /><span className="text-[11px] text-neutral-500">{p.name}</span></div>
              <span className="text-[11px] font-medium text-[#7A8B76]">{p.engagement}</span>
            </div>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "#F5F5F4" }}>
              <motion.div className="h-full rounded-full" style={{ background: "linear-gradient(90deg, #A38A70, #7A8B76)" }} initial={{ width: 0 }} animate={{ width: `${p.value}%` }} transition={{ duration: 0.8, delay: 0.2 + i * 0.1, ease: EASE }} />
            </div>
          </motion.div>
        ))}
      </div>
      <div className="flex-1 rounded-xl p-3" style={{ background: "white", border: "1px solid #EAEAEC" }}>
        <div className="text-[11px] text-neutral-400 mb-2">This week</div>
        <div className="relative flex items-end gap-1.5 h-14">
          {weekData.map((v, i) => (
            <div key={i} className="relative flex-1 cursor-pointer" style={{ height: "100%", display: "flex", alignItems: "flex-end" }} onMouseEnter={() => setHoveredBar(i)} onMouseLeave={() => setHoveredBar(null)}>
              <AnimatePresence>
                {hoveredBar === i && (<motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} className="absolute -top-7 left-1/2 -translate-x-1/2 px-2 py-1 rounded-md text-[9px] text-neutral-700 whitespace-nowrap z-10" style={{ background: "white", border: "1px solid #EAEAEC", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>{weekLabels[i]}: {v}K</motion.div>)}
              </AnimatePresence>
              <motion.div className="w-full rounded-[3px]" style={{ height: `${v}%`, transformOrigin: "bottom", background: hoveredBar === i ? "linear-gradient(to top, rgba(163,138,112,0.8), rgba(163,138,112,0.3))" : i % 3 === 0 ? "rgba(163,138,112,0.6)" : i % 3 === 1 ? "rgba(163,138,112,0.3)" : "#F5F5F4", transition: "background 0.2s" }} initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ duration: 0.45, delay: 0.1 * i, ease: EASE }} />
            </div>
          ))}
        </div>
        <div className="flex gap-1.5 mt-1">{weekLabels.map((d) => <div key={d} className="flex-1 text-center text-[8px] text-neutral-400">{d}</div>)}</div>
      </div>
    </div>
  );
}

function TrendsTab() {
  const [saved, setSaved] = useState<number[]>([]);
  const trends = [
    { topic: "AI Productivity Tools", momentum: "+340%", timing: "Peak in ~48h", hot: true, score: 9.2 },
    { topic: "Creator Economy Burnout", momentum: "+180%", timing: "Peak in ~72h", hot: true, score: 7.8 },
    { topic: "LinkedIn Personal Branding", momentum: "+95%", timing: "Trending now", hot: false, score: 6.4 },
    { topic: "Short-Form Video Strategy", momentum: "+210%", timing: "Peak in ~36h", hot: true, score: 8.9 },
  ];
  return (
    <div className="p-5 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-[13px] font-medium text-neutral-700">Live Trend Feed</span>
        <div className="ml-auto flex items-center gap-1.5 text-[11px] text-neutral-500"><span className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70 animate-pulse" /> Updated 2m ago</div>
      </div>
      <div className="space-y-2.5 flex-1">
        {trends.map((trend, i) => (
          <motion.div key={trend.topic} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.08 }} className="flex items-center justify-between p-3 rounded-xl" style={{ background: "white", border: "1px solid #EAEAEC" }}>
            <div className="flex-1 min-w-0 mr-3">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[12.5px] font-medium text-neutral-700 truncate">{trend.topic}</span>
                {trend.hot && <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full flex-shrink-0" style={{ background: "rgba(163,138,112,0.1)", color: "#8B6F52", border: "1px solid rgba(163,138,112,0.2)" }}>🔥 HOT</span>}
              </div>
              <div className="text-[10px] text-neutral-400">{trend.timing} · Score {trend.score}/10</div>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="text-[12px] font-semibold" style={{ color: "#A38A70" }}>{trend.momentum}</div>
              <button onClick={() => setSaved((prev) => prev.includes(i) ? prev.filter((x) => x !== i) : [...prev, i])} className="w-7 h-7 rounded-lg border flex items-center justify-center transition-all duration-200"
                style={saved.includes(i) ? { background: "rgba(163,138,112,0.15)", border: "1px solid rgba(163,138,112,0.3)", color: "#8B6F52" } : { border: "1px solid #EAEAEC", color: "#A3A3A3" }}>
                {saved.includes(i) ? <Check className="w-3 h-3" /> : <Bookmark className="w-3 h-3" />}
              </button>
            </div>
          </motion.div>
        ))}
      </div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} className="mt-3 flex items-start gap-2.5 p-3 rounded-xl" style={{ background: "rgba(163,138,112,0.06)", border: "1px solid rgba(163,138,112,0.12)" }}>
        <div className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: "#A38A70" }} />
        <span className="text-[11px] text-neutral-500 leading-relaxed"><span className="font-medium text-[#8B6F52]">AI Coach · </span>Write about AI Productivity Tools now — 48hr head start over competitors. Save trends to add to your calendar.</span>
      </motion.div>
    </div>
  );
}

const TAB_CONTENT = { calendar: CalendarTab, coach: CoachTab, analytics: AnalyticsTab, trends: TrendsTab };

export default function ProductShowcase() {
  const [activeTab, setActiveTab] = useState("calendar");
  const shouldReduceMotion = useReducedMotion();
  return (
    <section id="showcase" className="py-24 relative overflow-hidden bg-[#F9F8F6]">
      <div className="absolute top-0 left-1/4 w-[600px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(ellipse, rgba(163,138,112,0.05) 0%, transparent 60%)" }} />
      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">
        <div className="max-w-xl mb-12">
          <motion.div initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }} className="flex items-center gap-2 mb-6">
            <div className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70" /><span className="eyebrow">Product</span>
          </motion.div>
          <motion.h2 initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.55, delay: 0.07 }} className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-neutral-900 mb-4">
            See Ittera <span className="gradient-text">in action</span>
          </motion.h2>
          <motion.p initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5, delay: 0.14 }} className="text-[15px] text-neutral-500 leading-[1.75]">
            Try the real interface — paste content for AI scoring, click days to add posts, hover bars for data, save trends.
          </motion.p>
        </div>
        <motion.div initial={shouldReduceMotion ? false : { opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-60px" }} transition={{ duration: 0.7, ease: EASE }}
          className="rounded-2xl overflow-hidden" style={{ border: "1px solid #EAEAEC", background: "white", boxShadow: "0 20px 60px rgba(0,0,0,0.06)" }}>
          <div className="flex items-center gap-2 px-4 py-3" style={{ borderBottom: "1px solid #EAEAEC", background: "#F5F5F4" }}>
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: "rgba(255,95,87,0.7)" }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: "rgba(254,188,46,0.7)" }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: "rgba(40,200,64,0.7)" }} />
            </div>
            <div className="flex-1 mx-4 h-5 rounded-md flex items-center justify-center" style={{ background: "rgba(0,0,0,0.04)" }}><span className="text-[10px] text-neutral-400 tracking-wide">app.iterra.ai</span></div>
            <div className="flex items-center gap-1.5 text-[10px] text-neutral-500"><span className="w-1.5 h-1.5 rounded-full animate-pulse bg-[#A38A70]/70" /> Interactive demo</div>
          </div>
          <div className="flex overflow-x-auto" style={{ borderBottom: "1px solid #EAEAEC", background: "#F5F5F4" }}>
            {TABS.map((tab) => {
              const Icon = tab.icon; const isActive = activeTab === tab.id;
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} className="relative flex items-center gap-2 px-5 py-3.5 text-[12.5px] font-medium transition-colors whitespace-nowrap" style={{ color: isActive ? "#171717" : "rgba(163,163,163,1)" }}>
                  {isActive && <motion.div layoutId="tab-indicator" className="absolute inset-x-0 bottom-0 h-px" style={{ background: "#0F172A" }} transition={{ type: "spring", bounce: 0.2, duration: 0.4 }} />}
                  <Icon className="w-3.5 h-3.5 flex-shrink-0" /><span className="hidden sm:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>
          <div className="min-h-[480px] sm:min-h-[520px] bg-white">
            <AnimatePresence mode="wait">
              <motion.div key={activeTab} initial={shouldReduceMotion ? false : { opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={shouldReduceMotion ? undefined : { opacity: 0, y: -6 }} transition={{ duration: 0.22, ease: "easeInOut" }} className="h-full">
                {(() => { const Content = TAB_CONTENT[activeTab as keyof typeof TAB_CONTENT]; return <Content />; })()}
              </motion.div>
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
