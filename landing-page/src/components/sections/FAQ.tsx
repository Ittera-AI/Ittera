"use client";

import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { FAQ_ITEMS } from "@/lib/constants";
import { Plus } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const EASE = [0.16, 1, 0.3, 1] as const;

export default function FAQ() {
  const [open, setOpen] = useState<number | null>(null);
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const sectionBg    = isDark ? "#0C0B09"                    : "#F9F8F6";
  const headingColor = isDark ? "#F2EDE8"                    : "#171717";
  const subColor     = isDark ? "rgba(242,237,232,0.45)"     : "#737373";
  const linkColor    = isDark ? "rgba(242,237,232,0.7)"      : "#525252";
  const linkHover    = isDark ? "#F2EDE8"                    : "#171717";
  const dividerColor = isDark ? "#2E2922"                    : "#EAEAEC";
  const itemHoverBg  = isDark ? "rgba(255,255,255,0.03)"     : "#F5F5F4";
  const qColor       = isDark ? "rgba(242,237,232,0.75)"     : "#404040";
  const qOpenColor   = isDark ? "#F2EDE8"                    : "#171717";
  const aColor       = isDark ? "rgba(242,237,232,0.45)"     : "#737373";
  const plusIdleBg   = isDark ? "#1C1916"                    : "#F3F4F6";
  const plusIdleBorder = isDark ? "#2E2922"                  : "#EAEAEC";
  const plusIdleColor  = isDark ? "rgba(242,237,232,0.3)"    : "#9CA3AF";
  const plusOpenBg   = isDark ? "rgba(196,168,130,0.12)"     : "rgba(163,138,112,0.1)";
  const plusOpenBorder = isDark ? "rgba(196,168,130,0.3)"    : "rgba(163,138,112,0.3)";
  const plusOpenColor  = isDark ? "#C4A882"                  : "#A38A70";

  return (
    <section id="faq" className="relative py-12 sm:py-24 overflow-hidden" style={{ background: sectionBg }}>

      {/* Background orb */}
      <motion.div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full pointer-events-none"
        style={{ background: `radial-gradient(ellipse, ${isDark ? "rgba(163,138,112,0.04)" : "rgba(163,138,112,0.03)"} 0%, transparent 65%)`, filter: "blur(60px)" }}
        animate={shouldReduceMotion ? undefined : { scale: [1, 1.06, 1], opacity: [0.6, 1, 0.6] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Shimmer top border */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-px pointer-events-none"
        style={{ background: "linear-gradient(90deg, transparent, rgba(163,138,112,0.2), rgba(122,139,118,0.12), transparent)" }}
        animate={shouldReduceMotion ? undefined : { opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="relative z-10 max-w-3xl mx-auto px-6 lg:px-10">

        {/* ── Header ── */}
        <div className="mb-14">
          <motion.h2
            initial={shouldReduceMotion ? false : { opacity: 0, y: 14, filter: "blur(6px)" }}
            whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: EASE }}
            className="text-[28px] sm:text-[42px] lg:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] mb-4"
            style={{ color: headingColor }}
          >
            Questions{" "}
            <span style={{ color: isDark ? "#C4A882" : "#8B6F52" }}>answered</span>
          </motion.h2>

          <motion.p
            initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.12, ease: EASE }}
            className="text-[15px]"
            style={{ color: subColor }}
          >
            Can&apos;t find an answer?{" "}
            <a
              href="#"
              className="underline underline-offset-2 transition-colors duration-150"
              style={{ color: linkColor }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = linkHover; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = linkColor; }}
            >
              Chat with us
            </a>
          </motion.p>
        </div>

        {/* ── Accordion ── */}
        <div style={{ borderTop: `1px solid ${dividerColor}` }}>
          {FAQ_ITEMS.map((item, i) => (
            <motion.div
              key={i}
              initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: i * 0.06, ease: EASE }}
              style={{ borderBottom: `1px solid ${dividerColor}` }}
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between gap-4 text-left -mx-3 px-3 rounded-lg transition-colors duration-200 py-5"
                style={{ background: open === i ? itemHoverBg : "transparent" }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = itemHoverBg; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = open === i ? itemHoverBg : "transparent"; }}
              >
                <span
                  className="text-[14.5px] font-medium transition-colors duration-150"
                  style={{ color: open === i ? qOpenColor : qColor }}
                >
                  {item.question}
                </span>

                <motion.div
                  className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 transition-colors duration-200"
                  style={{
                    background:    open === i ? plusOpenBg     : plusIdleBg,
                    border:        `1px solid ${open === i ? plusOpenBorder : plusIdleBorder}`,
                    color:         open === i ? plusOpenColor  : plusIdleColor,
                  }}
                  animate={{ rotate: open === i ? 45 : 0 }}
                  transition={{ duration: 0.22, ease: EASE }}
                >
                  <Plus className="w-3 h-3" />
                </motion.div>
              </button>

              <AnimatePresence initial={false}>
                {open === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.28, ease: "easeInOut" }}
                    className="overflow-hidden"
                  >
                    <p
                      className="pt-1 pb-5 px-3 text-[13.5px] leading-relaxed max-w-xl"
                      style={{ color: aColor }}
                    >
                      {item.answer}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  );
}
