"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Eye, EyeOff, ArrowRight } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";

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

function LinkedInIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M6.94 8.5a1.56 1.56 0 1 1 0-3.12 1.56 1.56 0 0 1 0 3.12ZM5.62 9.68h2.65V18H5.62V9.68Zm4.31 0h2.54v1.14h.04c.35-.67 1.22-1.38 2.52-1.38 2.69 0 3.19 1.77 3.19 4.07V18h-2.64v-3.99c0-.95-.02-2.17-1.32-2.17-1.32 0-1.52 1.03-1.52 2.1V18H9.93V9.68Z" />
    </svg>
  );
}

function InputField({
  type,
  value,
  onChange,
  placeholder,
  autoComplete,
  isDark,
  children,
}: {
  type: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  autoComplete?: string;
  isDark: boolean;
  children?: React.ReactNode;
}) {
  const inputBg     = isDark ? "#1C1916" : "#F9F8F6";
  const inputBorder = isDark ? "#2E2922" : "#EAEAEC";
  const inputColor  = isDark ? "#F2EDE8" : "#171717";
  const focusBg     = isDark ? "#141210" : "white";

  return (
    <div className="relative">
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete={autoComplete}
        className="w-full h-11 px-4 pr-11 text-[13.5px] outline-none transition-all duration-200"
        style={{
          background: inputBg,
          border: `1px solid ${inputBorder}`,
          borderRadius: "8px",
          color: inputColor,
        }}
        onFocus={(e) => {
          e.currentTarget.style.border = "1px solid rgba(163,138,112,0.5)";
          e.currentTarget.style.background = focusBg;
        }}
        onBlur={(e) => {
          e.currentTarget.style.border = `1px solid ${inputBorder}`;
          e.currentTarget.style.background = inputBg;
        }}
      />
      <style>{`input::placeholder { color: ${isDark ? "rgba(242,237,232,0.25)" : "rgba(23,23,23,0.35)"}; }`}</style>
      {children && (
        <div className="absolute right-3.5 top-1/2 -translate-y-1/2">{children}</div>
      )}
    </div>
  );
}

