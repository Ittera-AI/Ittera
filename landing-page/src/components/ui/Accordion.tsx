"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Plus, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

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

  return (
    <div className={cn("space-y-3", className)}>
      {items.map((item, index) => (
        <div
          key={index}
          className="bg-white border-b border-[#EAEAEC] overflow-hidden"
        >
          <button
            onClick={() => setOpenIndex(openIndex === index ? null : index)}
            className="w-full flex items-center justify-between px-6 py-5 text-left hover:bg-[#F5F5F4] transition-colors"
            aria-expanded={openIndex === index}
          >
            <span
              className={cn(
                "text-base font-medium pr-4",
                openIndex === index ? "text-neutral-900" : "text-neutral-600"
              )}
            >
              {item.question}
            </span>
            <span
              className={cn(
                "flex-shrink-0 p-1.5 rounded-lg border transition-colors",
                openIndex === index
                  ? "bg-[#A38A70]/10 border-[#A38A70]/30"
                  : "bg-neutral-100 border-[#EAEAEC]"
              )}
            >
              {openIndex === index ? (
                <Minus
                  className={cn(
                    "w-4 h-4",
                    openIndex === index ? "text-[#A38A70]" : "text-neutral-400"
                  )}
                />
              ) : (
                <Plus className="w-4 h-4 text-neutral-400" />
              )}
            </span>
          </button>

          <AnimatePresence initial={false}>
            {openIndex === index && (
              <motion.div
                key="content"
                initial={shouldReduceMotion ? false : { height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={shouldReduceMotion ? undefined : { height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                style={{ overflow: "hidden" }}
              >
                <p className="px-6 pb-5 text-neutral-500 leading-relaxed">
                  {item.answer}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
}
