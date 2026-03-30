"use client";

import { Twitter, Linkedin, Github, Youtube } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const FOOTER_LINKS = {
  Product: [
    { label: "Features", href: "#features" },
    { label: "How it works", href: "#how-it-works" },
    { label: "Pricing", href: "#pricing" },
    { label: "Changelog", href: "#" },
    { label: "Roadmap", href: "#" },
  ],
  Company: [
    { label: "About", href: "#" },
    { label: "Blog", href: "#" },
    { label: "Careers", href: "#" },
    { label: "Press", href: "#" },
    { label: "Contact", href: "#" },
  ],
  Legal: [
    { label: "Privacy", href: "#" },
    { label: "Terms", href: "#" },
    { label: "Cookies", href: "#" },
    { label: "Security", href: "#" },
  ],
};

const SOCIAL_LINKS = [
  { icon: Twitter,  label: "Twitter",  href: "#" },
  { icon: Linkedin, label: "LinkedIn", href: "#" },
  { icon: Github,   label: "GitHub",   href: "#" },
  { icon: Youtube,  label: "YouTube",  href: "#" },
];

export default function Footer() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const footerBg      = isDark ? "#0C0B09" : "#F9F8F6";
  const borderColor   = isDark ? "#2E2922" : "#EAEAEC";
  const brandColor    = isDark ? "#F2EDE8" : "#262626";
  const descColor     = isDark ? "rgba(242,237,232,0.45)" : "#737373";
  const socialBg      = isDark ? "#141210" : "white";
  const socialColor   = isDark ? "rgba(242,237,232,0.4)" : "#737373";
  const socialBgH     = isDark ? "#1C1916" : "#F5F5F4";
  const socialBorderH = isDark ? "#3D3730" : "#D4D4D4";
  const socialColorH  = isDark ? "#F2EDE8" : "#171717";
  const catColor      = isDark ? "rgba(242,237,232,0.28)" : "#a3a3a3";
  const linkColor     = isDark ? "rgba(242,237,232,0.4)" : "#a3a3a3";
  const linkColorH    = isDark ? "#F2EDE8" : "#404040";
  const copyColor     = isDark ? "rgba(242,237,232,0.22)" : "#D4D4D4";
  const taglineColor  = isDark ? "rgba(242,237,232,0.16)" : "#E5E5E5";

  return (
    <footer style={{ background: footerBg, borderTop: `1px solid ${borderColor}` }}>
      <div className="max-w-7xl mx-auto px-6 lg:px-10 py-10 sm:py-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-8 sm:gap-10 lg:gap-12">
          {/* Brand */}
          <div className="col-span-2">
            <a href="/" className="flex items-center gap-2.5 mb-4">
              <svg width="20" height="20" viewBox="0 0 22 22" fill="none" aria-hidden="true">
                <path d="M11 2L13.5 8.5L20 11L13.5 13.5L11 20L8.5 13.5L2 11L8.5 8.5L11 2Z" fill="url(#footer-logo-grad)" />
                <defs>
                  <linearGradient id="footer-logo-grad" x1="2" y1="2" x2="20" y2="20" gradientUnits="userSpaceOnUse">
                    <stop stopColor={isDark ? "#C4A882" : "#0F172A"} />
                    <stop offset="1" stopColor="#A38A70" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="text-[15px] font-semibold tracking-tight" style={{ color: brandColor }}>Ittera</span>
            </a>
            <p className="text-[13px] leading-[1.75] max-w-xs mb-6" style={{ color: descColor }}>
              The AI content strategy engine for creators, founders, and marketers who play to win.
            </p>
            <div className="flex items-center gap-2.5">
              {SOCIAL_LINKS.map(({ icon: Icon, label, href }) => (
                <a
                  key={label}
                  href={href}
                  aria-label={label}
                  className="w-10 h-10 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center transition-all duration-200"
                  style={{ background: socialBg, border: `1px solid ${borderColor}`, color: socialColor }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLAnchorElement).style.background = socialBgH;
                    (e.currentTarget as HTMLAnchorElement).style.borderColor = socialBorderH;
                    (e.currentTarget as HTMLAnchorElement).style.color = socialColorH;
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLAnchorElement).style.background = socialBg;
                    (e.currentTarget as HTMLAnchorElement).style.borderColor = borderColor;
                    (e.currentTarget as HTMLAnchorElement).style.color = socialColor;
                  }}
                >
                  <Icon className="w-3.5 h-3.5" />
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.entries(FOOTER_LINKS).map(([category, links]) => (
            <div key={category}>
              <h3 className="text-[12px] font-semibold mb-4 tracking-wide uppercase" style={{ color: catColor }}>
                {category}
              </h3>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-[13px] transition-all duration-200"
                      style={{ color: linkColor }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = linkColorH; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = linkColor; }}
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 pt-7 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
          style={{ borderTop: `1px solid ${borderColor}` }}>
          <p className="text-[12px]" style={{ color: copyColor }}>
            © {new Date().getFullYear()} Ittera, Inc. All rights reserved.
          </p>
          <p className="text-[12px]" style={{ color: taglineColor }}>
            Built for creators who compound.
          </p>
        </div>
      </div>
    </footer>
  );
}
