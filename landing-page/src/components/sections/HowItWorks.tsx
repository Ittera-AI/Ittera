"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Link, Brain, Rocket } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const STEPS = [
  {
    num: "01",
    icon: Link,
    title: "Connect your platforms",
    description:
      "Link LinkedIn, X, Instagram, and your analytics in under two minutes. Ittera pulls your historical data immediately.",
  },
  {
    num: "02",
    icon: Brain,
    title: "AI analyzes your audience",
    description:
      "The engine maps engagement patterns, peak windows, and content formats that resonate — specific to your audience.",
  },
  {
    num: "03",
    icon: Rocket,
    title: "Execute with confidence",
    description:
      "Your calendar fills with AI-recommended content. You review, adjust, publish. Strategy runs on autopilot.",
  },
];

export default function HowItWorks() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="how-it-works" className="py-24 relative bg-[#F9F8F6]">
      <div className="max-w-7xl mx-auto px-6 lg:px-10">
        <div className="max-w-xl mb-16">
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: EASE }}
            className="flex items-center gap-2 mb-6"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">How it works</span>
          </motion.div>

          <motion.h2
            initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: EASE }}
            className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-neutral-900"
          >
            Up and running <span className="gradient-text">in minutes</span>
          </motion.h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.num}
                initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.5, delay: i * 0.1, ease: EASE }}
                className="relative p-7 rounded-2xl bg-white border border-[#EAEAEC] hover:border-[#D4D4D4] transition-all duration-300"
                style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
              >
                <div className="flex items-center justify-between mb-6">
                  <div className="w-10 h-10 rounded-xl bg-neutral-50 border border-[#EAEAEC] flex items-center justify-center">
                    <Icon className="w-4.5 h-4.5 text-neutral-500" />
                  </div>
                  <span className="text-[11px] font-mono text-neutral-200 tracking-wider">{step.num}</span>
                </div>
                <h3 className="text-[15px] font-semibold text-neutral-900 mb-2.5 tracking-tight">{step.title}</h3>
                <p className="text-[13px] text-neutral-500 leading-[1.7]">{step.description}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
