"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, type UpdatePermanentContextRequest } from "@/lib/api";
import {
  ArrowRight,
  Sparkles,
  Loader2,
  AlertCircle,
  Building2,
  Compass,
  Users,
  Target,
  type LucideIcon,
} from "lucide-react";

type PlatformId = "linkedin" | "twitter" | "instagram";

const PLATFORMS: { id: PlatformId; label: string }[] = [
  { id: "linkedin", label: "LinkedIn" },
  { id: "twitter", label: "X / Twitter" },
  { id: "instagram", label: "Instagram" },
];

interface FormState {
  brand_name: string;
  niche: string;
  primary_platform: PlatformId;
  bio: string;
  target_audience: string;
  content_mission: string;
}

const EMPTY: FormState = {
  brand_name: "",
  niche: "",
  primary_platform: "linkedin",
  bio: "",
  target_audience: "",
  content_mission: "",
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.detail;
  if (error instanceof Error) return error.message;
  return "Something went wrong. Please try again.";
}

export default function ContextOnboardingPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prefill from the user's existing permanent context (idempotent re-entry).
  useEffect(() => {
    let active = true;
    api.context
      .get()
      .then((ctx) => {
        if (!active) return;
        const p = ctx.permanent;
        setForm({
          brand_name: p.brand_name ?? "",
          niche: p.niche ?? "",
          primary_platform: (p.primary_platform as PlatformId) || "linkedin",
          bio: p.bio ?? "",
          target_audience: p.target_audience ?? "",
          content_mission: p.content_mission ?? "",
        });
      })
      .catch(() => {
        /* No existing context yet — start from an empty form. */
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  const canContinue = form.bio.trim().length > 0 && form.target_audience.trim().length > 0;

  async function handleSave(next: "persona" | "dashboard") {
    if (!canContinue || saving) return;
    setSaving(true);
    setError(null);
    const payload: UpdatePermanentContextRequest = {
      brand_name: form.brand_name.trim() || null,
      niche: form.niche.trim() || null,
      primary_platform: form.primary_platform,
      bio: form.bio.trim(),
      target_audience: form.target_audience.trim(),
      content_mission: form.content_mission.trim() || null,
    };
    try {
      await api.context.updatePermanent(payload);
      router.push(next === "persona" ? "/onboarding/persona" : "/dashboard");
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ background: "var(--background)" }}
      >
        <Loader2 size={32} className="animate-spin text-[var(--bronze)]" />
      </div>
    );
  }

  return (
    <div
      className="relative min-h-screen px-6 py-16 md:py-24 flex flex-col items-center"
      style={{ background: "var(--background)" }}
    >
      {/* Ambient background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse at top, rgba(163,138,112,0.12), transparent 70%)" }}
      />

      <div className="relative z-10 w-full max-w-2xl animate-in slide-in-from-bottom-6 fade-in duration-700">
        {/* Header */}
        <div className="mb-10 text-center space-y-4">
          <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-md">
            <Sparkles size={16} className="text-[var(--bronze)]" />
            <span className="text-xs font-semibold text-foreground uppercase tracking-widest">
              Step 1 of 2 · Your Foundation
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">
            Tell us who you are
          </h1>
          <p className="text-base md:text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed">
            This is your <span className="text-foreground font-medium">permanent context</span> — the
            identity behind every piece Ittera helps you create. It never changes unless you say so.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div
            className="mb-8 flex items-center gap-3 rounded-2xl border px-5 py-4 text-sm font-medium backdrop-blur-md"
            style={{ background: "rgba(239,68,68,0.1)", borderColor: "rgba(239,68,68,0.2)", color: "#ef4444" }}
          >
            <AlertCircle size={18} className="flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Form card */}
        <div
          className="rounded-[2rem] border border-white/8 p-8 md:p-10 space-y-7 shadow-2xl"
          style={{ background: "rgba(20,20,20,0.45)", backdropFilter: "blur(20px)" }}
        >
          <div className="grid md:grid-cols-2 gap-6">
            <Field label="Brand or name" icon={Building2} hint="Personal or company brand">
              <input
                type="text"
                value={form.brand_name}
                onChange={(e) => update("brand_name", e.target.value)}
                placeholder="e.g. Jane Doe or Iterra"
                className={inputClass}
              />
            </Field>

            <Field label="Niche" icon={Compass} hint="Your primary topic area">
              <input
                type="text"
                value={form.niche}
                onChange={(e) => update("niche", e.target.value)}
                placeholder="e.g. B2B SaaS growth"
                className={inputClass}
              />
            </Field>
          </div>

          <Field label="Primary platform" icon={Target} hint="Where you publish most">
            <div className="flex flex-wrap gap-3">
              {PLATFORMS.map((p) => {
                const active = form.primary_platform === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => update("primary_platform", p.id)}
                    className="px-5 py-2.5 rounded-full text-sm font-semibold border transition-all duration-300"
                    style={{
                      background: active ? "rgba(163,138,112,0.15)" : "rgba(255,255,255,0.04)",
                      borderColor: active ? "var(--bronze)" : "rgba(255,255,255,0.1)",
                      color: active ? "var(--bronze)" : "rgba(255,255,255,0.6)",
                    }}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
          </Field>

          <Field label="Bio" icon={Sparkles} hint="2–4 sentences, in your own words" required>
            <textarea
              value={form.bio}
              onChange={(e) => update("bio", e.target.value)}
              rows={3}
              placeholder="Who you are and what you bring to your audience."
              className={textareaClass}
            />
          </Field>

          <Field label="Target audience" icon={Users} hint="Who you create for" required>
            <textarea
              value={form.target_audience}
              onChange={(e) => update("target_audience", e.target.value)}
              rows={2}
              placeholder="e.g. Early-stage founders and product leaders scaling their first GTM motion."
              className={textareaClass}
            />
          </Field>

          <Field label="Content mission" icon={Compass} hint="Why you create — the change you drive">
            <textarea
              value={form.content_mission}
              onChange={(e) => update("content_mission", e.target.value)}
              rows={2}
              placeholder="e.g. Help technical founders communicate value without the jargon."
              className={textareaClass}
            />
          </Field>
        </div>

        {/* Actions */}
        <div className="mt-10 flex items-center justify-between gap-6">
          <button
            type="button"
            onClick={() => handleSave("dashboard")}
            disabled={!canContinue || saving}
            className="text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"
          >
            Save &amp; finish later
          </button>

          <div className="flex flex-col items-end gap-2">
            <button
              type="button"
              onClick={() => handleSave("persona")}
              disabled={!canContinue || saving}
              className="group flex items-center gap-2 rounded-full px-8 py-4 text-sm font-bold text-white transition-all hover:scale-105 active:scale-[0.98] disabled:opacity-30 disabled:scale-100 disabled:cursor-not-allowed shadow-[0_0_30px_-10px_var(--bronze)] hover:shadow-[0_0_40px_-10px_var(--bronze)]"
              style={{ background: "linear-gradient(135deg, var(--bronze), #7A6040)" }}
            >
              {saving ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  Continue to Persona
                  <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
                </>
              )}
            </button>
            {!canContinue && (
              <p className="text-xs text-muted-foreground">Bio and target audience are required.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Field wrapper ────────────────────────────────────────────────────────────

const inputClass =
  "w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none transition-colors focus:border-[var(--bronze)] focus:ring-1 focus:ring-[var(--bronze)]/40";

const textareaClass = `${inputClass} resize-none leading-relaxed`;

function Field({
  label,
  icon: Icon,
  hint,
  required,
  children,
}: {
  label: string;
  icon: LucideIcon;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Icon size={15} className="text-[var(--bronze)]" />
        <label className="text-sm font-semibold text-foreground">
          {label}
          {required && <span className="text-[var(--bronze)]"> *</span>}
        </label>
        {hint && <span className="text-xs text-muted-foreground">· {hint}</span>}
      </div>
      {children}
    </div>
  );
}
