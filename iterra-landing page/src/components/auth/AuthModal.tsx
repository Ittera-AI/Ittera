"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Eye, EyeOff, ArrowRight } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  );
}

function InputField({
  type,
  value,
  onChange,
  placeholder,
  autoComplete,
  children,
}: {
  type: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  autoComplete?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="relative">
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete={autoComplete}
        className="w-full h-11 px-4 pr-11 rounded-xl text-[13.5px] text-white/80 placeholder-white/22 outline-none transition-all duration-200"
        style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.08)",
        }}
        onFocus={(e) => {
          e.currentTarget.style.border = "1px solid rgba(108,71,255,0.45)";
          e.currentTarget.style.background = "rgba(108,71,255,0.04)";
        }}
        onBlur={(e) => {
          e.currentTarget.style.border = "1px solid rgba(255,255,255,0.08)";
          e.currentTarget.style.background = "rgba(255,255,255,0.04)";
        }}
      />
      {children && (
        <div className="absolute right-3.5 top-1/2 -translate-y-1/2">{children}</div>
      )}
    </div>
  );
}

export default function AuthModal() {
  const { authOpen, authMode, setAuthMode, closeAuth, signIn, signUp } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Reset fields when mode changes
  useEffect(() => {
    setName("");
    setEmail("");
    setPassword("");
    setError("");
    setShowPw(false);
  }, [authMode]);

  // Escape to close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") closeAuth(); };
    if (authOpen) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [authOpen, closeAuth]);

  // Lock body scroll
  useEffect(() => {
    if (authOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [authOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (authMode === "signup" && !name.trim()) {
      setError("Please enter your name.");
      return;
    }
    if (!email.includes("@") || !email.includes(".")) {
      setError("Please enter a valid email address.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setLoading(true);
    try {
      if (authMode === "signin") {
        await signIn(email, password);
      } else {
        await signUp(email, password, name);
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => setAuthMode(authMode === "signin" ? "signup" : "signin");

  return (
    <AnimatePresence>
      {authOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-[100]"
            style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(12px)" }}
            onClick={closeAuth}
          />

          {/* Modal */}
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.95, y: 24 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 12 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-[101] flex items-center justify-center p-4"
            style={{ pointerEvents: "none" }}
          >
            <div
              className="relative w-full max-w-[420px] rounded-2xl overflow-hidden"
              style={{
                background: "linear-gradient(160deg, #0f1020 0%, #080910 100%)",
                border: "1px solid rgba(255,255,255,0.07)",
                boxShadow: "0 48px 140px rgba(0,0,0,0.85), 0 0 0 1px rgba(255,255,255,0.04), inset 0 1px 0 rgba(255,255,255,0.07)",
                pointerEvents: "auto",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Top glow halo */}
              <div
                className="absolute top-0 left-1/2 -translate-x-1/2 w-72 h-32 pointer-events-none"
                style={{ background: "radial-gradient(ellipse at top, rgba(108,71,255,0.22) 0%, transparent 70%)" }}
              />

              {/* Close */}
              <button
                onClick={closeAuth}
                aria-label="Close"
                className="absolute top-4 right-4 z-10 w-7 h-7 rounded-lg flex items-center justify-center text-white/25 hover:text-white/55 hover:bg-white/[0.05] transition-all duration-200"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="relative p-8">
                {/* Brand */}
                <div className="flex items-center gap-2 mb-7">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L14.5 9L21 12L14.5 15L12 22L9.5 15L3 12L9.5 9L12 2Z" fill="url(#auth-grad)" />
                    <defs>
                      <linearGradient id="auth-grad" x1="3" y1="2" x2="21" y2="22" gradientUnits="userSpaceOnUse">
                        <stop stopColor="#a78bfa" />
                        <stop offset="0.5" stopColor="#6c47ff" />
                        <stop offset="1" stopColor="#00d4ff" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <span className="text-[14px] font-semibold tracking-tight text-white/85">Ittera</span>
                </div>

                {/* Headline */}
                <AnimatePresence mode="wait">
                  <motion.div
                    key={authMode}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.18 }}
                    className="mb-6"
                  >
                    <h2 className="text-[22px] font-bold tracking-tight text-white mb-1.5">
                      {authMode === "signin" ? "Welcome back" : "Join the waitlist"}
                    </h2>
                    <p className="text-[13px] text-white/38">
                      {authMode === "signin" ? (
                        <>No account?{" "}
                          <button type="button" onClick={switchMode} className="text-violet-400/80 hover:text-violet-300 transition-colors font-medium">
                            Create one free
                          </button>
                        </>
                      ) : (
                        <>Already have an account?{" "}
                          <button type="button" onClick={switchMode} className="text-violet-400/80 hover:text-violet-300 transition-colors font-medium">
                            Sign in
                          </button>
                        </>
                      )}
                    </p>
                  </motion.div>
                </AnimatePresence>

                {/* Social auth */}
                <div className="grid grid-cols-2 gap-2 mb-5">
                  {[
                    { label: "Google", icon: <GoogleIcon /> },
                    { label: "GitHub", icon: <GitHubIcon /> },
                  ].map((p) => (
                    <button
                      key={p.label}
                      type="button"
                      className="flex items-center justify-center gap-2 h-10 rounded-xl text-[12.5px] font-medium text-white/40 hover:text-white/65 hover:bg-white/[0.05] transition-all duration-200"
                      style={{ border: "1px solid rgba(255,255,255,0.07)" }}
                    >
                      {p.icon}
                      {p.label}
                    </button>
                  ))}
                </div>

                {/* Divider */}
                <div className="flex items-center gap-3 mb-5">
                  <div className="flex-1 h-px bg-white/[0.06]" />
                  <span className="text-[10.5px] text-white/18 font-medium tracking-wide">OR EMAIL</span>
                  <div className="flex-1 h-px bg-white/[0.06]" />
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-3" noValidate>
                  <AnimatePresence initial={false}>
                    {authMode === "signup" && (
                      <motion.div
                        key="name"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.22, ease: "easeInOut" }}
                        className="overflow-hidden"
                      >
                        <InputField
                          type="text"
                          value={name}
                          onChange={setName}
                          placeholder="Your name"
                          autoComplete="name"
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <InputField
                    type="email"
                    value={email}
                    onChange={setEmail}
                    placeholder="Email address"
                    autoComplete="email"
                  />

                  <InputField
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={setPassword}
                    placeholder="Password (min. 6 chars)"
                    autoComplete={authMode === "signin" ? "current-password" : "new-password"}
                  >
                    <button
                      type="button"
                      onClick={() => setShowPw((v) => !v)}
                      className="text-white/22 hover:text-white/50 transition-colors"
                    >
                      {showPw ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </InputField>

                  {authMode === "signin" && (
                    <div className="text-right">
                      <button type="button" className="text-[11.5px] text-white/25 hover:text-violet-400/70 transition-colors">
                        Forgot password?
                      </button>
                    </div>
                  )}

                  <AnimatePresence>
                    {error && (
                      <motion.p
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="text-[12px] text-red-400/80 px-3 py-2 rounded-lg"
                        style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)" }}
                      >
                        {error}
                      </motion.p>
                    )}
                  </AnimatePresence>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full h-11 rounded-xl text-[13.5px] font-semibold text-white flex items-center justify-center gap-2 btn-glow disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                    style={{ background: "linear-gradient(135deg, #6c47ff 0%, #4f32d4 55%, #00a8cc 100%)", marginTop: "8px" }}
                  >
                    {loading ? (
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    ) : (
                      <>
                        {authMode === "signin" ? "Sign in to Ittera" : "Create my account"}
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>

                <p className="mt-5 text-[10.5px] text-white/16 text-center leading-relaxed">
                  By continuing you agree to our{" "}
                  <a href="#" className="text-white/28 hover:text-white/45 underline underline-offset-2 transition-colors">Terms</a>
                  {" "}and{" "}
                  <a href="#" className="text-white/28 hover:text-white/45 underline underline-offset-2 transition-colors">Privacy Policy</a>.
                  {" "}No spam, ever.
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
