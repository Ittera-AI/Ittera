"use client";

import { useState, useEffect } from "react";
import { User } from "@/context/AuthContext";
import { BrandProfile } from "@/services/product.service";
import { Loader2, ArrowRight, Zap, Target, Star, PenLine, CalendarDays } from "lucide-react";
import { Button } from "@/components/ui/Button";

type EliteWelcomeProps = {
  user: User | null;
  brandProfile: BrandProfile | null;
  onDismiss: () => void;
};

export function EliteWelcome({ user, brandProfile, onDismiss }: EliteWelcomeProps) {
  const [step, setStep] = useState<number>(1);
  const [loadingText, setLoadingText] = useState("Calibrating your content engine...");

  // Step 1: Loading sequence
  useEffect(() => {
    if (step === 1) {
      const timers = [
        setTimeout(() => setLoadingText("Loading Persona..."), 800),
        setTimeout(() => setLoadingText("Syncing Niche..."), 1600),
        setTimeout(() => setLoadingText("Analyzing Audience..."), 2400),
        setTimeout(() => setStep(2), 3500),
      ];
      return () => timers.forEach(clearTimeout);
    }
  }, [step]);

  // Handle dismissal
  const handleFinish = () => {
    onDismiss();
  };

  const name = user?.name ? user.name.split(" ")[0] : "Creator";
  const niche = brandProfile?.profile?.audience || "your industry";
  const tone = brandProfile?.profile?.voice_tone || "authoritative";

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-background/80 backdrop-blur-xl transition-all duration-500">
      <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_center,rgba(163,138,112,0.15)_0,transparent_50%)]" />

      {/* Step 1: Initialization */}
      {step === 1 && (
        <div className="relative z-10 flex flex-col items-center justify-center space-y-8 animate-in fade-in zoom-in duration-700">
          <div className="relative flex h-32 w-32 items-center justify-center">
            {/* Outer spinning ring */}
            <div className="absolute inset-0 rounded-full border-t-2 border-r-2 border-[var(--bronze)] opacity-40 animate-[spin_3s_linear_infinite]" />
            {/* Inner pulse */}
            <div className="h-16 w-16 rounded-full bg-[var(--bronze)] opacity-20 animate-ping duration-1000" />
            <Loader2 className="absolute h-8 w-8 text-[var(--bronze)] animate-spin" />
          </div>
          <h2 className="text-2xl font-light tracking-wide text-foreground animate-pulse">
            {loadingText}
          </h2>
        </div>
      )}

      {/* Step 2: The Reveal */}
      {step === 2 && (
        <div className="relative z-10 w-full max-w-2xl p-8 animate-in slide-in-from-bottom-8 fade-in duration-700">
          <div className="rounded-3xl border border-white/10 bg-black/40 p-10 shadow-2xl backdrop-blur-2xl dark:bg-zinc-950/40">
            <div className="mb-8 text-center">
              <h1 className="text-4xl font-bold tracking-tight text-foreground bg-gradient-to-br from-foreground to-foreground/60 bg-clip-text text-transparent">
                Engine Calibrated
              </h1>
              <p className="mt-4 text-lg text-muted-foreground">
                Welcome to your personalized Ittera Cockpit, <span className="font-semibold text-foreground">{name}</span>.
              </p>
            </div>

            <div className="mb-8 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/5 bg-white/5 p-5 transition-transform hover:scale-105">
                <Target className="mb-3 h-6 w-6 text-[var(--bronze)]" />
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Target Niche</h3>
                <p className="mt-1 text-lg font-semibold text-foreground">{niche}</p>
              </div>
              <div className="rounded-2xl border border-white/5 bg-white/5 p-5 transition-transform hover:scale-105">
                <Star className="mb-3 h-6 w-6 text-[var(--olive)]" />
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Voice & Tone</h3>
                <p className="mt-1 text-lg font-semibold text-foreground capitalize">{tone}</p>
              </div>
            </div>

            <div className="flex justify-center">
              <Button onClick={() => setStep(3)} className="group h-12 rounded-full px-8 text-base shadow-[0_0_40px_-10px_var(--bronze)] hover:shadow-[0_0_60px_-15px_var(--bronze)] transition-all duration-300">
                Continue
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: The Tour */}
      {step === 3 && (
        <div className="relative z-10 w-full max-w-3xl p-8 animate-in slide-in-from-bottom-8 fade-in duration-700">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold tracking-tight text-foreground">
              Here's how to dominate your niche
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              Your workflow is optimized for impact.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3 mb-12">
            <div className="flex flex-col items-center text-center p-6 rounded-2xl bg-gradient-to-b from-white/5 to-transparent border border-white/5">
              <div className="h-12 w-12 rounded-full bg-[var(--card)] flex items-center justify-center mb-4 border border-white/10 shadow-lg">
                <Zap className="h-6 w-6 text-[var(--bronze)]" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">1. Catch Signals</h3>
              <p className="text-sm text-muted-foreground">Use the Trend Radar to spot viral opportunities daily.</p>
            </div>
            
            <div className="flex flex-col items-center text-center p-6 rounded-2xl bg-gradient-to-b from-white/5 to-transparent border border-white/5">
              <div className="h-12 w-12 rounded-full bg-[var(--card)] flex items-center justify-center mb-4 border border-white/10 shadow-lg">
                <PenLine className="h-6 w-6 text-[var(--olive)]" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">2. Draft with Voice</h3>
              <p className="text-sm text-muted-foreground">The AI generates drafts matching your exact tone and pillars.</p>
            </div>

            <div className="flex flex-col items-center text-center p-6 rounded-2xl bg-gradient-to-b from-white/5 to-transparent border border-white/5">
              <div className="h-12 w-12 rounded-full bg-[var(--card)] flex items-center justify-center mb-4 border border-white/10 shadow-lg">
                <CalendarDays className="h-6 w-6 text-indigo-400" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">3. Publish & Learn</h3>
              <p className="text-sm text-muted-foreground">Schedule directly to your platforms and track what works.</p>
            </div>
          </div>

          <div className="flex justify-center">
            <button 
              onClick={handleFinish} 
              className="relative overflow-hidden rounded-full px-10 py-4 text-lg font-semibold text-white shadow-2xl transition-all hover:scale-105 active:scale-95"
              style={{ background: "linear-gradient(135deg, var(--bronze), #8B6040)" }}
            >
              <span className="relative z-10 flex items-center gap-2">
                Ignite the Engine
                <Zap className="h-5 w-5" />
              </span>
              <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent" />
            </button>
          </div>
        </div>
      )}
      
      <style>{`
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
}
