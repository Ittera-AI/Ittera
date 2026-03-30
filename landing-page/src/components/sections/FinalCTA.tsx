"use client";

import { useState } from "react";
import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const EASE = [0.16, 1, 0.3, 1] as const;

const LINES = [
  "The creators who dominate tomorrow",
  "started their flywheel yesterday.",
];

const CUBIC: [number, number, number, number] = [0.16, 1, 0.3, 1];

const wordVariants = {
  hidden: { opacity: 0, y: 44, filter: "blur(10px)" },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.65, delay: i * 0.075, ease: CUBIC },
  }),
};

export default function FinalCTA() {
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [email, setEmail]       = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading]   = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes("@")) return;
    setLoading(true);
    setTimeout(() => { setLoading(false); setSubmitted(true); }, 1000);
  };

  const inputBg          = isDark ? "#1C1916" : "white";
  const inputBorder      = isDark ? "#2E2922" : "#EAEAEC";
  const inputColor       = isDark ? "#F2EDE8" : "#262626";
  const btnBg            = isDark ? "linear-gradient(135deg, #C4A882 0%, #A38A70 100%)" : "#0F172A";
  const btnColor         = isDark ? "#0C0B09" : "white";
  const footerColor      = isDark ? "rgba(242,237,232,0.45)" : "#a3a3a3";

  const line0 = LINES[0].split(" ");
  const line1 = LINES[1].split(" ");

  return (
    <section className={`relative py-16 sm:py-32 overflow-hidden ${isDark ? "bg-[#0C0B09]" : "bg-[#F9F8F6]"}`}>

      {/* --- Animated background orbs --- */}
      <motion.div
        className="absolute top-1/3 left-1/4 w-72 h-72 rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(163,138,112,0.08) 0%, transparent 70%)", filter: "blur(50px)" }}
        animate={{ x: [0, 22, -12, 0], y: [0, -18, 12, 0] }}
        transition={{ duration: 9, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-1/3 right-1/4 w-56 h-56 rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(122,139,118,0.06) 0%, transparent 70%)", filter: "blur(40px)" }}
        animate={{ x: [0, -16, 10, 0], y: [0, 14, -9, 0] }}
        transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute top-1/2 right-1/3 w-40 h-40 rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(163,138,112,0.05) 0%, transparent 70%)", filter: "blur(30px)" }}
        animate={{ x: [0, 12, -18, 0], y: [0, -10, 6, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* --- Shimmer top border --- */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-px pointer-events-none"
        style={{ background: "linear-gradient(90deg, transparent, rgba(163,138,112,0.25), rgba(122,139,118,0.15), transparent)" }}
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="relative z-10 max-w-3xl mx-auto px-6 lg:px-10 text-center">

        {/* --- Headline: word-by-word stagger --- */}
        <div className="mb-8">
          {/* Line 0 */}
          <div className="text-[26px] sm:text-[40px] lg:text-[62px] font-bold tracking-[-0.035em] leading-[1.1] flex flex-wrap justify-center gap-x-[0.22em] overflow-hidden">
            {line0.map((word, i) => (
              <motion.span
                key={i}
                custom={i}
                variants={shouldReduceMotion ? {} : wordVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className={isDark ? "text-neutral-100" : "text-neutral-900"}
              >
                {word}
              </motion.span>
            ))}
          </div>

          {/* Line 1 — brand color, continues the stagger index */}
          <div className="text-[26px] sm:text-[40px] lg:text-[62px] font-bold tracking-[-0.035em] leading-[1.1] flex flex-wrap justify-center gap-x-[0.22em] overflow-hidden">
            {line1.map((word, i) => (
              <motion.span
                key={i}
                custom={line0.length + i}
                variants={shouldReduceMotion ? {} : wordVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                style={{ color: isDark ? "#C4A882" : "#8B6F52" }}
              >
                {word}
              </motion.span>
            ))}
          </div>
        </div>

        {/* --- Body paragraph with blur-in --- */}
        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 14, filter: "blur(6px)" }}
          whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.55, ease: EASE }}
          className={`text-[16px] leading-[1.8] max-w-xl mx-auto mb-10 ${isDark ? "text-neutral-400" : "text-neutral-500"}`}
        >
          You&apos;re either building your content engine now, or watching others
          compound their audience while you figure out what to post.{" "}
          <motion.strong
            initial={shouldReduceMotion ? false : { opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 1.1 }}
            className={isDark ? "text-neutral-200 font-semibold" : "text-neutral-800 font-semibold"}
          >
            Don&apos;t wait.
          </motion.strong>
        </motion.p>

        {/* --- Form with spring entrance --- */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 28, scale: 0.96 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.65, delay: 0.7, ease: [0.34, 1.56, 0.64, 1] }}
          className="mb-5"
        >
          <AnimatePresence mode="wait">
            {submitted ? (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.88, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -6 }}
                transition={{ duration: 0.45, ease: EASE }}
                className="inline-flex items-center gap-3 px-6 py-3.5 rounded-xl text-[14px] font-medium text-[#8B6F52]"
                style={{ background: "rgba(163,138,112,0.08)", border: "1px solid rgba(163,138,112,0.25)" }}
              >
                <motion.span
                  className="w-2 h-2 rounded-full bg-[#A38A70]/80"
                  animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                  transition={{ duration: 1.4, repeat: Infinity }}
                />
                You&apos;re on the list. We&apos;ll be in touch.
              </motion.div>
            ) : (
              <motion.form
                key="form"
                onSubmit={handleSubmit}
                className="flex flex-col sm:flex-row gap-2.5 justify-center max-w-md mx-auto"
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <motion.input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="flex-1 h-12 px-4 rounded-lg text-[14px] outline-none transition-colors duration-200"
                  style={{ background: inputBg, border: `1px solid ${inputBorder}`, color: inputColor }}
                  whileFocus={{ scale: 1.015 }}
                  transition={{ duration: 0.2 }}
                  onFocus={(e) => { e.currentTarget.style.border = "1px solid rgba(163,138,112,0.55)"; }}
                  onBlur={(e)  => { e.currentTarget.style.border = `1px solid ${inputBorder}`; }}
                />
                <motion.button
                  type="submit"
                  disabled={loading || !email.includes("@")}
                  className="h-12 px-7 rounded-lg text-[14px] font-semibold flex items-center justify-center gap-2 whitespace-nowrap disabled:opacity-50"
                  style={{ background: btnBg, color: btnColor }}
                  whileHover={{ y: -2, scale: 1.03 }}
                  whileTap={{ scale: 0.96 }}
                  transition={{ duration: 0.18 }}
                >
                  {loading ? (
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : (
                    <>
                      Claim my spot
                      <motion.span
                        animate={{ x: [0, 4, 0] }}
                        transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
                      >
                        <ArrowRight className="w-4 h-4" />
                      </motion.span>
                    </>
                  )}
                </motion.button>
              </motion.form>
            )}
          </AnimatePresence>
        </motion.div>

        {/* --- Footer note --- */}
        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 6 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 1.0 }}
          className="text-[12px]"
          style={{ color: footerColor }}
        >
          No credit card. No spam. Just early access to the product we&apos;re building for you.
        </motion.p>

      </div>
    </section>
  );
}
