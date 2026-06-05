"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { Loader2, AlertTriangle, CheckCircle2, Scissors } from "lucide-react";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { productService, type TwitterTierResponse } from "@/services/product.service";

/**
 * Split content into thread segments at sentence boundaries.
 * Client-side preview — mirrors the backend split_into_thread algorithm.
 */
function splitIntoThread(content: string, maxChars = 280): string[] {
  const trimmed = content.trim();
  if (trimmed.length <= maxChars) return [trimmed];

  const sentences = trimmed.split(/(?<=[.!?])\s+/).filter((s) => s.trim());
  const numberingReserve = 6; // "XX/XX " worst case
  const effectiveMax = maxChars - numberingReserve;

  const segments: string[] = [];
  let current = "";

  for (const sentence of sentences) {
    if (sentence.length > effectiveMax) {
      // Flush current segment
      if (current) {
        segments.push(current.trim());
        current = "";
      }
      // Word-boundary split for long sentences
      const words = sentence.split(/\s+/);
      let wordSegment = "";
      for (const word of words) {
        if (wordSegment.length + word.length + 1 <= effectiveMax) {
          wordSegment = wordSegment ? `${wordSegment} ${word}` : word;
        } else {
          if (wordSegment) segments.push(wordSegment);
          wordSegment = word;
        }
      }
      if (wordSegment) current = wordSegment;
    } else if (current.length + sentence.length + 1 <= effectiveMax) {
      current = current ? `${current} ${sentence}` : sentence;
    } else {
      if (current) segments.push(current.trim());
      current = sentence;
    }
  }
  if (current) segments.push(current.trim());

  // Apply numbering
  if (segments.length > 1) {
    const total = segments.length;
    return segments.map((seg, i) => `${i + 1}/${total} ${seg}`);
  }
  return segments;
}

interface TwitterContentControlsProps {
  /** Current content in the draft editor */
  content: string;
  /** Whether Twitter is the currently selected platform */
  isActive: boolean;
  /** Notifies the parent of the resolved tier-aware character limit (for the editor counter). */
  onLimitChange?: (maxChars: number) => void;
}

/**
 * Twitter-specific controls shown on the Create page when Twitter/X is the active platform.
 * - Tier selector (free/premium)
 * - Real-time character count with progress bar
 * - Thread preview when content exceeds the tier limit
 */
