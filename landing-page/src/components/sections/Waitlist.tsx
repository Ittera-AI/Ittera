"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { ArrowRight, Zap, Star, Shield, Users, ChevronRight, TrendingUp } from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { supabase } from "@/lib/supabase";

const EASE = [0.16, 1, 0.3, 1] as const;
const DEFAULT_TOTAL_SEATS = 100;

type WaitlistStats = {
  total_joined: number;
  total_seats: number;
  remaining_seats: number;
  recent_joiners: string[];
};

type WaitlistMemberStatus = {
  email: string;
  joined: boolean;
  position: number | null;
  total_joined: number;
  total_seats: number;
  remaining_seats: number;
};

function useCounter(target: number, duration = 1800) {
  const [count, setCount] = useState(0);
  const [started, setStarted] = useState(false);
  const countRef = useRef(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    countRef.current = count;
  }, [count]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setStarted(true);
      },
      { threshold: 0.3 },
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!started) return;
    const start = countRef.current;
    if (start === target) return;

    const steps = 60;
    const increment = (target - start) / steps;
    let current = start;

    const interval = window.setInterval(() => {
      current += increment;
      const nextValue =
        increment >= 0 ? Math.min(current, target) : Math.max(current, target);
      setCount(Math.round(nextValue));
      if (nextValue === target) window.clearInterval(interval);
    }, duration / steps);

    return () => window.clearInterval(interval);
  }, [started, target, duration]);

  return { count, ref };
}

const PERKS = [
  { icon: Zap, title: "Beta access in Q2 2026", desc: "The first 100 seats get into the beta and help test the product before launch." },
  { icon: Star, title: "Early member pricing", desc: "Locked in early and protected as we grow." },
  { icon: Users, title: "Vote on what we build next", desc: "Direct line to the team." },
  { icon: Shield, title: "Beta testing cohort", desc: "Reserved for the first 100 members joining the beta program." },
];

function buildFallbackStats(): WaitlistStats {
  return {
    total_joined: 0,
    total_seats: DEFAULT_TOTAL_SEATS,
    remaining_seats: DEFAULT_TOTAL_SEATS,
    recent_joiners: [],
  };
}

