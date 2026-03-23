"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { ArrowRight, Zap, Star, Shield, Users, ChevronRight } from "lucide-react";

const TOTAL_SEATS = 1000;
const TAKEN_SEATS = 847;
const REMAINING = TOTAL_SEATS - TAKEN_SEATS;

function useCounter(target: number, duration = 1800) {
  const [count, setCount] = useState(0);
  const [started, setStarted] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setStarted(true); },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!started) return;
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    const interval = setInterval(() => {
      current = Math.min(current + increment, target);
      setCount(Math.floor(current));
      if (current >= target) clearInterval(interval);
    }, duration / steps);
    return () => clearInterval(interval);
  }, [started, target, duration]);

  return { count, ref };
}

const PERKS = [
  {
    icon: Zap,
    title: "Beta access in Q2 2026",
    desc: "Before public launch — you shape the product",
    accent: "#a78bfa",
  },
  {
    icon: Star,
    title: "Founding member pricing",
    desc: "Locked in forever, never increases",
    accent: "#f59e0b",
  },
  {
    icon: Users,
    title: "Vote on what we build next",
    desc: "Direct line to the founding team",
    accent: "#34d399",
  },
  {
    icon: Shield,
    title: "1-on-1 onboarding call",
    desc: "First 100 members only — book your slot",
    accent: "#60a5fa",
  },
];

const AVATARS = [
  { initials: "MC", from: "#a78bfa", to: "#6c47ff" },
  { initials: "JO", from: "#00d4ff", to: "#0099cc" },
  { initials: "SP", from: "#34d399", to: "#059669" },
  { initials: "RV", from: "#f59e0b", to: "#d97706" },
  { initials: "LN", from: "#f472b6", to: "#db2777" },
];

