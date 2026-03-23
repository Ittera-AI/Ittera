"use client";

import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const LINES = [
  "The creators who dominate tomorrow",
  "started their flywheel yesterday.",
];

export default function FinalCTA() {
  const shouldReduceMotion = useReducedMotion();
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes("@")) return;
    setLoading(true);
    setTimeout(() => { setLoading(false); setSubmitted(true); }, 1000);
  };

  return (
    <section className="relative py-32 overflow-hidden">
      {/* Deep radial backdrop */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 80% 60% at 50% 50%, rgba(108,71,255,0.16) 0%, rgba(0,212,255,0.06) 40%, transparent 70%)" }}
      />

      {/* Animated orbs */}
      <div
        className="absolute top-1/3 left-1/4 w-72 h-72 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(108,71,255,0.14) 0%, transparent 70%)",
          filter: "blur(50px)",
          animation: "float-1 9s ease-in-out infinite",
        }}
      />
      <div
        className="absolute bottom-1/3 right-1/4 w-56 h-56 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(0,212,255,0.1) 0%, transparent 70%)",
          filter: "blur(40px)",
          animation: "float-2 11s ease-in-out infinite",
        }}
      />
      <div
        className="absolute top-1/2 right-1/3 w-40 h-40 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(167,139,250,0.08) 0%, transparent 70%)",
          filter: "blur(30px)",
          animation: "float-3 7s ease-in-out infinite",
        }}
      />

      {/* Top edge */}
      <div className="absolute top-0 left-0 right-0 h-px pointer-events-none" style={{ background: "linear-gradient(90deg, transparent, rgba(108,71,255,0.3), rgba(0,212,255,0.18), transparent)" }} />

      <div className="relative z-10 max-w-3xl mx-auto px-6 lg:px-10 text-center">

        {/* Manifesto */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="mb-8"
        >
          {LINES.map((line, i) => (
            <div
              key={i}
              className="text-[40px] sm:text-[54px] lg:text-[62px] font-bold tracking-[-0.035em] leading-[1.06]"
            >
              {i === 0 ? (
                <span className="text-white">{line}</span>
              ) : (
                <span
                  style={{
                    background: "linear-gradient(135deg, #a78bfa 0%, #6c47ff 45%, #00d4ff 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                  }}
                >
                  {line}
                </span>
              )}
            </div>
          ))}
        </motion.div>

        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55, delay: 0.12, ease: "easeOut" }}
          className="text-[16px] text-white/38 leading-[1.8] max-w-xl mx-auto mb-10"
        >
          You&apos;re either building your content engine now, or watching others compound their audience while you figure out what to post. Don&apos;t wait.
        </motion.p>

        {/* Inline form — fast path */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55, delay: 0.2 }}
          className="mb-5"
        >
          {submitted ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="inline-flex items-center gap-3 px-6 py-3.5 rounded-xl border border-violet-500/25 bg-violet-500/[0.08] text-[14px] font-medium text-violet-300/80"
            >
              <span className="w-2 h-2 rounded-full bg-violet-400/80 animate-pulse" />
              You&apos;re on the list. We&apos;ll be in touch.
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2.5 justify-center max-w-md mx-auto">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="flex-1 h-12 px-4 rounded-xl text-[14px] text-white/70 placeholder-white/20 outline-none transition-all duration-200"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)" }}
                onFocus={(e) => {
                  e.currentTarget.style.border = "1px solid rgba(108,71,255,0.4)";
                  e.currentTarget.style.background = "rgba(108,71,255,0.04)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.border = "1px solid rgba(255,255,255,0.1)";
                  e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                }}
              />
              <button
                type="submit"
                disabled={loading || !email.includes("@")}
                className="btn-glow h-12 px-7 rounded-xl text-[14px] font-semibold text-white flex items-center justify-center gap-2 whitespace-nowrap disabled:opacity-50 transition-opacity"
                style={{ background: "linear-gradient(135deg, #6c47ff 0%, #4f32d4 55%, #00a8cc 100%)" }}
              >
                {loading ? (
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <>Claim my spot <ArrowRight className="w-4 h-4" /></>
                )}
              </button>
            </form>
          )}
        </motion.div>

        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-[12px] text-white/16"
        >
          No credit card. No spam. Just early access to the product we&apos;re building for you.
        </motion.p>
      </div>
    </section>
  );
}
