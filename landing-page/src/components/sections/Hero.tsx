"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Zap, TrendingUp } from "lucide-react";

const WORDS = ["content strategy", "every post", "your audience", "your growth"];
const EASE = [0.16, 1, 0.3, 1] as const;

function useTypewriter(words: string[], speed = 80, pause = 1800) {
  const [display, setDisplay] = useState("");
  const [wordIdx, setWordIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const current = words[wordIdx];
    if (!deleting && charIdx < current.length) {
      timer.current = setTimeout(() => setCharIdx((c) => c + 1), speed);
    } else if (!deleting && charIdx === current.length) {
      timer.current = setTimeout(() => setDeleting(true), pause);
    } else if (deleting && charIdx > 0) {
      timer.current = setTimeout(() => setCharIdx((c) => c - 1), speed / 2);
    } else if (deleting && charIdx === 0) {
      setDeleting(false);
      setWordIdx((i) => (i + 1) % words.length);
    }
    setDisplay(current.slice(0, charIdx));
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [charIdx, deleting, wordIdx, words, speed, pause]);

  return display;
}

function DashboardMockup() {
  const shouldReduceMotion = useReducedMotion();
  const bars = [38, 62, 44, 78, 55, 91, 70, 58, 83, 67, 74, 88];

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { opacity: 0, y: 48, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative w-full"
    >
      {/* Glow */}
      <div
        className="absolute -inset-8 pointer-events-none rounded-3xl"
        style={{ background: "radial-gradient(ellipse at 50% 60%, rgba(163,138,112,0.08) 0%, rgba(122,139,118,0.04) 50%, transparent 70%)" }}
      />

      {/* Floating badges */}
      <div className="float-badge-1 absolute hidden lg:flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border border-[#EAEAEC] bg-white text-[12px] font-medium -left-8 top-[18%]" style={{ boxShadow: "0 4px 16px rgba(0,0,0,0.06)" }}>
        <span className="w-2 h-2 rounded-full bg-emerald-400/80 animate-pulse" />
        <span className="text-neutral-500">Engagement</span>
        <span className="text-emerald-600 font-semibold">+340%</span>
      </div>

      <div className="float-badge-2 absolute hidden lg:flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border border-[#EAEAEC] bg-white text-[12px] font-medium -right-6 top-[28%]" style={{ boxShadow: "0 4px 16px rgba(0,0,0,0.06)" }}>
        <Zap className="w-3.5 h-3.5 text-[#A38A70]" />
        <span className="text-neutral-500">AI Coach</span>
        <span className="text-[#8B6F52] font-semibold">Live</span>
      </div>

      <div className="float-badge-3 absolute hidden lg:flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border border-[#EAEAEC] bg-white text-[12px] font-medium -left-6 bottom-[16%]" style={{ boxShadow: "0 4px 16px rgba(0,0,0,0.06)" }}>
        <TrendingUp className="w-3.5 h-3.5 text-[#7A8B76]" />
        <span className="text-neutral-500">Trend score</span>
        <span className="text-[#7A8B76] font-semibold">9.2/10</span>
      </div>

      {/* Window */}
      <div className="relative rounded-2xl overflow-hidden border border-[#EAEAEC] bg-white" style={{ boxShadow: "0 20px 60px rgba(0,0,0,0.08)" }}>
        {/* Titlebar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b" style={{ background: "#F5F5F4", borderBottom: "1px solid #EAEAEC" }}>
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]/80" />
          </div>
          <div className="flex-1 mx-6 h-5 rounded-md flex items-center justify-center" style={{ background: "rgba(0,0,0,0.04)" }}>
            <span className="text-[11px] text-neutral-400 tracking-wide">app.ittera.ai</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-emerald-400/70">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400/70 animate-pulse" />
            Live
          </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-12 gap-px bg-[#EAEAEC]">
          {/* Sidebar */}
          <div className="col-span-3 p-3 flex flex-col gap-2" style={{ background: "#F5F5F4" }}>
            {["Dashboard", "Calendar", "Analytics", "Trends", "Library"].map((item, i) => (
              <div
                key={item}
                className={`text-[10px] px-2 py-1.5 rounded-lg ${i === 0 ? "font-medium" : "text-neutral-500"}`}
                style={i === 0 ? { background: "rgba(163,138,112,0.1)", color: "#8B6F52" } : {}}
              >
                {item}
              </div>
            ))}
          </div>

          {/* Main */}
          <div className="col-span-9 p-4 space-y-3" style={{ background: "white" }}>
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: "Total Reach", value: "142K", change: "+23%", color: "text-emerald-600" },
                { label: "Posts Scheduled", value: "28", change: "this month", color: "text-neutral-400" },
                { label: "Avg Score", value: "9.2", change: "↑ from 7.1", color: "text-[#7A8B76]" },
              ].map((s) => (
                <div key={s.label} className="p-2.5 rounded-xl bg-white border border-[#EAEAEC]">
                  <div className="text-[16px] font-bold text-neutral-900 tracking-tight leading-none">{s.value}</div>
                  <div className="text-[9px] text-neutral-400 mt-1">{s.label}</div>
                  <div className={`text-[9px] mt-0.5 font-medium ${s.color}`}>{s.change}</div>
                </div>
              ))}
            </div>

            <div className="p-3 rounded-xl bg-white border border-[#EAEAEC]">
              <div className="text-[10px] text-neutral-400 mb-2">Weekly engagement</div>
              <div className="flex items-end gap-0.5 h-10">
                {bars.map((h, i) => (
                  <motion.div
                    key={i}
                    className="flex-1 rounded-[2px]"
                    style={{
                      height: `${h}%`,
                      transformOrigin: "bottom",
                      background:
                        i % 4 === 0
                          ? "linear-gradient(to top, rgba(163,138,112,0.85), rgba(163,138,112,0.3))"
                          : i % 4 === 1
                          ? "rgba(163,138,112,0.3)"
                          : i % 4 === 2
                          ? "rgba(163,138,112,0.28)"
                          : "rgba(0,0,0,0.06)",
                    }}
                    initial={{ scaleY: 0 }}
                    animate={{ scaleY: 1 }}
                    transition={{ duration: 0.5, delay: 0.7 + i * 0.04, ease: EASE }}
                  />
                ))}
              </div>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.2 }}
              className="flex items-start gap-2 p-2.5 rounded-xl"
              style={{ background: "rgba(163,138,112,0.06)", border: "1px solid rgba(163,138,112,0.15)" }}
            >
              <div className="w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: "rgba(163,138,112,0.2)" }}>
                <svg width="8" height="8" viewBox="0 0 10 10" fill="none">
                  <path d="M5 1L6.2 3.8L9 4.4L7 6.3L7.5 9L5 7.6L2.5 9L3 6.3L1 4.4L3.8 3.8L5 1Z" fill="#A38A70" />
                </svg>
              </div>
              <p className="text-[10px] leading-relaxed" style={{ color: "#8B6F52" }}>
                <span className="font-semibold">AI Coach · </span>
                Thursday 8AM is your peak window — 2.8× expected reach.
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function Hero() {
  const shouldReduceMotion = useReducedMotion();
  const typed = useTypewriter(WORDS);

  return (
    <section className="relative min-h-screen flex items-center pt-20 pb-16 overflow-hidden">
      {/* BG orbs */}
      <div
        className="absolute top-[-10%] left-[-5%] w-[700px] h-[700px] rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(163,138,112,0.06) 0%, transparent 65%)", filter: "blur(60px)" }}
      />
      <div
        className="absolute bottom-[-5%] right-[-5%] w-[500px] h-[500px] rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(122,139,118,0.04) 0%, transparent 65%)", filter: "blur(60px)" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10 w-full">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left */}
          <div>
            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: EASE }}
              className="flex items-center gap-2.5 mb-7"
            >
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={{ background: "rgba(163,138,112,0.08)", border: "1px solid rgba(163,138,112,0.2)" }}>
                <span className="w-1.5 h-1.5 rounded-full bg-[#A38A70] live-dot animate-pulse" />
                <span className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: "#8B6F52" }}>
                  Early Access Open
                </span>
              </div>
            </motion.div>

            <motion.h1
              initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.08, ease: [0.16, 1, 0.3, 1] }}
              className="text-[46px] sm:text-[58px] lg:text-[62px] font-bold tracking-[-0.035em] leading-[1.05] text-[#171717] mb-2"
            >
              AI that masters
            </motion.h1>

            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.14, ease: [0.16, 1, 0.3, 1] }}
              className="text-[46px] sm:text-[58px] lg:text-[62px] font-bold tracking-[-0.035em] leading-[1.05] mb-7"
              style={{ minHeight: "1.1em" }}
            >
              <span
                style={{
                  background: "linear-gradient(135deg, #A38A70 0%, #0F172A 60%, #7A8B76 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                {typed}
              </span>
              <span
                className="cursor-blink"
                style={{
                  background: "linear-gradient(135deg, #A38A70, #0F172A)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                |
              </span>
            </motion.div>

            <motion.p
              initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.22, ease: EASE }}
              className="text-[17px] text-neutral-500 leading-[1.78] max-w-[460px] mb-9"
            >
              Ittera is the AI content strategy engine that analyzes your audience, predicts trending topics, and fills your calendar — so you can focus on creating.
            </motion.p>

            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.3, ease: EASE }}
              className="flex flex-col sm:flex-row gap-3 mb-10"
            >
              <a
                href="#waitlist"
                className="btn-glow inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-lg text-[14.5px] font-semibold text-white bg-[#0F172A] transition-transform duration-200 hover:-translate-y-px"
              >
                Join the Waitlist
                <ArrowRight className="w-4 h-4" />
              </a>
              <a
                href="#showcase"
                className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-lg text-[14.5px] font-medium text-neutral-600 border border-[#EAEAEC] hover:border-[#D4D4D4] hover:bg-[#F5F5F4] transition-all duration-200"
              >
                See it in action
              </a>
            </motion.div>

            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.45 }}
              className="flex items-center gap-3"
            >
              <div className="flex -space-x-2">
                {["AM", "PK", "JL", "SR", "MO"].map((initials, i) => (
                  <div
                    key={i}
                    className="w-7 h-7 rounded-full border-2 border-[#F9F8F6] flex items-center justify-center text-[9px] font-bold text-white"
                    style={{
                      background: i % 2 === 0
                        ? "linear-gradient(135deg, #0F172A, #A38A70)"
                        : "linear-gradient(135deg, #7A8B76, #0F172A)",
                    }}
                  >
                    {initials}
                  </div>
                ))}
              </div>
              <p className="text-[12px] text-neutral-400">
                <span className="text-neutral-600 font-medium">12 creators</span> already on the waitlist
              </p>
            </motion.div>
          </div>

          {/* Right */}
          <div className="relative">
            <DashboardMockup />
          </div>
        </div>
      </div>
    </section>
  );
}
