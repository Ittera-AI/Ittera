"use client";

import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";

/**
 * Step 1 placeholder — full permanent context questionnaire lands in Phase 1.
 * For P0 integration, this route establishes the onboarding step order.
 */
export default function OnboardingContextPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center px-6">
      <div className="max-w-lg text-center space-y-6">
        <p className="text-sm uppercase tracking-widest text-[var(--bronze)]">Step 1 of 2</p>
        <h1 className="text-3xl font-bold tracking-tight">Permanent context</h1>
        <p className="text-white/60 leading-relaxed">
          The brand questionnaire (name, summary, goals, platforms) will live here in Phase 1.
          For now, continue to connect your social accounts and build your persona.
        </p>
        <button
          type="button"
          onClick={() => router.push("/onboarding/persona")}
          className="inline-flex items-center gap-2 rounded-full bg-[var(--bronze)] px-6 py-3 text-sm font-semibold text-black transition hover:opacity-90"
        >
          Continue to connect accounts
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
