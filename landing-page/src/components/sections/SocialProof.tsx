"use client";

import { motion, useReducedMotion } from "framer-motion";

const EASE = [0.16, 1, 0.3, 1] as const;

const TESTIMONIALS = [
  {
    quote:
      "I went from spending 3 hours planning content every week to 20 minutes. The AI Coach's timing predictions alone have doubled my LinkedIn reach.",
    name: "Mia Chen",
    role: "Solo Creator · 84K followers",
    initials: "MC",
    accentFrom: "#A38A70",
    accentTo: "#0F172A",
    stars: 5,
  },
  {
    quote:
      "The Trend Radar is genuinely spooky-accurate. I posted about AI productivity tools 48 hours before it exploded — 4.2× my average engagement that week.",
    name: "James Okonkwo",
    role: "Founder · Building in public",
    initials: "JO",
    accentFrom: "#7A8B76",
    accentTo: "#A38A70",
    stars: 5,
  },
  {
    quote:
      "Ittera is the first tool that feels like it was built FOR creators, not adapted from a marketing dashboard. The repurposing engine alone is worth it.",
    name: "Sara Patel",
    role: "Content Strategist · Agency founder",
    initials: "SP",
    accentFrom: "#A38A70",
    accentTo: "#7A8B76",
    stars: 5,
  },
  {
    quote:
      "I was skeptical about AI coaching. Then it told me my Thursday 8AM posts outperform Friday posts by 3.1×. Checked my analytics — dead right. Mind blown.",
    name: "Raj Verma",
    role: "Developer Advocate · 120K on LinkedIn",
    initials: "RV",
    accentFrom: "#0F172A",
    accentTo: "#A38A70",
    stars: 5,
  },
  {
    quote:
      "Every other content tool is a scheduler pretending to be strategic. Ittera actually thinks about your audience so you can focus on the creative work.",
    name: "Leila Nasser",
    role: "Newsletter writer · 48K subscribers",
    initials: "LN",
    accentFrom: "#7A8B76",
    accentTo: "#0F172A",
    stars: 5,
  },
];

const STATS = [
  { value: "12+", label: "Creators on the waitlist" },
  { value: "48h", label: "Early trend signal window" },
  { value: "12h", label: "Saved per creator / week" },
  { value: "3.4×", label: "Avg engagement uplift" },
];

export default function SocialProof() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section className="py-20 relative overflow-hidden bg-[#F9F8F6]">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "linear-gradient(180deg, transparent, rgba(163,138,112,0.04) 50%, transparent)" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, ease: EASE }}
          className="flex items-center justify-center gap-4 mb-12"
        >
          <div className="h-px flex-1 max-w-[80px]" style={{ background: "linear-gradient(90deg, transparent, rgba(0,0,0,0.06))" }} />
          <span className="text-[11px] font-semibold tracking-[0.16em] uppercase text-neutral-400">
            From our beta community
          </span>
          <div className="h-px flex-1 max-w-[80px]" style={{ background: "linear-gradient(90deg, rgba(0,0,0,0.06), transparent)" }} />
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {TESTIMONIALS.map((t, i) => (
            <motion.div
              key={t.name}
              initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.07, ease: EASE }}
              className={`group relative p-6 rounded-2xl border border-[#EAEAEC] bg-white hover:border-[#D4D4D4] transition-all duration-300 ${i === 4 ? "md:col-span-2 lg:col-span-1" : ""}`}
              style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
            >
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                style={{ background: "radial-gradient(260px at 20% 20%, rgba(163,138,112,0.04), transparent)" }}
              />

              <div className="relative z-10">
                <div className="flex gap-0.5 mb-4">
                  {[...Array(t.stars)].map((_, s) => (
                    <svg key={s} width="11" height="11" viewBox="0 0 10 10">
                      <path
                        d="M5 1L6.2 3.8L9 4.4L7 6.3L7.5 9L5 7.6L2.5 9L3 6.3L1 4.4L3.8 3.8L5 1Z"
                        fill="#A38A70"
                        fillOpacity="0.85"
                      />
                    </svg>
                  ))}
                </div>

                <p className="text-[13.5px] text-neutral-600 leading-[1.75] mb-5">
                  &ldquo;{t.quote}&rdquo;
                </p>

                <div className="flex items-center gap-3">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0"
                    style={{
                      background: `linear-gradient(135deg, ${t.accentFrom}4D, ${t.accentTo}33)`,
                      border: `1px solid ${t.accentFrom}22`,
                    }}
                  >
                    {t.initials}
                  </div>
                  <div>
                    <div className="text-[13px] font-semibold text-neutral-900">{t.name}</div>
                    <div className="text-[11px] text-neutral-400">{t.role}</div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3, ease: EASE }}
          className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-8 pt-10"
          style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}
        >
          {STATS.map((stat) => (
            <div key={stat.label} className="text-center md:text-left">
              <div
                className="text-[32px] sm:text-[38px] font-bold tracking-[-0.03em] leading-none mb-1.5"
                style={{
                  background: "linear-gradient(135deg, #171717 0%, rgba(23,23,23,0.6) 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {stat.value}
              </div>
              <div className="text-[13px] text-neutral-400">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
