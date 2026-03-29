"use client";

import { motion } from "framer-motion";
import { X, Check } from "lucide-react";
const EASE = [0.16, 1, 0.3, 1] as const;

const OLD_WAY = [
  "5+ disconnected tools for one workflow",
  "Manual data analysis across platforms",
  "Guessing optimal posting times",
  "Hours spent reformatting for each platform",
  "Reactive trend-chasing after it peaks",
  "No clear ROI on your content effort",
];

const NEW_WAY = [
  "One unified AI strategy engine",
  "Real-time performance insights, automated",
  "AI-predicted optimal windows per platform",
  "Instant repurposing in 10+ formats",
  "Trend Radar surfaces opportunities 48hrs early",
  "Clear attribution from content to growth",
];

export default function Solution() {
  return (
    <section id="solution" className="py-24 relative overflow-hidden">
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse, rgba(163,138,112,0.04) 0%, transparent 65%)" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">
        <div className="max-w-xl mb-16">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: EASE }}
            className="flex items-center gap-2 mb-6"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">The solution</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: EASE }}
            className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-neutral-900"
          >
            One system.{" "}
            <span className="gradient-text">Everything aligned.</span>
          </motion.h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-4xl">
          {/* Old way */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: EASE }}
            className="rounded-2xl p-7"
            style={{
              background: "linear-gradient(180deg, rgba(255,255,255,1) 0%, rgba(245,245,244,0.92) 100%)",
              border: "1px solid #EAEAEC",
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
            }}
            whileHover={{
              y: -4,
              boxShadow: "0 18px 36px -18px rgba(0,0,0,0.12)",
            }}
          >
            <div className="text-[11px] font-medium tracking-[0.12em] uppercase text-neutral-400 mb-6">
              Before Ittera
            </div>
            <ul className="space-y-3.5">
              {OLD_WAY.map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <X className="w-3.5 h-3.5 text-neutral-300 mt-0.5 flex-shrink-0" />
                  <span className="text-[13.5px] text-neutral-400 leading-snug">{item}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* New way */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1, ease: EASE }}
            className="rounded-2xl p-7 relative overflow-hidden"
            style={{
              background: "linear-gradient(180deg, rgba(163,138,112,0.12) 0%, rgba(255,255,255,0.96) 42%, rgba(122,139,118,0.08) 100%)",
              border: "1px solid rgba(163,138,112,0.24)",
              boxShadow: "0 10px 30px -18px rgba(163,138,112,0.3)",
            }}
            whileHover={{
              y: -4,
              boxShadow: "0 24px 50px -24px rgba(163,138,112,0.35)",
            }}
          >
            <div
              className="absolute top-0 right-0 w-48 h-48 pointer-events-none"
              style={{ background: "radial-gradient(circle, rgba(163,138,112,0.12) 0%, transparent 70%)" }}
            />
            <div className="text-[11px] font-medium tracking-[0.12em] uppercase mb-6 relative" style={{ color: "rgba(163,138,112,0.7)" }}>
              With Ittera
            </div>
            <ul className="space-y-3.5 relative">
              {NEW_WAY.map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <Check className="w-3.5 h-3.5 text-[#A38A70] mt-0.5 flex-shrink-0" />
                  <span className="text-[13.5px] text-neutral-700 leading-snug">{item}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
