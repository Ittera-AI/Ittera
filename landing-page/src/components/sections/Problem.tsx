"use client";

import { motion } from "framer-motion";
import { useTheme } from "@/context/ThemeContext";
const EASE = [0.16, 1, 0.3, 1] as const;

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
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const cardBg     = isDark ? "#141210" : "white";
  const cardHover  = isDark ? "#1C1916" : "#F5F5F4";
  const gridGap    = isDark ? "#2E2922" : "#EAEAEC";
  const numColor   = isDark ? "rgba(242,237,232,0.12)" : "#E5E5E5";
  const titleColor = isDark ? "#F2EDE8" : "#171717";
  const descColor  = isDark ? "rgba(242,237,232,0.5)" : "#737373";
  const quoteColor = isDark ? "rgba(242,237,232,0.55)" : "#737373";
  const quoteStrong= isDark ? "#F2EDE8" : "#404040";

  return (
    <section id="problem" className="py-12 sm:py-24 bg-[#F9F8F6] relative">
      <div
        className="absolute top-0 right-0 w-[500px] h-[500px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse at top right, rgba(163,138,112,0.04) 0%, transparent 60%)" }}
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
            <span className="eyebrow">The problem</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: EASE }}
            className="text-[28px] sm:text-[42px] lg:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] mb-5"
            style={{ color: titleColor }}
          >
            Content strategy is broken
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.14, ease: EASE }}
            className="text-[16px] leading-[1.75]"
            style={{ color: descColor }}
          >
            Creators and marketers are drowning in tools that don&apos;t work together,
            spending more time managing content than creating it.
          </motion.p>
        </div>

        <div
          className="grid grid-cols-1 sm:grid-cols-2 gap-px rounded-2xl overflow-hidden"
          style={{ background: gridGap, border: `1px solid ${gridGap}` }}
        >
          {PAIN_POINTS.map((point, i) => (
            <motion.div
              key={point.num}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.45, delay: i * 0.06 }}
              className="p-7 transition-colors duration-300"
              style={{ background: cardBg }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = cardHover; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = cardBg; }}
            >
              <div className="text-[11px] font-mono mb-4 tracking-wider" style={{ color: numColor }}>{point.num}</div>
              <h3 className="text-[15px] font-semibold mb-2.5 tracking-tight" style={{ color: titleColor }}>{point.title}</h3>
              <p className="text-[13.5px] leading-[1.7]" style={{ color: descColor }}>{point.description}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-12 pl-5 border-l-2 border-[#A38A70]/40"
        >
          <p className="text-[17px] leading-relaxed max-w-2xl" style={{ color: quoteColor }}>
            The average creator wastes{" "}
            <span className="font-semibold" style={{ color: quoteStrong }}>12+ hours every week</span>{" "}
            on content operations that should take two.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
