"use client";

import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
const EASE = [0.16, 1, 0.3, 1] as const;

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
    <section className="relative py-32 bg-[#F9F8F6] overflow-hidden">
      {/* Animated orbs */}
      <div
        className="absolute top-1/3 left-1/4 w-72 h-72 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(163,138,112,0.06) 0%, transparent 70%)",
          filter: "blur(50px)",
          animation: "float-1 9s ease-in-out infinite",
        }}
      />
      <div
        className="absolute bottom-1/3 right-1/4 w-56 h-56 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(122,139,118,0.04) 0%, transparent 70%)",
          filter: "blur(40px)",
          animation: "float-2 11s ease-in-out infinite",
        }}
      />
      <div
        className="absolute top-1/2 right-1/3 w-40 h-40 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(163,138,112,0.04) 0%, transparent 70%)",
          filter: "blur(30px)",
          animation: "float-3 7s ease-in-out infinite",
        }}
      />

      {/* Top edge */}
      <div
        className="absolute top-0 left-0 right-0 h-px pointer-events-none"
        style={{ background: "linear-gradient(90deg, transparent, rgba(163,138,112,0.2), rgba(122,139,118,0.12), transparent)" }}
      />

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
                <span className="text-neutral-900">{line}</span>
              ) : (
                <span
                  style={{
                    background: "linear-gradient(135deg, #A38A70 0%, #0F172A 45%, #7A8B76 100%)",
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
          transition={{ duration: 0.55, delay: 0.12, ease: EASE }}
          className="text-[16px] text-neutral-500 leading-[1.8] max-w-xl mx-auto mb-10"
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
              className="inline-flex items-center gap-3 px-6 py-3.5 rounded-xl text-[14px] font-medium text-[#8B6F52]"
              style={{ background: "rgba(163,138,112,0.08)", border: "1px solid rgba(163,138,112,0.25)" }}
            >
              <span className="w-2 h-2 rounded-full bg-[#A38A70]/80 animate-pulse" />
              You&apos;re on the list. We&apos;ll be in touch.
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2.5 justify-center max-w-md mx-auto">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="flex-1 h-12 px-4 rounded-lg text-[14px] text-neutral-800 placeholder:text-neutral-400 outline-none transition-all duration-200"
                style={{ background: "white", border: "1px solid #EAEAEC" }}
                onFocus={(e) => {
                  e.currentTarget.style.border = "1px solid rgba(163,138,112,0.5)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.border = "1px solid #EAEAEC";
                }}
              />
              <button
                type="submit"
                disabled={loading || !email.includes("@")}
                className="h-12 px-7 rounded-lg text-[14px] font-semibold text-white flex items-center justify-center gap-2 whitespace-nowrap disabled:opacity-50 transition-all duration-200 hover:-translate-y-px"
                style={{ background: "#0F172A" }}
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
          className="text-[12px] text-neutral-400"
        >
          No credit card. No spam. Just early access to the product we&apos;re building for you.
        </motion.p>
      </div>
    </section>
  );
}
