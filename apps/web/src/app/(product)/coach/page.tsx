"use client";

import { useState } from "react";
import { Zap, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { ProductShell } from "@/components/product/ProductShell";
import { useProduct } from "@/hooks/useProduct";

const PLATFORMS = [
  { value: "linkedin", label: "LinkedIn" },
  { value: "twitter", label: "X / Twitter" },
  { value: "instagram", label: "Instagram" },
] as const;

function ScoreRing({ score }: { score: number }) {
  const size = 80;
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score);
  const color =
    score >= 0.8 ? "var(--olive)" : score >= 0.6 ? "var(--bronze)" : "#ef4444";
  const label = score >= 0.8 ? "Strong" : score >= 0.6 ? "Good" : "Needs work";

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rotate-[-90deg]">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={6} />
          <circle
            cx={size / 2} cy={size / 2} r={r}
            fill="none" stroke={color} strokeWidth={6}
            strokeDasharray={circ} strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 800ms cubic-bezier(0.23,1,0.32,1)" }}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="text-lg font-bold text-foreground">{Math.round(score * 100)}</span>
          <span className="text-[9px] text-muted-foreground">/ 100</span>
        </div>
      </div>
      <p className="text-xs font-semibold" style={{ color }}>{label}</p>
    </div>
  );
}

export default function CoachPage() {
  const product = useProduct();
  const [content, setContent] = useState("");
  const [platform, setPlatform] = useState<"linkedin" | "twitter" | "instagram">("linkedin");
  const [goal, setGoal] = useState("");
  const result = product.coachResult;

  async function handleAnalyze() {
    if (!content.trim()) return;
    await product.coachAnalyze(content.trim(), platform, goal.trim() || undefined);
  }

  return (
    <ProductShell>
      <div className="flex flex-col gap-8">
        {/* Header */}
        <div>
          <p className="eyebrow">Engagement Coach</p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-[-0.04em]">Make your content earn its place</h1>
          <p className="mt-1.5 max-w-xl text-sm text-muted-foreground">
            Paste any content draft. Coach scores it on hook strength, structure, and platform fit — then tells you exactly how to improve it.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          {/* Input panel */}
          <div className="flex flex-col gap-5">
            <div
              className="rounded-xl border p-5 flex flex-col gap-5"
              style={{ background: "var(--card)" }}
            >
              {/* Platform */}
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2">
                  Platform
                </label>
                <div className="flex gap-1.5">
                  {PLATFORMS.map(({ value, label }) => (
                    <button
                      key={value}
                      onClick={() => setPlatform(value)}
                      className="flex-1 rounded-lg py-2 text-xs font-semibold transition-all active:scale-[0.97]"
                      style={{
                        background: platform === value ? "var(--foreground)" : "var(--muted)",
                        color: platform === value ? "var(--background)" : "var(--text-muted)",
                      }}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Content */}
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2">
                  Content draft
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste your content draft here. The more complete, the more accurate the coaching…"
                  className="w-full resize-none rounded-lg border px-3 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 transition-all leading-relaxed"
                  style={{
                    background: "var(--muted)",
                    borderColor: "var(--border)",
                    minHeight: "180px",
                  }}
                />
                <p className="text-[10px] text-muted-foreground mt-1 text-right">
                  {content.length} characters
                </p>
              </div>

              {/* Goal */}
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2">
                  Goal <span className="font-normal normal-case tracking-normal text-muted-foreground/60">(optional)</span>
                </label>
                <input
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="e.g. drive profile visits, establish credibility, get saves…"
                  className="w-full rounded-lg border px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 transition-all"
                  style={{ background: "var(--muted)", borderColor: "var(--border)" }}
                />
              </div>

              <button
                onClick={() => void handleAnalyze()}
                disabled={!content.trim() || product.isLoading}
                className="flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold transition-all active:scale-[0.97] disabled:opacity-40"
                style={{ background: "var(--foreground)", color: "var(--background)" }}
              >
                {product.isLoading ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Zap size={14} />
                )}
                {product.isLoading ? "Analyzing…" : "Analyze with Coach"}
              </button>
            </div>
          </div>

          {/* Results panel */}
          <div className="flex flex-col gap-4">
            {result ? (
              <>
                {/* Score */}
                <div
                  className="rounded-xl border p-5 flex flex-col items-center gap-4"
                  style={{ background: "var(--card)" }}
                >
                  <ScoreRing score={result.score} />
                  <p className="text-sm text-muted-foreground text-center leading-relaxed max-w-xs">
                    {result.summary}
                  </p>
                </div>

                {/* Suggestions */}
                <div
                  className="rounded-xl border p-5 flex flex-col gap-3"
                  style={{ background: "var(--card)" }}
                >
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Coaching notes
                  </p>
                  <div className="space-y-2">
                    {result.suggestions.map((s, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 rounded-lg p-3"
                        style={{
                          background: "var(--muted)",
                          animation: `fadeUp 240ms cubic-bezier(0.23,1,0.32,1) ${i * 60}ms both`,
                        }}
                      >
                        {result.score >= 0.8 ? (
                          <CheckCircle2 size={14} className="flex-shrink-0 mt-0.5" style={{ color: "var(--olive)" }} />
                        ) : (
                          <AlertCircle size={14} className="flex-shrink-0 mt-0.5" style={{ color: "var(--bronze)" }} />
                        )}
                        <p className="text-xs text-foreground leading-relaxed">{s}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div
                className="rounded-xl border flex flex-col items-center justify-center py-16 px-5 text-center"
                style={{ background: "var(--card)" }}
              >
                <Zap size={32} className="text-muted-foreground/30 mb-3" />
                <p className="text-sm font-medium text-foreground">Coach is ready</p>
                <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                  Paste your draft on the left and hit analyze. You&apos;ll get a score, a summary, and actionable coaching notes.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </ProductShell>
  );
}
