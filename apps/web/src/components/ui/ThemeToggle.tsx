"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "@/context/ThemeContext";

const STARS = [
  { top: "22%", left: "12%", size: 1.5, dur: 2.2 },
  { top: "65%", left: "22%", size: 1,   dur: 2.8 },
  { top: "38%", left: "35%", size: 1.2, dur: 1.9 },
];

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
      className="relative flex items-center w-[52px] h-7 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/50 cursor-pointer flex-shrink-0"
      style={{
        background: isDark
          ? "linear-gradient(135deg, #1A1410 0%, #0C0B09 100%)"
          : "linear-gradient(135deg, #EDE8E1 0%, #F9F8F6 100%)",
        border: isDark
          ? "1px solid rgba(196,168,130,0.18)"
          : "1px solid rgba(163,138,112,0.22)",
        boxShadow: isDark
          ? "0 2px 10px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04)"
          : "0 2px 8px rgba(0,0,0,0.07), inset 0 1px 0 rgba(255,255,255,0.9)",
        transition: "background 0.5s ease, border-color 0.5s ease, box-shadow 0.5s ease",
      }}
    >
      {/* Night stars inside the track */}
      <AnimatePresence>
        {isDark && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="absolute inset-0 rounded-full overflow-hidden pointer-events-none"
          >
            {STARS.map((s, i) => (
              <motion.span
                key={i}
                className="absolute rounded-full bg-white"
                style={{ top: s.top, left: s.left, width: s.size, height: s.size }}
                animate={{ opacity: [0.25, 0.85, 0.25] }}
                transition={{ duration: s.dur, repeat: Infinity, delay: i * 0.4, ease: "easeInOut" }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sliding orb */}
      <motion.div
        animate={{ x: isDark ? 26 : 2 }}
        transition={{ type: "spring", stiffness: 480, damping: 32 }}
        className="absolute w-[22px] h-[22px] rounded-full flex items-center justify-center"
        style={{
          background: isDark
            ? "linear-gradient(145deg, #D4B896 0%, #A38A70 100%)"
            : "linear-gradient(145deg, #FFE066 0%, #FFB830 100%)",
          boxShadow: isDark
            ? "0 2px 8px rgba(0,0,0,0.45), 0 0 14px rgba(196,168,130,0.28)"
            : "0 2px 8px rgba(0,0,0,0.14), 0 0 20px rgba(255,184,48,0.55)",
        }}
      >
        {/* Icon crossfade */}
        <AnimatePresence mode="wait" initial={false}>
          {isDark ? (
            <motion.svg
              key="moon"
              initial={{ opacity: 0, rotate: -40, scale: 0.6 }}
              animate={{ opacity: 1, rotate: 0, scale: 1 }}
              exit={{ opacity: 0, rotate: 40, scale: 0.6 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              width="12" height="12" viewBox="0 0 24 24" fill="none"
            >
              <path
                d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
                fill="#0C0B09"
                stroke="#0C0B09"
                strokeWidth="0.5"
              />
            </motion.svg>
          ) : (
            <motion.svg
              key="sun"
              initial={{ opacity: 0, rotate: 40, scale: 0.6 }}
              animate={{ opacity: 1, rotate: 0, scale: 1 }}
              exit={{ opacity: 0, rotate: -40, scale: 0.6 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              width="12" height="12" viewBox="0 0 24 24" fill="none"
            >
              <circle cx="12" cy="12" r="4.5" fill="white" />
              <path
                d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
                stroke="white"
                strokeWidth="1.75"
                strokeLinecap="round"
              />
            </motion.svg>
          )}
        </AnimatePresence>
      </motion.div>
    </button>
  );
}
