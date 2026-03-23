"use client";

import { motion } from "framer-motion";

const PAIN_POINTS = [
  {
    num: "01",
    title: "No unified strategy",
    description:
      "Spreadsheets, Notion docs, five scheduling tools — none talking to each other. Content chaos costs you hours every week and clarity every day.",
  },
  {
    num: "02",
    title: "You're guessing, not knowing",
    description:
      "You publish and hope. Without real signal from your own audience data, you're blindly copying trends that worked for someone else.",
  },
  {
    num: "03",
    title: "Manual repurposing kills momentum",
    description:
      "Reformatting every piece of content for each platform takes forever. By the time you're done, the moment has passed.",
  },
  {
    num: "04",
    title: "Reactive, never strategic",
    description:
      "Always chasing trends instead of leading them. Without a forward-looking engine, you're permanently one step behind.",
  },
];

export default function Problem() {
  return (
    <section id="problem" className="py-24 relative">
      <div
        className="absolute top-0 right-0 w-[500px] h-[500px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse at top right, rgba(109,77,255,0.07) 0%, transparent 60%)" }}
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
            <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
            <span className="eyebrow">The problem</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: "easeOut" }}
            className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-white mb-5"
          >
            Content strategy is broken
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.14, ease: "easeOut" }}
            className="text-[16px] text-white/42 leading-[1.75]"
          >
            Creators and marketers are drowning in tools that don&apos;t work together,
            spending more time managing content than creating it.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-white/[0.04] rounded-2xl overflow-hidden border border-white/[0.04]">
          {PAIN_POINTS.map((point, i) => (
            <motion.div
              key={point.num}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.45, delay: i * 0.06 }}
              className="bg-[#06070d] p-7 hover:bg-white/[0.015] transition-colors duration-300"
            >
              <div className="text-[11px] font-mono text-white/18 mb-4 tracking-wider">{point.num}</div>
              <h3 className="text-[15px] font-semibold text-white/80 mb-2.5 tracking-tight">{point.title}</h3>
              <p className="text-[13.5px] text-white/35 leading-[1.7]">{point.description}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-12 pl-5 border-l-2 border-white/[0.08]"
        >
          <p className="text-[17px] text-white/38 leading-relaxed max-w-2xl">
            The average creator wastes{" "}
            <span className="text-white/70 font-semibold">12+ hours every week</span>{" "}
            on content operations that should take two.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
