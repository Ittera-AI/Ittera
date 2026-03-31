"use client";

import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import { Github, Linkedin } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const EASE = [0.16, 1, 0.3, 1] as const;

const founders = [
  {
    name: "Ujjawal Anand",
    role: "Co-Founder",
    bio: "Building the AI and growth engine behind Ittera so creators can turn audience signal into repeatable momentum.",
    avatar: "UA",
    photo: "/founders/ujjawal.png",
    tags: ["AI Strategy", "Growth", "Engineering"],
    gradientFrom: "#0F172A",
    gradientTo: "#A38A70",
    accentColor: "#A38A70",
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
    photo: "/founders/kshitij.png",
    tags: ["Product", "ML/AI", "Strategy"],
    gradientFrom: "#7A8B76",
    gradientTo: "#0F172A",
    accentColor: "#7A8B76",
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
    photo: "/founders/suvansh.jpeg",
    tags: ["Systems", "Design", "Architecture"],
    gradientFrom: "#A38A70",
    gradientTo: "#7A8B76",
    accentColor: "#C4A882",
    social: {
      github: "https://github.com/Suvichan2005",
      linkedin: "https://www.linkedin.com/in/suvanshagarwal/",
    },
  },
];

const CUBIC_EASE: [number, number, number, number] = [0.16, 1, 0.3, 1];
const CUBIC_SPRING: [number, number, number, number] = [0.34, 1.56, 0.64, 1];

const wordVariants = {
  hidden: { opacity: 0, y: 36, filter: "blur(8px)" },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.6, delay: i * 0.07, ease: CUBIC_EASE },
  }),
};

const cardVariants = {
  hidden: { opacity: 0, y: 28, scale: 0.97 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.6, delay: 0.2 + i * 0.1, ease: CUBIC_EASE },
  }),
};

const tagVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: (i: number) => ({
    opacity: 1,
    scale: 1,
    transition: { duration: 0.3, delay: i * 0.06, ease: CUBIC_EASE },
  }),
};

