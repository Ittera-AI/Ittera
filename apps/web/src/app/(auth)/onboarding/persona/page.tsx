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
      <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-8"
        style={{ background: "var(--background)" }}>
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse 60% 50% at 50% 50%, rgba(163,138,112,0.1), transparent)" }} />
        <div className="relative flex h-32 w-32 items-center justify-center">
          <div className="absolute inset-0 rounded-full" style={{ border: "2px solid var(--border)" }} />
          <div className="absolute inset-0 rounded-full animate-spin"
            style={{ border: "2px solid transparent", borderTopColor: "var(--bronze)", borderRightColor: "var(--bronze)", animationDuration: "1.4s" }} />
          <div className="absolute inset-4 rounded-full" style={{ border: "1px solid var(--border)" }} />
          <Sparkles size={24} style={{ color: "var(--bronze)" }} />
        </div>
        <div className="text-center max-w-xs">
          <h2 className="text-2xl font-bold tracking-tight text-foreground mb-2">Building your persona</h2>
          <p className="text-sm text-muted-foreground transition-all duration-500" key={loadingPhrase}>{loadingPhrase}</p>
        </div>
        <div className="w-72 h-1.5 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
          <div className="h-full rounded-full transition-all duration-1000"
            style={{ width: `${loadingProgress}%`, background: "linear-gradient(90deg, var(--bronze), var(--olive))" }} />
        </div>
        <p className="text-xs text-muted-foreground tabular-nums">{loadingProgress}%</p>
      </div>
    );
  }

  // ── Welcome ──
  if (step === "welcome") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-16"
        style={{ background: "var(--background)" }}>
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(163,138,112,0.07), transparent)" }} />
        <div className="relative z-10 max-w-md w-full text-center space-y-8">
          <div className="flex justify-center">
            <div className="h-16 w-16 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-xl"
              style={{ background: "linear-gradient(135deg, var(--bronze), #7A6040)" }}>
              It
            </div>
          </div>
          <div>
            <p className="eyebrow mb-3">Persona Engine</p>
            <h1 className="text-4xl font-bold tracking-tight text-foreground leading-tight">
              Connect your accounts.<br />Build your persona.
            </h1>
            <p className="mt-4 text-base text-muted-foreground leading-relaxed">
              Log in with the platforms you create on. Ittera analyzes your real content to build a
              persona that powers your entire strategy.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { icon: MessageSquare, label: "Voice & Tone" },
              { icon: Target, label: "Content Pillars" },
              { icon: Users, label: "Audience Fit" },
            ].map(({ icon: Icon, label }) => (
              <div key={label} className="rounded-xl border p-3 flex flex-col items-center gap-1.5"
                style={{ background: "var(--card)" }}>
                <Icon size={15} style={{ color: "var(--bronze)" }} />
                <p className="text-[11px] font-semibold text-foreground text-center">{label}</p>
              </div>
            ))}
          </div>
          <button
            onClick={() => setStep("connect")}
            className="group w-full rounded-2xl py-4 text-base font-semibold text-white flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-lg"
            style={{ background: "linear-gradient(135deg, var(--bronze), #7A6040)" }}>
            Get started
            <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
          </button>
          <p className="text-xs text-muted-foreground">
            Only public data is read. We never post or modify anything on your behalf.
          </p>
        </div>
      </div>
    );
  }

  // ── Connect step ──
  if (step === "connect") {
    return (
      <div className="min-h-screen px-4 py-12" style={{ background: "var(--background)" }}>
        <div className="mx-auto max-w-lg">
          {/* Progress */}
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-5">
              {[0, 1].map((i) => (
                <div key={i} className="h-1.5 rounded-full transition-all duration-500"
                  style={{ width: i === 0 ? 28 : 8, background: i === 0 ? "var(--bronze)" : "var(--border)" }} />
              ))}
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Log in to your accounts</h1>
            <p className="mt-2 text-muted-foreground text-sm">
              A secure popup will open for each platform. Connect at least one.
            </p>
          </div>

          {/* Error */}
          {connectError && (
            <div className="mb-4 flex items-center gap-2 rounded-xl border px-4 py-3 text-sm"
              style={{ background: "rgba(239,68,68,0.08)", borderColor: "rgba(239,68,68,0.3)", color: "#ef4444" }}>
              <AlertCircle size={15} className="flex-shrink-0" />
              {connectError}
            </div>
          )}

          {/* Platform cards */}
          <div className="space-y-4">
            {PLATFORMS.map((platform) => {
              const Icon = platform.icon;
              const isConnected = !!connected[platform.id];
              const isConnecting = connecting === platform.id;

              return (
                <div key={platform.id} className="rounded-2xl border overflow-hidden transition-all duration-300"
                  style={{
                    background: "var(--card)",
                    borderColor: isConnected ? "var(--bronze)" : "var(--border)",
                    boxShadow: isConnected ? "0 0 0 1px var(--bronze), 0 8px 24px -8px rgba(163,138,112,0.2)" : "none",
                  }}>
                  {/* Top gradient strip */}
                  <div className="h-1 w-full" style={{ background: platform.gradient }} />

                  <div className="p-5">
                    <div className="flex items-start gap-4">
                      {/* Icon */}
                      <div className="h-12 w-12 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md"
                        style={{ background: platform.bg }}>
                        <Icon size={22} />
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-bold text-foreground">{platform.name}</span>
                          {platform.recommended && (
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                              style={{ background: "rgba(163,138,112,0.15)", color: "var(--bronze)" }}>
                              Best signals
                            </span>
                          )}
                          {isConnected && (
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1"
                              style={{ background: "rgba(122,139,118,0.15)", color: "var(--olive)" }}>
                              <CheckCircle2 size={10} />
                              @{connected[platform.id]}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">{platform.tagline}</p>
                        {/* Perks */}
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {platform.perks.map((perk) => (
                            <span key={perk} className="text-[10px] px-2 py-0.5 rounded-full border"
                              style={{ background: "var(--muted)", color: "var(--muted-foreground)", borderColor: "var(--border)" }}>
                              {perk}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="mt-4 flex items-center gap-2">
                      {isConnected ? (
                        <>
                          <div className="flex-1 flex items-center gap-2 rounded-xl px-3 py-2.5"
                            style={{ background: "rgba(122,139,118,0.1)" }}>
                            <CheckCircle2 size={15} style={{ color: "var(--olive)" }} />
                            <span className="text-sm font-medium" style={{ color: "var(--olive)" }}>
                              Connected as @{connected[platform.id]}
                            </span>
                          </div>
                          <button
                            onClick={() => handleDisconnect(platform.id)}
                            className="px-3 py-2.5 rounded-xl text-xs font-medium text-muted-foreground hover:text-foreground transition-colors border"
                            style={{ borderColor: "var(--border)", background: "var(--muted)" }}>
                            Remove
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => handleConnect(platform.id)}
                          disabled={isConnecting}
                          className="w-full flex items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:cursor-wait shadow-sm"
                          style={{ background: platform.gradient }}>
                          {isConnecting ? (
                            <>
                              <Loader2 size={15} className="animate-spin" />
                              Opening login window...
                            </>
                          ) : (
                            <>
                              <ExternalLink size={15} />
                              Log in with {platform.name}
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

          {/* Connected count */}
          {connectedCount > 0 && (
            <div className="mt-4 flex items-center gap-2 text-sm" style={{ color: "var(--olive)" }}>
              <CheckCircle2 size={14} />
              {connectedCount} account{connectedCount > 1 ? "s" : ""} connected
            </div>
          )}

          <div className="mt-8 flex items-center justify-between">
            <button onClick={() => setStep("welcome")}
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ChevronLeft size={16} />
              Back
            </button>
            <button
              onClick={() => setStep("context")}
              disabled={connectedCount === 0}
              className="flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ background: "linear-gradient(135deg, var(--bronze), #7A6040)" }}>
              Continue
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Context step ──
  const inputStyle = { background: "var(--muted)", borderColor: "var(--border)", color: "var(--foreground)" };
  const inputCls = "w-full rounded-xl border px-3.5 py-3 text-sm outline-none transition-all";
  function onFocus(e: React.FocusEvent<HTMLInputElement>) {
    e.target.style.borderColor = "var(--bronze)";
    e.target.style.boxShadow = "0 0 0 3px rgba(163,138,112,0.12)";
  }
  function onBlur(e: React.FocusEvent<HTMLInputElement>) {
    e.target.style.borderColor = "var(--border)";
    e.target.style.boxShadow = "none";
  }

  return (
    <div className="min-h-screen px-4 py-12" style={{ background: "var(--background)" }}>
      <div className="mx-auto max-w-lg">
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-5">
            {[0, 1].map((i) => (
              <div key={i} className="h-1.5 rounded-full transition-all duration-500"
                style={{ width: i === 1 ? 28 : 8, background: i <= 1 ? "var(--bronze)" : "var(--border)" }} />
            ))}
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Authorize and build</h1>
          <p className="mt-2 text-muted-foreground text-sm">
            We will analyze your public content to build your custom persona.
          </p>
        </div>

        <div className="space-y-3">
          {/* Connected accounts summary */}
          <div className="rounded-2xl border p-4" style={{ background: "var(--card)" }}>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Connected accounts
            </p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(connected).map(([id, username]) => {
                const p = PLATFORMS.find((pl) => pl.id === id)!;
                const Icon = p.icon;
                return (
                  <div key={id} className="flex items-center gap-2 rounded-full pl-1 pr-3 py-1 border text-sm font-medium"
                    style={{ background: "var(--muted)", borderColor: "var(--border)" }}>
                    <div className="h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0"
                      style={{ background: p.bg }}>
                      <Icon size={12} />
                    </div>
                    <span className="text-foreground">@{username}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Consent */}
          <div
            className="rounded-2xl border p-4 flex items-start gap-3 cursor-pointer transition-all"
            onClick={() => setConsent((c) => !c)}
            style={{
              background: consent ? "rgba(163,138,112,0.06)" : "var(--card)",
              borderColor: consent ? "var(--bronze)" : "var(--border)",
              boxShadow: consent ? "0 0 0 1px var(--bronze)" : "none",
            }}>
            <div className="flex-shrink-0 mt-0.5 h-5 w-5 rounded-md border-2 flex items-center justify-center transition-all"
              style={{ borderColor: consent ? "var(--bronze)" : "var(--border)", background: consent ? "var(--bronze)" : "transparent" }}>
              {consent && (
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path d="M2 5l2.5 2.5L8 3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Authorize persona analysis</p>
              <p className="text-xs text-muted-foreground mt-0.5 leading-snug">
                I authorize Ittera to analyze my connected accounts' public content to build my creator persona. Ittera will never post, modify, or share my content.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-8 flex items-center justify-between">
          <button onClick={() => setStep("connect")}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ChevronLeft size={16} />
            Back
          </button>
          <button
            onClick={handleBuild}
            disabled={!consent}
            className="group flex items-center gap-2 rounded-xl px-8 py-3.5 text-sm font-semibold text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg"
            style={{ background: "linear-gradient(135deg, var(--bronze), #7A6040)" }}>
            <Sparkles size={15} />
            Build my persona
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
