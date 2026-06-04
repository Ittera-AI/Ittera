"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, CheckCircle2 } from "lucide-react";

import { ProductShell } from "@/components/product/ProductShell";
import { useAuth } from "@/context/AuthContext";
import { useProduct } from "@/hooks/useProduct";
import type { BrandProfileData } from "@/services/product.service";

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden mb-6 transition-all duration-300 hover:shadow-md">
      <div className="border-b px-6 py-5 bg-muted/10">
        <h2 className="text-lg font-semibold tracking-tight text-foreground">{title}</h2>
        {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
      </div>
      <div className="px-6 py-6 bg-card space-y-6">{children}</div>
    </div>
  );
}

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:gap-8 border-b border-border/50 pb-6 last:border-0 last:pb-0">
      <label className="flex-shrink-0 pt-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground sm:w-40">{label}</label>
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
          className="flex items-center justify-center gap-2 rounded-lg border border-border bg-background px-4 py-2 h-9 text-xs font-medium text-foreground transition-all hover:bg-muted active:scale-[0.97] shadow-sm"
        >
          {product.isLoading ? <Loader2 size={14} className="animate-spin" /> : null}
          Re-generate Profile
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
            className="flex items-center justify-center gap-2 rounded-lg border border-border bg-background px-5 py-2.5 h-10 text-sm font-medium transition-all hover:bg-muted active:scale-[0.97] disabled:opacity-40 shadow-sm"
          >
            {saved ? <CheckCircle2 size={16} className="text-emerald-500" /> : null}
            {saved ? "Saved!" : "Save edits"}
          </button>
          <button
            type="button"
            onClick={() => void handleConfirm()}
            disabled={product.isLoading || isConfirmed}
            className="flex items-center justify-center gap-2 rounded-lg bg-foreground text-background px-6 py-2.5 h-10 text-sm font-semibold transition-all active:scale-[0.97] hover:bg-foreground/90 disabled:opacity-40 shadow-sm"
          >
            {isConfirmed ? "✓ Voice confirmed" : "Confirm voice profile"}
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
  const loadPublishingSettings = product.loadPublishingSettings;

  useEffect(() => {
    void loadDashboard().catch(() => undefined);
    void loadPublishingSettings().catch(() => undefined);
  }, [loadDashboard, loadPublishingSettings]);

  const profile = product.brandProfile?.profile;
  const isConfirmed = product.brandProfile?.is_confirmed ?? false;
  const confidence = useMemo(
    () => Math.round((product.brandProfile?.ai_confidence_score ?? 0) * 100),
    [product.brandProfile],
  );
  const version = product.brandProfile?.version ?? 0;
  const xConnection = product.socialConnections.find((connection) => connection.platform === "twitter");
  const autoPostEnabled = product.publishingSettings?.auto_post_enabled ?? false;
  const linkedinNeedsReconnect = !!product.linkedin?.reconnect_required;
  const xNeedsReconnect = !!xConnection?.reconnect_required;

  return (
    <ProductShell>
      <div className="flex max-w-4xl flex-col gap-8 pb-12">
        <div className="mb-4">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-500 mb-2">Settings</p>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Brand & Account</h1>
          <p className="mt-2 text-sm text-muted-foreground max-w-2xl">Configure your brand voice and view account details.</p>
        </div>

        <Section title="Account Details" description="Your personal information and active plan.">
          <div className="space-y-4">
            <FieldRow label="Name">
              <p className="text-sm font-medium text-foreground">{user?.name ?? "—"}</p>
            </FieldRow>
            <FieldRow label="Email">
              <p className="text-sm text-muted-foreground">{user?.email ?? "—"}</p>
            </FieldRow>
            <FieldRow label="Plan">
              <span
                className="inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                style={{ background: "rgba(163,138,112,0.15)", color: "var(--bronze)" }}
              >
                Founding Cohort
              </span>
            </FieldRow>
          </div>
        </Section>

        <Section title="Connected Accounts" description="Manage your social media integrations and posting status.">
          <div className="space-y-6">
            <FieldRow label="LinkedIn">
              <div className="flex flex-col gap-3">
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
                {product.linkedin?.connected ? (
                  <div className="flex flex-wrap gap-2">
                    <span
                      className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                      style={{
                        background: product.linkedin.posting_ready ? "rgba(150,165,145,0.15)" : "rgba(196,168,130,0.18)",
                        color: product.linkedin.posting_ready ? "var(--olive)" : "var(--bronze)",
                      }}
                    >
                      {product.linkedin.posting_ready ? "Posting ready" : "Reconnect for posting"}
                    </span>
                    <span
                      className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                      style={{
                        background: product.linkedin.read_sync_ready ? "rgba(150,165,145,0.15)" : "var(--muted)",
                        color: product.linkedin.read_sync_ready ? "var(--olive)" : "var(--text-muted)",
                      }}
                    >
                      {product.linkedin.read_sync_ready ? "Read sync ready" : "Read sync pending approval"}
                    </span>
                  </div>
                ) : null}
                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => void product.connectLinkedIn()}
                    disabled={product.isLoading || (!!product.linkedin?.connected && !linkedinNeedsReconnect)}
                    className="flex items-center justify-center rounded-lg border border-border bg-background px-5 py-2.5 h-10 text-sm font-medium text-foreground transition-all hover:bg-muted active:scale-[0.97] disabled:opacity-40 shadow-sm"
                  >
                    {linkedinNeedsReconnect ? "Reconnect LinkedIn" : "Connect LinkedIn"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void product.syncLinkedIn()}
                    disabled={product.isLoading || !product.linkedin?.connected || !product.linkedin?.read_sync_ready}
                    className="flex items-center justify-center rounded-lg border border-border bg-background px-5 py-2.5 h-10 text-sm font-medium text-foreground transition-all hover:bg-muted active:scale-[0.97] disabled:opacity-40 shadow-sm"
                  >
                    Sync Posts
                  </button>
                  <button
                    type="button"
                    onClick={() => void product.disconnectLinkedIn()}
                    disabled={product.isLoading || !product.linkedin?.connected}
                    className="flex items-center justify-center rounded-lg border border-destructive/30 bg-destructive/5 px-5 py-2.5 h-10 text-sm font-medium text-destructive transition-all hover:bg-destructive/10 active:scale-[0.97] disabled:opacity-40 shadow-sm"
                  >
                    Disconnect
                  </button>
                </div>
                {product.linkedin?.message ? <p className="text-xs text-muted-foreground">{product.linkedin.message}</p> : null}
                {product.linkedin?.missing_posting_scopes?.length ? (
                  <p className="text-xs text-destructive">Missing posting scopes: {product.linkedin.missing_posting_scopes.join(", ")}</p>
                ) : null}
              </div>
            </FieldRow>
            
            <div className="h-px bg-border" />
            
            <FieldRow label="X (Twitter)">
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-foreground">
                    {xConnection ? `@${xConnection.username}` : "Not connected"}
                  </p>
                  <span
                    className="rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                    style={{
                      background: xConnection ? "rgba(150,165,145,0.15)" : "var(--muted)",
                      color: xConnection ? "var(--olive)" : "var(--text-muted)",
                    }}
                  >
                    {xConnection ? "Connected" : "Offline"}
                  </span>
                </div>
                {xConnection ? (
                  <div className="flex flex-wrap gap-2">
                    <span
                      className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold"
                      style={{
                        background: xConnection.posting_ready ? "rgba(150,165,145,0.15)" : "rgba(196,168,130,0.18)",
                        color: xConnection.posting_ready ? "var(--olive)" : "var(--bronze)",
                      }}
                    >
                      {xConnection.posting_ready ? "Posting ready" : "Reconnect required"}
                    </span>
                  </div>
                ) : null}
                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => void product.connectTwitter()}
                    disabled={product.isLoading || (!!xConnection && !xNeedsReconnect)}
                    className="flex items-center justify-center rounded-lg border border-border bg-background px-5 py-2.5 h-10 text-sm font-medium text-foreground transition-all hover:bg-muted active:scale-[0.97] disabled:opacity-40 shadow-sm"
                  >
                    {xNeedsReconnect ? "Reconnect X" : "Connect X"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void product.disconnectTwitter()}
                    disabled={product.isLoading || !xConnection}
                    className="flex items-center justify-center rounded-lg border border-destructive/30 bg-destructive/5 px-5 py-2.5 h-10 text-sm font-medium text-destructive transition-all hover:bg-destructive/10 active:scale-[0.97] disabled:opacity-40 shadow-sm"
                  >
                    Disconnect X
                  </button>
                </div>
                {xConnection?.missing_scopes?.length ? (
                  <p className="mt-2 text-xs text-destructive">Missing X scopes: {xConnection.missing_scopes.join(", ")}</p>
                ) : null}
              </div>
            </FieldRow>
            {product.error ? <p className="mt-2 text-xs text-destructive">{product.error}</p> : null}
          </div>
        </Section>

        <Section title="Publishing Preferences" description="Configure global publishing behavior.">
          <div className="space-y-4">
            <FieldRow label="Auto-post">
              <label className="group flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-colors hover:bg-muted/50" style={{ borderColor: autoPostEnabled ? "var(--olive)" : "var(--border)" }}>
                <input
                  type="checkbox"
                  checked={autoPostEnabled}
                  onChange={(event) => void product.updatePublishingSettings({ auto_post_enabled: event.target.checked })}
                  className="mt-1 h-4 w-4 rounded border accent-foreground focus:ring-1 focus:ring-ring"
                />
                <div className="flex flex-col gap-1">
                  <span className="text-sm font-medium text-foreground">
                    {autoPostEnabled ? "Publish scheduled posts automatically" : "Send review email before scheduled posts"}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    When off, scheduled posts wait for approval and a review email is sent 24 hours before publish time.
                  </span>
                </div>
              </label>
            </FieldRow>
          </div>
        </Section>

        <Section title="Brand Voice Profile" description="Your AI-generated writing style and content strategy.">
          {profile ? (
            <BrandProfileSection key={version} initialProfile={profile} isConfirmed={isConfirmed} confidence={confidence} />
          ) : (
            <div className="rounded-lg px-4 py-4 text-sm text-muted-foreground border flex items-center justify-center bg-muted/30">
              No profile yet. Sync LinkedIn posts then click Re-generate.
            </div>
          )}
        </Section>

        <Section title="Storage & Integrations" description="Manage your Google Drive connection, Calendar sync, and data privacy settings.">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border border-border/50 rounded-xl p-6 bg-gradient-to-r from-muted/20 to-transparent hover:border-border transition-colors">
            <div>
              <h3 className="text-base font-semibold text-foreground">Google Workspace & Privacy</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-lg">Manage your cloud storage location, calendar synchronization, and data retention rules.</p>
            </div>
            <a href="/settings/storage" className="shrink-0">
              <button className="rounded-lg border border-border bg-background px-5 py-2.5 h-10 text-sm font-semibold transition-all hover:bg-muted active:scale-[0.97] shadow-sm">
                Manage Integrations
              </button>
            </a>
          </div>
        </Section>
      </div>
    </ProductShell>
  );
}