export default function Waitlist() {
  const shouldReduceMotion = useReducedMotion();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [position, setPosition] = useState(0);
  const [error, setError] = useState("");
  const { count, ref } = useCounter(TAKEN_SEATS);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes("@") || !email.includes(".")) {
      setError("Please enter a valid email address.");
      return;
    }
    setError("");
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setPosition(TAKEN_SEATS + 1);
      setSubmitted(true);
    }, 1300);
  };

  const progressPct = (TAKEN_SEATS / TOTAL_SEATS) * 100;

  return (
    <section id="waitlist" className="py-28 relative overflow-hidden">
      {/* BG */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse at 50% 50%, rgba(108,71,255,0.1) 0%, rgba(0,212,255,0.04) 40%, transparent 70%)" }}
      />
      <div className="absolute top-0 left-0 right-0 h-px pointer-events-none" style={{ background: "linear-gradient(90deg, transparent, rgba(108,71,255,0.35), rgba(0,212,255,0.2), transparent)" }} />
      <div className="absolute bottom-0 left-0 right-0 h-px pointer-events-none" style={{ background: "linear-gradient(90deg, transparent, rgba(108,71,255,0.2), transparent)" }} />

      <div className="relative z-10 max-w-2xl mx-auto px-6 lg:px-10 text-center" ref={ref}>
        {/* Eyebrow */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex items-center justify-center gap-2 mb-8"
        >
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-violet-500/20 bg-violet-500/[0.08]">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400/80 animate-pulse" />
            <span className="text-[11px] font-semibold text-violet-300/70 tracking-wider uppercase">
              Founding Cohort · {REMAINING} seats left
            </span>
          </div>
        </motion.div>

        {/* Counter */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, scale: 0.92 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="mb-2"
        >
          <span
            className="text-[80px] sm:text-[100px] font-bold tracking-[-0.04em] leading-none tabular-nums"
            style={{
              background: "linear-gradient(135deg, #a78bfa 0%, #6c47ff 45%, #00d4ff 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            {count.toLocaleString()}
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h2
          initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55, delay: 0.1 }}
          className="text-[34px] sm:text-[44px] font-bold tracking-[-0.03em] leading-[1.1] text-white mb-4"
        >
          creators already waiting.
          <br />
          <span className="text-white/35">Don&apos;t get left behind.</span>
        </motion.h2>

        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.16 }}
          className="text-[15px] text-white/38 leading-[1.75] max-w-lg mx-auto mb-4"
        >
          Ittera is in private development. Founding members get locked-in pricing, direct product input, and beta access before the world.
        </motion.p>

        {/* Capacity bar */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mb-8 max-w-sm mx-auto"
        >
          <div className="flex justify-between text-[11px] text-white/28 mb-1.5">
            <span>{TAKEN_SEATS} joined</span>
            <span className="text-amber-400/70 font-medium">{REMAINING} seats remaining</span>
          </div>
          <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: "linear-gradient(90deg, #6c47ff, #a78bfa, #00d4ff)" }}
              initial={{ width: 0 }}
              whileInView={{ width: `${progressPct}%` }}
              viewport={{ once: true }}
              transition={{ duration: 1.2, delay: 0.4, ease: "easeOut" }}
            />
          </div>
          <div className="text-right text-[10px] text-white/18 mt-1">{TOTAL_SEATS} total founding seats</div>
        </motion.div>

        {/* Form */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55, delay: 0.22 }}
          className="mb-4"
        >
          <AnimatePresence mode="wait">
            {submitted ? (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-4 py-8"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.1 }}
                  className="w-16 h-16 rounded-2xl flex items-center justify-center"
                  style={{
                    background: "linear-gradient(135deg, rgba(108,71,255,0.3), rgba(0,212,255,0.2))",
                    border: "1px solid rgba(108,71,255,0.35)",
                    boxShadow: "0 0 40px rgba(108,71,255,0.2)",
                  }}
                >
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                    <path d="M20 6L9 17L4 12" stroke="#a78bfa" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </motion.div>
                <div>
                  <p className="text-[20px] font-bold text-white/85 mb-1">You&apos;re #{position} on the list.</p>
                  <p className="text-[14px] text-white/35 max-w-xs mx-auto">
                    We&apos;ll reach out with beta details before public launch. Welcome to the founding cohort.
                  </p>
                </div>
                <a
                  href={`https://twitter.com/intent/tweet?text=Just%20joined%20the%20%40itteraai%20waitlist%20%E2%80%94%20an%20AI%20content%20strategy%20engine%20for%20creators.%20Spot%20%23${position}.%20%F0%9F%9A%80`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-[12.5px] font-medium text-white/45 border border-white/[0.08] hover:border-white/[0.16] hover:text-white/65 transition-all duration-200"
                >
                  Share on X
                  <ChevronRight className="w-3.5 h-3.5" />
                </a>
              </motion.div>
            ) : (
              <motion.form
                key="form"
                onSubmit={handleSubmit}
                className="flex flex-col sm:flex-row gap-2.5 max-w-md mx-auto"
              >
                <div className="flex-1 relative">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => { setEmail(e.target.value); setError(""); }}
                    placeholder="your@email.com"
                    className="w-full h-12 px-4 rounded-xl text-[14px] text-white/70 placeholder-white/20 outline-none transition-all duration-200"
                    style={{
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.1)",
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.border = "1px solid rgba(108,71,255,0.4)";
                      e.currentTarget.style.background = "rgba(108,71,255,0.04)";
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.border = "1px solid rgba(255,255,255,0.1)";
                      e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                    }}
                  />
                  {error && (
                    <p className="absolute -bottom-5 left-0 text-[11px] text-red-400/70">{error}</p>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-glow h-12 px-6 rounded-xl text-[14px] font-semibold text-white flex items-center justify-center gap-2 whitespace-nowrap disabled:opacity-60 transition-opacity"
                  style={{ background: "linear-gradient(135deg, #6c47ff 0%, #4f32d4 60%, #00a8cc 100%)" }}
                >
                  {loading ? (
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : (
                    <>Get Early Access <ArrowRight className="w-4 h-4" /></>
                  )}
                </button>
              </motion.form>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Avatars + privacy */}
        {!submitted && (
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.32 }}
            className="flex items-center justify-center gap-3 mb-10"
          >
            <div className="flex -space-x-2">
              {AVATARS.map((a, i) => (
                <div
                  key={i}
                  className="w-6 h-6 rounded-full border-2 border-[#030407] flex items-center justify-center text-[8px] font-bold text-white/80"
                  style={{ background: `linear-gradient(135deg, ${a.from}, ${a.to})` }}
                >
                  {a.initials}
                </div>
              ))}
            </div>
            <p className="text-[12px] text-white/25">
              No spam · Unsubscribe any time
            </p>
          </motion.div>
        )}

        {/* Perks */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.36 }}
          className="grid grid-cols-2 gap-3"
        >
          {PERKS.map((perk) => {
            const Icon = perk.icon;
            return (
              <div
                key={perk.title}
                className="flex items-start gap-3 p-4 rounded-xl text-left"
                style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}
              >
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                  style={{ background: `${perk.accent}18`, border: `1px solid ${perk.accent}28` }}
                >
                  <Icon className="w-3.5 h-3.5" style={{ color: perk.accent + "cc" }} />
                </div>
                <div>
                  <p className="text-[12.5px] font-semibold text-white/60 leading-tight mb-0.5">{perk.title}</p>
                  <p className="text-[11px] text-white/28 leading-tight">{perk.desc}</p>
                </div>
              </div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
