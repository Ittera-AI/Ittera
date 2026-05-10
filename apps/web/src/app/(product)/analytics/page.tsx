"use client";

import { useEffect, useState } from "react";
import { X, TrendingUp } from "lucide-react";
import { ProductShell } from "@/components/product/ProductShell";
import { useProduct } from "@/hooks/useProduct";
import type { AnalyticsPost } from "@/services/product.service";

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold text-foreground">{pct}</span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--muted)" }}>
        <div
          className="h-full rounded-full"
          style={{
            width: `${pct}%`,
            background:
              pct >= 70
                ? "var(--olive)"
                : pct >= 50
                ? "var(--bronze)"
                : "rgba(239,68,68,0.7)",
            transition: "width 600ms cubic-bezier(0.23,1,0.32,1)",
          }}
        />
      </div>
    </div>
  );
}

function EngagementChart({ posts }: { posts: AnalyticsPost[] }) {
  if (posts.length === 0) return null;
  const sorted = [...posts].sort((a, b) => b.engagement_rate - a.engagement_rate).slice(0, 10);
  const max = Math.max(...sorted.map((p) => p.engagement_rate), 0.01);

  return (
    <div className="flex items-end gap-1.5 h-28 mt-2">
      {sorted.map((post) => {
        const pct = (post.engagement_rate / max) * 100;
        return (
          <div key={post.id} className="flex-1 flex flex-col items-center gap-1 group" title={post.content.slice(0, 60)}>
            <div
              className="w-full rounded-t-sm transition-all duration-300"
              style={{
                height: `${pct}%`,
                minHeight: "4px",
                background: "var(--bronze)",
                opacity: 0.7,
              }}
            />
            <span className="text-[9px] text-muted-foreground font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              {Math.round(post.engagement_rate * 1000) / 10}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default function AnalyticsPage() {
  const product = useProduct();
  const loadAnalytics = product.loadAnalytics;
  const [selected, setSelected] = useState<AnalyticsPost | null>(null);

  useEffect(() => {
    void loadAnalytics();
  }, [loadAnalytics]);

  const topPost = [...product.analytics].sort((a, b) => b.engagement_rate - a.engagement_rate)[0];
  const avgEngagement =
    product.analytics.length > 0
      ? product.analytics.reduce((s, p) => s + p.engagement_rate, 0) / product.analytics.length
      : 0;
  const totalLikes = product.analytics.reduce((s, p) => s + p.likes, 0);

  return (
    <ProductShell>
      <div className="flex flex-col gap-6">
        {/* Header */}
        <div>
          <p className="eyebrow">Analytics</p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-[-0.04em]">Learn what works</h1>
          <p className="mt-1.5 max-w-xl text-sm text-muted-foreground">
            Review post performance. Click any row to open the Engagement Coach.
          </p>
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Posts tracked", value: product.analytics.length },
            { label: "Avg engagement", value: `${Math.round(avgEngagement * 1000) / 10}%` },
            { label: "Total likes", value: totalLikes },
          ].map(({ label, value }) => (
            <div
              key={label}
              className="rounded-xl border p-4 text-center"
              style={{ background: "var(--card)" }}
            >
              <p className="text-2xl font-semibold text-foreground tracking-tight">{value}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* Engagement Chart */}
        {product.analytics.length > 0 && (
          <div className="rounded-xl border p-5" style={{ background: "var(--card)" }}>
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp size={14} style={{ color: "var(--bronze)" }} />
              <h2 className="text-sm font-semibold text-foreground">Engagement rate — top 10 posts</h2>
            </div>
            <p className="text-xs text-muted-foreground mb-3">Hover a bar to see the rate. Sorted best to worst.</p>
            <EngagementChart posts={product.analytics} />
          </div>
        )}

        {/* Top post spotlight */}
        {topPost && (
          <div
            className="rounded-xl border p-5"
            style={{ background: "var(--card)", borderColor: "rgba(163,138,112,0.3)" }}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="eyebrow">Top performing post</p>
              <span
                className="text-xs font-semibold px-2.5 py-1 rounded-full"
                style={{ background: "rgba(163,138,112,0.12)", color: "var(--bronze)" }}
              >
                {Math.round(topPost.engagement_rate * 1000) / 10}% engagement
              </span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap max-w-3xl">
              {topPost.content.slice(0, 280)}
              {topPost.content.length > 280 && "…"}
            </p>
            {topPost.analysis && (
              <div className="mt-4 grid grid-cols-3 gap-3">
                <ScoreBar label="Hook" value={topPost.analysis.hook_score / 100} />
                <ScoreBar label="Tone match" value={topPost.analysis.tone_match_score / 100} />
                <ScoreBar label="Structure" value={topPost.analysis.structure_score / 100} />
              </div>
            )}
          </div>
        )}

        {/* Posts table */}
        <div className="rounded-xl border overflow-hidden" style={{ background: "var(--card)" }}>
          <div className="px-5 py-4 border-b">
            <h2 className="text-sm font-semibold text-foreground">All posts</h2>
            <p className="text-xs text-muted-foreground mt-0.5">Click a row to open Coach analysis.</p>
          </div>
          {product.analytics.length === 0 ? (
            <div className="px-5 py-10 text-center">
              <p className="text-sm text-muted-foreground">No posts yet. Sync LinkedIn to see performance data.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    {["Post", "Likes", "Comments", "Engagement", "Coach"].map((h) => (
                      <th key={h} className="px-4 py-3 text-xs font-semibold text-muted-foreground">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {product.analytics.map((post) => (
                    <tr
                      key={post.id}
                      className="cursor-pointer transition-colors hover:bg-muted/40"
                      onClick={() => setSelected(post)}
                    >
                      <td className="px-4 py-3 max-w-xs">
                        <p className="truncate text-xs text-foreground">{post.content}</p>
                      </td>
                      <td className="px-4 py-3 text-xs font-medium">{post.likes}</td>
                      <td className="px-4 py-3 text-xs font-medium">{post.comments}</td>
                      <td className="px-4 py-3 text-xs font-semibold" style={{ color: "var(--bronze)" }}>
                        {Math.round(post.engagement_rate * 1000) / 10}%
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">
                        {post.analysis ? `Hook: ${post.analysis.hook_score}` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Analysis side panel */}
      {selected && (
        <div className="fixed inset-y-0 right-0 z-50 flex">
          <div
            className="fixed inset-0 lg:hidden"
            style={{ background: "rgba(0,0,0,0.4)" }}
            onClick={() => setSelected(null)}
          />
          <div
            className="relative ml-auto w-full max-w-sm border-l flex flex-col"
            style={{
              background: "var(--card)",
              animation: "slideInRight 220ms cubic-bezier(0.32,0.72,0,1)",
            }}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <h2 className="text-sm font-semibold text-foreground">Coach analysis</h2>
              <button
                onClick={() => setSelected(null)}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-muted active:scale-[0.97] transition-all"
              >
                <X size={14} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
              <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {selected.content.slice(0, 320)}
                {selected.content.length > 320 && "…"}
              </p>

              <button
                onClick={() => void product.analyze(selected.id)}
                disabled={product.isLoading}
                className="w-full rounded-lg border px-4 py-2.5 text-sm font-medium text-foreground transition-all active:scale-[0.97] hover:bg-muted disabled:opacity-50"
                style={{ background: "var(--muted)" }}
              >
                {product.isLoading ? "Analyzing…" : "Analyze with Coach"}
              </button>

              {selected.analysis && (
                <div className="space-y-4">
                  <div className="space-y-3">
                    <ScoreBar label="Hook score" value={selected.analysis.hook_score / 100} />
                    <ScoreBar label="Tone match" value={selected.analysis.tone_match_score / 100} />
                    <ScoreBar label="Structure" value={selected.analysis.structure_score / 100} />
                  </div>
                  <div
                    className="rounded-lg p-4 space-y-3 text-xs"
                    style={{ background: "var(--muted)" }}
                  >
                    <div>
                      <p className="font-semibold text-foreground mb-1">Strength</p>
                      <p className="text-muted-foreground">{selected.analysis.top_strength}</p>
                    </div>
                    <div>
                      <p className="font-semibold text-foreground mb-1">Improve</p>
                      <p className="text-muted-foreground">{selected.analysis.top_improvement}</p>
                    </div>
                    {selected.analysis.rewrite_suggestion && (
                      <div>
                        <p className="font-semibold text-foreground mb-1">Rewrite suggestion</p>
                        <p className="text-muted-foreground">{selected.analysis.rewrite_suggestion}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>
    </ProductShell>
  );
}
