"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Twitter, Linkedin } from "lucide-react";

const FOUNDERS = [
  {
    name: "Alex Morgan",
    role: "Co-founder & CEO",
    bio: "Ex-growth lead at a Series B creator platform. Spent 6 years helping creators grow audiences from 0 to 1M+. Obsessed with the intersection of AI and authentic content.",
    initials: "AM",
    gradientFrom: "#6c47ff",
    gradientTo: "#4f32d4",
    twitter: "#",
    linkedin: "#",
    tags: ["Creator Growth", "AI Strategy", "Product"],
  },
  {
    name: "Priya Sharma",
    role: "Co-founder & CTO",
    bio: "Former ML engineer at a top AI lab. Built recommendation systems used by 50M+ users. Now applying that expertise to content strategy — making enterprise-grade AI accessible to every creator.",
    initials: "PS",
    gradientFrom: "#00a8cc",
    gradientTo: "#0066aa",
    twitter: "#",
    linkedin: "#",
    tags: ["Machine Learning", "Infra", "Recommendations"],
  },
  {
    name: "Jordan Kim",
    role: "Co-founder & CPO",
    bio: "Previously led product at two content tools acquired by major platforms. Has shipped 20+ features used by professional creators daily. Believes great UX is the ultimate unfair advantage.",
    initials: "JK",
    gradientFrom: "#f59e0b",
    gradientTo: "#d97706",
    twitter: "#",
    linkedin: "#",
    tags: ["Product Design", "UX", "Creator Tools"],
  },
];

export default function Founders() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="team" className="py-24 relative overflow-hidden">
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse at bottom, rgba(108,71,255,0.06) 0%, transparent 60%)" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">
        <div className="max-w-xl mb-14">
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="flex items-center gap-2 mb-6"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-violet-400/70" />
            <span className="eyebrow">Team</span>
          </motion.div>

          <motion.h2
            initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: "easeOut" }}
            className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-white mb-4"
          >
            Built by people who{" "}
            <span className="gradient-text">get it.</span>
          </motion.h2>

          <motion.p
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.14, ease: "easeOut" }}
            className="text-[15px] text-white/38 leading-[1.75]"
          >
            We&apos;ve been creators, built creator tools, and scaled creator platforms. Ittera is the product we always wanted.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {FOUNDERS.map((founder, i) => (
            <motion.div
              key={founder.name}
              initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.1, ease: "easeOut" }}
              className="group relative p-7 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:border-white/[0.1] transition-all duration-300 overflow-hidden"
            >
              {/* Hover glow */}
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                style={{ background: `radial-gradient(300px circle at 50% 0%, ${founder.gradientFrom}0a, transparent)` }}
              />

              <div className="relative z-10">
                {/* Avatar */}
                <div className="mb-5">
                  <div
                    className="w-14 h-14 rounded-2xl flex items-center justify-center text-[18px] font-bold text-white/90 mb-1"
                    style={{ background: `linear-gradient(135deg, ${founder.gradientFrom}, ${founder.gradientTo})` }}
                  >
                    {founder.initials}
                  </div>
                </div>

                {/* Name & role */}
                <h3 className="text-[16px] font-semibold text-white/85 tracking-tight mb-0.5">{founder.name}</h3>
                <p
                  className="text-[12px] font-medium mb-4"
                  style={{ color: founder.gradientFrom + "bb" }}
                >
                  {founder.role}
                </p>

                {/* Bio */}
                <p className="text-[13px] text-white/38 leading-[1.75] mb-5">{founder.bio}</p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5 mb-5">
                  {founder.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-[10.5px] px-2.5 py-1 rounded-full border text-white/30"
                      style={{ background: `${founder.gradientFrom}0d`, borderColor: `${founder.gradientFrom}22` }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Social */}
                <div className="flex items-center gap-2">
                  <a
                    href={founder.twitter}
                    aria-label={`${founder.name} on Twitter`}
                    className="w-8 h-8 rounded-lg border border-white/[0.06] bg-white/[0.03] flex items-center justify-center text-white/25 hover:text-white/55 hover:border-white/[0.12] transition-all duration-200"
                  >
                    <Twitter className="w-3.5 h-3.5" />
                  </a>
                  <a
                    href={founder.linkedin}
                    aria-label={`${founder.name} on LinkedIn`}
                    className="w-8 h-8 rounded-lg border border-white/[0.06] bg-white/[0.03] flex items-center justify-center text-white/25 hover:text-white/55 hover:border-white/[0.12] transition-all duration-200"
                  >
                    <Linkedin className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
