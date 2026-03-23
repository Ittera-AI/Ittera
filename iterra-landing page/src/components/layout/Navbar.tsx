"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, LogOut, ChevronDown } from "lucide-react";
import { NAV_LINKS } from "@/lib/constants";
import { useAuth } from "@/context/AuthContext";

export default function Navbar() {
  const { user, openAuth, signOut } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("");
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Scroll + active section detection
  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 60);

      // Find active section
      const sections = NAV_LINKS.map((l) => l.href.replace("#", ""));
      for (const id of [...sections].reverse()) {
        const el = document.getElementById(id);
        if (el && el.getBoundingClientRect().top <= 100) {
          setActiveSection(id);
          return;
        }
      }
      setActiveSection("");
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close user menu on outside click
  useEffect(() => {
    if (!userMenuOpen) return;
    const h = () => setUserMenuOpen(false);
    window.addEventListener("click", h);
    return () => window.removeEventListener("click", h);
  }, [userMenuOpen]);

  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-50 transition-all duration-500"
        style={{
          background: scrolled ? "rgba(3,4,7,0.88)" : "transparent",
          backdropFilter: scrolled ? "blur(24px) saturate(180%)" : "none",
          borderBottom: scrolled ? "1px solid rgba(255,255,255,0.05)" : "1px solid transparent",
        }}
      >
        <nav className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <a href="/" className="flex items-center gap-2.5 group flex-shrink-0">
              <div className="relative">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L14.5 9L21 12L14.5 15L12 22L9.5 15L3 12L9.5 9L12 2Z" fill="url(#nav-grad)" />
                  <defs>
                    <linearGradient id="nav-grad" x1="3" y1="2" x2="21" y2="22" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#a78bfa" />
                      <stop offset="0.5" stopColor="#6c47ff" />
                      <stop offset="1" stopColor="#00d4ff" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <span className="text-[15px] font-semibold tracking-tight text-white/90 group-hover:text-white transition-colors">
                Ittera
              </span>
            </a>

            {/* Desktop nav links */}
            <div className="hidden md:flex items-center gap-1">
              {NAV_LINKS.map((link) => {
                const isActive = activeSection === link.href.replace("#", "");
                return (
                  <a
                    key={link.href}
                    href={link.href}
                    className="relative px-3 py-1.5 text-[13px] font-medium transition-colors duration-200 rounded-lg"
                    style={{ color: isActive ? "rgba(255,255,255,0.85)" : "rgba(255,255,255,0.38)" }}
                    onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.color = "rgba(255,255,255,0.65)"; }}
                    onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.color = "rgba(255,255,255,0.38)"; }}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="nav-active"
                        className="absolute inset-0 rounded-lg"
                        style={{ background: "rgba(108,71,255,0.1)", border: "1px solid rgba(108,71,255,0.15)" }}
                        transition={{ type: "spring", bounce: 0.25, duration: 0.4 }}
                      />
                    )}
                    <span className="relative z-10">{link.label}</span>
                  </a>
                );
              })}
            </div>

            {/* Desktop CTAs */}
            <div className="hidden md:flex items-center gap-2.5">
              {user ? (
                /* Logged-in user avatar + dropdown */
                <div className="relative" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => setUserMenuOpen((v) => !v)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-white/[0.07] bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/[0.12] transition-all duration-200"
                  >
                    <div
                      className="w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-bold text-white/90"
                      style={{ background: "linear-gradient(135deg, #6c47ff, #00d4ff)" }}
                    >
                      {user.initials}
                    </div>
                    <span className="text-[13px] font-medium text-white/65 max-w-[100px] truncate">{user.name}</span>
                    <ChevronDown className="w-3 h-3 text-white/25" />
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
                          background: "rgba(12,13,20,0.98)",
                          border: "1px solid rgba(255,255,255,0.08)",
                          boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
                        }}
                      >
                        <div className="p-3 border-b border-white/[0.05]">
                          <p className="text-[12px] font-semibold text-white/75 truncate">{user.name}</p>
                          <p className="text-[11px] text-white/30 truncate">{user.email}</p>
                        </div>
                        <div className="p-1.5">
                          <button
                            onClick={() => { signOut(); setUserMenuOpen(false); }}
                            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] text-white/45 hover:text-white/70 hover:bg-white/[0.05] transition-all duration-150"
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
                    className="text-[13px] font-medium text-white/35 hover:text-white/65 transition-colors px-3 py-1.5"
                  >
                    Sign in
                  </button>
                  <button
                    onClick={() => openAuth("signup")}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-[13px] font-semibold text-white btn-glow"
                    style={{ background: "linear-gradient(135deg, #6c47ff, #4f32d4)" }}
                  >
                    Get Early Access
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path d="M2.5 6h7M6.5 3l3 3-3 3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </button>
                </>
              )}
            </div>

            {/* Mobile toggle */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-lg text-white/40 hover:text-white/70 hover:bg-white/[0.05] transition-colors"
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
            style={{ background: "rgba(3,4,7,0.97)", backdropFilter: "blur(24px)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}
          >
            <div className="max-w-7xl mx-auto px-6 py-5 flex flex-col gap-1">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="text-[15px] text-white/45 hover:text-white/80 transition-colors py-3 border-b border-white/[0.04]"
                >
                  {link.label}
                </a>
              ))}
              <div className="flex flex-col gap-2.5 pt-4">
                {user ? (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold text-white/90"
                        style={{ background: "linear-gradient(135deg, #6c47ff, #00d4ff)" }}
                      >
                        {user.initials}
                      </div>
                      <span className="text-[14px] text-white/60">{user.name}</span>
                    </div>
                    <button
                      onClick={() => { signOut(); setMobileOpen(false); }}
                      className="text-[13px] text-white/35 hover:text-white/60 transition-colors flex items-center gap-1.5"
                    >
                      <LogOut className="w-3.5 h-3.5" /> Sign out
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => { openAuth("signin"); setMobileOpen(false); }}
                      className="text-center text-[14px] font-medium text-white/45 py-3 border border-white/[0.08] rounded-xl hover:border-white/[0.16] transition-colors"
                    >
                      Sign in
                    </button>
                    <button
                      onClick={() => { openAuth("signup"); setMobileOpen(false); }}
                      className="text-center text-[14px] font-semibold text-white py-3 rounded-xl btn-glow"
                      style={{ background: "linear-gradient(135deg, #6c47ff, #4f32d4)" }}
                    >
                      Get Early Access
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
