"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, CheckCircle2, Sparkles, Zap, Twitter, Linkedin, Instagram, ExternalLink, Camera } from "lucide-react";

import { ProductShell } from "@/components/product/ProductShell";
import { useAuth } from "@/context/AuthContext";
import { useProduct } from "@/hooks/useProduct";
import type { BrandProfileData } from "@/services/product.service";
import { api } from "@/lib/api";
import { supabase } from "@/lib/supabase";

function Section({ title, children, icon: Icon }: { title: string; children: React.ReactNode; icon?: any }) {
  return (
    <div className="rounded-[2.5rem] border border-white/5 overflow-hidden transition-all duration-700 hover:shadow-[0_20px_60px_-15px_rgba(163,138,112,0.1)] relative group" 
      style={{ background: "rgba(255,255,255,0.02)", backdropFilter: "blur(20px)" }}>
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[var(--bronze)]/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
      <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
      
      <div className="border-b border-white/5 px-8 md:px-10 py-6 md:py-8 relative z-10 flex items-center gap-3">
        {Icon && (
          <div className="bg-[var(--bronze)]/10 p-2 rounded-xl border border-[var(--bronze)]/20 shadow-[0_0_15px_rgba(163,138,112,0.15)]">
            <Icon size={18} className="text-[var(--bronze)]" />
          </div>
        )}
        <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">{title}</h2>
      </div>
      <div className="px-8 md:px-10 py-8 md:py-10 relative z-10">{children}</div>
    </div>
  );
}

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2.5 sm:flex-row sm:items-start sm:gap-10">
      <label className="flex-shrink-0 text-xs font-bold uppercase tracking-widest text-white/40 sm:w-40 sm:pt-3 flex items-center gap-2">
        <div className="w-1 h-1 rounded-full bg-white/20" />
        {label}
      </label>
      <div className="flex-1 w-full">{children}</div>
    </div>
  );
}

