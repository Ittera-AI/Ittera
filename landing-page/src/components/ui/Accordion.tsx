"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Plus, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/context/ThemeContext";

interface AccordionItem {
  question: string;
  answer: string;
}

interface AccordionProps {
  items: AccordionItem[];
  className?: string;
}

export default function Accordion({ items, className }: AccordionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const bg      = isDark ? "#141210" : "white";
  const border  = isDark ? "#2E2922" : "#EAEAEC";
  const hover   = isDark ? "#1C1916" : "#F5F5F4";
  const textQ   = isDark ? "#F2EDE8" : undefined;
  const textQM  = isDark ? "rgba(242,237,232,0.65)" : undefined;
  const textA   = isDark ? "rgba(242,237,232,0.5)" : undefined;
  const iconBorder = isDark ? "#3D3730" : "rgba(163,138,112,0.3)";
  const iconBgN = isDark ? "#1C1916" : undefined;

  return (
    <div className={cn("space-y-3", className)}>
      {items.map((item, index) => {
        const isOpen = openIndex === index;
        return (
          <div
            key={index}
            className="overflow-hidden transition-colors duration-300"
            style={{ background: bg, borderBottom: `1px solid ${border}` }}
          >
            <button
              onClick={() => setOpenIndex(isOpen ? null : index)}
              className="w-full flex items-center justify-between px-6 py-5 text-left transition-colors duration-200"
              style={{ background: "transparent" }}
              aria-expanded={isOpen}
              onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = hover; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "transparent"; }}
            >
              <span
                className={cn("text-base font-medium pr-4")}
                style={{ color: isOpen ? (textQ ?? "#171717") : (textQM ?? "#525252") }}
              >
                {item.question}
              </span>
              <span
                className="flex-shrink-0 p-1.5 rounded-lg border transition-colors"
                style={isOpen
                  ? { background: "rgba(163,138,112,0.1)", borderColor: iconBorder }
                  : { background: iconBgN ?? "#F5F5F4", borderColor: border }}
              >
                {isOpen ? (
                  <Minus className="w-4 h-4" style={{ color: "#A38A70" }} />
                ) : (
                  <Plus className="w-4 h-4" style={{ color: isDark ? "rgba(242,237,232,0.3)" : "#a3a3a3" }} />
                )}
              </span>
            </button>

            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  key="content"
                  initial={shouldReduceMotion ? false : { height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={shouldReduceMotion ? undefined : { height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  style={{ overflow: "hidden" }}
                >
                  <p
                    className="px-6 pb-5 leading-relaxed text-[14px]"
                    style={{ color: textA ?? "#737373" }}
                  >
                    {item.answer}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}
