"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, useReducedMotion, useScroll, useMotionValueEvent } from "framer-motion";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import CursorGlow from "@/components/ui/CursorGlow";
import GrainOverlay from "@/components/ui/GrainOverlay";
import AuthModal from "@/components/auth/AuthModal";
import Footer from "@/components/layout/Footer";
import ProductShowcase from "@/components/sections/ProductShowcase";

const EASE = [0.16, 1, 0.3, 1] as const;
const CUBIC: [number, number, number, number] = [0.16, 1, 0.3, 1];

const wordVariants = {
  hidden: { opacity: 0, y: 40, filter: "blur(10px)" },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.65, delay: i * 0.08, ease: CUBIC },
  }),
};

// ─── Demo Nav ────────────────────────────────────────────────────────────────

function DemoNav() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [scrolled, setScrolled] = useState(false);

  const { scrollY } = useScroll();

  useMotionValueEvent(scrollY, "change", (latest) => {
    setScrolled(latest > 40);
  });

  const navBg = scrolled
    ? isDark ? "rgba(12,11,9,0.92)" : "rgba(249,248,246,0.92)"
    : "rgba(0,0,0,0)";
  const navBorder = scrolled
    ? isDark ? "#2E2922" : "#EAEAEC"
    : "transparent";
  const brandColor = isDark ? "#F2EDE8" : "#171717";
  const backColor  = isDark ? "rgba(242,237,232,0.4)" : "rgba(23,23,23,0.45)";
  const backHover  = isDark ? "#F2EDE8" : "#171717";

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        background: navBg,
        backdropFilter: scrolled ? "blur(20px) saturate(150%)" : "none",
        borderBottom: `1px solid ${navBorder}`,
        transition: "background 0.5s cubic-bezier(0.16,1,0.3,1), border-color 0.5s cubic-bezier(0.16,1,0.3,1)",
      }}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-10">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M12 2L14.5 9L21 12L14.5 15L12 22L9.5 15L3 12L9.5 9L12 2Z"
                fill="url(#demo-nav-grad)"
              />
              <defs>
                <linearGradient id="demo-nav-grad" x1="3" y1="2" x2="21" y2="22" gradientUnits="userSpaceOnUse">
                  <stop stopColor={isDark ? "#C4A882" : "#0F172A"} />
                  <stop offset="1" stopColor="#A38A70" />
                </linearGradient>
              </defs>
            </svg>
            <span className="text-[15px] font-semibold tracking-tight" style={{ color: brandColor }}>
              Ittera
            </span>
          </Link>

          {/* Back link */}
          <div>
            <Link
              href="/"
              className="group flex items-center gap-1.5 text-[13px] font-medium transition-colors duration-200"
              style={{ color: backColor }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = backHover; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = backColor; }}
            >
              <span className="transition-transform duration-200 group-hover:-translate-x-1">
                <ArrowLeft className="w-3.5 h-3.5" />
              </span>
              Back to Ittera
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

// ─── Demo Hero ────────────────────────────────────────────────────────────────

