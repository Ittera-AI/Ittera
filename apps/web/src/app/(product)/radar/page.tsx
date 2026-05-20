"use client";

import { useState } from "react";
import { Radar as RadarIcon, RefreshCw, Loader2, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { ProductShell } from "@/components/product/ProductShell";
import { useProduct } from "@/hooks/useProduct";
import type { RadarTrendItem } from "@/services/product.service";

const PLATFORMS = ["linkedin", "twitter", "instagram"] as const;

function ScoreArc({ score }: { score: number }) {
  const size = 48;
  const r = (size - 6) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score);
  const color = score >= 0.85 ? "var(--bronze)" : score >= 0.7 ? "var(--olive)" : "var(--text-muted)";
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rotate-[-90deg]">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={4} />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={color} strokeWidth={4}
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 700ms cubic-bezier(0.23,1,0.32,1)" }}
        />
      </svg>
      <span className="absolute text-[9px] font-bold" style={{ color }}>
        {Math.round(score * 100)}
      </span>
    </div>
  );
}

function TrendCard({ item, onUse }: { item: RadarTrendItem; onUse: (item: RadarTrendItem) => void }) {
  return (
    <div
      className="rounded-xl border p-5 flex flex-col gap-4 transition-all duration-150 hover:border-border-hover"
      style={{ background: "var(--card)" }}
    >
      <div className="flex items-start gap-4">
        <ScoreArc score={item.score} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-foreground leading-snug">{item.topic}</p>
          <div className="flex flex-wrap gap-1 mt-1.5">
            {item.platforms.map((p) => (
              <span
                key={p}
                className="text-[10px] font-medium px-2 py-0.5 rounded-full capitalize"
                style={{ background: "var(--muted)", color: "var(--text-soft)" }}
              >
                {p}
              </span>
            ))}
          </div>
        </div>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed">{item.summary}</p>
      <button
        onClick={() => onUse(item)}
        className="flex items-center gap-1.5 self-start rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-all active:scale-[0.97]"
      >
        Use in Create
        <ArrowRight size={11} />
      </button>
    </div>
  );
}

export default function RadarPage() {
  const product = useProduct();
  const router = useRouter();
  const [niche, setNiche] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["linkedin"]);

  function togglePlatform(p: string) {
    setSelectedPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
    );
  }

  async function handleScan() {
    if (!niche.trim()) return;
    await product.scanRadar(niche.trim(), selectedPlatforms);
  }

  function handleUse(item: RadarTrendItem) {
    // Navigate to create with the topic as part of the URL query
    void router.push(`/create`);
    // We store the topic in localStorage for /create to pick up
    if (typeof window !== "undefined") {
      localStorage.setItem("ittera-radar-prompt", item.summary);
    }
  }

  const results = product.radarResult;

  return (
    <ProductShell>
      <div className="flex flex-col gap-8">
        {/* Header */}
        <div>
          <p className="eyebrow">Trend Radar</p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-[-0.04em]">Catch today&apos;s signals</h1>
          <p className="mt-1.5 max-w-xl text-sm text-muted-foreground">
            Enter your niche and target platforms. Radar surfaces the strongest content angles — scored by momentum.
          </p>
        </div>

        {/* Scan form */}
        <div
          className="rounded-xl border p-6 flex flex-col gap-5"
          style={{ background: "var(--card)" }}
        >
          <div className="grid gap-5 sm:grid-cols-[1fr_auto]">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2">
                Your niche
              </label>
              <input
                value={niche}
                onChange={(e) => setNiche(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && void handleScan()}
                placeholder="e.g. AI, startup, marketing, content, technology…"
                className="w-full rounded-lg border px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 transition-all"
                style={{ background: "var(--muted)", borderColor: "var(--border)" }}
              />
            </div>

            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2">
                Platforms
              </label>
              <div className="flex gap-1.5">
                {PLATFORMS.map((p) => (
                  <button
                    key={p}
                    onClick={() => togglePlatform(p)}
                    className="rounded-lg px-3 py-2.5 text-xs font-semibold capitalize transition-all active:scale-[0.97]"
                    style={{
                      background: selectedPlatforms.includes(p) ? "var(--foreground)" : "var(--muted)",
                      color: selectedPlatforms.includes(p) ? "var(--background)" : "var(--text-muted)",
                      border: selectedPlatforms.includes(p) ? "none" : "1px solid var(--border)",
                    }}
                  >
                    {p === "twitter" ? "X" : p}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <button
            onClick={() => void handleScan()}
            disabled={!niche.trim() || product.isLoading}
            className="self-start flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold transition-all active:scale-[0.97] disabled:opacity-40"
            style={{ background: "var(--foreground)", color: "var(--background)" }}
          >
            {product.isLoading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <RadarIcon size={14} />
            )}
            {product.isLoading ? "Scanning…" : "Scan Radar"}
          </button>
        </div>

        {/* Results */}
        {results && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-semibold text-foreground">
                  {results.trends.length} trends found
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Scanned {new Date(results.scanned_at).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
                </p>
              </div>
              <button
                type="button"
                aria-label="Rescan trends"
                onClick={() => void handleScan()}
                className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-all active:scale-[0.97]"
              >
                <RefreshCw size={11} aria-hidden />
                Rescan
              </button>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {results.trends.map((item, i) => (
                <div
                  key={item.topic}
                  style={{
                    animation: `fadeUp 280ms cubic-bezier(0.23,1,0.32,1) both`,
                    animationDelay: `${i * 55}ms`,
                  }}
                >
                  <TrendCard item={item} onUse={handleUse} />
                </div>
              ))}
            </div>
          </div>
        )}

        {!results && !product.isLoading && (
          <div className="py-16 text-center">
            <RadarIcon size={32} className="mx-auto text-muted-foreground/30 mb-3" />
            <p className="text-sm text-muted-foreground">Enter your niche above and hit Scan Radar to discover trending angles.</p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </ProductShell>
  );
}
