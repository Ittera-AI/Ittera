"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion, AnimatePresence, useMotionValue, useSpring } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const WORDS = ["content strategy", "every post", "your audience", "your growth"];
const EASE  = [0.16, 1, 0.3, 1] as const;

/* ─── Typewriter ──────────────────────────────────────────────────────────── */
function useTypewriter(words: string[], speed = 80, pause = 1800) {
  const [display, setDisplay]   = useState(words[0]);
  const [wordIdx, setWordIdx]   = useState(0);
  const [charIdx, setCharIdx]   = useState(words[0].length);
  const [deleting, setDeleting] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const current = words[wordIdx];
    if (!deleting && charIdx < current.length)     timer.current = setTimeout(() => setCharIdx(c => c + 1), speed);
    else if (!deleting && charIdx === current.length) timer.current = setTimeout(() => setDeleting(true), pause);
    else if (deleting && charIdx > 0)              timer.current = setTimeout(() => setCharIdx(c => c - 1), speed / 2);
    else if (deleting && charIdx === 0)            { setDeleting(false); setWordIdx(i => (i + 1) % words.length); }
    setDisplay(current.slice(0, charIdx));
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [charIdx, deleting, wordIdx, words, speed, pause]);

  return display;
}

/* ─── Static data ─────────────────────────────────────────────────────────── */
const ACCOUNTS = [
  { abbr: "in", color: "#0A66C2", name: "LinkedIn",  connected: true  },
  { abbr: "𝕏",  color: "#171717", name: "Twitter/X", connected: true  },
  { abbr: "IG", color: "#E1306C", name: "Instagram", connected: true  },
  { abbr: "▶",  color: "#FF0000", name: "YouTube",   connected: false },
  { abbr: "TK", color: "#69C9D0", name: "TikTok",    connected: false },
];

const CAL_POSTS: Record<number, { color: string }[]> = {
  1: [{ color: "#0A66C2" }],
  3: [{ color: "#7A8B76" }, { color: "#0A66C2" }],
  5: [{ color: "#0A66C2" }],
  7: [{ color: "#E1306C" }],
  8: [{ color: "#0A66C2" }],
  10:[{ color: "#0A66C2" }, { color: "#7A8B76" }],
  12:[{ color: "#E1306C" }],
  15:[{ color: "#7A8B76" }],
  17:[{ color: "#0A66C2" }],
  19:[{ color: "#E1306C" }, { color: "#0A66C2" }],
  22:[{ color: "#0A66C2" }],
  24:[{ color: "#7A8B76" }],
  26:[{ color: "#0A66C2" }],
  28:[{ color: "#E1306C" }],
};
const TODAY = 10;

const UPCOMING = [
  { platform: "LinkedIn",  color: "#0A66C2", abbr: "in", time: "Today 2:00 PM",  topic: "AI tools changing content strategy" },
  { platform: "Twitter/X", color: "#171717", abbr: "𝕏",  time: "Today 5:30 PM",  topic: "Thread: Creator economy in 2025"    },
  { platform: "Instagram", color: "#E1306C", abbr: "IG", time: "Wed 11:00 AM",   topic: "Behind the scenes: content process"  },
];

const ENGINE_DRAFTS = [
  {
    platform: "LinkedIn", abbr: "in", color: "#0A66C2", tag: "Professional",
    lines: [
      "5 ways AI is transforming content",
      "strategy in 2025 👇",
      "",
      "Most creators spend 70% of their",
      "time on distribution, not creation.",
      "Here's how top creators flip it...",
    ],
    stat: "Est. 3.2K reach · Best: Tue 9 AM",
  },
  {
    platform: "Twitter / X", abbr: "𝕏", color: "#171717", tag: "Thread",
    lines: [
      "Thread: AI changed how I create",
      "content forever 🧵",
      "",
      "1/ I used to spend 6 hrs on one",
      "piece. Now 45 min. Here's the",
      "exact system I use...",
    ],
    stat: "Est. 1.1K impressions · 14 replies",
  },
  {
    platform: "Instagram", abbr: "IG", color: "#E1306C", tag: "Caption",
    lines: [
      "POV: your content strategy just",
      "leveled up ✨",
      "",
      "The creators winning right now",
      "aren't working harder — they're",
      "working smarter. #ContentAI",
    ],
    stat: "Est. 890 reach · 4.8% eng rate",
  },
];

