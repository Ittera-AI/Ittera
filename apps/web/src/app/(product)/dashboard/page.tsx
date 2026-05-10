"use client";

import Link from "next/link";
import { useEffect, useMemo } from "react";
import { PenLine, CalendarDays, BarChart2, Radar, ArrowRight, CheckCircle2, Circle, Loader2 } from "lucide-react";

import { ProductShell } from "@/components/product/ProductShell";
import { useAuth } from "@/context/AuthContext";
import { useProduct } from "@/hooks/useProduct";

function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div
      className="rounded-xl border p-5 flex flex-col gap-1 transition-all duration-200 hover:border-border-hover"
      style={{ background: "var(--card)" }}
    >
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</p>
      <p
        className="text-3xl font-semibold tracking-tight mt-1"
        style={accent ? { color: "var(--bronze)" } : undefined}
      >
        {value}
      </p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  );
}

function ScoreRing({ score, size = 44 }: { score: number; size?: number }) {
  const r = (size - 6) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score);
  const color = score >= 0.7 ? "var(--olive)" : score >= 0.5 ? "var(--bronze)" : "#ef4444";

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rotate-[-90deg]">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={4} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={4}
        strokeDasharray={circ}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset 600ms cubic-bezier(0.23,1,0.32,1)" }}
      />
    </svg>
  );
}

const STEPS = [
  { key: "source", label: "Connect LinkedIn source" },
  { key: "sync", label: "Sync post history" },
  { key: "profile", label: "Generate brand profile" },
  { key: "confirm", label: "Confirm your voice" },
] as const;

