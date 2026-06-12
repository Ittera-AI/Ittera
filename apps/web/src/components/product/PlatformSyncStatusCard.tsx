"use client";

import { useState, useCallback, useEffect } from "react";
import { Loader2, CheckCircle2, XCircle, AlertTriangle, RefreshCw, Clock, Wifi, WifiOff } from "lucide-react";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { productService, type TwitterTierResponse } from "@/services/product.service";

/**
 * Represents the sync status for a connected social platform.
 * Matches the backend response from GET /api/v1/sync/{platform}/status.
 */
export interface PlatformSyncStatus {
  platform: string;
  connected: boolean;
  username: string | null;
  lastSyncedAt: string | null;
  syncedPosts: number;
  postingReady: boolean;
  readSyncReady: boolean;
  missingScopes: string[];
  reconnectRequired: boolean;
  syncInProgress: boolean;
  syncStatus: string | null; // "initiated" | "in_progress" | "completed" | "failed"
  syncError: string | null;
  message: string | null;
}

interface PlatformSyncStatusCardProps {
  status: PlatformSyncStatus;
  onSyncNow: (platform: string) => Promise<void>;
  onConnect?: (platform: string) => Promise<void>;
  onDisconnect?: (platform: string) => Promise<void>;
}

function formatLastSynced(isoDate: string | null): string {
  if (!isoDate) return "Never synced";
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

function getPlatformDisplayName(platform: string): string {
  switch (platform) {
    case "linkedin":
      return "LinkedIn";
    case "twitter":
      return "X (Twitter)";
    case "instagram":
      return "Instagram";
    default:
      return platform.charAt(0).toUpperCase() + platform.slice(1);
  }
}

function SyncProgressIndicator({ syncStatus, syncError }: { syncStatus: string | null; syncError: string | null }) {
  if (!syncStatus) return null;

  const steps = ["initiated", "in_progress", "completed"];
  const isFailed = syncStatus === "failed";

  return (
    <div className="mt-3 space-y-2">
      <div className="flex items-center gap-2">
        {syncStatus === "initiated" && (
          <>
            <Clock size={14} className="text-amber-500 animate-pulse" />
            <span className="text-xs text-amber-600">Sync initiated...</span>
          </>
        )}
        {syncStatus === "in_progress" && (
          <>
            <Loader2 size={14} className="text-blue-500 animate-spin" />
            <span className="text-xs text-blue-600">Syncing posts...</span>
          </>
        )}
        {syncStatus === "completed" && (
          <>
            <CheckCircle2 size={14} className="text-emerald-500" />
            <span className="text-xs text-emerald-600">Sync completed</span>
          </>
        )}
        {isFailed && (
          <>
            <XCircle size={14} className="text-destructive" />
            <span className="text-xs text-destructive">Sync failed</span>
          </>
        )}
      </div>

      {/* Progress bar */}
      {!isFailed && (
        <div className="flex gap-1">
          {steps.map((step) => {
            const stepIndex = steps.indexOf(step);
            const currentIndex = steps.indexOf(syncStatus);
            const isActive = stepIndex <= currentIndex;
            return (
              <div
                key={step}
                className="h-1 flex-1 rounded-full transition-colors duration-300"
                style={{
                  background: isActive ? "var(--olive)" : "var(--muted)",
                }}
              />
            );
          })}
        </div>
      )}

      {isFailed && syncError && (
        <p className="text-xs text-destructive/80 mt-1">{syncError}</p>
      )}
    </div>
  );
}

/**
 * Twitter tier selector shown in settings for connected Twitter accounts.
 * Allows users to indicate their subscription tier (free/premium) which
 * affects character limits for content generation.
 */
function TwitterTierSelector({ connected }: { connected: boolean }) {
  const [tierData, setTierData] = useState<TwitterTierResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!connected) return;
    let cancelled = false;
    setLoading(true);
    productService
      .getTwitterTier()
      .then((data) => {
        if (!cancelled) setTierData(data);
      })
      .catch(() => {
        if (!cancelled) setTierData({ tier: "free", max_chars: 280, is_thread_eligible: true });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [connected]);

  const handleTierChange = useCallback(async (newTier: string) => {
    if (newTier !== "free" && newTier !== "premium") return;
    setLoading(true);
    setError(null);
    try {
      const data = await productService.updateTwitterTier(newTier);
      setTierData(data);
    } catch {
      setError("Could not update tier.");
    } finally {
      setLoading(false);
    }
  }, []);

  if (!connected) return null;

  const tier = tierData?.tier ?? "free";
  const maxChars = tierData?.max_chars ?? 280;

  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-border/50 bg-muted/20 px-3 py-2.5">
      <div className="flex flex-col gap-0.5">
        <span className="text-xs font-semibold text-foreground">X Subscription Tier</span>
        <span className="text-[10px] text-muted-foreground">
          Character limit: {maxChars.toLocaleString()} chars
        </span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-36">
          <Select value={tier} onValueChange={(val) => void handleTierChange(val)} disabled={loading}>
            <SelectTrigger className="h-8 text-xs rounded-lg">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="free">Free (280 chars)</SelectItem>
              <SelectItem value="premium">Premium (25K)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {loading && <Loader2 size={12} className="animate-spin text-muted-foreground" />}
        {error && <span className="text-[10px] text-destructive">{error}</span>}
      </div>
    </div>
  );
}

