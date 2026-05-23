"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, LogOut, LayoutDashboard, ChevronDown } from "lucide-react";
import { NAV_LINKS } from "@/lib/constants";
import { ROUTES, waitlistDestination } from "@/lib/routes";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import ThemeToggle from "@/components/ui/ThemeToggle";

export default function Navbar() {
  const { user, hasWorkspaceAccess, isWaitlistedUser, waitlistPosition, openAuth, signOut } = useAuth();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const waitlistLabel =
    waitlistPosition != null ? `Waitlisted · #${waitlistPosition}` : "Waitlisted";

  const homeHref = user ? waitlistDestination(hasWorkspaceAccess) : ROUTES.home;

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

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
        setActiveSection(sectionIds.find((id) => visible.has(id)) ?? "");
      },
      { rootMargin: "-56px 0px -45% 0px", threshold: 0 },
    );

    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const navBg = isDark ? "rgba(18, 16, 14, 0.65)" : "rgba(255, 255, 255, 0.75)";
  const navBorder = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)";
  const linkActive = isDark ? "#F2EDE8" : "#171717";
  const linkMuted = isDark ? "rgba(242,237,232,0.4)" : "rgba(23,23,23,0.45)";
  const linkHover = isDark ? "rgba(242,237,232,0.8)" : "rgba(23,23,23,0.8)";
  const drawerBg = isDark ? "rgba(12,11,9,0.98)" : "rgba(249,248,246,0.98)";
  const joinWaitlistBg = isDark
    ? "linear-gradient(135deg, #C4A882 0%, #A38A70 100%)"
    : "#0F172A";
  const joinWaitlistColor = isDark ? "#0C0B09" : "white";
  const waitlistPillBg = isDark ? "rgba(163,138,112,0.12)" : "rgba(163,138,112,0.08)";
  const waitlistPillBorder = isDark ? "rgba(163,138,112,0.28)" : "rgba(163,138,112,0.25)";
  const waitlistPillColor = isDark ? "#C4A882" : "#8B6F52";
  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-50"
        style={{
          background: navBg,
          backdropFilter: "blur(20px) saturate(180%)",
          WebkitBackdropFilter: "blur(20px) saturate(180%)",
          borderBottom: `1px solid ${navBorder}`,
          boxShadow: scrolled
            ? isDark
              ? "0 8px 36px -6px rgba(0,0,0,0.55)"
              : "0 8px 36px -6px rgba(0,0,0,0.12)"
            : isDark
              ? "0 4px 30px -4px rgba(0,0,0,0.4)"
              : "0 4px 30px -4px rgba(0,0,0,0.08)",
          transition: "all 0.5s cubic-bezier(0.16,1,0.3,1)",
        }}
      >
        <nav className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="flex items-center justify-between h-14">
            <Link href={homeHref} className="flex items-center gap-2.5 group flex-shrink-0">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L14.5 9L21 12L14.5 15L12 22L9.5 15L3 12L9.5 9L12 2Z" fill="url(#nav-grad)" />
                <defs>
                  <linearGradient id="nav-grad" x1="3" y1="2" x2="21" y2="22" gradientUnits="userSpaceOnUse">
                    <stop stopColor={isDark ? "#C4A882" : "#0F172A"} />
                    <stop offset="1" stopColor="#A38A70" />
                  </linearGradient>
                </defs>
              </svg>
              <span
                className="text-[15px] font-semibold tracking-tight transition-colors"
                style={{ color: isDark ? "#F2EDE8" : "#171717" }}
              >
                Ittera
              </span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              {NAV_LINKS.map((link) => {
                const isPageLink = !link.href.startsWith("#");
                const isActive = !isPageLink && activeSection === link.href.slice(1);
                const sharedProps = {
                  className: "relative px-3 py-1.5 text-[13px] font-medium transition-colors duration-200 rounded-lg",
                  style: { color: isActive ? linkActive : linkMuted } as React.CSSProperties,
                  onMouseEnter: (e: React.MouseEvent<HTMLElement>) => {
                    if (!isActive) (e.currentTarget as HTMLElement).style.color = linkHover;
                  },
                  onMouseLeave: (e: React.MouseEvent<HTMLElement>) => {
                    if (!isActive) (e.currentTarget as HTMLElement).style.color = linkMuted;
                  },
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
                return isPageLink ? (
                  <Link key={link.href} href={link.href} {...sharedProps}>
                    {inner}
                  </Link>
                ) : (
                  <a key={link.href} href={link.href} {...sharedProps}>
                    {inner}
                  </a>
                );
              })}
            </div>

            <div className="hidden md:flex items-center gap-2.5">
              <ThemeToggle />

              {user ? (
                <div className="flex items-center gap-2">
                  {isWaitlistedUser ? (
                    <Link
                      href={ROUTES.waitlistStatus}
                      className="inline-flex items-center rounded-full px-3 py-1.5 text-[12px] font-semibold tracking-wide tabular-nums"
                      style={{
                        background: waitlistPillBg,
                        border: `1px solid ${waitlistPillBorder}`,
                        color: waitlistPillColor,
                      }}
                    >
                      {waitlistLabel}
                    </Link>
                  ) : null}
                  {hasWorkspaceAccess ? (
                    <Link
                      href="/dashboard"
                      className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] font-semibold transition-colors"
                      style={{
                        color: isDark ? "#F2EDE8" : "#171717",
                        border: `1px solid ${isDark ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.08)"}`,
                        background: isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.04)",
                      }}
                    >
                      <LayoutDashboard className="w-3.5 h-3.5" />
                      Dashboard
                    </Link>
                  ) : null}
                  <div className="relative" ref={profileRef}>
                    <button
                      type="button"
                      onClick={() => setProfileOpen((o) => !o)}
                      className="flex items-center gap-2 rounded-full px-2.5 py-1.5 transition-colors"
                      style={{
                        color: isDark ? "#F2EDE8" : "#171717",
                        border: `1px solid ${isDark ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.08)"}`,
                        background: profileOpen
                          ? isDark ? "rgba(255,255,255,0.07)" : "rgba(15,23,42,0.06)"
                          : isDark ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.65)",
                      }}
                    >
                      <span
                        className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold flex-shrink-0"
                        style={{ background: isDark ? "#C4A882" : "#0F172A", color: isDark ? "#0C0B09" : "white" }}
                      >
                        {user.initials || "IT"}
                      </span>
                      <span className="max-w-[120px] truncate text-[12px] font-semibold">{user.name}</span>
                      <ChevronDown
                        className="w-3 h-3 flex-shrink-0 transition-transform duration-200"
                        style={{
                          opacity: 0.5,
                          transform: profileOpen ? "rotate(180deg)" : "rotate(0deg)",
                        }}
                      />
                    </button>

                    <AnimatePresence>
                      {profileOpen && (
                        <motion.div
                          initial={{ opacity: 0, y: 6, scale: 0.97 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: 6, scale: 0.97 }}
                          transition={{ duration: 0.14 }}
                          className="absolute right-0 top-[calc(100%+8px)] w-56 rounded-xl overflow-hidden z-50"
                          style={{
                            background: isDark ? "rgba(22,20,17,0.98)" : "rgba(255,255,255,0.99)",
                            border: `1px solid ${isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.07)"}`,
                            boxShadow: isDark
                              ? "0 16px 48px rgba(0,0,0,0.65), 0 4px 12px rgba(0,0,0,0.4)"
                              : "0 16px 48px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.06)",
                            backdropFilter: "blur(20px)",
                          }}
                        >
                          <div
                            className="px-4 py-3.5"
                            style={{ borderBottom: `1px solid ${isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)"}` }}
                          >
                            <p
                              className="text-[12px] font-semibold truncate"
                              style={{ color: isDark ? "#F2EDE8" : "#171717" }}
                            >
                              {user.name}
                            </p>
                            <p
                              className="text-[11px] mt-0.5 truncate"
                              style={{ color: isDark ? "rgba(242,237,232,0.4)" : "#9CA3AF" }}
                            >
                              {user.email}
                            </p>
                          </div>

                          <div className="py-1.5">
                            <button
                              type="button"
                              onClick={() => { void signOut(); setProfileOpen(false); }}
                              className="flex w-full items-center gap-2.5 px-4 py-2.5 text-[13px] font-medium transition-colors"
                              style={{ color: isDark ? "rgba(242,237,232,0.55)" : "#6B7280" }}
                              onMouseEnter={(e) => {
                                (e.currentTarget as HTMLElement).style.color = isDark ? "#F2EDE8" : "#111827";
                                (e.currentTarget as HTMLElement).style.background = isDark ? "rgba(255,255,255,0.05)" : "#F9FAFB";
                              }}
                              onMouseLeave={(e) => {
                                (e.currentTarget as HTMLElement).style.color = isDark ? "rgba(242,237,232,0.55)" : "#6B7280";
                                (e.currentTarget as HTMLElement).style.background = "transparent";
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
                </div>
              ) : (
                <>
                  <button
                    type="button"
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
                    type="button"
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

            <button
              type="button"
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

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18 }}
            className="fixed top-[56px] left-0 right-0 z-40 md:hidden"
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
                return isPageLink ? (
                  <Link key={link.href} href={link.href} {...sharedMobileProps}>
                    {link.label}
                  </Link>
                ) : (
                  <a key={link.href} href={link.href} {...sharedMobileProps}>
                    {link.label}
                  </a>
                );
              })}

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
                  <>
                    {isWaitlistedUser ? (
                      <Link
                        href={ROUTES.waitlistStatus}
                        onClick={() => setMobileOpen(false)}
                        className="text-center text-[13px] font-semibold py-3 rounded-xl tabular-nums"
                        style={{
                          color: waitlistPillColor,
                          border: `1px solid ${waitlistPillBorder}`,
                          background: waitlistPillBg,
                        }}
                      >
                        {waitlistLabel}
                      </Link>
                    ) : null}
                    {hasWorkspaceAccess ? (
                      <Link
                        href="/dashboard"
                        onClick={() => setMobileOpen(false)}
                        className="flex items-center justify-center gap-2 text-center text-[14px] font-semibold py-3 rounded-xl transition-colors"
                        style={{
                          color: isDark ? "#F2EDE8" : "#171717",
                          border: `1px solid ${isDark ? "#2E2922" : "#EAEAEC"}`,
                          background: isDark ? "rgba(255,255,255,0.04)" : "white",
                        }}
                      >
                        <LayoutDashboard className="h-4 w-4" />
                        Dashboard
                        <span
                          className="ml-1 flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold"
                          style={{ background: isDark ? "#C4A882" : "#0F172A", color: isDark ? "#0C0B09" : "white" }}
                        >
                          {user.initials || "IT"}
                        </span>
                      </Link>
                    ) : null}
                    <div
                      className="flex items-center justify-center gap-2 text-center text-[14px] font-semibold py-3 rounded-xl"
                      style={{
                        color: isDark ? "#F2EDE8" : "#171717",
                        border: `1px solid ${isDark ? "#2E2922" : "#EAEAEC"}`,
                        background: isDark ? "rgba(255,255,255,0.03)" : "white",
                      }}
                    >
                      <span
                        className="flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-bold"
                        style={{ background: isDark ? "#C4A882" : "#0F172A", color: isDark ? "#0C0B09" : "white" }}
                      >
                        {user.initials || "IT"}
                      </span>
                      <span className="max-w-[190px] truncate">{user.name}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        signOut();
                        setMobileOpen(false);
                      }}
                      className="text-center text-[14px] font-medium py-3 rounded-xl transition-colors flex items-center justify-center gap-1.5"
                      style={{
                        color: isDark ? "rgba(242,237,232,0.5)" : "#737373",
                        border: `1px solid ${isDark ? "#2E2922" : "#EAEAEC"}`,
                      }}
                    >
                      <LogOut className="w-3.5 h-3.5" /> Sign out
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => {
                        openAuth("signin");
                        setMobileOpen(false);
                      }}
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
                      type="button"
                      onClick={() => {
                        openAuth("signup");
                        setMobileOpen(false);
                      }}
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
