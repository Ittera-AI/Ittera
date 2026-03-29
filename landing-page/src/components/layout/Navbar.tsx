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
          background: scrolled ? "rgba(249,248,246,0.92)" : "rgba(249,248,246,0)",
          backdropFilter: scrolled ? "blur(20px) saturate(150%)" : "none",
          borderBottom: scrolled ? "1px solid #EAEAEC" : "1px solid transparent",
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
                      <stop stopColor="#0F172A" />
                      <stop offset="1" stopColor="#A38A70" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <span className="text-[15px] font-semibold tracking-tight text-neutral-900 group-hover:text-neutral-700 transition-colors">
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
                    style={{ color: isActive ? "#171717" : "rgba(23,23,23,0.45)" }}
                    onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.color = "rgba(23,23,23,0.8)"; }}
                    onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.color = "rgba(23,23,23,0.45)"; }}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="nav-active"
                        className="absolute inset-0 rounded-lg"
                        style={{ background: "rgba(163,138,112,0.08)", border: "1px solid rgba(163,138,112,0.2)" }}
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
                    className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-[#EAEAEC] bg-white hover:bg-[#F5F5F4] hover:border-[#D4D4D4] transition-all duration-200"
                  >
                    <div
                      className="w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-bold text-white"
                      style={{ background: "linear-gradient(135deg, #0F172A, #A38A70)" }}
                    >
                      {user.initials}
                    </div>
                    <span className="text-[13px] font-medium text-neutral-600 max-w-[100px] truncate">{user.name}</span>
                    <ChevronDown className="w-3 h-3 text-neutral-400" />
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
                          background: "white",
                          border: "1px solid #EAEAEC",
                          boxShadow: "0 8px 30px rgba(0,0,0,0.10)",
                        }}
                      >
                        <div className="p-3 border-b border-[#EAEAEC]">
                          <p className="text-[12px] font-semibold text-neutral-700 truncate">{user.name}</p>
                          <p className="text-[11px] text-neutral-400 truncate">{user.email}</p>
                        </div>
                        <div className="p-1.5">
                          <button
                            onClick={() => { signOut(); setUserMenuOpen(false); }}
                            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] text-neutral-500 hover:text-neutral-900 hover:bg-[#F5F5F4] transition-all duration-150"
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
                    className="text-[13px] font-medium text-neutral-500 hover:text-neutral-800 transition-colors px-3 py-1.5"
                  >
                    Sign in
                  </button>
                  <button
                    onClick={() => openAuth("signup")}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-[13px] font-semibold text-white transition-all duration-300 hover:-translate-y-px"
                    style={{ background: "#0F172A" }}
                  >
                    Join Waitlist
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
              className="md:hidden p-2 rounded-lg text-neutral-500 hover:text-neutral-800 hover:bg-[#F5F5F4] transition-colors"
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
            style={{ background: "rgba(249,248,246,0.98)", backdropFilter: "blur(24px)", borderBottom: "1px solid #EAEAEC" }}
          >
            <div className="max-w-7xl mx-auto px-6 py-5 flex flex-col gap-1">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="text-[15px] text-neutral-500 hover:text-neutral-900 hover:bg-[#F5F5F4] transition-colors py-3 px-2 rounded-lg border-b border-[#EAEAEC]"
                >
                  {link.label}
                </a>
              ))}
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
                      <span className="text-[14px] text-neutral-500">{user.name}</span>
                    </div>
                    <button
                      onClick={() => { signOut(); setMobileOpen(false); }}
                      className="text-[13px] text-neutral-400 hover:text-neutral-700 transition-colors flex items-center gap-1.5"
                    >
                      <LogOut className="w-3.5 h-3.5" /> Sign out
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => { openAuth("signin"); setMobileOpen(false); }}
                      className="text-center text-[14px] font-medium text-neutral-500 py-3 border border-[#EAEAEC] rounded-xl hover:border-[#D4D4D4] hover:bg-[#F5F5F4] transition-all duration-300"
                    >
                      Sign in
                    </button>
                    <button
                      onClick={() => { openAuth("signup"); setMobileOpen(false); }}
                      className="text-center text-[14px] font-semibold text-white py-3 rounded-xl transition-all duration-300 hover:-translate-y-px"
                      style={{ background: "#0F172A" }}
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