function DemoHero() {
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const headingLines = [
    ["See", "every", "workspace."],
    ["Every", "workflow."],
  ];
  // flatten for global word index (for stagger)
  const line0 = headingLines[0];
  const line1 = headingLines[1];

  return (
    <section
      className="relative pt-32 pb-16 sm:pt-40 sm:pb-20 overflow-hidden text-center"
      style={{ background: isDark ? "#0C0B09" : "#F9F8F6" }}
    >
      {/* Ambient orbs */}
      <div
        className="absolute top-0 left-[10%] w-[600px] h-[600px] rounded-full pointer-events-none -translate-x-1/4 -translate-y-1/4"
        style={{ background: "radial-gradient(circle, rgba(163,138,112,0.18) 0%, transparent 60%)" }}
      />
      <div
        className="absolute top-0 right-[10%] w-[500px] h-[500px] rounded-full pointer-events-none translate-x-1/4 -translate-y-1/4"
        style={{ background: "radial-gradient(circle, rgba(122,139,118,0.14) 0%, transparent 60%)" }}
      />

      <div className="relative z-10 max-w-4xl mx-auto px-6 lg:px-10">
        {/* Badge */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: EASE }}
          className="inline-flex items-center gap-2 mb-8"
        >
          <div
            className="flex items-center gap-2 rounded-full px-3.5 py-1.5 text-[11px] font-semibold uppercase tracking-[0.22em]"
            style={{
              background: isDark ? "rgba(163,138,112,0.1)" : "rgba(163,138,112,0.08)",
              border: `1px solid ${isDark ? "rgba(163,138,112,0.22)" : "rgba(163,138,112,0.2)"}`,
              color: "#8B6F52",
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#A38A70] animate-pulse" />
            Live Demo
          </div>
        </motion.div>

        {/* Heading — word-by-word stagger */}
        <div className="mb-6">
          <div className="text-[34px] sm:text-[52px] lg:text-[64px] font-bold tracking-[-0.035em] leading-[1.06] flex flex-wrap justify-center gap-x-[0.22em] overflow-hidden mb-1">
            {line0.map((word, i) => (
              <motion.span
                key={i}
                custom={i}
                variants={shouldReduceMotion ? {} : wordVariants}
                initial="hidden"
                animate="visible"
                style={{ color: isDark ? "#F2EDE8" : "#171717" }}
              >
                {word}
              </motion.span>
            ))}
          </div>
          <div className="text-[34px] sm:text-[52px] lg:text-[64px] font-bold tracking-[-0.035em] leading-[1.06] flex flex-wrap justify-center gap-x-[0.22em] overflow-hidden">
            {line1.map((word, i) => (
              <motion.span
                key={i}
                custom={line0.length + i}
                variants={shouldReduceMotion ? {} : wordVariants}
                initial="hidden"
                animate="visible"
                className={i === line1.length - 1 ? "gradient-text" : ""}
                style={i === line1.length - 1 ? {} : { color: isDark ? "#F2EDE8" : "#171717" }}
              >
                {word}
              </motion.span>
            ))}
          </div>
        </div>

        {/* Subheading */}
        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 14, filter: "blur(6px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          transition={{ duration: 0.7, delay: 0.55, ease: EASE }}
          className="text-[16px] leading-[1.8] max-w-lg mx-auto"
          style={{ color: isDark ? "rgba(242,237,232,0.56)" : "#5F5A55" }}
        >
          Six workspaces. Three scenarios. Real strategy — live.
        </motion.p>

        {/* Decorative divider */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, scaleX: 0 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{ duration: 0.6, delay: 0.7, ease: EASE }}
          className="mt-8 h-px max-w-xs mx-auto"
          style={{ background: "linear-gradient(90deg, transparent, rgba(163,138,112,0.3), transparent)" }}
        />
      </div>
    </section>
  );
}

// ─── Demo CTA ────────────────────────────────────────────────────────────────

function DemoCTA() {
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const btnBg    = isDark ? "linear-gradient(135deg, #C4A882 0%, #A38A70 100%)" : "#0F172A";
  const btnColor = isDark ? "#0C0B09" : "white";
  const noteColor = isDark ? "rgba(242,237,232,0.28)" : "#A3A3A3";

  const headingWords = ["Your", "strategy", "starts", "here."];

  return (
    <section
      className="relative py-20 sm:py-28 overflow-hidden text-center"
      style={{ background: isDark ? "#0C0B09" : "#F9F8F6" }}
    >
      {/* Shimmer top border */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-px pointer-events-none"
        style={{ background: "linear-gradient(90deg, transparent, rgba(163,138,112,0.25), rgba(122,139,118,0.15), transparent)" }}
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Animated orbs */}
      <motion.div
        className="absolute top-1/3 left-1/4 w-[450px] h-[450px] rounded-full pointer-events-none will-change-transform"
        style={{ background: "radial-gradient(circle, rgba(163,138,112,0.16) 0%, transparent 60%)" }}
        animate={{ x: [0, 22, -12, 0], y: [0, -18, 12, 0] }}
        transition={{ duration: 9, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-1/3 right-1/4 w-[350px] h-[350px] rounded-full pointer-events-none will-change-transform"
        style={{ background: "radial-gradient(circle, rgba(122,139,118,0.14) 0%, transparent 60%)" }}
        animate={{ x: [0, -16, 10, 0], y: [0, 14, -9, 0] }}
        transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute top-1/2 right-1/3 w-[250px] h-[250px] rounded-full pointer-events-none will-change-transform"
        style={{ background: "radial-gradient(circle, rgba(163,138,112,0.12) 0%, transparent 60%)" }}
        animate={{ x: [0, 12, -18, 0], y: [0, -10, 6, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="relative z-10 max-w-2xl mx-auto px-6 lg:px-10">
        {/* Heading */}
        <div className="text-[30px] sm:text-[44px] font-bold tracking-[-0.03em] leading-[1.08] flex flex-wrap justify-center gap-x-[0.22em] overflow-hidden mb-5">
          {headingWords.map((word, i) => (
            <motion.span
              key={i}
              custom={i}
              variants={shouldReduceMotion ? {} : wordVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              style={{ color: isDark ? "#F2EDE8" : "#171717" }}
            >
              {word}
            </motion.span>
          ))}
        </div>

        {/* Body */}
        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 14, filter: "blur(6px)" }}
          whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.5, ease: EASE }}
          className="text-[16px] leading-[1.8] max-w-lg mx-auto mb-9"
          style={{ color: isDark ? "rgba(242,237,232,0.56)" : "#5F5A55" }}
        >
          Join the founding cohort of creators building their content flywheel with Ittera.
        </motion.p>

        {/* CTA button */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 24, scale: 0.95 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.65, delay: 0.65, ease: [0.34, 1.56, 0.64, 1] }}
          className="flex justify-center"
        >
          <div className="group">
            <Link
              href="/#waitlist"
              className="h-12 px-7 rounded-lg text-[14px] font-semibold flex items-center justify-center gap-2 will-change-transform transition-all duration-300 group-hover:-translate-y-0.5 group-hover:scale-[1.02] group-active:scale-95"
              style={{ background: btnBg, color: btnColor }}
            >
              Claim your founding spot
              <span className="transition-transform duration-300 group-hover:translate-x-1">
                <ArrowRight className="w-4 h-4" />
              </span>
            </Link>
          </div>
        </motion.div>

        {/* Note */}
        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 6 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.9, ease: EASE }}
          className="mt-4 text-[12px]"
          style={{ color: noteColor }}
        >
          Free during beta. No credit card required.
        </motion.p>
      </div>
    </section>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DemoPage() {
  return (
    <div className="min-h-screen overflow-x-hidden">
      <CursorGlow />
      <GrainOverlay />
      <AuthModal />
      <DemoNav />
      <main className="relative" style={{ zIndex: 1 }}>
        <DemoHero />
        <ProductShowcase />
        <DemoCTA />
      </main>
      <Footer />
    </div>
  );
}
