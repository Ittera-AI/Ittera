"use client";

import { motion } from "framer-motion";
import { TESTIMONIALS } from "@/lib/constants";

const EASE = [0.16, 1, 0.3, 1] as const;

const METRICS = [
  { value: "340%", label: "Average engagement lift" },
  { value: "12h", label: "Saved weekly per creator" },
  { value: "6×", label: "Faster content production" },
];

export default function Benefits() {
  return (
    <section id="benefits" className="py-12 sm:py-24 relative overflow-hidden bg-[#F9F8F6]">
      <div
        className="absolute bottom-0 right-0 w-[500px] h-[400px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse at bottom right, rgba(163,138,112,0.04) 0%, transparent 60%)" }}
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
            <span className="eyebrow">Results</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: EASE }}
            className="text-[28px] sm:text-[42px] lg:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-neutral-900"
          >
            Real outcomes. <span className="gradient-text">First 90 days.</span>
          </motion.h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-12">
          {METRICS.map((metric, i) => (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08, ease: EASE }}
              className="p-7 rounded-2xl bg-white border border-[#EAEAEC]"
              style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
            >
              <div className="text-[36px] sm:text-[52px] font-bold tracking-[-0.04em] text-neutral-900 leading-none mb-2">
                {metric.value}
              </div>
              <div className="text-[13px] text-neutral-400">{metric.label}</div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {TESTIMONIALS.map((testimonial, i) => (
            <motion.div
              key={testimonial.name}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.45, delay: i * 0.07, ease: EASE }}
              className="p-6 rounded-2xl bg-white border border-[#EAEAEC] hover:border-[#D4D4D4] transition-all duration-300"
              style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
            >
              <p className="text-[13.5px] text-neutral-600 leading-[1.7] mb-5 italic">
                &ldquo;{testimonial.quote}&rdquo;
              </p>
              <div className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-bold text-white flex-shrink-0"
                  style={{ background: "rgba(163,138,112,0.2)" }}
                >
                  {testimonial.avatar}
                </div>
                <div>
                  <div className="text-[13px] font-semibold text-neutral-700">{testimonial.name}</div>
                  <div className="text-[11.5px] text-neutral-400">{testimonial.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