export default function AuthModal() {
  const { authOpen, authMode, authSeedEmail, setAuthMode, closeAuth, signIn, signUp, signInWithGoogle, signInWithLinkedIn, resetPassword } = useAuth();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resetSent, setResetSent] = useState(false);

  // Reset fields when mode changes
  useEffect(() => {
    setName("");
    setEmail(authSeedEmail);
    setPassword("");
    setError("");
    setShowPw(false);
    setResetSent(false);
  }, [authMode, authSeedEmail]);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => setAuthMode(authMode === "signin" ? "signup" : "signin");

  // Theme tokens
  const modalBg       = isDark ? "#141210" : "rgba(255,255,255,0.98)";
  const modalBorder   = isDark ? "#2E2922" : "#EAEAEC";
  const modalShadow   = isDark ? "0 48px 140px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.04) inset" : "0 48px 140px rgba(0,0,0,0.15), 0 1px 0 rgba(255,255,255,0.9) inset";
  const titleColor    = isDark ? "#F2EDE8" : "#171717";
  const subtextColor  = isDark ? "rgba(242,237,232,0.45)" : "#737373";
  const labelColor    = isDark ? "rgba(242,237,232,0.6)" : "#525252";
  const dividerColor  = isDark ? "#2E2922" : "#EAEAEC";
  const dividerText   = isDark ? "rgba(242,237,232,0.3)" : "#A3A3A3";
  const socialBg      = isDark ? "#1C1916" : "white";
  const socialBorder  = isDark ? "#2E2922" : "#EAEAEC";
  const socialText    = isDark ? "rgba(242,237,232,0.6)" : "#404040";
  const socialHoverBg     = isDark ? "#252019" : "#F5F5F4";
  const socialHoverBorder = isDark ? "#3D3730" : "#D4D4D4";
  const socialHoverText   = isDark ? "#F2EDE8" : "#171717";
  const closeBtnHover = isDark ? "#1C1916" : "#F5F5F4";
  const closeBtnColor = isDark ? "rgba(242,237,232,0.4)" : "#A3A3A3";
  const forgotColor   = isDark ? "rgba(242,237,232,0.3)" : "#A3A3A3";
  const legalColor    = isDark ? "rgba(242,237,232,0.25)" : "#A3A3A3";
  const legalLinkColor= isDark ? "rgba(242,237,232,0.45)" : "#737373";
  const submitBg      = isDark ? "linear-gradient(135deg, #C4A882 0%, #A38A70 100%)" : "#0F172A";
  const submitColor   = isDark ? "#0C0B09" : "white";
  const logoStop1     = isDark ? "#C4A882" : "#0F172A";

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
            style={{ background: isDark ? "rgba(0,0,0,0.6)" : "rgba(0,0,0,0.35)", backdropFilter: "blur(12px)" }}
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
              className="relative w-full max-w-[420px] rounded-xl overflow-hidden"
              style={{
                background: modalBg,
                border: `1px solid ${modalBorder}`,
                boxShadow: modalShadow,
                pointerEvents: "auto",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Top glow halo */}
              <div
                className="absolute top-0 left-1/2 -translate-x-1/2 w-72 h-32 pointer-events-none"
                style={{ background: "radial-gradient(ellipse at top, rgba(163,138,112,0.10) 0%, transparent 70%)" }}
              />

              {/* Close */}
              <button
                onClick={closeAuth}
                aria-label="Close"
                className="absolute top-4 right-4 z-10 w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-200"
                style={{ color: closeBtnColor }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = closeBtnHover;
                  (e.currentTarget as HTMLButtonElement).style.color = isDark ? "#F2EDE8" : "#404040";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                  (e.currentTarget as HTMLButtonElement).style.color = closeBtnColor;
                }}
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
                        <stop stopColor={logoStop1} />
                        <stop offset="1" stopColor="#A38A70" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <span className="text-[14px] font-semibold tracking-tight" style={{ color: titleColor }}>Ittera</span>
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
                    <h2 className="text-[22px] font-bold tracking-tight mb-1.5" style={{ color: titleColor }}>
                      {authMode === "signin" ? "Welcome back" : "Join the waitlist"}
                    </h2>
                    <p className="text-[13px]" style={{ color: subtextColor }}>
                      {authMode === "signin" ? (
                        <>No account?{" "}
                          <button type="button" onClick={switchMode} className="text-[#A38A70] hover:text-[#8B7260] transition-colors font-medium">
                            Create one free
                          </button>
                        </>
                      ) : (
                        <>Already have an account?{" "}
                          <button type="button" onClick={switchMode} className="text-[#A38A70] hover:text-[#8B7260] transition-colors font-medium">
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
                    { label: "Google", icon: <GoogleIcon />, onClick: signInWithGoogle, disabled: false },
                    { label: "LinkedIn", icon: <LinkedInIcon />, onClick: signInWithLinkedIn, disabled: false },
                  ].map((p) => (
                    <button
                      key={p.label}
                      type="button"
                      onClick={p.onClick}
                      disabled={p.disabled || loading}
                      className="flex items-center justify-center gap-2 h-10 rounded-xl text-[12.5px] font-medium transition-all duration-200"
                      style={{
                        background: socialBg,
                        border: `1px solid ${socialBorder}`,
                        color: socialText,
                        opacity: p.disabled ? 0.5 : 1,
                        cursor: p.disabled ? "not-allowed" : "pointer",
                      }}
                      onMouseEnter={(e) => {
                        if (p.disabled) return;
                        (e.currentTarget as HTMLButtonElement).style.background = socialHoverBg;
                        (e.currentTarget as HTMLButtonElement).style.borderColor = socialHoverBorder;
                        (e.currentTarget as HTMLButtonElement).style.color = socialHoverText;
                      }}
                      onMouseLeave={(e) => {
                        if (p.disabled) return;
                        (e.currentTarget as HTMLButtonElement).style.background = socialBg;
                        (e.currentTarget as HTMLButtonElement).style.borderColor = socialBorder;
                        (e.currentTarget as HTMLButtonElement).style.color = socialText;
                      }}
                    >
                      {p.icon}
                      {p.label}
                    </button>
                  ))}
                </div>

                {/* Divider */}
                <div className="flex items-center gap-3 mb-5">
                  <div className="flex-1 h-px" style={{ background: dividerColor }} />
                  <span className="text-[10.5px] font-medium tracking-wide" style={{ color: dividerText }}>OR EMAIL</span>
                  <div className="flex-1 h-px" style={{ background: dividerColor }} />
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
                        <label className="block text-[12px] font-medium mb-1" style={{ color: labelColor }}>Full name</label>
                        <InputField
                          type="text"
                          value={name}
                          onChange={setName}
                          placeholder="Your name"
                          autoComplete="name"
                          isDark={isDark}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div>
                    <label className="block text-[12px] font-medium mb-1" style={{ color: labelColor }}>Email</label>
                    <InputField
                      type="email"
                      value={email}
                      onChange={setEmail}
                      placeholder="Email address"
                      autoComplete="email"
                      isDark={isDark}
                    />
                  </div>

                  <div>
                    <label className="block text-[12px] font-medium mb-1" style={{ color: labelColor }}>Password</label>
                    <InputField
                      type={showPw ? "text" : "password"}
                      value={password}
                      onChange={setPassword}
                      placeholder="Password (min. 6 chars)"
                      autoComplete={authMode === "signin" ? "current-password" : "new-password"}
                      isDark={isDark}
                    >
                      <button
                        type="button"
                        onClick={() => setShowPw((v) => !v)}
                        className="transition-colors"
                        style={{ color: forgotColor }}
                        onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = isDark ? "#F2EDE8" : "#525252"; }}
                        onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = forgotColor; }}
                      >
                        {showPw ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      </button>
                    </InputField>
                  </div>

                  {authMode === "signin" && (
                    <div className="text-right">
                      <button
                        type="button"
                        disabled={loading}
                        className="text-[11.5px] hover:text-[#A38A70] transition-colors disabled:opacity-50"
                        style={{ color: resetSent ? "#A38A70" : forgotColor }}
                        onClick={async () => {
                          if (!email.includes("@")) {
                            setError("Enter your email address above first.");
                            return;
                          }
                          setLoading(true);
                          setError("");
                          try {
                            await resetPassword(email);
                            setResetSent(true);
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Failed to send reset email.");
                          } finally {
                            setLoading(false);
                          }
                        }}
                      >
                        {resetSent ? "Reset email sent — check your inbox" : "Forgot password?"}
                      </button>
                    </div>
                  )}

                  <AnimatePresence>
                    {error && (
                      <motion.p
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="text-[12px] text-red-400 px-3 py-2 rounded-lg"
                        style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)" }}
                      >
                        {error}
                      </motion.p>
                    )}
                  </AnimatePresence>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full h-11 text-[13.5px] font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:-translate-y-px"
                    style={{
                      background: submitBg,
                      color: submitColor,
                      borderRadius: "8px",
                      marginTop: "8px",
                    }}
                    onMouseEnter={(e) => {
                      if (!loading) (e.currentTarget as HTMLButtonElement).style.boxShadow = isDark ? "0 4px 20px rgba(163,138,112,0.25)" : "0 4px 20px rgba(0,0,0,0.10)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.boxShadow = "none";
                    }}
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

                <p className="mt-5 text-[10.5px] text-center leading-relaxed" style={{ color: legalColor }}>
                  By continuing you agree to our{" "}
                  <a href="#" className="underline underline-offset-2 transition-colors hover:text-[#A38A70]" style={{ color: legalLinkColor }}>Terms</a>
                  {" "}and{" "}
                  <a href="#" className="underline underline-offset-2 transition-colors hover:text-[#A38A70]" style={{ color: legalLinkColor }}>Privacy Policy</a>.
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
