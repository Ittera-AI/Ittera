"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, LogOut, ChevronDown } from "lucide-react";
import { NAV_LINKS } from "@/lib/constants";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import ThemeToggle from "@/components/ui/ThemeToggle";

export default function Navbar() {
  const { user, openAuth, signOut } = useAuth();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("");
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Navbar blur on scroll
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Active section via IntersectionObserver — reliable, no scroll event needed
  useEffect(() => {
    const sectionIds = NAV_LINKS
      .filter((l) => l.href.startsWith("#"))
      .map((l) => l.href.slice(1));

    const visible = new Set<string>();

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            visible.add(entry.target.id);
          } else {
            visible.delete(entry.target.id);
          }
        });
        // Pick the topmost visible section (first in page order)
        setActiveSection(sectionIds.find((id) => visible.has(id)) ?? "");
      },
      // Active zone: from 64px below top (below navbar) to 45% up from bottom
      { rootMargin: "-64px 0px -45% 0px", threshold: 0 }
    );

    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  // Close user menu on outside click
  useEffect(() => {
    if (!userMenuOpen) return;
    const h = () => setUserMenuOpen(false);
    window.addEventListener("click", h);
    return () => window.removeEventListener("click", h);
  }, [userMenuOpen]);

  // Derived theme tokens
  const navBg = scrolled
    ? isDark
      ? "rgba(12,11,9,0.92)"
      : "rgba(249,248,246,0.92)"
    : "rgba(0,0,0,0)";

  const navBorder = scrolled
    ? isDark ? "#2E2922" : "#EAEAEC"
    : "transparent";

  const linkActive   = isDark ? "#F2EDE8"              : "#171717";
  const linkMuted    = isDark ? "rgba(242,237,232,0.4)" : "rgba(23,23,23,0.45)";
  const linkHover    = isDark ? "rgba(242,237,232,0.8)" : "rgba(23,23,23,0.8)";

  const userBtnBg    = isDark ? "#1C1916"  : "white";
  const userBtnBorder= isDark ? "#2E2922"  : "#EAEAEC";
  const userBtnHover = isDark ? "#242019"  : "#F5F5F4";
  const userBtnBorderHover = isDark ? "#3D3730" : "#D4D4D4";

  const dropdownBg   = isDark ? "#1C1916"  : "white";
  const dropdownBorder=isDark ? "#2E2922"  : "#EAEAEC";

  const drawerBg     = isDark
    ? "rgba(12,11,9,0.98)"
    : "rgba(249,248,246,0.98)";

  const joinWaitlistBg = isDark
    ? "linear-gradient(135deg, #C4A882 0%, #A38A70 100%)"
    : "#0F172A";
  const joinWaitlistColor = isDark ? "#0C0B09" : "white";

  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-50"
        style={{
          background: navBg,
          backdropFilter: scrolled ? "blur(20px) saturate(150%)" : "none",
          borderBottom: `1px solid ${navBorder}`,
          transition: "background 0.5s cubic-bezier(0.16,1,0.3,1), border-color 0.5s cubic-bezier(0.16,1,0.3,1), backdrop-filter 0.5s cubic-bezier(0.16,1,0.3,1)",
        }}
      >
        <nav className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="flex items-center justify-between h-16">

            {/* Logo */}
            <Link href="/" className="flex items-center gap-2.5 group flex-shrink-0">
              <div className="relative">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L14.5 9L21 12L14.5 15L12 22L9.5 15L3 12L9.5 9L12 2Z" fill="url(#nav-grad)" />
                  <defs>
                    <linearGradient id="nav-grad" x1="3" y1="2" x2="21" y2="22" gradientUnits="userSpaceOnUse">
                      <stop stopColor={isDark ? "#C4A882" : "#0F172A"} />
                      <stop offset="1" stopColor="#A38A70" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <span
                className="text-[15px] font-semibold tracking-tight transition-colors"
                style={{ color: isDark ? "#F2EDE8" : "#171717" }}
              >
                Ittera
              </span>
            </Link>

            {/* Desktop nav links */}
            <div className="hidden md:flex items-center gap-1">
              {NAV_LINKS.map((link) => {
                const isPageLink = !link.href.startsWith("#");
                const isActive = !isPageLink && activeSection === link.href.slice(1);
                const sharedProps = {
                  className: "relative px-3 py-1.5 text-[13px] font-medium transition-colors duration-200 rounded-lg",
                  style: { color: isActive ? linkActive : linkMuted } as React.CSSProperties,
                  onMouseEnter: (e: React.MouseEvent<HTMLElement>) => { if (!isActive) (e.currentTarget as HTMLElement).style.color = linkHover; },
                  onMouseLeave: (e: React.MouseEvent<HTMLElement>) => { if (!isActive) (e.currentTarget as HTMLElement).style.color = linkMuted; },
                };
                const inner = (
                  <>
                    {isActive && (
                      <motion.div
                        layoutId="nav-active"
                        className="absolute inset-0 rounded-lg"
                        style={{
                          background: isDark ? "rgba(196,168,130,0.1)" : "rgba(163,138,112,0.08)",
                          border: `1px solid ${isDark ? "rgba(196,168,130,0.22)" : "rgba(163,138,112,0.2)"}`,
                        }}
                        transition={{ type: "spring", bounce: 0.25, duration: 0.4 }}
                      />
                    )}
                    <span className="relative z-10">{link.label}</span>
                  </>
                );
                return isPageLink
                  ? <Link key={link.href} href={link.href} {...sharedProps}>{inner}</Link>
                  : <a key={link.href} href={link.href} {...sharedProps}>{inner}</a>;
              })}
            </div>

            {/* Desktop CTAs + Theme Toggle */}
            <div className="hidden md:flex items-center gap-2.5">
              {/* Artistic theme toggle */}
              <ThemeToggle />

              {user ? (
                /* Logged-in user avatar + dropdown */
                <div className="relative" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => setUserMenuOpen((v) => !v)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-xl transition-all duration-200"
                    style={{
                      border: `1px solid ${userBtnBorder}`,
                      background: userBtnBg,
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.background = userBtnHover;
                      (e.currentTarget as HTMLButtonElement).style.borderColor = userBtnBorderHover;
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.background = userBtnBg;
                      (e.currentTarget as HTMLButtonElement).style.borderColor = userBtnBorder;
                    }}
                  >
                    <div
                      className="w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-bold text-white"
                      style={{ background: "linear-gradient(135deg, #0F172A, #A38A70)" }}
                    >
                      {user.initials}
                    </div>
                    <span
                      className="text-[13px] font-medium max-w-[100px] truncate"
                      style={{ color: isDark ? "rgba(242,237,232,0.7)" : "#525252" }}
                    >
                      {user.name}
                    </span>
                    <ChevronDown
                      className="w-3 h-3"
                      style={{ color: isDark ? "rgba(242,237,232,0.3)" : "#a3a3a3" }}
                    />
                  </button>

                  <AnimatePresence>
                    {userMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: 6, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 4, scale: 0.97 }}
                        transition={{ duration: 0.15 }}
                        className="absolute right-0 top-full mt-2 w-52 rounded-xl overflow-hidden"
                        style={{
                          background: dropdownBg,
                          border: `1px solid ${dropdownBorder}`,
                          boxShadow: isDark
                            ? "0 8px 30px rgba(0,0,0,0.5)"
                            : "0 8px 30px rgba(0,0,0,0.10)",
                        }}
                      >
                        <div
                          className="p-3"
                          style={{ borderBottom: `1px solid ${dropdownBorder}` }}
                        >
                          <p
                            className="text-[12px] font-semibold truncate"
                            style={{ color: isDark ? "rgba(242,237,232,0.85)" : "#404040" }}
                          >
                            {user.name}
                          </p>
                          <p
                            className="text-[11px] truncate"
                            style={{ color: isDark ? "rgba(242,237,232,0.4)" : "#a3a3a3" }}
                          >
                            {user.email}
                          </p>
                        </div>
                        <div className="p-1.5">
                          <button
                            onClick={() => { signOut(); setUserMenuOpen(false); }}
                            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] transition-all duration-150"
                            style={{ color: isDark ? "rgba(242,237,232,0.5)" : "#737373" }}
                            onMouseEnter={(e) => {
                              (e.currentTarget as HTMLButtonElement).style.color = isDark ? "#F2EDE8" : "#171717";
                              (e.currentTarget as HTMLButtonElement).style.background = isDark ? "#242019" : "#F5F5F4";
                            }}
                            onMouseLeave={(e) => {
                              (e.currentTarget as HTMLButtonElement).style.color = isDark ? "rgba(242,237,232,0.5)" : "#737373";
                              (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                            }}
                          >
                            <LogOut className="w-3.5 h-3.5" />
                            Sign out
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ) : (
                <>
                  <button
                    onClick={() => openAuth("signin")}
                    className="text-[13px] font-medium transition-colors px-3 py-1.5"
                    style={{ color: isDark ? "rgba(242,237,232,0.5)" : "#737373" }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.color = isDark ? "#F2EDE8" : "#171717";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.color = isDark ? "rgba(242,237,232,0.5)" : "#737373";
                    }}
                  >
                    Sign in
                  </button>
                  <button
                    onClick={() => openAuth("signup")}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-[13px] font-semibold transition-all duration-300 hover:-translate-y-px"
                    style={{ background: joinWaitlistBg, color: joinWaitlistColor }}
                  >
                    Join Waitlist
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path
                        d="M2.5 6h7M6.5 3l3 3-3 3"
                        stroke={joinWaitlistColor}
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                </>
              )}
            </div>

            {/* Mobile toggle button */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2.5 rounded-lg transition-colors"
              style={{ color: isDark ? "rgba(242,237,232,0.5)" : "#737373" }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color = isDark ? "#F2EDE8" : "#171717";
                (e.currentTarget as HTMLButtonElement).style.background = isDark ? "#1C1916" : "#F5F5F4";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color = isDark ? "rgba(242,237,232,0.5)" : "#737373";
                (e.currentTarget as HTMLButtonElement).style.background = "transparent";
              }}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </nav>
      </header>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18 }}
            className="fixed top-[64px] left-0 right-0 z-40 md:hidden"
            style={{
              background: drawerBg,
              backdropFilter: "blur(24px)",
              borderBottom: `1px solid ${isDark ? "#2E2922" : "#EAEAEC"}`,
            }}
          >
            <div className="max-w-7xl mx-auto px-6 py-5 flex flex-col gap-1">
              {NAV_LINKS.map((link) => {
                const isPageLink = !link.href.startsWith("#");
                const sharedMobileProps = {
                  onClick: () => setMobileOpen(false),
                  className: "text-[15px] py-3 px-2 rounded-lg transition-colors",
                  style: {
                    color: isDark ? "rgba(242,237,232,0.5)" : "#737373",
                    borderBottom: `1px solid ${isDark ? "#2E2922" : "#EAEAEC"}`,
                  } as React.CSSProperties,
                  onMouseEnter: (e: React.MouseEvent<HTMLElement>) => {
                    (e.currentTarget as HTMLElement).style.color = isDark ? "#F2EDE8" : "#171717";
                    (e.currentTarget as HTMLElement).style.background = isDark ? "#1C1916" : "#F5F5F4";
                  },
                  onMouseLeave: (e: React.MouseEvent<HTMLElement>) => {
                    (e.currentTarget as HTMLElement).style.color = isDark ? "rgba(242,237,232,0.5)" : "#737373";
                    (e.currentTarget as HTMLElement).style.background = "transparent";
                  },
                };
                return isPageLink
                  ? <Link key={link.href} href={link.href} {...sharedMobileProps}>{link.label}</Link>
                  : <a key={link.href} href={link.href} {...sharedMobileProps}>{link.label}</a>;
              })}

              {/* Theme toggle row */}
              <div
                className="flex items-center justify-between py-3 px-2"
                style={{ borderBottom: `1px solid ${isDark ? "#2E2922" : "#EAEAEC"}` }}
              >
                <span
                  className="text-[14px] font-medium"
                  style={{ color: isDark ? "rgba(242,237,232,0.55)" : "#737373" }}
                >
                  {isDark ? "Dark mode" : "Light mode"}
                </span>
                <ThemeToggle />
              </div>

              <div className="flex flex-col gap-2.5 pt-4">
                {user ? (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold text-white"
                        style={{ background: "linear-gradient(135deg, #0F172A, #A38A70)" }}
                      >
                        {user.initials}
                      </div>
                      <span
                        className="text-[14px]"
                        style={{ color: isDark ? "rgba(242,237,232,0.6)" : "#737373" }}
                      >
                        {user.name}
                      </span>
                    </div>
                    <button
                      onClick={() => { signOut(); setMobileOpen(false); }}
                      className="text-[13px] transition-colors flex items-center gap-1.5"
                      style={{ color: isDark ? "rgba(242,237,232,0.4)" : "#a3a3a3" }}
                    >
                      <LogOut className="w-3.5 h-3.5" /> Sign out
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => { openAuth("signin"); setMobileOpen(false); }}
                      className="text-center text-[14px] font-medium py-3 rounded-xl transition-all duration-300"
                      style={{
                        color: isDark ? "rgba(242,237,232,0.6)" : "#737373",
                        border: `1px solid ${isDark ? "#2E2922" : "#EAEAEC"}`,
                        background: "transparent",
                      }}
                    >
                      Sign in
                    </button>
                    <button
                      onClick={() => { openAuth("signup"); setMobileOpen(false); }}
                      className="text-center text-[14px] font-semibold py-3 rounded-xl transition-all duration-300 hover:-translate-y-px"
                      style={{ background: joinWaitlistBg, color: joinWaitlistColor }}
                    >
                      Join Waitlist
                    </button>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
