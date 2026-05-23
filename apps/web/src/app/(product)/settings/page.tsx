"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, CheckCircle2 } from "lucide-react";

import { ProductShell } from "@/components/product/ProductShell";
import { useAuth } from "@/context/AuthContext";
import { useProduct } from "@/hooks/useProduct";
import type { BrandProfileData } from "@/services/product.service";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border overflow-hidden" style={{ background: "var(--card)" }}>
      <div className="border-b px-5 py-4">
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
      </div>
      <div className="px-5 py-5">{children}</div>
    </div>
  );
}

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:gap-8">
      <label className="flex-shrink-0 text-xs font-semibold uppercase tracking-wider text-muted-foreground sm:w-32">{label}</label>
      <div className="flex-1">{children}</div>
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
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
            style={{ background: isConfirmed ? "var(--olive)" : "rgba(163,138,112,0.6)" }}
          />
          <p className="text-xs font-medium text-foreground">{isConfirmed ? "Voice confirmed" : "Profile not confirmed"}</p>
          {confidence > 0 ? (
            <span className="text-[11px] text-muted-foreground">— AI confidence: {confidence}%</span>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => void product.generateBrandProfile()}
          disabled={product.isLoading}
          className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:bg-muted hover:text-foreground active:scale-[0.97]"
        >
          {product.isLoading ? <Loader2 size={11} className="animate-spin" /> : null}
          Re-generate
        </button>
      </div>

      <div className="space-y-4">
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
                  rows={3}
                  className="w-full resize-none rounded-lg border px-3 py-2 text-sm text-foreground transition-all focus:outline-none focus:ring-2"
                  style={{ background: "var(--muted)", borderColor: "var(--border)" }}
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
                  className="w-full rounded-lg border px-3 py-2 text-sm text-foreground transition-all focus:outline-none focus:ring-2"
                  style={{ background: "var(--muted)", borderColor: "var(--border)" }}
                />
              )}
            </FieldRow>
          );
        })}

        <div className="flex flex-wrap gap-2 pt-1">
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={product.isLoading}
            className="flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-all hover:bg-muted active:scale-[0.97] disabled:opacity-40"
          >
            {saved ? <CheckCircle2 size={13} style={{ color: "var(--olive)" }} /> : null}
            {saved ? "Saved!" : "Save edits"}
          </button>
          <button
            type="button"
            onClick={() => void handleConfirm()}
            disabled={product.isLoading || isConfirmed}
            className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-all active:scale-[0.97] disabled:opacity-40"
            style={{ background: "var(--foreground)", color: "var(--background)" }}
          >
            {isConfirmed ? "✓ Voice confirmed" : "This is me — confirm voice"}
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

  return (
    <ProductShell>
      <div className="flex max-w-2xl flex-col gap-6">
        <div>
          <p className="eyebrow">Settings</p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-[-0.04em]">Brand & Account</h1>
          <p className="mt-1.5 max-w-xl text-sm text-muted-foreground">Configure your brand voice and view account details.</p>
        </div>

        <Section title="Account">
          <div className="space-y-4">
            <FieldRow label="Name">
              <p className="text-sm text-foreground">{user?.name ?? "—"}</p>
            </FieldRow>
            <FieldRow label="Email">
              <p className="text-sm text-muted-foreground">{user?.email ?? "—"}</p>
            </FieldRow>
            <FieldRow label="Plan">
              <span
                className="rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                style={{ background: "rgba(163,138,112,0.15)", color: "var(--bronze)" }}
              >
                Founding Cohort
              </span>
            </FieldRow>
          </div>
        </Section>

        <Section title="LinkedIn source">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">{product.linkedin?.platform_username ?? "Not connected"}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {product.linkedin?.synced_posts
                    ? `${product.linkedin.synced_posts} posts synced`
                    : "No posts synced yet"}
                </p>
              </div>
              <span
                className="rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                style={{
                  background: product.linkedin?.connected ? "rgba(150,165,145,0.15)" : "var(--muted)",
                  color: product.linkedin?.connected ? "var(--olive)" : "var(--text-muted)",
                }}
              >
                {product.linkedin?.connected ? "Connected" : "Offline"}
              </span>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => void product.connectLinkedIn()}
                disabled={product.isLoading || !!product.linkedin?.connected}
                className="rounded-lg border px-3 py-2 text-xs font-medium text-muted-foreground transition-all hover:bg-muted hover:text-foreground active:scale-[0.97] disabled:opacity-40"
              >
                Connect mock LinkedIn
              </button>
              <button
                type="button"
                onClick={() => void product.syncLinkedIn()}
                disabled={product.isLoading || !product.linkedin?.connected}
                className="rounded-lg border px-3 py-2 text-xs font-medium text-muted-foreground transition-all hover:bg-muted hover:text-foreground active:scale-[0.97] disabled:opacity-40"
              >
                Sync posts
              </button>
            </div>
          </div>
        </Section>

        <Section title="Brand Profile">
          {profile ? (
            <BrandProfileSection key={version} initialProfile={profile} isConfirmed={isConfirmed} confidence={confidence} />
          ) : (
            <div className="rounded-lg px-4 py-3 text-xs text-muted-foreground" style={{ background: "var(--muted)" }}>
              No profile yet. Sync LinkedIn posts then click Re-generate.
            </div>
          )}
        </Section>
      </div>
    </ProductShell>
  );
}
