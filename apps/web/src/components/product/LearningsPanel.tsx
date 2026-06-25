"use client";

import { useEffect, useState } from "react";
import { Clock, Lightbulb, ListChecks, TrendingUp } from "lucide-react";

import { api, type AssembledContext } from "@/lib/api";

/**
 * "What We've Learned" — surfaces the self-learning loop's output for a platform:
 * the synthesized memory (learned_summary / why_wins / recommendations from the
 * active LearnedInsight) and the user-approved optimal posting times promoted into
 * permanent context.
 *
 * Renders nothing until the loop has produced data, so creation surfaces are
 * unchanged for brand-new users (graceful degradation).
 */
export function LearningsPanel({ platform }: { platform: string }) {
  const [ctx, setCtx] = useState<AssembledContext | null>(null);

  useEffect(() => {
    let active = true;
    api.context
      .get(platform)
      .then((c) => {
        if (active) setCtx(c);
      })
      .catch(() => {
        /* No context yet — keep the panel hidden. */
      });
    return () => {
      active = false;
    };
  }, [platform]);

  if (!ctx) return null;

  const report = ctx.report;
  const bestTimes = ctx.permanent.platform_facts?.[platform]?.best_post_times ?? [];
  const whyWins = report.why_wins ?? [];
  const recommendations = report.recommendations ?? [];

  const hasLearnings =
    Boolean(report.learned_summary) ||
    whyWins.length > 0 ||
    recommendations.length > 0 ||
    bestTimes.length > 0;

  if (!hasLearnings) return null;

  return (
    <div className="relative overflow-hidden rounded-xl border border-primary/20 bg-primary/[0.04] p-4 shadow-sm">
      <div className="absolute inset-x-0 -top-px h-px w-full bg-gradient-to-r from-transparent via-primary/40 to-transparent" />

      <div className="flex items-center gap-2">
        <Lightbulb className="h-4 w-4 text-primary" aria-hidden />
        <p className="text-xs font-semibold uppercase tracking-wider text-primary">
          What we&apos;ve learned
        </p>
      </div>

      {report.learned_summary ? (
        <p className="mt-2.5 text-sm leading-relaxed text-foreground/90">{report.learned_summary}</p>
      ) : null}

      {bestTimes.length > 0 ? (
        <div className="mt-3 flex items-center gap-2 text-sm">
          <Clock className="h-4 w-4 shrink-0 text-primary/80" aria-hidden />
          <span className="text-muted-foreground">Best times to post:</span>
          <div className="flex flex-wrap gap-1.5">
            {bestTimes.map((t) => (
              <span
                key={t}
                className="rounded-full border border-primary/30 bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {whyWins.length > 0 ? (
        <div className="mt-3">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <TrendingUp className="h-3.5 w-3.5 text-primary/80" aria-hidden />
            Why your posts win
          </div>
          <ul className="mt-1.5 space-y-1">
            {whyWins.slice(0, 3).map((w) => (
              <li key={w} className="text-sm leading-snug text-foreground/85">
                • {w}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {recommendations.length > 0 ? (
        <div className="mt-3">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <ListChecks className="h-3.5 w-3.5 text-primary/80" aria-hidden />
            Do next
          </div>
          <ul className="mt-1.5 space-y-1">
            {recommendations.slice(0, 3).map((r) => (
              <li key={r} className="text-sm leading-snug text-foreground/85">
                • {r}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
