"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Github, Linkedin } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const founders = [
  {
    name: "Ujjawal Anand",
    role: "Co-Founder",
    bio: "Building the AI and growth engine behind Ittera so creators can turn audience signal into repeatable momentum.",
    avatar: "UA",
    tags: ["AI Strategy", "Growth", "Engineering"],
    gradientFrom: "#0F172A",
    gradientTo: "#A38A70",
    social: {
      github: "https://github.com/anand-official",
      linkedin: "https://www.linkedin.com/in/ujjawalanandofficial/",
    },
  },
  {
    name: "Kshitij Singh",
    role: "Co-Founder",
    bio: "Architecting the product and intelligence layer that powers Ittera's real-time content analytics and trend detection.",
    avatar: "KS",
    tags: ["Product", "ML/AI", "Strategy"],
    gradientFrom: "#7A8B76",
    gradientTo: "#0F172A",
    social: {
      github: "https://github.com/Kshitij-KS",
      linkedin: "https://www.linkedin.com/in/kshitij-singh-ks/",
    },
  },
  {
    name: "Suvansh Agarwal",
    role: "Co-Founder",
    bio: "Building the technical systems that make Ittera's content intelligence reliable, fast, and easy to scale.",
    avatar: "SA",
    tags: ["Systems", "Design", "Architecture"],
    gradientFrom: "#A38A70",
    gradientTo: "#7A8B76",
    social: {
      github: "https://github.com/Suvichan2005",
      linkedin: "https://www.linkedin.com/in/suvanshagarwal/",
    },
  },
];

export default function Founders() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="team" className="py-24 bg-[#F9F8F6] relative overflow-hidden">
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse at bottom, rgba(163,138,112,0.04) 0%, transparent 60%)" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10">
        <div className="max-w-xl mb-14">
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: EASE }}
            className="flex items-center gap-2 mb-6"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">Team</span>
          </motion.div>

          <motion.h2
            initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.07, ease: EASE }}
            className="text-[42px] sm:text-[52px] font-bold tracking-[-0.03em] leading-[1.06] text-neutral-900 mb-4"
          >
            Built by people who <span className="gradient-text">get it.</span>
          </motion.h2>

          <motion.p
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.14, ease: EASE }}
            className="text-[15px] text-neutral-500 leading-[1.75]"
          >
            We&apos;ve been creators, built creator tools, and scaled creator platforms. Ittera is the product we always wanted.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {founders.map((founder, i) => (
            <motion.div
              key={founder.name}
              initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.1, ease: EASE }}
              className="group relative p-7 rounded-2xl transition-all duration-300 overflow-hidden"
              style={{
                background: "white",
                border: "1px solid #EAEAEC",
                boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
              }}
              whileHover={{
                y: -6,
                scale: 1.01,
                borderColor: "#D4D4D4",
                boxShadow: "0 24px 50px -18px rgba(15,23,42,0.12), 0 10px 24px -12px rgba(163,138,112,0.18)",
              }}
            >
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                style={{ background: "radial-gradient(300px at 50% 0%, rgba(163,138,112,0.08), transparent)" }}
              />

              <div className="relative z-10">
                <div className="mb-5">
                  <div
                    className="w-14 h-14 rounded-2xl flex items-center justify-center text-[18px] font-bold text-white mb-1"
                    style={{ background: `linear-gradient(135deg, ${founder.gradientFrom}, ${founder.gradientTo})` }}
                  >
                    {founder.avatar}
                  </div>
                </div>

                <h3 className="text-[16px] font-semibold text-neutral-900 tracking-tight mb-0.5">{founder.name}</h3>
                <p className="text-[12px] font-medium mb-4" style={{ color: founder.gradientFrom + "BF" }}>
                  {founder.role}
                </p>

                <p className="text-[13px] text-neutral-500 leading-relaxed mb-5">{founder.bio}</p>

                <div className="flex flex-wrap gap-1.5 mb-5">
                  {founder.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-[10.5px] px-2.5 py-1 rounded-full text-neutral-500"
                      style={{ background: "rgba(163,138,112,0.06)", border: "1px solid rgba(163,138,112,0.15)" }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  <a
                    href={founder.social.github}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`${founder.name} on GitHub`}
                    className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 text-neutral-400 hover:text-neutral-700"
                    style={{ background: "#F9F8F6", border: "1px solid #EAEAEC" }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "#F5F5F4";
                      e.currentTarget.style.borderColor = "#D4D4D4";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "#F9F8F6";
                      e.currentTarget.style.borderColor = "#EAEAEC";
                    }}
                  >
                    <Github className="w-3.5 h-3.5" />
                  </a>
                  <a
                    href={founder.social.linkedin}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`${founder.name} on LinkedIn`}
                    className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 text-neutral-400 hover:text-neutral-700"
                    style={{ background: "#F9F8F6", border: "1px solid #EAEAEC" }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "#F5F5F4";
                      e.currentTarget.style.borderColor = "#D4D4D4";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "#F9F8F6";
                      e.currentTarget.style.borderColor = "#EAEAEC";
                    }}
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
