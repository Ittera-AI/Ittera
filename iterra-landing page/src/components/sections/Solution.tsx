"use client";

import { motion } from "framer-motion";
import { X, Check } from "lucide-react";

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
        style={{ background: "radial-gradient(ellipse, rgba(109,77,255,0.08) 0%, transparent 65%)" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">
        <div className="max-w-xl mb-16">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="flex items-center gap-2 mb-6"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-violet-400/70" />
            <span className="eyebrow">The solution</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: "easeOut" }}
            className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-white"
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
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="rounded-2xl border border-white/[0.05] bg-white/[0.02] p-7"
          >
            <div className="text-[11px] font-medium tracking-[0.12em] uppercase text-white/25 mb-6">
              Before Ittera
            </div>
            <ul className="space-y-3.5">
              {OLD_WAY.map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <X className="w-3.5 h-3.5 text-white/18 mt-0.5 flex-shrink-0" />
                  <span className="text-[13.5px] text-white/32 leading-snug">{item}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* New way */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
            className="rounded-2xl border border-violet-500/20 bg-violet-500/[0.04] p-7 relative overflow-hidden"
          >
            <div
              className="absolute top-0 right-0 w-48 h-48 pointer-events-none"
              style={{ background: "radial-gradient(circle, rgba(124,92,252,0.12) 0%, transparent 70%)" }}
            />
            <div className="text-[11px] font-medium tracking-[0.12em] uppercase text-violet-400/60 mb-6 relative">
              With Ittera
            </div>
            <ul className="space-y-3.5 relative">
              {NEW_WAY.map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <Check className="w-3.5 h-3.5 text-violet-400/70 mt-0.5 flex-shrink-0" />
                  <span className="text-[13.5px] text-white/65 leading-snug">{item}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
