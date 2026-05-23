"use client";

import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Calendar,
  Check,
  ChevronDown,
  LogOut,
  MessageSquare,
  RefreshCw,
  Share2,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import GrainOverlay from "@/components/ui/GrainOverlay";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { ROUTES } from "@/lib/routes";
import type { User } from "@/context/AuthContext";

const EASE: [number, number, number, number] = [0.16, 1, 0.3, 1];
const RING_R = 82;
const RING_C = +(2 * Math.PI * RING_R).toFixed(2);

export type WaitlistStats = {
  total_joined: number;
  total_seats: number;
  remaining_seats: number;
  recent_joiners: string[];
};

type Props = {
  user: User;
  waitlistPosition: number | null;
  positionLoading: boolean;
  positionError?: string | null;
  stats: WaitlistStats | null;
  refreshing: boolean;
  justRefreshed: boolean;
  refreshError: string | null;
  onRefresh: () => void;
  onSignOut: () => void;
};

const STEPS = ["Applied", "In review", "Approved"] as const;
const ACTIVE_STEP = 1;

const MODULES = [
  { icon: Calendar, label: "Calendar" },
  { icon: Zap, label: "Repurpose" },
  { icon: TrendingUp, label: "Radar" },
  { icon: MessageSquare, label: "Coach" },
];

function easeOutCubic(t: number) {
  return 1 - Math.pow(1 - t, 3);
}

function useCountUp(target: number | null, reducedMotion: boolean) {
  const [animated, setAnimated] = useState(0);

  useEffect(() => {
    if (target == null) return;
    if (reducedMotion) return;

    let step = 0;
    const steps = 32;
    const duration = 1100;
    const timer = setInterval(() => {
      step += 1;
      setAnimated(Math.round(easeOutCubic(step / steps) * target));
      if (step >= steps) clearInterval(timer);
    }, duration / steps);
    return () => clearInterval(timer);
  }, [target, reducedMotion]);

  if (target == null) return 0;
  if (reducedMotion) return target;
  return animated;
}

function PositionRing({
  position,
  fill,
  reducedMotion,
  loading,
  error,
}: {
  position: number | null;
  fill: number;
  reducedMotion: boolean;
  loading: boolean;
  error?: string | null;
}) {
  const offset = +(RING_C - (fill / 100) * RING_C).toFixed(2);
  const display = useCountUp(position, reducedMotion);

  return (
    <div className="relative mx-auto lg:mx-0" style={{ width: 240, height: 240 }}>
      <div
        className="absolute inset-4 rounded-full opacity-80"
        style={{
          background: "radial-gradient(circle, rgba(163,138,112,0.22) 0%, transparent 72%)",
          filter: "blur(20px)",
        }}
      />

      <svg width="240" height="240" viewBox="0 0 200 200" aria-hidden="true" className="h-full w-full">
        <defs>
          <linearGradient id="wl-ring" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--bronze)" />
            <stop offset="100%" stopColor="var(--olive)" />
          </linearGradient>
        </defs>
        <circle cx="100" cy="100" r={RING_R} fill="none" stroke="var(--border)" strokeWidth="1" />
        <motion.circle
          cx="100"
          cy="100"
          r={RING_R}
          fill="none"
          stroke="url(#wl-ring)"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeDasharray={RING_C}
          initial={{ strokeDashoffset: RING_C }}
          animate={{ strokeDashoffset: offset }}
          transition={reducedMotion ? { duration: 0 } : { duration: 1.4, ease: EASE }}
          transform="rotate(-90 100 100)"
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {loading ? (
          <div className="flex flex-col items-center gap-2">
            <div
              className="h-7 w-7 animate-spin rounded-full border-2 border-transparent"
              style={{
                borderTopColor: "var(--bronze)",
                borderRightColor: "rgba(163,138,112,0.15)",
              }}
            />
            <span className="text-xs font-medium text-[var(--text-muted)]">Loading position…</span>
          </div>
        ) : position != null ? (
          <>
            <span className="text-[9px] font-bold uppercase tracking-[0.24em] text-[var(--text-muted)]">
              Queue
            </span>
            <div className="mt-1 flex items-start leading-none">
              <span className="mt-3 text-xl font-black text-[var(--bronze)]">#</span>
              <span className="text-[4.5rem] font-black tabular-nums tracking-[-0.04em] lg:text-[5.5rem]">
                {display}
              </span>
            </div>
          </>
        ) : error ? (
          <div className="flex flex-col items-center gap-2 px-4 text-center">
            <span className="text-xs font-semibold text-red-500 dark:text-red-400">Could not load position</span>
            <span className="text-[10px] leading-relaxed text-[var(--text-muted)]">{error}</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 px-4 text-center">
            <div className="flex h-11 w-11 items-center justify-center rounded-full border border-[rgba(163,138,112,0.25)] bg-[rgba(163,138,112,0.1)]">
              <Check className="h-5 w-5 text-[var(--bronze)]" strokeWidth={2.5} />
            </div>
            <span className="text-xs font-semibold text-[var(--text-soft)]">You&apos;re on the list</span>
            <span className="text-[10px] text-[var(--text-muted)]">Tap Check status to refresh</span>
          </div>
        )}
      </div>
    </div>
  );
}