export default function DashboardPage() {
  const { user } = useAuth();
  const product = useProduct();
  const loadDashboard = product.loadDashboard;
  const loadDrafts = product.loadDrafts;
  const loadCalendar = product.loadCalendar;

  useEffect(() => {
    void loadDashboard();
    void loadDrafts();
    void loadCalendar();
  }, [loadDashboard, loadDrafts, loadCalendar]);

  const greeting = useMemo(() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  }, []);

  const stepStatus = {
    source: !!product.linkedin?.connected,
    sync: !!product.linkedin?.synced_posts,
    profile: !!product.brandProfile?.profile,
    confirm: !!product.brandProfile?.is_confirmed,
  };

  const doneCount = Object.values(stepStatus).filter(Boolean).length;
  const progress = doneCount / STEPS.length;

  const scheduled = product.calendar.filter((e) => e.status === "scheduled").length;
  const published = product.calendar.filter((e) => e.status === "published").length;

  const recentDrafts = product.drafts.slice(0, 3);

  return (
    <ProductShell>
      <div className="flex flex-col gap-8">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="eyebrow">{greeting}</p>
            <h1 className="mt-1.5 text-3xl font-semibold tracking-[-0.04em]">
              {user ? `${user.name.split(" ")[0]}'s workspace` : "Your content cockpit"}
            </h1>
            <p className="mt-1.5 max-w-xl text-sm text-muted-foreground">
              Build the strategy loop: signal → voice → draft → publish → learn.
            </p>
          </div>
          {/* Setup progress ring */}
          {doneCount < 4 && (
            <div className="flex items-center gap-3 rounded-xl border px-4 py-3" style={{ background: "var(--card)" }}>
              <div className="relative">
                <ScoreRing score={progress} size={48} />
                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-semibold" style={{ color: "var(--bronze)" }}>
                  {doneCount}/4
                </span>
              </div>
              <div>
                <p className="text-xs font-semibold text-foreground">Setup progress</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">Complete to unlock all features</p>
              </div>
            </div>
          )}
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Drafts" value={product.drafts.length} sub="total created" />
          <StatCard label="Scheduled" value={scheduled} sub="upcoming posts" accent={scheduled > 0} />
          <StatCard label="Published" value={published} sub="posts live" />
          <StatCard
            label="LinkedIn posts"
            value={product.linkedin?.synced_posts ?? 0}
            sub="synced"
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          {/* Setup checklist */}
          <div className="rounded-xl border p-6" style={{ background: "var(--card)" }}>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-sm font-semibold text-foreground">Getting started</h2>
                <p className="text-xs text-muted-foreground mt-0.5">Complete these steps to unlock the full content engine.</p>
              </div>
              {doneCount === 4 && (
                <span
                  className="text-xs font-semibold px-2.5 py-1 rounded-full"
                  style={{ background: "rgba(150,165,145,0.15)", color: "var(--olive)" }}
                >
                  Ready ✓
                </span>
              )}
            </div>
            <div className="space-y-3">
              {STEPS.map(({ key, label }, i) => {
                const done = stepStatus[key];
                return (
                  <div
                    key={key}
                    className="flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors"
                    style={{
                      background: done ? "rgba(150,165,145,0.08)" : "transparent",
                      animationDelay: `${i * 60}ms`,
                    }}
                  >
                    {done ? (
                      <CheckCircle2 size={16} style={{ color: "var(--olive)" }} className="flex-shrink-0" />
                    ) : (
                      <Circle size={16} className="text-muted-foreground/40 flex-shrink-0" />
                    )}
                    <span className={`text-sm ${done ? "line-through text-muted-foreground" : "text-foreground"}`}>
                      {label}
                    </span>
                    {!done && i === doneCount && (
                      <span
                        className="ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full"
                        style={{ background: "rgba(163,138,112,0.15)", color: "var(--bronze)" }}
                      >
                        Next
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
            <div className="mt-5 flex gap-2 flex-wrap">
              <button
                onClick={() => void product.connectLinkedIn()}
                disabled={product.isLoading || stepStatus.source}
                className="flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-all active:scale-[0.97] disabled:opacity-40"
                style={{ background: "var(--muted)" }}
              >
                {product.isLoading && <Loader2 size={12} className="animate-spin" />}
                Connect LinkedIn
              </button>
              <button
                onClick={() => void product.syncLinkedIn()}
                disabled={product.isLoading || !stepStatus.source || stepStatus.sync}
                className="flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-all active:scale-[0.97] disabled:opacity-40"
                style={{ background: "var(--muted)" }}
              >
                Sync posts
              </button>
              <button
                onClick={() => void product.generateBrandProfile()}
                disabled={product.isLoading || !stepStatus.sync || stepStatus.confirm}
                className="flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-all active:scale-[0.97] disabled:opacity-40"
                style={{ background: "var(--muted)" }}
              >
                Generate profile
              </button>
            </div>
          </div>

          {/* Quick actions */}
          <div className="flex flex-col gap-3">
            <h2 className="text-sm font-semibold text-foreground px-0.5">Quick actions</h2>
            {[
              { href: "/create", icon: PenLine, label: "Create content", sub: "Turn a trend into a draft" },
              { href: "/calendar", icon: CalendarDays, label: "View calendar", sub: `${scheduled} post${scheduled !== 1 ? "s" : ""} scheduled` },
              { href: "/analytics", icon: BarChart2, label: "See analytics", sub: "Review your top posts" },
              { href: "/radar", icon: Radar, label: "Scan Trend Radar", sub: "Catch today&apos;s signals" },
            ].map(({ href, icon: Icon, label, sub }) => (
              <Link
                key={href}
                href={href}
                className="group flex items-center gap-4 rounded-xl border px-4 py-3.5 transition-all duration-150 hover:border-border-hover active:scale-[0.98]"
                style={{ background: "var(--card)" }}
              >
                <div
                  className="h-9 w-9 flex-shrink-0 rounded-lg flex items-center justify-center"
                  style={{ background: "var(--muted)" }}
                >
                  <Icon size={16} className="text-muted-foreground group-hover:text-foreground transition-colors" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground">{label}</p>
                  <p className="text-xs text-muted-foreground truncate" dangerouslySetInnerHTML={{ __html: sub }} />
                </div>
                <ArrowRight size={14} className="text-muted-foreground/40 group-hover:text-muted-foreground transition-colors flex-shrink-0" />
              </Link>
            ))}
          </div>
        </div>

        {/* Recent drafts */}
        {recentDrafts.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-foreground">Recent drafts</h2>
              <Link href="/create" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                View all →
              </Link>
            </div>
            <div className="space-y-2">
              {recentDrafts.map((draft) => (
                <div
                  key={draft.id}
                  className="flex items-center gap-4 rounded-xl border px-4 py-3.5"
                  style={{ background: "var(--card)" }}
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-foreground truncate">
                      {(draft.content ?? "").split("\n")[0]?.slice(0, 72) || "Untitled draft"}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {draft.platform} · {draft.status}
                    </p>
                  </div>
                  <span
                    className="flex-shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize"
                    style={{
                      background:
                        draft.status === "published"
                          ? "rgba(150,165,145,0.15)"
                          : draft.status === "scheduled"
                          ? "rgba(163,138,112,0.15)"
                          : "var(--muted)",
                      color:
                        draft.status === "published"
                          ? "var(--olive)"
                          : draft.status === "scheduled"
                          ? "var(--bronze)"
                          : "var(--text-muted)",
                    }}
                  >
                    {draft.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </ProductShell>
  );
}