const TRENDS = [
  { tag: "#AITools",        pct: 88, delta: "+340%", source: "Reddit",  hot: true  },
  { tag: "#CreatorEconomy", pct: 72, delta: "+218%", source: "YouTube", hot: false },
  { tag: "#Automation",     pct: 58, delta: "+156%", source: "Google",  hot: false },
  { tag: "#ContentAI",      pct: 43, delta: "+98%",  source: "Reddit",  hot: false },
  { tag: "#PersonalBrand",  pct: 36, delta: "+74%",  source: "Google",  hot: false },
];

const SOURCES = ["All", "Reddit", "YouTube", "Google"];

/* ─── Sidebar nav SVG icons ──────────────────────────────────────────────── */
const NAV = [
  { label: "Dashboard", tab: -1,
    icon: <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><rect x="1" y="1" width="5.5" height="5.5" rx="1.2" fill="currentColor" opacity="0.8"/><rect x="8.5" y="1" width="5.5" height="5.5" rx="1.2" fill="currentColor" opacity="0.8"/><rect x="1" y="8.5" width="5.5" height="5.5" rx="1.2" fill="currentColor" opacity="0.8"/><rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1.2" fill="currentColor" opacity="0.25"/></svg> },
  { label: "Calendar",  tab: 0,
    icon: <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><rect x="1.5" y="3" width="12" height="10.5" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/><path d="M1.5 6.5h12" stroke="currentColor" strokeWidth="1.3"/><path d="M4.5 1.5v2M10.5 1.5v2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg> },
  { label: "Engine",    tab: 1,
    icon: <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M9 1.5L3.5 8.5h4.5L6.5 13.5 13 6.5H8.5L10 1.5z" fill="currentColor" opacity="0.85"/></svg> },
  { label: "Radar",     tab: 2,
    icon: <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><circle cx="7.5" cy="7.5" r="5.5" stroke="currentColor" strokeWidth="1.3" fill="none"/><circle cx="7.5" cy="7.5" r="2.5" stroke="currentColor" strokeWidth="1.3" fill="none"/><circle cx="7.5" cy="7.5" r="1" fill="currentColor"/><path d="M7.5 7.5L12 3.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" opacity="0.6"/></svg> },
  { label: "Settings",  tab: -1,
    icon: <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><circle cx="7.5" cy="7.5" r="2" stroke="currentColor" strokeWidth="1.3" fill="none"/><path d="M7.5 1.5v1.5M7.5 12v1.5M1.5 7.5H3M12 7.5h1.5M3 3l1 1M11 11l1 1M12 3l-1 1M4 11l-1 1" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg> },
];

/* ─── Dashboard Mockup ────────────────────────────────────────────────────── */
function DashboardMockup({ isDark }: { isDark: boolean }) {
  const shouldReduceMotion = useReducedMotion();
  const [activeTab,    setActiveTab]    = useState(1);   // 0=Cal 1=Engine 2=Radar
  const [hoveredDay,   setHoveredDay]   = useState<number | null>(null);
  const [generating,   setGenerating]   = useState(false);
  const [activeSource, setActiveSource] = useState(0);
  const [genDone,      setGenDone]      = useState(true);

  // spring-tracked mouse position for inner glow
  const mouseX = useMotionValue(0.5);
  const mouseY = useMotionValue(0.5);
  const glowX  = useSpring(mouseX, { stiffness: 80, damping: 20 });
  const glowY  = useSpring(mouseY, { stiffness: 80, damping: 20 });

  const win      = isDark ? "#141210"                  : "white";
  const winBrd   = isDark ? "#2E2922"                  : "#EAEAEC";
  const hdrBg    = isDark ? "#1C1916"                  : "#F5F5F4";
  const sideBg   = isDark ? "#181512"                  : "#F7F6F4";
  const cardBg   = isDark ? "#1C1916"                  : "#F9F8F6";
  const cardBrd  = isDark ? "#2E2922"                  : "#EAEAEC";
  const txtPri   = isDark ? "#F2EDE8"                  : "#171717";
  const txtSoft  = isDark ? "rgba(242,237,232,0.65)"   : "#525252";
  const txtMuted = isDark ? "rgba(242,237,232,0.35)"   : "#9CA3AF";
  const brand    = isDark ? "#C4A882"                  : "#A38A70";
  const brandDim = isDark ? "rgba(196,168,130,0.12)"   : "rgba(163,138,112,0.09)";
  const brandBrd = isDark ? "rgba(196,168,130,0.28)"   : "rgba(163,138,112,0.22)";
  const green    = "#7A8B76";
  const trackBg  = isDark ? "rgba(255,255,255,0.06)"   : "rgba(0,0,0,0.06)";
  const navAct   = isDark ? "rgba(196,168,130,0.14)"   : "rgba(163,138,112,0.1)";

  const filteredTrends = activeSource === 0
    ? TRENDS
    : TRENDS.filter(t => t.source === SOURCES[activeSource]);

  function handleRepurpose() {
    setGenDone(false);
    setGenerating(true);
    setTimeout(() => { setGenerating(false); setGenDone(true); }, 1600);
  }

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { opacity: 0, y: 52, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 1.1, delay: 0.45, ease: EASE }}
      className="relative w-full"
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        mouseX.set((e.clientX - rect.left) / rect.width);
        mouseY.set((e.clientY - rect.top)  / rect.height);
      }}
    >
      {/* Ambient glow that tracks mouse */}
      <motion.div
        className="absolute -inset-8 rounded-3xl pointer-events-none"
        style={{
          background: isDark
            ? "radial-gradient(ellipse at 50% 55%, rgba(196,168,130,0.09) 0%, transparent 60%)"
            : "radial-gradient(ellipse at 50% 55%, rgba(163,138,112,0.07) 0%, transparent 60%)",
        }}
      />

      <motion.div
        className="relative rounded-2xl overflow-hidden select-none"
        style={{
          border: `1px solid ${winBrd}`,
          background: win,
          boxShadow: isDark
            ? "0 32px 72px rgba(0,0,0,0.5), 0 4px 20px rgba(0,0,0,0.35)"
            : "0 32px 72px rgba(0,0,0,0.1), 0 4px 20px rgba(0,0,0,0.06)",
        }}
        whileHover={{ scale: 1.005 }}
        transition={{ duration: 0.3 }}
      >
        {/* Inner glow follows cursor */}
        <motion.div
          className="absolute inset-0 pointer-events-none rounded-2xl"
          style={{
            background: isDark
              ? `radial-gradient(300px circle at ${glowX.get() * 100}% ${glowY.get() * 100}%, rgba(196,168,130,0.07), transparent 60%)`
              : `radial-gradient(300px circle at ${glowX.get() * 100}% ${glowY.get() * 100}%, rgba(163,138,112,0.06), transparent 60%)`,
            zIndex: 0,
          }}
        />

        {/* ── Title bar ── */}
        <div
          className="relative z-10 flex items-center gap-3 px-4 py-3"
          style={{ background: hdrBg, borderBottom: `1px solid ${winBrd}` }}
        >
          <div className="flex gap-1.5 flex-shrink-0">
            {["#ff5f57","#febc2e","#28c840"].map((c, i) => (
              <motion.div key={i} className="w-2.5 h-2.5 rounded-full"
                style={{ background: c + "CC" }}
                whileHover={{ scale: 1.3, background: c }}
                transition={{ duration: 0.15 }}
              />
            ))}
          </div>
          <div
            className="flex-1 h-5 rounded-md flex items-center px-2.5 gap-1.5 min-w-0"
            style={{ background: isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)" }}
          >
            <motion.span className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0"
              animate={{ opacity: [1, 0.35, 1] }} transition={{ duration: 2.4, repeat: Infinity }} />
            <span className="text-[10px] truncate" style={{ color: txtMuted }}>app.iterra.ai/dashboard</span>
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <motion.span className="w-1.5 h-1.5 rounded-full bg-emerald-400"
              animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 2, repeat: Infinity }} />
            <span className="text-[10px] font-medium" style={{ color: txtMuted }}>syncing</span>
          </div>
        </div>

        {/* ── App body: sidebar + main ── */}
        <div className="relative z-10 flex" style={{ height: "420px" }}>

          {/* ── Sidebar ── */}
          <div
            className="w-[54px] flex flex-col flex-shrink-0"
            style={{ background: sideBg, borderRight: `1px solid ${winBrd}` }}
          >
            {/* Logo */}
            <div className="flex items-center justify-center py-3" style={{ borderBottom: `1px solid ${winBrd}` }}>
              <motion.div
                className="w-7 h-7 rounded-lg flex items-center justify-center text-[9px] font-black tracking-tight"
                style={{ background: `linear-gradient(135deg, ${brand}, ${green})`, color: isDark ? "#0C0B09" : "white" }}
                whileHover={{ scale: 1.1, rotate: 5 }}
                transition={{ duration: 0.2 }}
              >IT</motion.div>
            </div>

            {/* Nav */}
            <div className="flex-1 py-2 flex flex-col gap-0.5 px-1.5">
              {NAV.map((item, i) => {
                const isActive = item.tab === activeTab;
                return (
                  <motion.button
                    key={i}
                    onClick={() => { if (item.tab >= 0) setActiveTab(item.tab); }}
                    className="w-full h-8 rounded-lg flex items-center justify-center"
                    style={{
                      background: isActive ? navAct : "transparent",
                      color: isActive ? brand : txtMuted,
                    }}
                    whileHover={{ background: isActive ? navAct : isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)", scale: 1.08 }}
                    whileTap={{ scale: 0.93 }}
                    transition={{ duration: 0.14 }}
                    title={item.label}
                  >
                    {item.icon}
                    {isActive && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="absolute left-0 w-0.5 h-5 rounded-r-full"
                        style={{ background: brand }}
                        transition={{ duration: 0.2, ease: EASE }}
                      />
                    )}
                  </motion.button>
                );
              })}
            </div>

            {/* Connected accounts */}
            <div className="pb-3 px-1.5" style={{ borderTop: `1px solid ${winBrd}` }}>
              <div className="text-[6px] font-bold text-center pt-2 pb-2 uppercase tracking-[0.15em]" style={{ color: txtMuted }}>
                linked
              </div>
              <div className="flex flex-col items-center gap-1.5">
                {ACCOUNTS.map((acc, i) => (
                  <motion.div
                    key={i}
                    className="relative w-7 h-7 rounded-full flex items-center justify-center text-[8px] font-bold cursor-pointer"
                    style={{
                      background: acc.connected ? acc.color : isDark ? "#2E2922" : "#E5E7EB",
                      color: acc.connected ? "white" : txtMuted,
                      opacity: acc.connected ? 1 : 0.45,
                    }}
                    whileHover={{ scale: 1.18, opacity: 1 }}
                    transition={{ duration: 0.15 }}
                    title={acc.name}
                  >
                    {acc.abbr}
                    {acc.connected ? (
                      <motion.span
                        className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 flex items-center justify-center"
                        style={{ border: `1.5px solid ${win}` }}
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 2.5, repeat: Infinity, delay: i * 0.4 }}
                      />
                    ) : (
                      <span
                        className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full flex items-center justify-center text-[7px] font-bold"
                        style={{ background: isDark ? "#3D3730" : "#D1D5DB", color: txtMuted, border: `1.5px solid ${win}` }}
                      >+</span>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          </div>

          {/* ── Main area ── */}
          <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

            {/* Tabs + status */}
            <div
              className="flex items-center px-3 pt-2 flex-shrink-0"
              style={{ borderBottom: `1px solid ${winBrd}` }}
            >
              {["Calendar", "Engine", "Radar"].map((tab, i) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(i)}
                  className="relative px-3 py-2 text-[11px] font-medium transition-colors duration-150"
                  style={{ color: activeTab === i ? brand : txtMuted }}
                >
                  {tab}
                  {activeTab === i && (
                    <motion.div
                      layoutId="tab-indicator"
                      className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full"
                      style={{ background: brand }}
                      transition={{ duration: 0.22, ease: EASE }}
                    />
                  )}
                </button>
              ))}
              <div className="ml-auto flex items-center gap-1.5 pb-1.5">
                <motion.div className="w-1.5 h-1.5 rounded-full bg-emerald-400"
                  animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 2, repeat: Infinity }} />
                <span className="text-[9px]" style={{ color: txtMuted }}>3 accounts live</span>
              </div>
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-hidden p-3">
              <AnimatePresence mode="wait" initial={false}>

                {/* ══ CALENDAR ══ */}
                {activeTab === 0 && (
                  <motion.div key="cal"
                    initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }}
                    transition={{ duration: 0.22 }}
                    className="h-full flex gap-3"
                  >
                    {/* Mini calendar */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10.5px] font-semibold" style={{ color: txtPri }}>April 2026</span>
                        <div className="flex gap-2">
                          {[["#0A66C2","LI"],["#7A8B76","TW"],["#E1306C","IG"]].map(([c,l]) => (
                            <span key={l} className="flex items-center gap-0.5 text-[7.5px]" style={{ color: txtMuted }}>
                              <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: c }} />{l}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="grid grid-cols-7 gap-0.5 mb-0.5">
                        {["M","T","W","T","F","S","S"].map((d,i) => (
                          <div key={i} className="text-center text-[7.5px] font-semibold py-0.5" style={{ color: txtMuted }}>{d}</div>
                        ))}
                      </div>
                      {[0,1,2,3].map(week => (
                        <div key={week} className="grid grid-cols-7 gap-0.5 mb-0.5">
                          {[0,1,2,3,4,5,6].map(day => {
                            const num = week * 7 + day + 1;
                            const isToday = num === TODAY;
                            const posts   = CAL_POSTS[num];
                            return (
                              <motion.div key={day}
                                className="flex flex-col items-center py-1 rounded-md cursor-pointer"
                                style={{ background: isToday ? brand : hoveredDay === num ? brandDim : "transparent" }}
                                whileHover={{ scale: 1.12 }}
                                transition={{ duration: 0.12 }}
                                onMouseEnter={() => setHoveredDay(num)}
                                onMouseLeave={() => setHoveredDay(null)}
                              >
                                <span className="text-[9px] font-medium"
                                  style={{ color: isToday ? (isDark ? "#0C0B09" : "white") : txtSoft }}>{num}</span>
                                {posts && (
                                  <div className="flex gap-[2px] mt-0.5">
                                    {posts.slice(0,2).map((p,pi) => (
                                      <div key={pi} className="w-1 h-1 rounded-full" style={{ background: p.color }} />
                                    ))}
                                  </div>
                                )}
                              </motion.div>
                            );
                          })}
                        </div>
                      ))}
                    </div>

                    {/* Upcoming */}
                    <div className="w-[128px] flex-shrink-0 flex flex-col">
                      <div className="text-[10px] font-semibold mb-2" style={{ color: txtPri }}>Upcoming</div>
                      <div className="flex-1 space-y-1.5">
                        {UPCOMING.map((p,i) => (
                          <motion.div key={i}
                            initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.09, ease: EASE }}
                            className="p-2 rounded-lg cursor-pointer"
                            style={{ background: cardBg, border: `1px solid ${cardBrd}` }}
                            whileHover={{ scale: 1.03, borderColor: brandBrd }}
                          >
                            <div className="flex items-center gap-1 mb-0.5">
                              <div className="w-3.5 h-3.5 rounded-full flex items-center justify-center text-[6.5px] font-bold text-white flex-shrink-0"
                                style={{ background: p.color }}>{p.abbr}</div>
                              <span className="text-[7.5px]" style={{ color: txtMuted }}>{p.time}</span>
                            </div>
                            <div className="text-[8.5px] leading-snug" style={{ color: txtSoft,
                              display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                              {p.topic}
                            </div>
                          </motion.div>
                        ))}
                      </div>
                      <motion.button
                        className="mt-2 text-center text-[8.5px] py-1.5 rounded-lg w-full"
                        style={{ background: brandDim, color: brand, border: `1px solid ${brandBrd}` }}
                        whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                      >+ Schedule post</motion.button>
                    </div>
                  </motion.div>
                )}

                {/* ══ ENGINE ══ */}
                {activeTab === 1 && (
                  <motion.div key="engine"
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.22 }}
                    className="h-full flex flex-col gap-2.5"
                  >
                    {/* Input row */}
                    <div className="flex items-center gap-2 px-2.5 py-2 rounded-xl"
                      style={{ background: cardBg, border: `1px solid ${brandBrd}` }}>
                      <span className="text-[9px] font-semibold flex-shrink-0" style={{ color: brand }}>✦</span>
                      <span className="flex-1 text-[10px]" style={{ color: txtSoft }}>
                        AI tools are transforming content creation in 2025
                      </span>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {[["#0A66C2","in"],["#171717","𝕏"],["#E1306C","IG"]].map(([c,a],i) => (
                          <div key={i} className="w-[17px] h-[17px] rounded-full flex items-center justify-center text-[6.5px] font-bold text-white"
                            style={{ background: c }}>{a}</div>
                        ))}
                        <motion.button
                          className="ml-1 px-2.5 py-1 rounded-lg text-[8.5px] font-bold flex items-center gap-1"
                          style={{ background: brand, color: isDark ? "#0C0B09" : "white" }}
                          whileHover={{ scale: 1.06, y: -1 }} whileTap={{ scale: 0.95 }}
                          onClick={handleRepurpose}
                        >
                          {generating ? (
                            <svg className="animate-spin w-2.5 h-2.5" viewBox="0 0 24 24" fill="none">
                              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"/>
                              <path fill="currentColor" className="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                            </svg>
                          ) : "↻"} Repurpose
                        </motion.button>
                      </div>
                    </div>

                    {/* 3 platform draft cards */}
                    <div className="flex-1 grid grid-cols-3 gap-2 min-h-0">
                      {ENGINE_DRAFTS.map((draft, i) => (
                        <motion.div key={i}
                          className="flex flex-col rounded-xl overflow-hidden"
                          style={{ background: cardBg, border: `1px solid ${cardBrd}` }}
                          initial={{ opacity: 0, y: 14 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.1 + i * 0.08, ease: EASE }}
                          whileHover={{ scale: 1.025, borderColor: brandBrd,
                            boxShadow: isDark ? "0 8px 24px rgba(0,0,0,0.35)" : "0 8px 24px rgba(0,0,0,0.08)" }}
                        >
                          {/* Platform header */}
                          <div className="flex items-center gap-1.5 px-2.5 py-2 flex-shrink-0"
                            style={{ borderBottom: `1px solid ${cardBrd}` }}>
                            <div className="w-[15px] h-[15px] rounded flex items-center justify-center text-[6.5px] font-bold text-white flex-shrink-0"
                              style={{ background: draft.color }}>{draft.abbr}</div>
                            <span className="text-[9px] font-semibold flex-1 truncate" style={{ color: txtPri }}>{draft.platform}</span>
                            <span className="text-[7px] px-1 py-0.5 rounded font-medium flex-shrink-0"
                              style={{ background: brandDim, color: brand }}>{draft.tag}</span>
                          </div>

                          {/* Content */}
                          <div className="flex-1 p-2 min-h-0 overflow-hidden">
                            <AnimatePresence mode="wait">
                              {generating || !genDone ? (
                                <motion.div key="skeleton"
                                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                  className="space-y-1.5 pt-0.5"
                                >
                                  {[92, 78, 85, 60, 70, 50].map((w, li) => (
                                    <motion.div key={li}
                                      className="h-1.5 rounded-full"
                                      style={{ width: `${w}%`, background: trackBg }}
                                      animate={{ opacity: [0.3, 0.75, 0.3] }}
                                      transition={{ duration: 0.9, delay: li * 0.08, repeat: Infinity }}
                                    />
                                  ))}
                                </motion.div>
                              ) : (
                                <motion.div key="content"
                                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                  transition={{ duration: 0.35 }}
                                >
                                  {draft.lines.map((line, li) => (
                                    <motion.p key={li}
                                      initial={{ opacity: 0, x: -4 }}
                                      animate={{ opacity: 1, x: 0 }}
                                      transition={{ delay: li * 0.04 }}
                                      className="text-[8.5px] leading-[1.55]"
                                      style={{ color: line === "" ? undefined : txtSoft, minHeight: line === "" ? "6px" : undefined }}
                                    >{line}</motion.p>
                                  ))}
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>

                          {/* Stats footer */}
                          <div className="px-2.5 py-1.5 flex-shrink-0"
                            style={{ borderTop: `1px solid ${cardBrd}` }}>
                            <span className="text-[7.5px] font-medium" style={{ color: txtMuted }}>{draft.stat}</span>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* ══ RADAR ══ */}
                {activeTab === 2 && (
                  <motion.div key="radar"
                    initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }}
                    transition={{ duration: 0.22 }}
                    className="h-full flex flex-col gap-2.5"
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-[10.5px] font-semibold" style={{ color: txtPri }}>Trend Radar</span>
                        <div className="flex items-center gap-1 mt-0.5">
                          <motion.span className="w-1.5 h-1.5 rounded-full bg-emerald-400"
                            animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 1.6, repeat: Infinity }} />
                          <span className="text-[8.5px]" style={{ color: txtMuted }}>Reddit · YouTube · Google Trends</span>
                        </div>
                      </div>
                      {/* Source filter */}
                      <div className="flex items-center gap-1">
                        {SOURCES.map((s,i) => (
                          <motion.button key={s}
                            onClick={() => setActiveSource(i)}
                            className="px-1.5 py-0.5 rounded-full text-[7.5px] font-semibold"
                            style={{
                              background: activeSource === i ? brand : "transparent",
                              color: activeSource === i ? (isDark ? "#0C0B09" : "white") : txtMuted,
                              border: `1px solid ${activeSource === i ? brand : cardBrd}`,
                            }}
                            whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.94 }}
                            transition={{ duration: 0.14 }}
                          >{s}</motion.button>
                        ))}
                      </div>
                    </div>

                    {/* Trend list */}
                    <div className="flex-1 flex flex-col gap-1.5 overflow-hidden">
                      <AnimatePresence mode="wait">
                        <motion.div key={activeSource}
                          initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
                          transition={{ duration: 0.18 }}
                          className="flex flex-col gap-1.5"
                        >
                          {filteredTrends.map((t, i) => (
                            <motion.div key={i}
                              className="p-2.5 rounded-xl cursor-pointer"
                              style={{ background: cardBg, border: `1px solid ${cardBrd}` }}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: i * 0.06, ease: EASE }}
                              whileHover={{ scale: 1.015, background: brandDim, borderColor: brandBrd }}
                            >
                              <div className="flex items-center justify-between mb-1.5">
                                <div className="flex items-center gap-1.5">
                                  {t.hot && (
                                    <motion.span className="text-[11px]"
                                      animate={{ scale: [1, 1.25, 1] }}
                                      transition={{ duration: 1.5, repeat: Infinity }}>🔥</motion.span>
                                  )}
                                  <span className="text-[10.5px] font-semibold" style={{ color: txtPri }}>{t.tag}</span>
                                  <span className="text-[7px] px-1 py-0.5 rounded font-medium"
                                    style={{ background: trackBg, color: txtMuted }}>{t.source}</span>
                                </div>
                                <span className="text-[8.5px] font-bold px-1.5 py-0.5 rounded-full"
                                  style={{ background: brandDim, color: brand }}>{t.delta}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: trackBg }}>
                                  <motion.div className="h-full rounded-full"
                                    style={{ background: `linear-gradient(90deg, ${brand}, ${green})` }}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${t.pct}%` }}
                                    transition={{ duration: 0.95, delay: 0.2 + i * 0.1, ease: EASE }}
                                  />
                                </div>
                                <span className="text-[8px] font-bold flex-shrink-0" style={{ color: brand }}>{t.pct}</span>
                              </div>
                            </motion.div>
                          ))}
                        </motion.div>
                      </AnimatePresence>
                    </div>

                    {/* Insight */}
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
                      className="flex items-center gap-2 p-2 rounded-xl flex-shrink-0"
                      style={{ background: brandDim, border: `1px solid ${brandBrd}` }}>
                      <span style={{ color: brand }} className="text-[10px]">✦</span>
                      <span className="text-[9px]" style={{ color: txtSoft }}>
                        <span style={{ color: brand }} className="font-semibold">#AITools</span> peaking —{" "}
                        create now for <span style={{ color: txtPri }} className="font-semibold">3.2× avg reach</span>
                      </span>
                    </motion.div>
                  </motion.div>
                )}

              </AnimatePresence>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ─── Hero ────────────────────────────────────────────────────────────────── */
export default function Hero() {
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const typed  = useTypewriter(WORDS);

  const heroText     = isDark ? "#F2EDE8"                   : "#171717";
  const descColor    = isDark ? "rgba(242,237,232,0.5)"     : "#737373";
  const secBtnColor  = isDark ? "rgba(242,237,232,0.6)"     : "#525252";
  const secBtnBorder = isDark ? "#2E2922"                   : "#EAEAEC";
  const secBtnHover  = isDark ? "#2E2922"                   : "#D4D4D4";
  const secBtnHoverBg= isDark ? "#1C1916"                   : "#F5F5F4";
  const avatarBorder = isDark ? "#141210"                   : "#F9F8F6";
  const socialCount  = isDark ? "#F2EDE8"                   : "#525252";
  const socialMuted  = isDark ? "rgba(242,237,232,0.4)"     : "#a3a3a3";
  const ctaBg        = isDark ? "linear-gradient(135deg, #C4A882 0%, #A38A70 100%)" : "#0F172A";
  const ctaColor     = isDark ? "#0C0B09"                   : "white";

  return (
    <section
      className="relative min-h-screen flex items-center pt-20 pb-16 overflow-hidden"
      style={{ background: isDark ? "#0C0B09" : "#F9F8F6" }}
    >
      <motion.div
        className="absolute top-[-10%] left-[-5%] w-[700px] h-[700px] rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(163,138,112,0.07) 0%, transparent 65%)", filter: "blur(60px)" }}
        animate={{ x: [0, 20, -10, 0], y: [0, -20, 12, 0] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-[-5%] right-[-5%] w-[500px] h-[500px] rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(122,139,118,0.05) 0%, transparent 65%)", filter: "blur(60px)" }}
        animate={{ x: [0, -15, 8, 0], y: [0, 15, -10, 0] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10 w-full">
        <div className="grid lg:grid-cols-[1fr_1.25fr] gap-10 items-center">

          {/* ── Left: copy ── */}
          <div>
            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: EASE }}
              className="flex items-center gap-2.5 mb-7"
            >
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full"
                style={{ background: "rgba(163,138,112,0.08)", border: "1px solid rgba(163,138,112,0.2)" }}>
                <span className="w-1.5 h-1.5 rounded-full bg-[#A38A70] live-dot animate-pulse" />
                <span className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: "#8B6F52" }}>
                  Early Access Open
                </span>
              </div>
            </motion.div>

            <motion.h1
              initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.08, ease: EASE }}
              className="text-[32px] sm:text-[46px] lg:text-[62px] font-bold tracking-[-0.035em] leading-[1.05] mb-2"
              style={{ color: heroText }}
            >AI that masters</motion.h1>

            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.14, ease: EASE }}
              className="text-[32px] sm:text-[46px] lg:text-[62px] font-bold tracking-[-0.035em] leading-[1.05] mb-7"
              style={{ minHeight: "1.1em", color: isDark ? "#C4A882" : "#8B6F52" }}
            >
              {typed}
              <span className="cursor-blink" style={{ color: isDark ? "#C4A882" : "#A38A70" }}>|</span>
            </motion.div>

            <motion.p
              initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.22, ease: EASE }}
              className="text-[15px] sm:text-[17px] leading-[1.78] max-w-full sm:max-w-[460px] mb-9"
              style={{ color: descColor }}
            >
              Iterra is the AI content strategy engine that analyzes your audience, predicts trending topics, and fills your calendar so you can focus on creating.
            </motion.p>

            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.3, ease: EASE }}
              className="flex flex-col sm:flex-row gap-3 mb-10"
            >
              <motion.a href="#waitlist"
                className="btn-glow inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-lg text-[14.5px] font-semibold"
                style={{ background: ctaBg, color: ctaColor }}
                whileHover={{ y: -2, scale: 1.02 }} whileTap={{ scale: 0.97 }}
                transition={{ duration: 0.18 }}
              >
                Join the Waitlist
                <motion.span animate={{ x: [0, 3, 0] }} transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}>
                  <ArrowRight className="w-4 h-4" />
                </motion.span>
              </motion.a>
              <a href="#showcase"
                className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-lg text-[14.5px] font-medium transition-all duration-200"
                style={{ color: secBtnColor, border: `1px solid ${secBtnBorder}` }}
                onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.borderColor = secBtnHover; (e.currentTarget as HTMLAnchorElement).style.background = secBtnHoverBg; }}
                onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.borderColor = secBtnBorder; (e.currentTarget as HTMLAnchorElement).style.background = "transparent"; }}
              >See it in action</a>
            </motion.div>

            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.45 }}
              className="flex items-center gap-3"
            >
              <div className="flex -space-x-2">
                {["AM","PK","JL","SR","MO"].map((init,i) => (
                  <motion.div key={i}
                    className="w-7 h-7 rounded-full border-2 flex items-center justify-center text-[9px] font-bold text-white"
                    style={{ borderColor: avatarBorder, background: i%2===0 ? "linear-gradient(135deg,#0F172A,#A38A70)" : "linear-gradient(135deg,#7A8B76,#0F172A)" }}
                    whileHover={{ scale: 1.15, zIndex: 10 }}
                    transition={{ duration: 0.15 }}
                  >{init}</motion.div>
                ))}
              </div>
              <p className="text-[12px]" style={{ color: socialMuted }}>
                <span className="font-medium" style={{ color: socialCount }}>Founding creators</span> joining the waitlist now
              </p>
            </motion.div>
          </div>

          {/* ── Right: dashboard ── */}
          <div className="relative">
            <DashboardMockup isDark={isDark} />
          </div>

        </div>
      </div>
    </section>
  );
}