function StepTrack() {
  return (
    <div className="flex items-start justify-between">
      {STEPS.map((label, i) => {
        const done = i < ACTIVE_STEP;
        const active = i === ACTIVE_STEP;
        return (
          <div key={label} className="flex flex-1 flex-col items-center" role="listitem">
            <div className="relative flex w-full items-center justify-center">
              {i > 0 && (
                <div
                  className="absolute right-1/2 top-3 h-px w-full -translate-y-1/2"
                  style={{
                    background:
                      done || active ? "rgba(163,138,112,0.4)" : "var(--border)",
                  }}
                  aria-hidden="true"
                />
              )}
              <div
                className={`relative z-10 flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-bold ${
                  active
                    ? "bg-[var(--bronze)] text-[#0C0B09] shadow-[0_0_0_4px_rgba(163,138,112,0.15)]"
                    : done
                      ? "border border-[rgba(163,138,112,0.35)] bg-[rgba(163,138,112,0.12)] text-[var(--bronze)]"
                      : "border border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)]"
                }`}
                aria-current={active ? "step" : undefined}
              >
                {done ? <Check className="h-3.5 w-3.5" strokeWidth={2.5} /> : i + 1}
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className="absolute left-1/2 top-3 h-px w-full -translate-y-1/2"
                  style={{
                    background:
                      i < ACTIVE_STEP ? "rgba(163,138,112,0.4)" : "var(--border)",
                  }}
                  aria-hidden="true"
                />
              )}
            </div>
            <span
              className={`mt-2 text-center text-[11px] font-semibold leading-tight ${
                active ? "text-[var(--bronze)]" : "text-[var(--text-muted)]"
              }`}
            >
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function ProfileDropdown({ user, onSignOut }: { user: User; onSignOut: () => void }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="group flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface-1)] py-1 pl-1 pr-3 transition-all duration-300 hover:bg-[var(--surface-2)] hover:shadow-sm"
      >
        <span
          className="flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-bold text-white shadow-sm"
          style={{ background: "linear-gradient(135deg, var(--bronze), #8B6040)" }}
        >
          {user.initials}
        </span>
        <span className="hidden text-[13px] font-medium tracking-tight text-[var(--text)] sm:block">
          {user.name.split(" ")[0]}
        </span>
        <ChevronDown
          className="h-3.5 w-3.5 text-[var(--text-muted)] transition-transform duration-300"
          style={{ transform: isOpen ? "rotate(180deg)" : "rotate(0deg)" }}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: 6, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 4, scale: 0.96 }}
              transition={{ duration: 0.16, ease: [0.16, 1, 0.3, 1] }}
              className="absolute right-0 top-[calc(100%+8px)] z-50 w-64 rounded-[1.25rem] border border-[var(--border)] bg-[var(--surface)]/85 p-2 shadow-[0_16px_40px_-12px_rgba(0,0,0,0.15)] backdrop-blur-2xl"
            >
              <div className="mb-1.5 rounded-xl bg-[var(--surface-1)]/50 px-3.5 py-3">
                <p className="text-[14px] font-semibold tracking-tight text-[var(--text)] truncate">
                  {user.name}
                </p>
                <p className="mt-0.5 text-[12px] text-[var(--text-muted)] truncate">
                  {user.email}
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  onSignOut();
                }}
                className="group flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13px] font-semibold text-[var(--text-muted)] transition-all duration-200 hover:bg-red-500/10 hover:text-red-500"
              >
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--surface-2)] transition-colors group-hover:bg-red-500/20 group-hover:text-red-600">
                  <LogOut className="h-3.5 w-3.5" />
                </div>
                Sign out
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function WaitlistStatusView({
  user,
  waitlistPosition,
  positionLoading,
  positionError,
  stats,
  refreshing,
  justRefreshed,
  refreshError,
  onRefresh,
  onSignOut,
}: Props) {
  const reducedMotion = Boolean(useReducedMotion());
  const [linkCopied, setLinkCopied] = useState(false);
  const firstName = user.name.split(/\s+/)[0] || "there";
  const ahead =
    waitlistPosition != null && waitlistPosition > 1 ? waitlistPosition - 1 : 0;
  const queueFill =
    waitlistPosition != null
      ? Math.max(12, Math.min(88, 100 - waitlistPosition * 0.45))
      : 36;
  const cohortFill =
    stats && stats.total_seats > 0
      ? Math.min(100, Math.round((stats.total_joined / stats.total_seats) * 100))
      : 0;

  const reveal = (delay: number) =>
    reducedMotion
      ? {}
      : {
          initial: { opacity: 0, y: 12 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.55, delay, ease: EASE },
        };

  const handleInviteFriend = async () => {
    const url = `${window.location.origin}/#waitlist`;
    try {
      await navigator.clipboard.writeText(url);
      setLinkCopied(true);
      window.setTimeout(() => setLinkCopied(false), 2500);
    } catch {
      window.prompt("Copy this link to invite a friend:", url);
    }
  };

  return (
    <main className="relative flex min-h-screen flex-col bg-[var(--bg)] text-[var(--text)]">
      <GrainOverlay />

      {/* Full-screen ambient */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 20% 0%, rgba(163,138,112,0.1) 0%, transparent 55%), radial-gradient(ellipse 60% 45% at 85% 100%, rgba(122,139,118,0.08) 0%, transparent 50%)",
        }}
      />
      <motion.div
        className="pointer-events-none absolute -left-32 top-1/4 h-[500px] w-[500px] rounded-full opacity-50"
        style={{ background: "radial-gradient(circle, rgba(163,138,112,0.12) 0%, transparent 70%)" }}
        animate={reducedMotion ? {} : { x: [0, 30, 0], y: [0, -20, 0] }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="pointer-events-none absolute -right-32 bottom-0 h-[420px] w-[420px] rounded-full opacity-40"
        style={{ background: "radial-gradient(circle, rgba(122,139,118,0.1) 0%, transparent 70%)" }}
        animate={reducedMotion ? {} : { x: [0, -25, 0], y: [0, 15, 0] }}
        transition={{ duration: 24, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-30"
        style={{ background: "radial-gradient(circle, rgba(163,138,112,0.08) 0%, transparent 60%)" }}
        animate={reducedMotion ? {} : { scale: [1, 1.05, 1], opacity: [0.2, 0.3, 0.2] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-px"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(163,138,112,0.35), transparent)",
        }}
      />

      {/* Header — full width */}
      <header className="sticky top-0 z-50 w-full border-b border-[var(--border)]/70 bg-[var(--bg)]/75 backdrop-blur-2xl">
        <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-12">
          <Link href={ROUTES.waitlistStatus} className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--onyx)] text-[10px] font-black text-white dark:bg-[var(--bronze)] dark:text-[#0C0B09]">
              It
            </div>
            <span className="text-[13px] font-semibold tracking-tight">Ittera</span>
          </Link>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <ProfileDropdown user={user} onSignOut={onSignOut} />
          </div>
        </div>
      </header>

      {/* Full-width body */}
      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 flex-col px-5 pb-12 pt-8 sm:px-8 sm:pt-10 lg:min-h-[calc(100vh-3.5rem)] lg:justify-center lg:px-12 lg:py-12">
        <div className="grid w-full gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:gap-8 xl:gap-12">
          {/* ── Left: status ── */}
          <motion.article
            {...reveal(0)}
            className="flex flex-col overflow-hidden rounded-[28px] border border-[var(--border)] bg-[var(--surface)]/95 shadow-[0_1px_0_rgba(255,255,255,0.04)_inset,0_32px_80px_-32px_var(--shadow-md)] backdrop-blur-sm lg:min-h-[560px]"
            aria-labelledby="waitlist-heading"
          >
            <div
              className="h-px w-full shrink-0"
              style={{
                background:
                  "linear-gradient(90deg, transparent 5%, rgba(163,138,112,0.5) 50%, transparent 95%)",
              }}
            />

            <div className="flex flex-1 flex-col px-6 py-8 sm:px-10 sm:py-10 lg:px-12 lg:py-12">
              <div className="mb-6 lg:mb-8">
                <span className="inline-flex items-center gap-2 rounded-full border border-[rgba(163,138,112,0.22)] bg-[rgba(163,138,112,0.06)] px-3.5 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--bronze)]">
                  <span className="relative flex h-1.5 w-1.5">
                    {!reducedMotion && (
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--bronze)] opacity-50" />
                    )}
                    <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[var(--bronze)]" />
                  </span>
                  In review
                </span>
              </div>

              <div className="grid flex-1 gap-8 lg:grid-cols-[auto_1fr] lg:items-center lg:gap-10">
                <div className="flex justify-center lg:justify-start">
                  <PositionRing
                    position={waitlistPosition}
                    fill={queueFill}
                    reducedMotion={reducedMotion}
                    loading={positionLoading}
                    error={positionError}
                  />
                </div>

                <div className="text-center lg:text-left">
                  <h1
                    id="waitlist-heading"
                    className="text-[1.75rem] font-bold leading-[1.12] tracking-[-0.025em] sm:text-[2rem] lg:text-[2.25rem]"
                  >
                    {positionLoading ? (
                      <>Loading your spot, {firstName}…</>
                    ) : waitlistPosition != null ? (
                      <>
                        You&apos;re{" "}
                        <span className="text-[var(--bronze)]">#{waitlistPosition}</span>
                        , {firstName}
                      </>
                    ) : positionError ? (
                      <>Couldn&apos;t load your spot, {firstName}</>
                    ) : (
                      <>You&apos;re in, {firstName}</>
                    )}
                  </h1>

                  <p className="mt-4 text-[14px] leading-[1.7] text-[var(--text-muted)] lg:max-w-md">
                    {ahead > 0 && (
                      <>
                        <span className="font-semibold text-[var(--text-soft)]">
                          {ahead.toLocaleString()}
                        </span>{" "}
                        {ahead === 1 ? "person" : "people"} ahead of you.{" "}
                      </>
                    )}
                    We&apos;ll email you at{" "}
                    <span className="font-medium text-[var(--text-soft)]">{user.email}</span> the
                    moment you&apos;re approved.
                  </p>

                  {/* Step track — desktop inline under copy */}
                  <div
                    className="mt-8 hidden rounded-2xl border border-[var(--border)] bg-[var(--surface-1)]/80 px-5 py-4 lg:block"
                    role="list"
                    aria-label="Approval progress"
                  >
                    <StepTrack />
                  </div>
                </div>
              </div>

              {/* Step track — mobile */}
              <div
                className="mt-8 rounded-2xl border border-[var(--border)] bg-[var(--surface-1)]/80 px-4 py-5 lg:hidden"
                role="list"
                aria-label="Approval progress"
              >
                <StepTrack />
              </div>

              {/* Cohort + actions — bottom of card */}
              <div className="mt-auto pt-8">
                {stats && stats.total_joined > 0 && (
                  <div className="mb-6">
                    <div className="mb-2 flex items-center justify-between text-xs">
                      <span className="font-medium text-[var(--text-muted)]">
                        {stats.total_joined.toLocaleString()} in cohort
                      </span>
                      <span className="font-semibold text-[var(--bronze)]">
                        {stats.remaining_seats} seats left
                      </span>
                    </div>
                    <div
                      className="h-1.5 overflow-hidden rounded-full bg-[var(--surface-2)]"
                      role="progressbar"
                      aria-valuenow={cohortFill}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label="Cohort capacity"
                    >
                      <motion.div
                        className="h-full rounded-full"
                        style={{
                          background:
                            "linear-gradient(90deg, var(--onyx) 0%, var(--bronze) 55%, var(--olive) 100%)",
                        }}
                        initial={{ width: "0%" }}
                        animate={{ width: `${cohortFill}%` }}
                        transition={reducedMotion ? { duration: 0 } : { duration: 1.1, ease: EASE }}
                      />
                    </div>
                    {stats.recent_joiners.length > 0 && (
                      <div className="mt-3 flex items-center gap-2 lg:justify-start">
                        <div className="flex -space-x-2" aria-hidden="true">
                          {stats.recent_joiners.slice(0, 5).map((init, idx) => (
                            <span
                              key={`${init}-${idx}`}
                              className="inline-flex h-6 w-6 items-center justify-center rounded-full border-2 border-[var(--surface)] bg-[var(--surface-2)] text-[8px] font-bold text-[var(--text-muted)]"
                            >
                              {init}
                            </span>
                          ))}
                        </div>
                        <span className="text-[11px] text-[var(--text-muted)]">Joined recently</span>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex flex-col gap-3 sm:flex-row">
                  <button
                    type="button"
                    onClick={onRefresh}
                    disabled={refreshing}
                    className="group relative inline-flex flex-1 items-center justify-center gap-2 overflow-hidden rounded-xl bg-[var(--onyx)] py-3.5 text-sm font-semibold text-white shadow-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100 dark:bg-[var(--bronze)] dark:text-[#0C0B09]"
                  >
                    <div className="absolute inset-0 translate-y-full bg-white/20 mix-blend-overlay transition-transform duration-300 group-hover:translate-y-0" />
                    <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : "transition-transform duration-500 group-hover:rotate-180"}`} />
                    {justRefreshed ? "Up to date" : "Check status"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleInviteFriend()}
                    className="group relative inline-flex flex-1 items-center justify-center gap-2 overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface-1)] py-3.5 text-sm font-semibold text-[var(--text)] transition-all duration-300 hover:scale-[1.02] hover:border-[rgba(163,138,112,0.3)] hover:bg-[var(--surface-2)] hover:shadow-sm"
                  >
                    <Share2 className="h-4 w-4 text-[var(--text-muted)] transition-transform duration-300 group-hover:scale-110 group-hover:text-[var(--bronze)]" />
                    {linkCopied ? "Link copied!" : "Invite a friend"}
                  </button>
                </div>
                {refreshError && (
                  <p className="mt-3 text-center text-xs text-red-500 dark:text-red-400" role="alert">
                    {refreshError}
                  </p>
                )}
              </div>
            </div>
          </motion.article>

          {/* ── Right: demo panel ── */}
          <motion.section
            {...reveal(0.1)}
            className="flex flex-col overflow-hidden rounded-[28px] border border-[rgba(163,138,112,0.18)] lg:min-h-[560px]"
            style={{
              background:
                "linear-gradient(160deg, rgba(163,138,112,0.09) 0%, rgba(122,139,118,0.04) 40%, var(--surface) 100%)",
            }}
          >
            <div className="flex flex-1 flex-col p-6 sm:p-8 lg:p-10">
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-[rgba(163,138,112,0.22)] bg-[rgba(163,138,112,0.1)]">
                  <Sparkles className="h-5 w-5 text-[var(--bronze)]" />
                </div>
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--bronze)]">
                    While you wait
                  </p>
                  <h2 className="text-lg font-bold tracking-tight sm:text-xl">
                    Explore the full product
                  </h2>
                </div>
              </div>

              <p className="max-w-md text-sm leading-relaxed text-[var(--text-muted)]">
                The demo is fully interactive — see the AI calendar, trend radar, and engagement
                coach before anyone else. No extra signup required.
              </p>

              {/* Module grid — fills space */}
              <div className="my-8 grid flex-1 grid-cols-2 gap-3 sm:gap-4">
                {MODULES.map(({ icon: Icon, label }) => (
                  <Link
                    key={label}
                    href={ROUTES.demo}
                    className="group flex flex-col justify-between rounded-2xl border border-[var(--border)] bg-[var(--surface)]/60 p-4 transition-all duration-300 hover:-translate-y-1 hover:border-[rgba(163,138,112,0.35)] hover:bg-[var(--surface)] hover:shadow-[0_8px_24px_-8px_rgba(163,138,112,0.15)]"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[rgba(163,138,112,0.08)] transition-transform duration-300 group-hover:scale-110 group-hover:bg-[rgba(163,138,112,0.15)]">
                      <Icon className="h-5 w-5 text-[var(--bronze)]" aria-hidden="true" />
                    </div>
                    <p className="mt-4 text-sm font-semibold transition-colors group-hover:text-[var(--bronze)]">{label}</p>
                  </Link>
                ))}
              </div>

              <Link
                href={ROUTES.demo}
                className="group relative mt-auto inline-flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)] py-4 text-sm font-semibold shadow-sm transition-all duration-300 hover:border-[rgba(163,138,112,0.3)] hover:bg-[var(--surface-1)] hover:shadow-md"
              >
                Explore the demo
                <ArrowRight className="h-4 w-4 text-[var(--bronze)] transition-transform duration-300 group-hover:translate-x-1" />
              </Link>
            </div>
          </motion.section>
        </div>

        {/* Footer — full width */}
        <motion.p
          {...reveal(0.2)}
          className="mt-8 text-center text-xs leading-relaxed text-[var(--text-muted)] lg:mt-10"
        >
          We approve in batches and notify you by email.{" "}
          <span className="font-medium text-[var(--text-soft)]">
            No action needed from your end.
          </span>
        </motion.p>
      </div>
    </main>
  );
}
