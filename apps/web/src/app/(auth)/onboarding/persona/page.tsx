"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api, PersonaProfile, SocialConnectionStatus } from "@/lib/api";
import { PersonaResults } from "@/components/persona/PersonaResults";
import { supabase } from "@/lib/supabase";
import {
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Target,
  Users,
  MessageSquare,
  ChevronLeft,
  Zap,
  Loader2,
  AlertCircle,
  ExternalLink,
} from "lucide-react";

// ─── Platform brand icons ─────────────────────────────────────────────────────

function XIcon({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function LinkedInIcon({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}

function InstagramIcon({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
    </svg>
  );
}

// ─── Platform config ──────────────────────────────────────────────────────────

type PlatformId = "twitter" | "linkedin" | "instagram";

const PLATFORMS: {
  id: PlatformId;
  name: string;
  icon: React.FC<{ size?: number }>;
  iconColor: string;
  bg: string;
  gradient: string;
  tagline: string;
  perks: string[];
  recommended?: boolean;
}[] = [
  {
    id: "twitter",
    name: "X / Twitter",
    icon: XIcon,
    iconColor: "#ffffff",
    bg: "#000000",
    gradient: "linear-gradient(135deg, #1a1a1a, #000000)",
    tagline: "Your voice at its rawest",
    perks: ["Tone & language style", "Topic patterns", "Engagement signals"],
    recommended: true,
  },
  {
    id: "linkedin",
    name: "LinkedIn",
    icon: LinkedInIcon,
    iconColor: "#ffffff",
    bg: "#0A66C2",
    gradient: "linear-gradient(135deg, #0A66C2, #004182)",
    tagline: "Your professional narrative",
    perks: ["Career positioning", "B2B audience fit", "Authority signals"],
  },
  {
    id: "instagram",
    name: "Instagram",
    icon: InstagramIcon,
    iconColor: "#ffffff",
    bg: "linear-gradient(135deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888)",
    gradient: "linear-gradient(135deg, #f09433, #bc1888)",
    tagline: "Your visual identity",
    perks: ["Aesthetic & vibe", "Community style", "Content pacing"],
  },
];

// ─── Loading phrases ──────────────────────────────────────────────────────────

const LOADING_PHRASES = [
  "Fetching your public content...",
  "Reading your voice and tone...",
  "Mapping content patterns...",
  "Identifying audience signals...",
  "Discovering content pillars...",
  "Synthesizing insights with AI...",
  "Finalizing your persona...",
];

// ─── Popup OAuth helper ───────────────────────────────────────────────────────

function openOAuthPopup(url: string): Window | null {
  const w = 520, h = 680;
  const left = window.screenX + (window.outerWidth - w) / 2;
  const top = window.screenY + (window.outerHeight - h) / 2;
  return window.open(url, "ittera_oauth", `width=${w},height=${h},left=${left},top=${top},toolbar=0,menubar=0`);
}

// ─── Main page ────────────────────────────────────────────────────────────────

type WizardStep = "welcome" | "connect" | "context" | "loading" | "results";

export default function PersonaOnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<WizardStep>("welcome");

  // Auth token for backend OAuth start URLs
  const [authToken, setAuthToken] = useState<string | null>(null);

  // Connected accounts: platformId -> username
  const [connected, setConnected] = useState<Partial<Record<PlatformId, string>>>({});
  // Which platform is currently in OAuth popup
  const [connecting, setConnecting] = useState<PlatformId | null>(null);
  const [connectError, setConnectError] = useState<string | null>(null);

  // Context fields
  const [consent, setConsent] = useState(false);

  // Loading
  const [loadingPhrase, setLoadingPhrase] = useState(LOADING_PHRASES[0]);
  const [loadingProgress, setLoadingProgress] = useState(0);

  // Results
  const [persona, setPersona] = useState<PersonaProfile | null>(null);

  // Get auth token on mount
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.access_token) setAuthToken(session.access_token);
    });
  }, []);

  // Load existing connections on mount
  useEffect(() => {
    api.connect.status().then((list) => {
      const map: Partial<Record<PlatformId, string>> = {};
      list.forEach((c) => {
        if (["twitter", "linkedin", "instagram"].includes(c.platform)) {
          map[c.platform as PlatformId] = c.username;
        }
      });
      if (Object.keys(map).length) setConnected(map);
    }).catch(() => {});
  }, []);

  // Listen for postMessage from OAuth popup
  useEffect(() => {
    function handleMessage(e: MessageEvent) {
      if (e.data?.type !== "ittera_oauth") return;
      const { platform, status: s, username, error } = e.data;
      setConnecting(null);
      if (s === "connected") {
        setConnected((prev) => ({ ...prev, [platform]: username }));
        setConnectError(null);
      } else {
        setConnectError(error || "Connection failed. Please try again.");
      }
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  // Loading animation
  useEffect(() => {
    if (step !== "loading") return;
    let i = 0;
    const t = setInterval(() => {
      i = Math.min(i + 1, LOADING_PHRASES.length - 1);
      setLoadingPhrase(LOADING_PHRASES[i]);
      setLoadingProgress(Math.round((i / (LOADING_PHRASES.length - 1)) * 100));
    }, 1800);
    return () => clearInterval(t);
  }, [step]);

  const connectedCount = Object.keys(connected).length;

  function handleConnect(platformId: PlatformId) {
    if (!authToken) {
      setConnectError("Please wait — fetching your session...");
      return;
    }
    setConnectError(null);
    setConnecting(platformId);
    const url = api.connect.startUrl(platformId, authToken);
    const popup = openOAuthPopup(url);
    if (!popup) {
      setConnecting(null);
      setConnectError("Popup was blocked. Please allow popups for this site.");
    } else {
      const timer = setInterval(() => {
        if (popup.closed) {
          clearInterval(timer);
          setConnecting((prev) => (prev === platformId ? null : prev));
        }
      }, 500);
    }
  }

  async function handleDisconnect(platformId: PlatformId) {
    await api.connect.disconnect(platformId).catch(() => {});
    setConnected((prev) => {
      const next = { ...prev };
      delete next[platformId];
      return next;
    });
  }

  async function handleBuild() {
    if (!consent || connectedCount === 0) return;
    setStep("loading");
    setLoadingProgress(0);
    try {
      await api.persona.startOnboarding();

      // Add connected platforms as persona sources, avoiding duplicates
      const existingSources = await api.persona.listSources();
      for (const [id, username] of Object.entries(connected) as [PlatformId, string][]) {
        const urlMap: Record<PlatformId, string> = {
          twitter: `https://x.com/${username}`,
          linkedin: `https://linkedin.com/in/${username}`,
          instagram: `https://instagram.com/${username}`,
        };
        const url = urlMap[id];
        if (!existingSources.some(s => s.url === url)) {
          await api.persona.addSource({ source_type: id, url });
        }
      }
      await api.persona.scrape();
      const result = await api.persona.analyze();
      await api.auth.onboarding({ primary_platform: "linkedin" });
      setPersona(result);
      setStep("results");
    } catch (err: any) {
      alert(err?.detail || err?.message || "Something went wrong.");
      setStep("context");
    }
  }

  // ── Results ──
  if (step === "results" && persona) {
    return <PersonaResults persona={persona} onConfirm={() => router.push("/dashboard")} />;
  }

  // ── Loading ──
  if (step === "loading") {
    return (
      <div className="fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden"
        style={{ background: "#050505" }}>
        
        {/* Dynamic ambient background */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full blur-[150px] opacity-20 animate-pulse duration-3000"
          style={{ background: "var(--bronze)" }} />
        
        <div className="relative z-10 flex flex-col items-center w-full max-w-2xl text-center px-6">
          <div className="relative flex h-48 w-48 items-center justify-center mb-12">
            {/* Expanding outer rings */}
            <div className="absolute inset-0 rounded-full border border-white/5 animate-[ping_3s_cubic-bezier(0,0,0.2,1)_infinite]" />
            <div className="absolute inset-4 rounded-full border border-[var(--bronze)]/20 animate-[ping_3s_cubic-bezier(0,0,0.2,1)_infinite_500ms]" />
            
            {/* Core spinner */}
            <div className="absolute inset-8 rounded-full border-2 border-white/5" />
            <div className="absolute inset-8 rounded-full animate-spin"
              style={{ border: "2px solid transparent", borderTopColor: "var(--bronze)", borderRightColor: "var(--bronze)", animationDuration: "1s" }} />
            
            {/* Center icon */}
            <div className="absolute inset-14 rounded-full bg-black/50 border border-white/10 backdrop-blur-xl flex items-center justify-center shadow-[0_0_30px_var(--bronze)]">
              <Sparkles size={32} className="text-[var(--bronze)] animate-pulse" />
            </div>
          </div>

          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-6">
            Synthesizing Intelligence
          </h2>
          
          <div className="h-8 mb-12 w-full">
            <p className="text-lg text-white/60 font-medium animate-in slide-in-from-bottom-2 fade-in duration-500" key={loadingPhrase}>
              {loadingPhrase}
            </p>
          </div>

          {/* Wide Progress Bar */}
          <div className="w-full max-w-md bg-white/5 h-2 rounded-full overflow-hidden border border-white/10 backdrop-blur-sm relative mx-auto">
            <div className="absolute top-0 bottom-0 left-0 transition-all duration-1000 ease-out rounded-full shadow-[0_0_20px_var(--bronze)]"
              style={{ width: `${loadingProgress}%`, background: "linear-gradient(90deg, #8B6040, var(--bronze))" }} />
          </div>
          <p className="mt-4 text-sm font-bold tracking-widest text-[var(--bronze)]">{loadingProgress}% COMPLETE</p>
        </div>
      </div>
    );
  }

  // ── Welcome ──
  if (step === "welcome") {
    return (
      <div className="relative min-h-screen flex items-center justify-center overflow-hidden" style={{ background: "var(--background)" }}>
        {/* Ambient background */}
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(circle at 70% 50%, rgba(163,138,112,0.15), transparent 60%)" }} />
        <div className="absolute -top-[40%] -right-[20%] w-[80%] h-[80%] rounded-full blur-[120px] opacity-20" style={{ background: "var(--bronze)" }} />
        
        <div className="relative z-10 w-full max-w-[1400px] px-8 py-16 grid lg:grid-cols-2 gap-16 lg:gap-24 items-center">
          
          {/* Left Side: Typography */}
          <div className="flex flex-col items-start space-y-8 max-w-xl mx-auto lg:mx-0 animate-in fade-in slide-in-from-left-8 duration-1000">
            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-md">
              <Sparkles size={16} className="text-[var(--bronze)]" />
              <span className="text-xs font-semibold text-foreground uppercase tracking-widest">Ittera Persona Engine</span>
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-bold tracking-tighter text-foreground leading-[1.1]">
              Clone your <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--bronze)] to-[#C0A080]">Digital Voice</span>
            </h1>
            
            <p className="text-lg lg:text-xl text-muted-foreground leading-relaxed">
              Log in with the platforms where you create. Ittera&apos;s AI Engine analyzes your actual content to build a highly accurate persona that powers your entire content strategy.
            </p>
            
            <button
              onClick={() => setStep("connect")}
              className="group relative overflow-hidden rounded-full px-10 py-5 text-lg font-semibold text-white shadow-[0_0_40px_-10px_var(--bronze)] hover:shadow-[0_0_60px_-15px_var(--bronze)] transition-all duration-500 hover:scale-[1.02] active:scale-[0.98]"
              style={{ background: "linear-gradient(135deg, var(--bronze), #8B6040)" }}>
              <span className="relative z-10 flex items-center gap-3">
                Ignite the Engine
                <ArrowRight size={20} className="transition-transform group-hover:translate-x-1" />
              </span>
              <div className="absolute inset-0 -translate-x-full animate-[shimmer_2.5s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent" />
            </button>
            
          </div>

          {/* Right Side: Visual Element */}
          <div className="hidden lg:flex relative h-[600px] w-full items-center justify-center animate-in fade-in zoom-in duration-1000 delay-300">
            <div className="absolute inset-0 rounded-[3rem] border border-white/5 bg-gradient-to-br from-white/5 to-transparent backdrop-blur-3xl shadow-2xl overflow-hidden flex items-center justify-center">
              {/* Decorative nodes */}
              <div className="relative w-full h-full flex items-center justify-center">
                <div className="absolute w-[400px] h-[400px] rounded-full border border-white/10 animate-[spin_60s_linear_infinite]" />
                <div className="absolute w-[300px] h-[300px] rounded-full border border-dashed border-white/10 animate-[spin_40s_linear_infinite_reverse]" />
                
                {/* Center Node */}
                <div className="relative z-10 w-24 h-24 rounded-2xl bg-black/50 border border-white/10 backdrop-blur-xl flex items-center justify-center shadow-[0_0_50px_-10px_var(--bronze)]">
                  <div className="text-[var(--bronze)] animate-pulse">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M12 2a10 10 0 100 20 10 10 0 000-20zM12 6v6l4 2" />
                    </svg>
                  </div>
                </div>

                {/* Floating Elements */}
                {[
                  { icon: MessageSquare, label: "Tone", angle: 0 },
                  { icon: Target, label: "Pillars", angle: 120 },
                  { icon: Users, label: "Audience", angle: 240 }
                ].map((item, i) => {
                  const rad = (item.angle * Math.PI) / 180;
                  const x = Math.cos(rad) * 150;
                  const y = Math.sin(rad) * 150;
                  const Icon = item.icon;
                  return (
                    <div key={item.label} className="absolute flex flex-col items-center gap-2 transition-transform duration-1000 hover:scale-110"
                      style={{ transform: `translate(${x}px, ${y}px)` }}>
                      <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 backdrop-blur-md flex items-center justify-center">
                        <Icon size={20} className="text-white/70" />
                      </div>
                      <span className="text-xs font-medium text-white/60 tracking-wider uppercase">{item.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          
        </div>
        <style>{`
          @keyframes shimmer { 100% { transform: translateX(100%); } }
        `}</style>
      </div>
    );
  }

  // ── Connect step ──
  if (step === "connect") {
    return (
      <div className="min-h-screen px-6 py-16 md:py-24 flex flex-col items-center justify-center" style={{ background: "var(--background)" }}>
        {/* Ambient background */}
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at top, rgba(163,138,112,0.1), transparent 70%)" }} />
        
        <div className="relative z-10 w-full max-w-[1200px] animate-in slide-in-from-bottom-8 fade-in duration-700">
          
          <div className="text-center mb-16 space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">
              Select your sources
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Connect the platforms where you&apos;re most active. Our engine will analyze your best-performing content to reverse-engineer your unique voice.
            </p>
          </div>

          {/* Error */}
          {connectError && (
            <div className="mb-8 max-w-xl mx-auto flex items-center justify-center gap-3 rounded-2xl border px-6 py-4 text-sm font-medium backdrop-blur-md"
              style={{ background: "rgba(239,68,68,0.1)", borderColor: "rgba(239,68,68,0.2)", color: "#ef4444" }}>
              <AlertCircle size={18} className="flex-shrink-0 animate-pulse" />
              {connectError}
            </div>
          )}

          {/* Platform cards grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
            {PLATFORMS.map((platform) => {
              const Icon = platform.icon;
              const isConnected = !!connected[platform.id];
              const isConnecting = connecting === platform.id;

              return (
                <div key={platform.id} className="group relative flex flex-col rounded-[2rem] border border-white/5 overflow-hidden transition-all duration-700 hover:-translate-y-2 hover:shadow-[0_20px_60px_-15px_rgba(163,138,112,0.2)]"
                  style={{
                    background: isConnected ? "rgba(163,138,112,0.05)" : "rgba(20,20,20,0.4)",
                    backdropFilter: "blur(20px)",
                    borderColor: isConnected ? "var(--bronze)" : "rgba(255,255,255,0.08)",
                  }}>
                  
                  {/* Premium Hover Glow */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none bg-gradient-to-br from-white/5 to-transparent" />
                  
                  {/* Premium gradient header */}
                  <div className="h-40 w-full relative overflow-hidden flex items-center justify-center transition-transform duration-700 group-hover:scale-105" style={{ background: platform.gradient }}>
                    <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />
                    {/* Glowing background behind icon */}
                    <div className="absolute w-32 h-32 bg-white/20 blur-[40px] rounded-full" />
                    
                    <div className="relative z-10 h-20 w-20 rounded-3xl flex items-center justify-center shadow-2xl border border-white/20 backdrop-blur-xl transition-all duration-500 group-hover:scale-110 group-hover:rotate-3"
                      style={{ background: platform.bg }}>
                      <Icon size={36} />
                    </div>
                  </div>

                  <div className="relative flex-1 p-8 flex flex-col z-10">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-2xl font-bold text-white tracking-tight">{platform.name}</h3>
                      {platform.recommended && (
                        <span className="text-[10px] font-bold tracking-widest uppercase px-3 py-1.5 rounded-full border border-[var(--bronze)]/30 shadow-[0_0_15px_rgba(163,138,112,0.15)]"
                          style={{ background: "rgba(163,138,112,0.1)", color: "var(--bronze)" }}>
                          Primary
                        </span>
                      )}
                    </div>
                    
                    <p className="text-base text-white/60 mb-8 leading-relaxed font-medium">{platform.tagline}</p>
                    
                    <div className="flex flex-wrap gap-2 mb-10">
                      {platform.perks.map((perk) => (
                        <span key={perk} className="text-xs font-semibold px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-white/70 shadow-sm">
                          {perk}
                        </span>
                      ))}
                    </div>

                    <div className="mt-auto pt-6 border-t border-white/10">
                      {isConnected ? (
                        <div className="flex items-center justify-between bg-black/40 rounded-2xl p-4 border border-[var(--olive)]/30 shadow-[0_0_20px_-5px_rgba(122,139,118,0.2)] animate-in fade-in zoom-in-95 slide-in-from-bottom-2 duration-500">
                          <div className="flex items-center gap-3">
                            <div className="bg-[var(--olive)]/20 p-1.5 rounded-full shadow-[0_0_15px_var(--olive)]">
                              <CheckCircle2 size={16} style={{ color: "var(--olive)" }} className="animate-[pulse_2s_ease-in-out_infinite]" />
                            </div>
                            <span className="text-sm font-bold text-white truncate max-w-[120px]">
                              @{connected[platform.id]}
                            </span>
                          </div>
                          <button
                            onClick={() => handleDisconnect(platform.id)}
                            className="text-[11px] font-bold text-white/40 hover:text-red-400 transition-colors uppercase tracking-wider bg-white/5 hover:bg-red-400/10 px-3 py-1.5 rounded-full">
                            Remove
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleConnect(platform.id)}
                          disabled={isConnecting}
                          className="group/btn relative w-full flex items-center justify-center gap-3 rounded-2xl py-4 text-sm font-bold text-white overflow-hidden transition-all duration-300 hover:brightness-110 active:scale-[0.98] disabled:opacity-50 disabled:scale-100 shadow-xl"
                          style={{ background: platform.gradient }}>
                          <div className="absolute inset-0 bg-white/0 group-hover/btn:bg-white/10 transition-colors" />
                          {isConnecting ? (
                            <>
                              <Loader2 size={18} className="animate-spin relative z-10" />
                              <span className="relative z-10">Connecting...</span>
                            </>
                          ) : (
                            <>
                              <ExternalLink size={18} className="relative z-10 transition-transform group-hover/btn:-translate-y-0.5 group-hover/btn:translate-x-0.5" />
                              <span className="relative z-10 tracking-wide">Connect {platform.name}</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-16 flex items-center justify-between border-t border-white/5 pt-8">
            <button onClick={() => setStep("welcome")}
              className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-all hover:-translate-x-1">
              <ChevronLeft size={18} />
              Back
            </button>
            <div className="flex items-center gap-6">
              {connectedCount > 0 ? (
                <span className="text-sm font-semibold animate-in fade-in" style={{ color: "var(--olive)" }}>
                  {connectedCount} source{connectedCount > 1 ? "s" : ""} secured
                </span>
              ) : (
                <button
                  onClick={() => {
                    sessionStorage.setItem("skipped_onboarding", "true");
                    router.push("/dashboard");
                  }}
                  className="text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors">
                  Skip for now
                </button>
              )}
              <button
                onClick={() => setStep("context")}
                disabled={connectedCount === 0}
                className="group flex items-center gap-2 rounded-full px-8 py-4 text-sm font-bold text-white transition-all hover:scale-105 active:scale-[0.98] disabled:opacity-30 disabled:scale-100 disabled:cursor-not-allowed shadow-[0_0_30px_-10px_var(--bronze)] hover:shadow-[0_0_40px_-10px_var(--bronze)]"
                style={{ background: "linear-gradient(135deg, var(--bronze), #7A6040)" }}>
                Continue to Analysis
                <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── Context step ──
  if (step === "context") {
    return (
      <div className="min-h-screen px-6 py-16 flex flex-col items-center justify-center" style={{ background: "var(--background)" }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(circle at bottom, rgba(163,138,112,0.15), transparent 60%)" }} />
        
        <div className="relative z-10 w-full max-w-[800px] animate-in slide-in-from-bottom-8 fade-in duration-700">
          
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold tracking-tight text-foreground">
              Ready for Engine Ignition
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              Review your sources and authorize the final analysis.
            </p>
          </div>

          <div className="rounded-[2.5rem] border border-white/10 bg-white/5 backdrop-blur-2xl p-8 md:p-12 shadow-2xl">
            
            {/* Sources Summary */}
            <div className="mb-10">
              <h3 className="text-sm font-bold tracking-widest text-muted-foreground uppercase mb-6 flex items-center gap-3">
                <Target size={16} className="text-[var(--bronze)]" />
                Data Sources
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {Object.entries(connected).map(([id, username]) => {
                  const p = PLATFORMS.find((pl) => pl.id === id)!;
                  const Icon = p.icon;
                  return (
                    <div key={id} className="flex items-center gap-4 rounded-2xl p-4 border border-white/5 bg-black/40 shadow-inner">
                      <div className="h-10 w-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg"
                        style={{ background: p.gradient }}>
                        <Icon size={18} className="text-white" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-muted-foreground">{p.name}</p>
                        <p className="text-sm font-bold text-foreground truncate">@{username}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Consent Toggle */}
            <div
              className="group relative overflow-hidden rounded-2xl border p-6 md:p-8 cursor-pointer transition-all duration-300"
              onClick={() => setConsent((c) => !c)}
              style={{
                background: consent ? "rgba(163,138,112,0.08)" : "rgba(0,0,0,0.4)",
                borderColor: consent ? "var(--bronze)" : "var(--border)",
                boxShadow: consent ? "0 0 0 1px var(--bronze), inset 0 0 40px rgba(163,138,112,0.1)" : "none",
              }}>
              
              {consent && <div className="absolute right-0 top-0 w-32 h-32 bg-[var(--bronze)]/20 blur-[50px] rounded-full" />}

              <div className="relative z-10 flex items-start gap-6">
                <div className="flex-shrink-0 mt-1 h-8 w-8 rounded-xl border-2 flex items-center justify-center transition-all duration-300 shadow-sm"
                  style={{ 
                    borderColor: consent ? "var(--bronze)" : "var(--muted-foreground)", 
                    background: consent ? "var(--bronze)" : "transparent",
                    transform: consent ? "scale(1.1)" : "scale(1)"
                  }}>
                  {consent && <CheckCircle2 size={20} className="text-white animate-in zoom-in" />}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-foreground mb-2 group-hover:text-white transition-colors">Authorize AI Analysis</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    I grant Ittera permission to analyze the public content from my connected accounts. 
                    This data will be used strictly to train my private voice model. Ittera will never post, share, or modify my content.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-12 flex flex-col-reverse sm:flex-row items-center justify-between gap-6">
              <button onClick={() => setStep("connect")}
                className="w-full sm:w-auto flex items-center justify-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground transition-all hover:-translate-x-1 py-4">
                <ChevronLeft size={18} />
                Modify sources
              </button>
              
              <button
                onClick={handleBuild}
                disabled={!consent}
                className="relative w-full sm:w-auto overflow-hidden rounded-full px-10 py-5 text-lg font-bold text-white transition-all duration-500 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:scale-100 disabled:cursor-not-allowed shadow-[0_0_40px_-10px_var(--bronze)]"
                style={{ background: "linear-gradient(135deg, var(--bronze), #8B6040)" }}>
                <span className="relative z-10 flex items-center justify-center gap-3">
                  <Zap size={20} className={consent ? "animate-pulse" : ""} />
                  Extract Persona
                </span>
                {consent && <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent" />}
              </button>
            </div>
          </div>
        </div>
        <style>{`
          @keyframes shimmer { 100% { transform: translateX(100%); } }
        `}</style>
      </div>
    );
  }

  return null;
}