/** Isolated draft state keyed by profile version — avoids syncing via effects. */
function BrandProfileSection({
  initialProfile,
  isConfirmed,
  confidence,
}: {
  initialProfile: BrandProfileData;
  isConfirmed: boolean;
  confidence: number;
}) {
  const product = useProduct();
  const [draft, setDraft] = useState(initialProfile);
  const [saved, setSaved] = useState(false);

  async function handleSave() {
    await product.updateBrandProfile(draft);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2000);
  }

  async function handleConfirm() {
    await product.confirmBrandProfile();
  }

  return (
    <div className="flex flex-col gap-10">
      {/* Top controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 p-6 rounded-3xl bg-black/40 border border-white/5 shadow-inner">
        <div className="flex items-center gap-4">
          <div className="relative flex items-center justify-center">
            <div className="absolute inset-0 rounded-full animate-ping opacity-40" style={{ background: isConfirmed ? "var(--olive)" : "var(--bronze)" }} />
            <div className="relative h-4 w-4 rounded-full border-2 border-black" style={{ background: isConfirmed ? "var(--olive)" : "var(--bronze)" }} />
          </div>
          <div>
            <p className="text-sm font-bold text-white">{isConfirmed ? "Voice Model Calibrated" : "Calibration Required"}</p>
            {confidence > 0 && (
              <p className="text-xs font-medium text-white/50 flex items-center gap-1.5 mt-1">
                <Sparkles size={10} className="text-[var(--bronze)]" />
                AI Confidence: <span className="text-white">{confidence}%</span>
              </p>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={() => void product.generateBrandProfile()}
          disabled={product.isLoading}
          className="group flex items-center gap-2 rounded-xl bg-white/5 border border-white/10 px-5 py-2.5 text-xs font-bold text-white transition-all hover:bg-white/10 hover:border-white/20 active:scale-[0.97] disabled:opacity-50"
        >
          {product.isLoading ? <Loader2 size={14} className="animate-spin text-[var(--bronze)]" /> : <Zap size={14} className="text-[var(--bronze)] group-hover:scale-110 transition-transform" />}
          Re-Analyze Voice
        </button>
      </div>

      {/* Editor Fields */}
      <div className="space-y-8">
        {[
          { label: "Voice tone", field: "voice_tone" as const, multiLine: false },
          { label: "Audience", field: "audience" as const, multiLine: false },
          { label: "Core topics", field: "core_topics" as const, multiLine: false, isArray: true },
          { label: "Writing patterns", field: "writing_patterns" as const, multiLine: false, isArray: true },
          { label: "Content pillars", field: "content_pillars" as const, multiLine: false, isArray: true },
          { label: "Hashtag strategy", field: "hashtag_strategy" as const, multiLine: false },
          { label: "Summary", field: "summary" as const, multiLine: true },
        ].map(({ label, field, multiLine, isArray }) => {
          const value = draft[field];
          const displayValue = Array.isArray(value) ? value.join(", ") : String(value ?? "");
          return (
            <FieldRow key={field} label={label}>
              {multiLine ? (
                <textarea
                  value={displayValue}
                  onChange={(e) => {
                    const v = e.target.value;
                    setDraft((d) => ({ ...d, [field]: v }));
                  }}
                  rows={4}
                  className="w-full resize-none rounded-2xl border border-white/10 bg-black/20 px-5 py-4 text-sm font-medium text-white shadow-inner transition-all hover:bg-black/30 focus:outline-none focus:border-[var(--bronze)] focus:ring-1 focus:ring-[var(--bronze)]/50"
                />
              ) : (
                <input
                  value={displayValue}
                  onChange={(e) => {
                    const v = e.target.value;
                    setDraft((d) => ({
                      ...d,
                      [field]: isArray ? v.split(",").map((s) => s.trim()).filter(Boolean) : v,
                    }));
                  }}
                  className="w-full rounded-2xl border border-white/10 bg-black/20 px-5 py-4 text-sm font-medium text-white shadow-inner transition-all hover:bg-black/30 focus:outline-none focus:border-[var(--bronze)] focus:ring-1 focus:ring-[var(--bronze)]/50"
                />
              )}
            </FieldRow>
          );
        })}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 pt-8 border-t border-white/5">
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={product.isLoading}
            className="w-full sm:w-auto relative flex items-center justify-center gap-2 rounded-2xl bg-white/5 border border-white/10 px-8 py-3.5 text-sm font-bold text-white transition-all hover:bg-white/10 hover:border-white/20 active:scale-[0.97] disabled:opacity-40"
          >
            {saved ? <CheckCircle2 size={16} className="text-[var(--olive)]" /> : null}
            {saved ? "Modifications Saved" : "Save Modifications"}
          </button>
          
          <button
            type="button"
            onClick={() => void handleConfirm()}
            disabled={product.isLoading || isConfirmed}
            className="w-full sm:w-auto group relative overflow-hidden flex items-center justify-center gap-2 rounded-2xl px-8 py-3.5 text-sm font-bold text-white transition-all active:scale-[0.97] disabled:opacity-40 shadow-[0_0_30px_-10px_var(--bronze)] hover:shadow-[0_0_40px_-10px_var(--bronze)]"
            style={{ background: isConfirmed ? "var(--olive)" : "linear-gradient(135deg, var(--bronze), #8B6040)" }}
          >
            {isConfirmed ? (
              <>
                <CheckCircle2 size={16} />
                Verified & Locked
              </>
            ) : (
              <>
                <span className="relative z-10 flex items-center gap-2">
                  <CheckCircle2 size={16} />
                  Confirm Voice Integrity
                </span>
                <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const product = useProduct();
  const loadDashboard = product.loadDashboard;

  type PlatformId = "twitter" | "linkedin" | "instagram";
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [connected, setConnected] = useState<Partial<Record<PlatformId, string>>>({});
  const [connecting, setConnecting] = useState<PlatformId | null>(null);
  const [connectError, setConnectError] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.access_token) setAuthToken(session.access_token);
    });
  }, []);

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

  function handleConnect(platformId: PlatformId) {
    if (!authToken) {
      setConnectError("Please wait — fetching your session...");
      return;
    }
    setConnectError(null);
    setConnecting(platformId);
    const url = api.connect.startUrl(platformId, authToken);
    
    const w = 520, h = 680;
    const left = window.screenX + (window.outerWidth - w) / 2;
    const top = window.screenY + (window.outerHeight - h) / 2;
    const popup = window.open(url, "ittera_oauth", `width=${w},height=${h},left=${left},top=${top},toolbar=0,menubar=0`);
    
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

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const profile = product.brandProfile?.profile;
  const isConfirmed = product.brandProfile?.is_confirmed ?? false;
  const confidence = useMemo(
    () => Math.round((product.brandProfile?.ai_confidence_score ?? 0) * 100),
    [product.brandProfile],
  );
  const version = product.brandProfile?.version ?? 0;

  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editName, setEditName] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !user) return;
    
    setAvatarError(null);
    setIsUploadingAvatar(true);
    try {
      const ext = file.name.split('.').pop();
      const fileName = `${user.email?.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.${ext}`;
      
      const { data, error } = await supabase.storage
        .from("avatars")
        .upload(fileName, file, { upsert: true });
        
      if (error) throw error;
      
      const { data: { publicUrl } } = supabase.storage.from("avatars").getPublicUrl(fileName);
      
      await supabase.auth.updateUser({
        data: { avatar_url: publicUrl }
      });
    } catch (err: any) {
      console.error("Avatar upload failed:", err);
      setAvatarError("Upload failed. Create a public 'avatars' bucket in Supabase.");
    } finally {
      setIsUploadingAvatar(false);
    }
  }

  function handleEditProfile() {
    setEditName(user?.name || "");
    setIsEditingProfile(true);
  }

  async function handleSaveProfile() {
    setIsSavingProfile(true);
    const { error } = await supabase.auth.updateUser({
      data: { full_name: editName, name: editName },
    });
    setIsSavingProfile(false);
    if (!error) {
      setIsEditingProfile(false);
    } else {
      console.error(error);
    }
  }

  return (
    <ProductShell>
      <div className="relative min-h-screen w-full pb-32">
        {/* Ambient Page Background */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 right-0 w-[800px] h-[800px] rounded-full blur-[150px] opacity-10 bg-[var(--bronze)]" />
          <div className="absolute -bottom-[20%] -left-[10%] w-[600px] h-[600px] rounded-full blur-[150px] opacity-10 bg-[var(--olive)]" />
        </div>

        <div className="relative z-10 mx-auto max-w-4xl flex flex-col gap-12 pt-12">
          
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 bg-white/5 backdrop-blur-md">
              <div className="w-1.5 h-1.5 rounded-full bg-[var(--bronze)] animate-pulse" />
              <span className="text-[10px] font-bold text-white/70 uppercase tracking-widest">Configuration Matrix</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white leading-tight">
              Settings & Profile
            </h1>
            <p className="max-w-xl text-lg text-white/50 font-medium">
              Manage your personal identity, external data pipelines, and core AI voice models.
            </p>
          </div>

          <Section title="Operator Identity">
            <div className="flex flex-col sm:flex-row gap-10 items-start">
              {/* Premium Avatar */}
              <div className="flex-shrink-0 relative group mb-6 sm:mb-0">
                <div className="absolute inset-0 rounded-[2.5rem] bg-gradient-to-br from-[var(--bronze)] to-[#8B6040] blur-xl opacity-40 group-hover:opacity-60 transition-opacity duration-500" />
                <label className="relative h-32 w-32 rounded-[2.5rem] bg-gradient-to-br from-[var(--bronze)] to-[#8B6040] p-[2px] shadow-2xl block cursor-pointer group/avatar overflow-hidden">
                  <div className="h-full w-full rounded-[2.4rem] bg-black/80 flex items-center justify-center backdrop-blur-xl relative overflow-hidden">
                    {user?.avatar_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={user.avatar_url} alt="Profile" className="h-full w-full object-cover rounded-[2.4rem]" />
                    ) : (
                      <span className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-br from-white to-white/40 uppercase">
                        {user?.name?.[0] ?? "O"}
                      </span>
                    )}
                    
                    {/* Hover Overlay */}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover/avatar:opacity-100 flex items-center justify-center transition-opacity duration-300">
                      <Camera size={24} className="text-white" />
                    </div>

                    {isUploadingAvatar && (
                      <div className="absolute inset-0 bg-black/80 flex items-center justify-center">
                        <Loader2 size={24} className="animate-spin text-[var(--bronze)]" />
                      </div>
                    )}
                  </div>
                  <input type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} disabled={isUploadingAvatar} />
                </label>
                {avatarError && <p className="absolute -bottom-10 left-0 right-0 text-center text-[10px] text-red-400 font-bold max-w-[128px] leading-tight">{avatarError}</p>}
              </div>
              
              <div className="space-y-8 flex-1 w-full pt-2">
                <FieldRow label="Full Name">
                  {isEditingProfile ? (
                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                      <input
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="w-full sm:w-auto rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-base font-bold text-white shadow-inner transition-all focus:outline-none focus:border-[var(--bronze)] focus:ring-1 focus:ring-[var(--bronze)]/50"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => void handleSaveProfile()}
                          disabled={isSavingProfile}
                          className="rounded-xl bg-white/10 px-4 py-2 text-xs font-bold text-white hover:bg-white/20 transition-colors disabled:opacity-50"
                        >
                          {isSavingProfile ? <Loader2 size={14} className="animate-spin" /> : "Save"}
                        </button>
                        <button
                          onClick={() => setIsEditingProfile(false)}
                          className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/50 hover:text-white transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-1.5 items-start">
                      <p className="text-xl font-bold text-white">{user?.name ?? "—"}</p>
                      <button onClick={handleEditProfile} className="text-[11px] font-bold tracking-widest uppercase text-[var(--bronze)] hover:brightness-125 transition-colors">
                        Edit Profile
                      </button>
                    </div>
                  )}
                </FieldRow>
                <FieldRow label="Email Address">
                  <div className="flex flex-col gap-1 items-start">
                    <p className="text-sm font-semibold text-white/60">{user?.email ?? "—"}</p>
                    <p className="text-[10px] font-bold text-white/20 uppercase tracking-widest mt-0.5">Read Only</p>
                  </div>
                </FieldRow>
                <FieldRow label="Access Tier">
                  <span
                    className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-bold tracking-widest uppercase border border-[var(--bronze)]/30 shadow-[0_0_20px_-5px_rgba(163,138,112,0.3)]"
                    style={{ background: "rgba(163,138,112,0.1)", color: "var(--bronze)" }}
                  >
                    <Sparkles size={14} />
                    Founding Cohort
                  </span>
                </FieldRow>
              </div>
            </div>
          </Section>

          <Section title="Data Pipelines">
            <div className="space-y-6">
              <p className="text-sm font-medium text-white/50 mb-8">
                Connect external platforms to feed live data into your persona intelligence engine.
              </p>
              
              {connectError && (
                <div className="flex items-center gap-3 rounded-2xl border px-5 py-4 text-sm font-bold bg-red-900/20 border-red-500/30 text-red-400 backdrop-blur-md">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  {connectError}
                </div>
              )}
              
              <div className="grid grid-cols-1 gap-4">
                {["twitter", "linkedin", "instagram"].map((platformId) => {
                  const isConnected = !!connected[platformId as PlatformId];
                  const isConnecting = connecting === platformId;
                  
                  const pConfig: Record<string, { name: string, icon: any, gradient: string }> = { 
                    twitter: { name: "X / Twitter", icon: Twitter, gradient: "linear-gradient(135deg, #1a1a1a, #000000)" }, 
                    linkedin: { name: "LinkedIn", icon: Linkedin, gradient: "linear-gradient(135deg, #0A66C2, #004182)" }, 
                    instagram: { name: "Instagram", icon: Instagram, gradient: "linear-gradient(135deg, #f09433, #bc1888)" } 
                  };
                  const cfg = pConfig[platformId];
                  const Icon = cfg.icon;

                  return (
                    <div key={platformId} className="group flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-3xl p-5 border border-white/5 transition-all duration-300 hover:bg-white/5" style={{ background: "rgba(0,0,0,0.2)" }}>
                      <div className="flex items-center gap-5">
                        <div className="h-14 w-14 rounded-2xl flex items-center justify-center shadow-lg border border-white/10" style={{ background: cfg.gradient }}>
                          <Icon size={24} className="text-white" />
                        </div>
                        <div>
                          <p className="text-base font-bold text-white tracking-tight">{cfg.name}</p>
                          {isConnected ? (
                            <p className="mt-1 flex items-center gap-1.5 text-xs font-semibold text-[var(--olive)] bg-[var(--olive)]/10 px-2.5 py-1 rounded-full border border-[var(--olive)]/20 w-fit">
                              <CheckCircle2 size={12} className="animate-pulse" />
                              Synced as @{connected[platformId as PlatformId]}
                            </p>
                          ) : (
                            <p className="mt-1 text-xs font-medium text-white/40">Pipeline disconnected</p>
                          )}
                        </div>
                      </div>
                      <div className="flex sm:justify-end">
                        {isConnected ? (
                          <button
                            type="button"
                            onClick={() => handleDisconnect(platformId as PlatformId)}
                            className="w-full sm:w-auto rounded-xl border border-white/10 bg-black/40 px-5 py-2.5 text-xs font-bold text-white/50 transition-all hover:bg-red-900/20 hover:text-red-400 hover:border-red-500/30 active:scale-[0.97]"
                          >
                            Terminate
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleConnect(platformId as PlatformId)}
                            disabled={isConnecting}
                            className="w-full sm:w-auto relative overflow-hidden flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-xs font-bold text-white transition-all hover:brightness-110 active:scale-[0.97] disabled:opacity-40"
                            style={{ background: cfg.gradient }}
                          >
                            {isConnecting ? (
                              <><Loader2 size={14} className="animate-spin relative z-10" /> Connecting...</>
                            ) : (
                              <><ExternalLink size={14} className="relative z-10" /> Establish Link</>
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </Section>

          <Section title="Cognitive Brand Identity">
            <p className="text-sm font-medium text-white/50 mb-8 max-w-2xl">
              This is your unique digital fingerprint. The engine continuously synthesizes your connected data streams to maintain an accurate voice model, which you can manually fine-tune below.
            </p>
            {profile ? (
              <BrandProfileSection key={version} initialProfile={profile} isConfirmed={isConfirmed} confidence={confidence} />
            ) : (
              <div className="rounded-[2rem] border border-dashed border-white/20 bg-black/20 p-12 text-center flex flex-col items-center justify-center gap-4">
                <div className="bg-[var(--bronze)]/10 p-4 rounded-full">
                  <Zap size={24} className="text-[var(--bronze)] opacity-50" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">Awaiting Data Ingestion</h3>
                  <p className="text-sm font-medium text-white/40 max-w-md mx-auto">
                    Establish at least one data pipeline above, then return to the Dashboard to ignite the persona synthesis engine.
                  </p>
                </div>
              </div>
            )}
          </Section>

        </div>
        
        <style>{`
          @keyframes shimmer { 100% { transform: translateX(100%); } }
        `}</style>
      </div>
    </ProductShell>
  );
}