export default function Founders() {
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const sectionBg   = isDark ? "#0C0B09" : "#F9F8F6";
  const cardBg      = isDark ? "#141210" : "white";
  const cardBorder  = isDark ? "#2E2922" : "#EAEAEC";
  const headingColor= isDark ? "#F2EDE8" : "#171717";
  const titleColor  = isDark ? "#F2EDE8" : "#171717";
  const bioColor    = isDark ? "rgba(242,237,232,0.5)" : "#737373";
  const tagBg       = isDark ? "rgba(196,168,130,0.08)" : "rgba(163,138,112,0.06)";
  const tagBorder   = isDark ? "rgba(196,168,130,0.18)" : "rgba(163,138,112,0.15)";
  const tagColor    = isDark ? "rgba(242,237,232,0.55)" : "#737373";
  const socialBg    = isDark ? "#1C1916" : "#F9F8F6";
  const socialBorder= isDark ? "#2E2922" : "#EAEAEC";
  const socialBgH   = isDark ? "#242019" : "#F5F5F4";
  const socialBorderH = isDark ? "#3D3730" : "#D4D4D4";
  const socialColor = isDark ? "rgba(242,237,232,0.4)" : "#a3a3a3";
  const socialColorH= isDark ? "#F2EDE8" : "#171717";

  const titleWords = "Built by people who".split(" ");

  return (
    <section
      id="team"
      className="relative py-12 sm:py-24 overflow-hidden"
      style={{ background: sectionBg }}
    >
      {/* Background orbs */}
      <motion.div
        className="absolute bottom-[-10%] left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full pointer-events-none"
        style={{ background: `radial-gradient(ellipse at bottom, ${isDark ? "rgba(163,138,112,0.14)" : "rgba(163,138,112,0.08)"} 0%, transparent 70%)` }}
        animate={shouldReduceMotion ? undefined : { scale: [1, 1.1, 1], opacity: [0.7, 1, 0.7] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute top-[-5%] right-[-5%] w-96 h-96 rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(122,139,118,0.1) 0%, transparent 70%)" }}
        animate={shouldReduceMotion ? undefined : { x: [0, -30, 0], y: [0, 40, 0] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Shimmer top border */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-px pointer-events-none"
        style={{ background: "linear-gradient(90deg, transparent, rgba(163,138,112,0.2), rgba(122,139,118,0.12), transparent)" }}
        animate={shouldReduceMotion ? undefined : { opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="relative z-10 max-w-6xl mx-auto px-6 lg:px-10 text-center">

        {/* ── Header ── */}
        <div className="max-w-2xl mx-auto mb-16">

          {/* Title — word stagger */}
          <h2 className="text-[28px] sm:text-[42px] lg:text-[52px] font-bold tracking-[-0.03em] leading-[1.08] mb-4 flex flex-wrap justify-center gap-x-[0.22em]">
            {titleWords.map((word, i) => (
              <motion.span
                key={i}
                custom={i}
                variants={shouldReduceMotion ? {} : wordVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                style={{ color: headingColor }}
              >
                {word}
              </motion.span>
            ))}
            <motion.span
              custom={titleWords.length}
              variants={shouldReduceMotion ? {} : wordVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              style={{ color: isDark ? "#C4A882" : "#8B6F52" }}
            >
              get&nbsp;it.
            </motion.span>
          </h2>

          {/* Subtitle */}
          <motion.p
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10, filter: "blur(4px)" }}
            whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.28, ease: EASE }}
            className="text-[15px] leading-[1.75]"
            style={{ color: isDark ? "rgba(242,237,232,0.5)" : "#737373" }}
          >
            We&apos;ve been creators, built creator tools, and scaled creator platforms.
            Ittera is the product we always wanted.
          </motion.p>
        </div>

        {/* ── Cards ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {founders.map((founder, i) => (
            <motion.div
              key={founder.name}
              custom={i}
              variants={shouldReduceMotion ? {} : cardVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-40px" }}
              className="group relative p-7 rounded-2xl overflow-hidden text-left"
              style={{
                background: cardBg,
                border: `1px solid ${cardBorder}`,
                boxShadow: isDark ? "0 1px 3px rgba(0,0,0,0.3)" : "0 1px 3px rgba(0,0,0,0.06)",
              }}
              whileHover={{
                y: -8,
                scale: 1.015,
                boxShadow: isDark
                  ? "0 28px 55px -18px rgba(0,0,0,0.55), 0 10px 24px -12px rgba(196,168,130,0.18)"
                  : "0 28px 55px -18px rgba(15,23,42,0.13), 0 10px 24px -12px rgba(163,138,112,0.2)",
              }}
              transition={{ duration: 0.25 }}
            >
              {/* Hover glow */}
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                style={{
                  background: isDark
                    ? `radial-gradient(320px at 50% 0%, rgba(196,168,130,0.08), transparent)`
                    : `radial-gradient(320px at 50% 0%, rgba(163,138,112,0.09), transparent)`,
                }}
              />

              <div className="relative z-10">
                {/* Avatar */}
                <motion.div
                  className="w-14 h-14 rounded-2xl overflow-hidden mb-5 flex-shrink-0"
                  style={{ border: `1px solid ${cardBorder}` }}
                  whileHover={{ scale: 1.08, rotate: 2 }}
                  transition={{ duration: 0.25 }}
                >
                  <Image
                    src={founder.photo}
                    alt={founder.name}
                    width={56}
                    height={56}
                    className="w-full h-full object-cover object-top"
                  />
                </motion.div>

                {/* Name + role */}
                <h3
                  className="text-[16px] font-semibold tracking-tight mb-0.5"
                  style={{ color: titleColor }}
                >
                  {founder.name}
                </h3>
                <p
                  className="text-[12px] font-medium mb-4"
                  style={{ color: founder.accentColor }}
                >
                  {founder.role}
                </p>

                {/* Bio */}
                <p
                  className="text-[13px] leading-relaxed mb-5"
                  style={{ color: bioColor }}
                >
                  {founder.bio}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5 mb-5">
                  {founder.tags.map((tag, ti) => (
                    <motion.span
                      key={tag}
                      custom={ti}
                      variants={shouldReduceMotion ? {} : tagVariants}
                      initial="hidden"
                      whileInView="visible"
                      viewport={{ once: true }}
                      className="text-[10.5px] px-2.5 py-1 rounded-full"
                      style={{ background: tagBg, border: `1px solid ${tagBorder}`, color: tagColor }}
                    >
                      {tag}
                    </motion.span>
                  ))}
                </div>

                {/* Social icons */}
                <div className="flex items-center gap-2">
                  {[
                    { href: founder.social.github,   label: `${founder.name} on GitHub`,   Icon: Github },
                    { href: founder.social.linkedin, label: `${founder.name} on LinkedIn`, Icon: Linkedin },
                  ].map(({ href, label, Icon }) => (
                    <motion.a
                      key={label}
                      href={href}
                      target="_blank"
                      rel="noreferrer"
                      aria-label={label}
                      className="w-10 h-10 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center transition-colors duration-200"
                      style={{ background: socialBg, border: `1px solid ${socialBorder}`, color: socialColor }}
                      whileHover={{ scale: 1.15, y: -1 }}
                      whileTap={{ scale: 0.92 }}
                      transition={{ duration: 0.18 }}
                      onMouseEnter={(e) => {
                        const el = e.currentTarget as HTMLAnchorElement;
                        el.style.background    = socialBgH;
                        el.style.borderColor   = socialBorderH;
                        el.style.color         = socialColorH;
                      }}
                      onMouseLeave={(e) => {
                        const el = e.currentTarget as HTMLAnchorElement;
                        el.style.background    = socialBg;
                        el.style.borderColor   = socialBorder;
                        el.style.color         = socialColor;
                      }}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </motion.a>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
