"use client";

import { motion } from "framer-motion";
import { TESTIMONIALS } from "@/lib/constants";

const METRICS = [
  { value: "340%", label: "Average engagement lift" },
  { value: "12h", label: "Saved weekly per creator" },
  { value: "6×", label: "Faster content production" },
];

export default function Benefits() {
  return (
    <section id="benefits" className="py-24 relative overflow-hidden">
      <div
        className="absolute bottom-0 right-0 w-[500px] h-[400px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse at bottom right, rgba(109,77,255,0.08) 0%, transparent 60%)" }}
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
            <span className="eyebrow">Results</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: "easeOut" }}
            className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-white"
          >
            Real outcomes.{" "}
            <span className="gradient-text">First 90 days.</span>
          </motion.h2>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-12">
          {METRICS.map((metric, i) => (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08, ease: "easeOut" }}
              className="p-7 rounded-2xl bg-white/[0.025] border border-white/[0.05]"
            >
              <div className="text-[52px] font-bold tracking-[-0.04em] text-white/85 leading-none mb-2">
                {metric.value}
              </div>
              <div className="text-[13px] text-white/35">{metric.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Testimonials */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {TESTIMONIALS.map((testimonial, i) => (
            <motion.div
              key={testimonial.name}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.45, delay: i * 0.07, ease: "easeOut" }}
              className="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:border-white/[0.09] transition-colors duration-300"
            >
              <p className="text-[13.5px] text-white/50 leading-[1.7] mb-5 italic">
                &ldquo;{testimonial.quote}&rdquo;
              </p>
              <div className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-bold text-white flex-shrink-0"
                  style={{ background: "rgba(124,92,252,0.25)" }}
                >
                  {testimonial.avatar}
                </div>
                <div>
                  <div className="text-[13px] font-semibold text-white/70">{testimonial.name}</div>
                  <div className="text-[11.5px] text-white/28">{testimonial.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