export function PlatformSyncStatusCard({ status, onSyncNow, onConnect, onDisconnect }: PlatformSyncStatusCardProps) {
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSyncNow = useCallback(async () => {
    setIsSyncing(true);
    try {
      await onSyncNow(status.platform);
    } finally {
      setIsSyncing(false);
    }
  }, [onSyncNow, status.platform]);

  const isLinkedInMissingReadScope = status.platform === "linkedin" && status.missingScopes.includes("r_member_social");
  const isSyncBusy = isSyncing || status.syncInProgress;

  return (
    <div className="rounded-xl border border-border bg-card p-5 transition-all duration-200 hover:shadow-sm">
      {/* Header: Platform name + connection status */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-foreground">{getPlatformDisplayName(status.platform)}</h3>
          {status.connected ? (
            <span
              className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold"
              style={{ background: "rgba(150,165,145,0.15)", color: "var(--olive)" }}
            >
              <Wifi size={10} />
              Connected
            </span>
          ) : (
            <span
              className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold"
              style={{ background: "var(--muted)", color: "var(--text-muted)" }}
            >
              <WifiOff size={10} />
              Offline
            </span>
          )}
        </div>
      </div>

      {/* Username + last sync time */}
      {status.connected && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-foreground">
              {status.username ? (status.platform === "twitter" ? `@${status.username}` : status.username) : "Unknown user"}
            </p>
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock size={11} />
              {formatLastSynced(status.lastSyncedAt)}
            </span>
          </div>

          {/* Readiness badges */}
          <div className="flex flex-wrap gap-2">
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
              style={{
                background: status.readSyncReady ? "rgba(150,165,145,0.15)" : "var(--muted)",
                color: status.readSyncReady ? "var(--olive)" : "var(--text-muted)",
              }}
            >
              {status.readSyncReady ? "✓ Sync ready" : "Sync not ready"}
            </span>
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
              style={{
                background: status.postingReady ? "rgba(150,165,145,0.15)" : "rgba(196,168,130,0.18)",
                color: status.postingReady ? "var(--olive)" : "var(--bronze)",
              }}
            >
              {status.postingReady ? "✓ Posting ready" : "Posting not ready"}
            </span>
            {status.syncedPosts > 0 && (
              <span
                className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                style={{ background: "rgba(150,165,145,0.1)", color: "var(--olive)" }}
              >
                {status.syncedPosts} posts imported
              </span>
            )}
          </div>

          {/* Missing scopes warning */}
          {status.missingScopes.length > 0 && (
            <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900/40 dark:bg-amber-950/20 px-3 py-2">
              <AlertTriangle size={14} className="text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-amber-700 dark:text-amber-300">
                <p className="font-medium">Missing scopes: {status.missingScopes.join(", ")}</p>
                {isLinkedInMissingReadScope && (
                  <p className="mt-1 text-amber-600 dark:text-amber-400">
                    LinkedIn read permission (<code className="text-[10px] bg-amber-100 dark:bg-amber-900/30 px-1 rounded">r_member_social</code>) requires separate developer app approval from LinkedIn. Posting still works without it.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Sync progress */}
          <SyncProgressIndicator syncStatus={status.syncStatus} syncError={status.syncError} />

          {/* Posts imported after completion */}
          {status.syncStatus === "completed" && status.syncedPosts > 0 && (
            <div className="flex items-center gap-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/40 px-3 py-2">
              <CheckCircle2 size={14} className="text-emerald-600 dark:text-emerald-400" />
              <span className="text-xs text-emerald-700 dark:text-emerald-300 font-medium">
                {status.syncedPosts} posts imported — ready for analysis
              </span>
            </div>
          )}

          {/* Platform message */}
          {status.message && !isLinkedInMissingReadScope && (
            <p className="text-xs text-muted-foreground">{status.message}</p>
          )}

          {/* Twitter tier selector — shown only for connected Twitter accounts */}
          {status.platform === "twitter" && <TwitterTierSelector connected={status.connected} />}

          {/* Sync Now button */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              type="button"
              onClick={() => void handleSyncNow()}
              disabled={isSyncBusy || !status.connected || !status.readSyncReady}
              className="flex items-center justify-center gap-2 rounded-lg border border-border bg-background px-4 py-2 h-9 text-xs font-medium text-foreground transition-all hover:bg-muted active:scale-[0.97] disabled:opacity-40 shadow-sm"
            >
              {isSyncBusy ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <RefreshCw size={14} />
              )}
              {isSyncBusy ? "Syncing..." : "Sync Now"}
            </button>

            {status.reconnectRequired && onConnect && (
              <button
                type="button"
                onClick={() => void onConnect(status.platform)}
                className="flex items-center justify-center rounded-lg border border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30 px-4 py-2 h-9 text-xs font-medium text-amber-700 dark:text-amber-300 transition-all hover:bg-amber-100 dark:hover:bg-amber-950/50 active:scale-[0.97] shadow-sm"
              >
                Reconnect
              </button>
            )}

            {onDisconnect && (
              <button
                type="button"
                onClick={() => void onDisconnect(status.platform)}
                disabled={!status.connected}
                className="flex items-center justify-center rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 h-9 text-xs font-medium text-destructive transition-all hover:bg-destructive/10 active:scale-[0.97] disabled:opacity-40 shadow-sm"
              >
                Disconnect
              </button>
            )}
          </div>
        </div>
      )}

      {/* Not connected state */}
      {!status.connected && onConnect && (
        <div className="pt-2">
          <button
            type="button"
            onClick={() => void onConnect(status.platform)}
            className="flex items-center justify-center rounded-lg border border-border bg-background px-5 py-2.5 h-10 text-sm font-medium text-foreground transition-all hover:bg-muted active:scale-[0.97] shadow-sm"
          >
            Connect {getPlatformDisplayName(status.platform)}
          </button>
        </div>
      )}
    </div>
  );
}
