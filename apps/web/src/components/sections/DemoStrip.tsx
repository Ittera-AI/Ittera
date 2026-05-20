"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const EASE = [0.16, 1, 0.3, 1] as const;

export default function DemoStrip() {
  const shouldReduceMotion = useReducedMotion() ?? false;
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const bg      = isDark ? "#141210" : "white";
  const border  = isDark ? "#2E2922" : "#EAEAEC";
  const textCol = isDark ? "rgba(242,237,232,0.56)" : "#5F5A55";
  const btnBg   = isDark ? "linear-gradient(135deg, #C4A882 0%, #A38A70 100%)" : "#0F172A";
  const btnCol  = isDark ? "#0C0B09" : "white";

  return (
    <section
      className="relative overflow-hidden"
      style={{ background: isDark ? "#0C0B09" : "#F9F8F6" }}
    >
      {/* Shimmer top border */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-px pointer-events-none"
        style={{ background: "linear-gradient(90deg, transparent, rgba(163,138,112,0.2), rgba(122,139,118,0.12), transparent)" }}
        animate={shouldReduceMotion ? undefined : { opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
      />
      {/* Shimmer bottom border */}
      <motion.div
        className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
        style={{ background: "linear-gradient(90deg, transparent, rgba(163,138,112,0.2), rgba(122,139,118,0.12), transparent)" }}
        animate={shouldReduceMotion ? undefined : { opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 1.75 }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10 py-5">
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45, ease: EASE }}
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-2xl px-6 py-5"
          style={{ background: bg, border: `1px solid ${border}` }}
        >
          {/* Left */}
          <div className="flex items-center gap-4">
            {/* Animated dot */}
            <div className="relative shrink-0">
              <span className="block w-2 h-2 rounded-full bg-[#A38A70]" />
              <motion.span
                className="absolute inset-0 rounded-full bg-[#A38A70]"
                animate={shouldReduceMotion ? undefined : { scale: [1, 2.2, 1], opacity: [0.6, 0, 0.6] }}
                transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
              />
            </div>
            <div>
              <div className="text-[13px] font-semibold" style={{ color: isDark ? "#F2EDE8" : "#171717" }}>
                See the full product in action
              </div>
              <div className="text-[12px] mt-0.5" style={{ color: textCol }}>
                Six workspaces, three scenarios, real strategy — no account needed.
              </div>
            </div>
          </div>

          {/* Right — CTA */}
          <motion.div
            whileHover={{ y: -1, scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            transition={{ duration: 0.16 }}
            className="shrink-0"
          >
            <Link
              href="/demo"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-semibold whitespace-nowrap"
              style={{ background: btnBg, color: btnCol }}
            >
              Open live demo
              <motion.span
                animate={shouldReduceMotion ? undefined : { x: [0, 3, 0] }}
                transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
              >
                <ArrowRight className="w-3.5 h-3.5" />
              </motion.span>
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
