"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FAQ_ITEMS } from "@/lib/constants";
import { Plus } from "lucide-react";
const EASE = [0.16, 1, 0.3, 1] as const;

export default function FAQ() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="faq" className="py-24 bg-[#F9F8F6] relative">
      <div className="max-w-3xl mx-auto px-6 lg:px-10">
        <div className="mb-14">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: EASE }}
            className="flex items-center gap-2 mb-6"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">FAQ</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: EASE }}
            className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-neutral-900 mb-4"
          >
            Questions answered
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.14, ease: EASE }}
            className="text-[15px] text-neutral-500"
          >
            Can&apos;t find an answer?{" "}
            <a href="#" className="text-neutral-600 hover:text-neutral-800 underline underline-offset-2 transition-colors">
              Chat with us
            </a>
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1, ease: EASE }}
          className="divide-y divide-[#EAEAEC]"
        >
          {FAQ_ITEMS.map((item, i) => (
            <div
              key={i}
              className="py-5 transition-colors duration-200 hover:bg-[#F5F5F4] -mx-3 px-3 rounded-lg"
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between gap-4 text-left group"
              >
                <span
                  className={`text-[14.5px] font-medium transition-colors ${
                    open === i ? "text-neutral-900" : "text-neutral-700 group-hover:text-neutral-900"
                  }`}
                >
                  {item.question}
                </span>
                <div
                  className={`w-6 h-6 rounded-full border flex items-center justify-center flex-shrink-0 transition-all duration-200 ${
                    open === i
                      ? "border-[#A38A70]/30 bg-[#A38A70]/10"
                      : "bg-neutral-100 border-[#EAEAEC]"
                  }`}
                >
                  <motion.div animate={{ rotate: open === i ? 45 : 0 }} transition={{ duration: 0.2 }}>
                    <Plus
                      className={`w-3 h-3 transition-colors ${
                        open === i ? "text-[#A38A70]" : "text-neutral-400"
                      }`}
                    />
                  </motion.div>
                </div>
              </button>
              <AnimatePresence>
                {open === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25, ease: "easeInOut" }}
                    className="overflow-hidden"
                  >
                    <p className="pt-3 text-[13.5px] text-neutral-500 leading-relaxed max-w-xl">
                      {item.answer}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