export default function Waitlist() {
  const shouldReduceMotion = useReducedMotion();
  const { theme } = useTheme();
  const { user, openAuth } = useAuth();
  const isDark = theme === "dark";

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [profession, setProfession] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [alreadyJoined, setAlreadyJoined] = useState(false);
  const [position, setPosition] = useState(0);
  const [error, setError] = useState("");
  const [stats, setStats] = useState<WaitlistStats>(buildFallbackStats);
  const [memberStatus, setMemberStatus] = useState<WaitlistMemberStatus | null>(null);
  const { count, ref } = useCounter(stats.total_joined);

  // Load total waitlist count from Supabase
  useEffect(() => {
    let cancelled = false;

    const loadStats = async () => {
      try {
        const { count: total } = await supabase
          .from("waitlist")
          .select("*", { count: "exact", head: true });

        if (!cancelled && total !== null) {
          setStats({
            total_joined: total,
            total_seats: DEFAULT_TOTAL_SEATS,
            remaining_seats: Math.max(DEFAULT_TOTAL_SEATS - total, 0),
            recent_joiners: [],
          });
        }
      } catch {
        // Keep local fallback values when Supabase is unavailable.
      }
    };

    loadStats();
    return () => {
      cancelled = true;
    };
  }, []);

  // Check if signed-in user is already on the waitlist
  useEffect(() => {
    if (!user?.email) {
      setMemberStatus(null);
      return;
    }

    let cancelled = false;

    const loadMemberStatus = async () => {
      try {
        const { data: row } = await supabase
          .from("waitlist")
          .select("created_at")
          .eq("email", user.email)
          .single();

        if (!row || cancelled) return;

        const { count: pos } = await supabase
          .from("waitlist")
          .select("*", { count: "exact", head: true })
          .lte("created_at", row.created_at);

        if (!cancelled) {
          setMemberStatus({
            email: user.email,
            joined: true,
            position: pos ?? null,
            total_joined: stats.total_joined,
            total_seats: stats.total_seats,
            remaining_seats: stats.remaining_seats,
          });
        }
      } catch {
        // Keep the waitlist state interactive even if the status lookup fails.
      }
    };

    loadMemberStatus();
    return () => {
      cancelled = true;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    if (memberStatus?.joined && memberStatus.position) {
      setPosition(memberStatus.position);
    }
  }, [memberStatus]);

  useEffect(() => {
    if (user?.email && !email) {
      setEmail(user.email);
    }
  }, [email, user]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail.includes("@") || !normalizedEmail.includes(".")) {
      setError("Please enter a valid email address.");
      return;
    }

    setEmail(normalizedEmail);
    setError("");
    setLoading(true);

    try {
      // Attempt insert — unique constraint on email catches duplicates
      const { data: inserted, error: insertError } = await supabase
        .from("waitlist")
        .insert({ email: normalizedEmail, name: name.trim() || null, profession: profession || null })
        .select("created_at")
        .single();

      let pos: number | null = null;
      let isAlreadyJoined = false;

      if (insertError) {
        // PostgreSQL unique violation code
        if (insertError.code === "23505") {
          isAlreadyJoined = true;
          const { data: existing } = await supabase
            .from("waitlist")
            .select("created_at")
            .eq("email", normalizedEmail)
            .single();

          if (existing) {
            const { count } = await supabase
              .from("waitlist")
              .select("*", { count: "exact", head: true })
              .lte("created_at", existing.created_at);
            pos = count ?? null;
          }
        } else {
          setError(insertError.message || "Something went wrong. Try again.");
          return;
        }
      } else if (inserted) {
        const { count } = await supabase
          .from("waitlist")
          .select("*", { count: "exact", head: true })
          .lte("created_at", inserted.created_at);
        pos = count ?? null;
      }

      const { count: newTotal } = await supabase
        .from("waitlist")
        .select("*", { count: "exact", head: true });

      setPosition(pos ?? 0);
      setAlreadyJoined(isAlreadyJoined);
      setSubmitted(true);
      setStats({
        total_joined: newTotal ?? stats.total_joined,
        total_seats: DEFAULT_TOTAL_SEATS,
        remaining_seats: Math.max(DEFAULT_TOTAL_SEATS - (newTotal ?? stats.total_joined), 0),
        recent_joiners: [],
      });
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const progressPct =
    stats.total_seats > 0 ? Math.min((stats.total_joined / stats.total_seats) * 100, 100) : 0;
  const signedInWaitlisted = Boolean(user && memberStatus?.joined);
  const showSuccessState = submitted || signedInWaitlisted;
  const effectivePosition = memberStatus?.position ?? position;

  const inputBg = isDark ? "#1C1916" : "white";
  const inputBorder = isDark ? "#2E2922" : "#EAEAEC";
  const inputColor = isDark ? "#F2EDE8" : "#262626";
  const perkBg = isDark ? "#141210" : "white";
  const perkBorder = isDark ? "#2E2922" : "#EAEAEC";
  const perkTitle = isDark ? "#F2EDE8" : "#404040";
  const perkDesc = isDark ? "rgba(242,237,232,0.45)" : "#737373";
  const progressTrack = isDark ? "#1C1916" : "#F5F5F4";
  const shareBg = isDark ? "#1C1916" : "#F5F5F4";
  const shareBorder = isDark ? "#2E2922" : "#EAEAEC";
  const shareColor = isDark ? "rgba(242,237,232,0.6)" : "#525252";
  const ctaBg = isDark ? "linear-gradient(135deg, #C4A882 0%, #A38A70 100%)" : "#0F172A";
  const ctaColor = isDark ? "#0C0B09" : "white";

  return (
    <section id="waitlist" className="relative overflow-hidden bg-[#F9F8F6] py-14 sm:py-28">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(163,138,112,0.08) 0%, rgba(122,139,118,0.05) 40%, transparent 70%)",
        }}
      />
      <div
        className="absolute top-0 left-0 right-0 h-px pointer-events-none"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(163,138,112,0.2), rgba(122,139,118,0.12), transparent)",
        }}
      />
      <div
        className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(163,138,112,0.2), rgba(122,139,118,0.12), transparent)",
        }}
      />

      <div className="relative z-10 mx-auto max-w-2xl px-6 text-center lg:px-10" ref={ref}>
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-8 flex items-center justify-center gap-2"
        >
          <div
            className="flex items-center gap-2 rounded-full px-3.5 py-1.5"
            style={{ background: "rgba(163,138,112,0.08)", border: "1px solid rgba(163,138,112,0.20)" }}
          >
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#A38A70]" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#8B6F52]">
              Beta Cohort · {stats.remaining_seats} seats left
            </span>
          </div>
        </motion.div>

        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, scale: 0.92 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: EASE }}
          className="mb-2"
        >
          <span
            className="text-[52px] sm:text-[80px] md:text-[100px] font-bold leading-none tracking-[-0.04em] tabular-nums"
            style={{ color: isDark ? "#C4A882" : "#2B241E" }}
          >
            {count.toLocaleString()}
          </span>
        </motion.div>

        <motion.h2
          initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55, delay: 0.1 }}
          className="mb-4 text-[22px] sm:text-[34px] md:text-[44px] font-bold leading-[1.1] tracking-[-0.03em] text-neutral-900"
        >
          creators already waiting.
          <br />
          <span className="text-neutral-500">Don&apos;t get left behind.</span>
        </motion.h2>

        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.16 }}
          className="mx-auto mb-4 max-w-lg text-[15px] leading-[1.75] text-neutral-500"
        >
          Ittera is being built quietly with a small early group. The first 100 people will step into the
          beta, test the product before anyone else, and help shape how Ittera feels before it opens to the public.
        </motion.p>

        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mx-auto mb-8 max-w-sm"
        >
          <div className="mb-1.5 flex justify-between text-[11px] text-neutral-500">
            <span>{stats.total_joined} joined</span>
            <span className="font-medium text-[#A38A70]/80">{stats.remaining_seats} seats remaining</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full" style={{ background: progressTrack }}>
            <motion.div
              className="h-full rounded-full"
              style={{ background: "linear-gradient(90deg, #0F172A, #A38A70, #7A8B76)" }}
              initial={{ width: 0 }}
              whileInView={{ width: `${progressPct}%` }}
              viewport={{ once: true }}
              transition={{ duration: 1.2, delay: 0.4, ease: EASE }}
            />
          </div>
          <div className="mt-1 text-right text-[10px] text-neutral-400">{stats.total_seats} total seats</div>
        </motion.div>

        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55, delay: 0.22 }}
          className="mb-4"
        >
          <AnimatePresence mode="wait">
            {showSuccessState ? (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-4 py-8"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.1 }}
                  className="flex h-16 w-16 items-center justify-center rounded-2xl"
                  style={{
                    background: "linear-gradient(135deg, rgba(163,138,112,0.15), rgba(122,139,118,0.10))",
                    border: "1px solid rgba(163,138,112,0.3)",
                    boxShadow: "0 0 30px rgba(163,138,112,0.12)",
                  }}
                >
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                    <path d="M20 6L9 17L4 12" stroke="#A38A70" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </motion.div>
                <div>
                  <p className="mb-1 text-[20px] font-bold text-neutral-900">
                    {signedInWaitlisted && !submitted
                      ? `You're already #${effectivePosition} on the list.`
                      : alreadyJoined
                        ? `You're already #${effectivePosition} on the list.`
                        : `You're #${effectivePosition} on the list.`}
                  </p>
                  <p className="mx-auto max-w-sm text-[14px] leading-6 text-neutral-500">
                    {signedInWaitlisted && !submitted
                      ? "Your account is already linked to a waitlist spot. We'll keep you updated here and by email."
                      : alreadyJoined
                      ? "That email is already locked in. Sign in or create your Ittera account with the same email to keep an eye on your beta status."
                      : "Check your inbox for a confirmation email. If you don't see it in a minute, check your spam folder — it sometimes lands there."}
                  </p>
                </div>
                {signedInWaitlisted ? (
                  <div
                    className="rounded-2xl px-4 py-3 text-[12px]"
                    style={{ background: shareBg, border: `1px solid ${shareBorder}`, color: shareColor }}
                  >
                    Signed in as {memberStatus?.email}. Current beta status: #{effectivePosition}.
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2 sm:flex-row">
                    <button
                      type="button"
                      onClick={() => openAuth("signup", email)}
                      className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-[12.5px] font-medium transition-all duration-200"
                      style={{ background: ctaBg, color: ctaColor }}
                    >
                      Create account to track status
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => openAuth("signin", email)}
                      className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-[12.5px] font-medium transition-all duration-200"
                      style={{ background: shareBg, border: `1px solid ${shareBorder}`, color: shareColor }}
                    >
                      Sign in instead
                    </button>
                  </div>
                )}
                <a
                  href={`https://twitter.com/intent/tweet?text=Just%20joined%20the%20%40itteraai%20waitlist%20-%20an%20AI%20content%20strategy%20engine%20for%20creators.%20Spot%20%23${effectivePosition}.`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 rounded-xl px-4 py-2 text-[12.5px] font-medium transition-all duration-200"
                  style={{ background: shareBg, border: `1px solid ${shareBorder}`, color: shareColor }}
                >
                  Share on X <ChevronRight className="h-3.5 w-3.5" />
                </a>
                <p className="text-[11px] text-neutral-400">
                  Confirmation email sent. Don&apos;t see it?{" "}
                  <span className="font-medium text-neutral-500">Check your spam folder.</span>
                </p>
              </motion.div>
            ) : (
              <motion.form key="form" onSubmit={handleSubmit} className="mx-auto flex max-w-md flex-col gap-2.5">
                {/* row 1: name + email */}
                <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your name"
                    className="h-12 w-full rounded-lg px-4 text-[14px] outline-none transition-all duration-200"
                    style={{ background: inputBg, border: `1px solid ${inputBorder}`, color: inputColor }}
                    onFocus={(e) => { e.currentTarget.style.border = "1px solid rgba(163,138,112,0.5)"; }}
                    onBlur={(e) => { e.currentTarget.style.border = `1px solid ${inputBorder}`; }}
                  />
                  <div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => { setEmail(e.target.value); setError(""); }}
                      placeholder="your@email.com"
                      required
                      className="h-12 w-full rounded-lg px-4 text-[14px] outline-none transition-all duration-200"
                      style={{ background: inputBg, border: `1px solid ${inputBorder}`, color: inputColor }}
                      onFocus={(e) => { e.currentTarget.style.border = "1px solid rgba(163,138,112,0.5)"; }}
                      onBlur={(e) => { e.currentTarget.style.border = `1px solid ${inputBorder}`; }}
                    />
                    {error && <p className="mt-1 text-[11px] text-red-400/70">{error}</p>}
                  </div>
                </div>

                {/* row 2: role / profession */}
                <select
                  value={profession}
                  onChange={(e) => setProfession(e.target.value)}
                  className="h-12 w-full rounded-lg px-4 text-[14px] outline-none transition-all duration-200 appearance-none"
                  style={{ background: inputBg, border: `1px solid ${inputBorder}`, color: profession ? inputColor : isDark ? "rgba(242,237,232,0.35)" : "#A3A3A3" }}
                  onFocus={(e) => { e.currentTarget.style.border = "1px solid rgba(163,138,112,0.5)"; }}
                  onBlur={(e) => { e.currentTarget.style.border = `1px solid ${inputBorder}`; }}
                >
                  <option value="" disabled>What best describes you?</option>
                  <option value="Creator / Influencer">Creator / Influencer</option>
                  <option value="Founder / Entrepreneur">Founder / Entrepreneur</option>
                  <option value="Working Professional">Working Professional</option>
                  <option value="Marketer">Marketer</option>
                  <option value="Developer">Developer</option>
                  <option value="Startup">Startup</option>
                  <option value="Agency">Agency</option>
                  <option value="Company">Company</option>
                  <option value="MSME">MSME</option>
                  <option value="Student">Student</option>
                  <option value="Other">Other</option>
                </select>

                {/* row 3: submit */}
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-glow flex h-12 items-center justify-center gap-2 rounded-lg px-6 text-[14px] font-semibold transition-all duration-200 hover:-translate-y-px disabled:opacity-60"
                  style={{ background: ctaBg, color: ctaColor }}
                >
                  {loading ? (
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : (
                    <>
                      Claim my seat
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </motion.form>
            )}
          </AnimatePresence>
        </motion.div>

        {!submitted && (
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 6 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.32 }}
            className="mb-10 mt-5"
          >
            {/* live stat strip */}
            <div
              className="mx-auto flex flex-wrap max-w-md items-center justify-between rounded-xl px-4 py-3 gap-x-4 gap-y-2"
              style={{ background: isDark ? "rgba(255,255,255,0.03)" : "rgba(15,23,42,0.03)", border: `1px solid ${isDark ? "rgba(255,255,255,0.07)" : "rgba(15,23,42,0.06)"}` }}
            >
              <div className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-[#7A8B76] animate-pulse" />
                <span className="text-[11px] font-medium" style={{ color: isDark ? "rgba(242,237,232,0.55)" : "#737373" }}>
                  <span className="font-semibold tabular-nums" style={{ color: isDark ? "#F2EDE8" : "#262626" }}>{stats.total_joined}</span> people joined
                </span>
              </div>
              <div className="h-3 w-px" style={{ background: isDark ? "rgba(255,255,255,0.1)" : "rgba(15,23,42,0.08)" }} />
              <div className="flex items-center gap-1.5">
                <TrendingUp className="h-3 w-3 text-[#A38A70]" />
                <span className="text-[11px]" style={{ color: isDark ? "rgba(242,237,232,0.55)" : "#737373" }}>
                  <span className="font-semibold tabular-nums" style={{ color: "#A38A70" }}>{stats.remaining_seats}</span> seats left
                </span>
              </div>
              <div className="h-3 w-px" style={{ background: isDark ? "rgba(255,255,255,0.1)" : "rgba(15,23,42,0.08)" }} />
              <p className="text-[11px]" style={{ color: isDark ? "rgba(242,237,232,0.35)" : "#A3A3A3" }}>No spam · Unsubscribe anytime</p>
            </div>
          </motion.div>
        )}

        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.36 }}
          className="grid grid-cols-2 gap-3"
        >
          {PERKS.map((perk) => {
            const Icon = perk.icon;
            return (
              <div
                key={perk.title}
                className="flex items-start gap-3 rounded-xl p-4 text-left"
                style={{ background: perkBg, border: `1px solid ${perkBorder}` }}
              >
                <div
                  className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg"
                  style={{ background: "rgba(163,138,112,0.1)" }}
                >
                  <Icon className="h-3.5 w-3.5 text-[#8B6F52]" />
                </div>
                <div>
                  <p className="mb-0.5 text-[12.5px] font-semibold leading-tight" style={{ color: perkTitle }}>
                    {perk.title}
                  </p>
                  <p className="text-[11px] leading-tight" style={{ color: perkDesc }}>
                    {perk.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}