export function TwitterContentControls({ content, isActive, onLimitChange }: TwitterContentControlsProps) {
  const [tierData, setTierData] = useState<TwitterTierResponse | null>(null);
  const [tierLoading, setTierLoading] = useState(false);
  const [tierError, setTierError] = useState<string | null>(null);

  // Fetch tier data when component becomes active
  const loadTier = useCallback(async () => {
    setTierLoading(true);
    setTierError(null);
    try {
      const data = await productService.getTwitterTier();
      setTierData(data);
    } catch {
      // Default to free tier if endpoint not reachable
      setTierData({ tier: "free", max_chars: 280, is_thread_eligible: true });
    } finally {
      setTierLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isActive) {
      void loadTier();
    }
  }, [isActive, loadTier]);

  const handleTierChange = useCallback(async (newTier: string) => {
    if (newTier !== "free" && newTier !== "premium") return;
    setTierLoading(true);
    setTierError(null);
    try {
      const data = await productService.updateTwitterTier(newTier);
      setTierData(data);
    } catch {
      setTierError("Could not update tier. Try again.");
    } finally {
      setTierLoading(false);
    }
  }, []);

  const maxChars = tierData?.max_chars ?? 280;
  const tier = tierData?.tier ?? "free";
  const isThreadEligible = tierData?.is_thread_eligible ?? true;
  const charCount = content.length;
  const isOverLimit = charCount > maxChars;
  const charPercent = Math.min((charCount / maxChars) * 100, 100);

  // Surface the resolved limit to the parent so the editor counter stays in sync (M2).
  useEffect(() => {
    if (isActive && onLimitChange) {
      onLimitChange(maxChars);
    }
  }, [isActive, maxChars, onLimitChange]);

  // Thread preview (only for free tier when over limit)
  const threadSegments = useMemo(() => {
    if (!isOverLimit || !isThreadEligible || !content.trim()) return null;
    return splitIntoThread(content, maxChars);
  }, [content, isOverLimit, isThreadEligible, maxChars]);

  if (!isActive) return null;

  return (
    <div className="flex flex-col gap-4">
      {/* Tier selector */}
      <div className="flex items-center gap-3">
        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground whitespace-nowrap">
          X tier
        </label>
        <div className="w-36">
          <Select value={tier} onValueChange={(val) => void handleTierChange(val)} disabled={tierLoading}>
            <SelectTrigger className="h-8 text-xs rounded-lg">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="free">Free (280 chars)</SelectItem>
              <SelectItem value="premium">Premium (25K)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {tierLoading && <Loader2 size={14} className="animate-spin text-muted-foreground" />}
        {tierError && <span className="text-xs text-destructive">{tierError}</span>}
      </div>

      {/* Character count bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {charCount.toLocaleString()} / {maxChars.toLocaleString()} characters
          </span>
          {charCount > 0 && (
            <span className={`text-xs font-medium ${isOverLimit ? "text-destructive" : charPercent > 90 ? "text-amber-600" : "text-emerald-600"}`}>
              {isOverLimit ? (
                <span className="flex items-center gap-1">
                  <AlertTriangle size={11} />
                  {charCount - maxChars} over
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <CheckCircle2 size={11} />
                  {maxChars - charCount} remaining
                </span>
              )}
            </span>
          )}
        </div>
        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-200"
            style={{
              width: `${Math.min(charPercent, 100)}%`,
              background: isOverLimit
                ? "var(--destructive)"
                : charPercent > 90
                  ? "rgb(217 119 6)" /* amber-600 */
                  : "rgb(5 150 105)", /* emerald-600 */
            }}
          />
        </div>
      </div>

      {/* Thread preview — shown when free tier content exceeds 280 chars */}
      {threadSegments && threadSegments.length > 1 && (
        <div className="rounded-xl border border-border/60 bg-muted/30 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Scissors size={14} className="text-primary" />
            <p className="text-xs font-semibold text-foreground">
              Thread Preview — {threadSegments.length} tweets
            </p>
          </div>
          <p className="text-xs text-muted-foreground">
            Content exceeds 280 chars. It will be auto-split into a thread on publish.
          </p>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {threadSegments.map((segment, index) => (
              <div
                key={index}
                className="rounded-lg border border-border/50 bg-background p-3 text-sm leading-relaxed"
              >
                <p className="whitespace-pre-wrap text-foreground">{segment}</p>
                <p className="mt-1.5 text-[10px] text-muted-foreground text-right">
                  {segment.length}/280
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface BrandProfileProgressProps {
  /** Total posts synced across all platforms */
  syncedPosts: number;
  /** Minimum threshold for brand profile generation */
  threshold?: number;
  /** Whether brand profile already exists */
  hasProfile: boolean;
}

/**
 * Shows progress toward the 5-post threshold for brand profile generation.
 * Displayed when the user hasn't yet met the minimum post requirement.
 */
export function BrandProfileProgress({ syncedPosts, threshold = 5, hasProfile }: BrandProfileProgressProps) {
  if (hasProfile || syncedPosts >= threshold) return null;

  const remaining = threshold - syncedPosts;
  const percent = Math.min((syncedPosts / threshold) * 100, 100);

  return (
    <div className="rounded-lg border border-border/50 bg-muted/20 px-4 py-3 space-y-2">
      <p className="text-xs font-medium text-foreground">
        {syncedPosts}/{threshold} posts synced — {remaining} more needed for brand analysis
      </p>
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{
            width: `${percent}%`,
            background: "var(--primary)",
          }}
        />
      </div>
      <p className="text-[11px] text-muted-foreground">
        Connect and sync your social accounts to unlock AI-powered brand voice analysis.
      </p>
    </div>
  );
}
