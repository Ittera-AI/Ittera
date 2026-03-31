"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  CalendarDays,
  Check,
  ChevronRight,
  ClipboardCopy,
  Edit3,
  Loader2,
  RefreshCw,
  Send,
  Sparkles,
  ThumbsUp,
  Wand2,
} from "lucide-react";

import { useTheme } from "@/context/ThemeContext";

const EASE = [0.16, 1, 0.3, 1] as const;

const WORKSPACES = [
  { id: "sync", label: "Sync", icon: RefreshCw },
  { id: "score", label: "Score", icon: Sparkles },
  { id: "plan", label: "Plan", icon: CalendarDays },
  { id: "repurpose", label: "Repurpose", icon: Wand2 },
  { id: "publish", label: "Publish", icon: Send },
  { id: "learn", label: "Learn", icon: BarChart3 },
] as const;

const CHANNELS = [
  { id: "linkedin", label: "LinkedIn", handle: "@ittera_ai", status: "Synced", volume: "94 posts" },
  { id: "x", label: "X / Twitter", handle: "@ittera_ai", status: "Synced", volume: "187 posts" },
  { id: "instagram", label: "Instagram", handle: "@ittera.ai", status: "Synced", volume: "42 reels" },
  { id: "youtube", label: "YouTube", handle: "Ittera", status: "Ready", volume: "Watch-time pending" },
  { id: "newsletter", label: "Newsletter", handle: "Substack", status: "Ready", volume: "List data pending" },
] as const;

const SCENARIOS = [
  {
    id: "launch",
    label: "Launch week",
    brief: "Build a coordinated launch arc across the whole stack.",
    nextAction: "Queue authority-led launch posts and a waitlist email.",
  },
  {
    id: "authority",
    label: "Authority push",
    brief: "Turn one strong idea into platform-native thought leadership.",
    nextAction: "Score the founder angle, then repurpose into carousel and email.",
  },
  {
    id: "ops",
    label: "Ops sprint",
    brief: "Recover consistency fast after missed publishing days.",
    nextAction: "Fill the calendar gaps and ship the fastest ready assets first.",
  },
] as const;

type WorkspaceId = (typeof WORKSPACES)[number]["id"];
type ChannelId = (typeof CHANNELS)[number]["id"];
type ScenarioId = (typeof SCENARIOS)[number]["id"];

type Tokens = {
  isDark: boolean;
  pageGlow: string;
  panelBg: string;
  panelBorder: string;
  panelShadow: string;
  surface: string;
  softSurface: string;
  accentSurface: string;
  text: string;
  muted: string;
  faint: string;
  accentText: string;
  success: string;
};

function useTokens(): Tokens {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return {
    isDark,
    pageGlow: isDark
      ? "radial-gradient(circle, rgba(196,168,130,0.08) 0%, transparent 70%)"
      : "radial-gradient(circle, rgba(163,138,112,0.08) 0%, transparent 70%)",
    panelBg: isDark ? "#141210" : "#FFFFFF",
    panelBorder: isDark ? "#2E2922" : "#EAE7E2",
    panelShadow: isDark ? "0 32px 90px rgba(0,0,0,0.42)" : "0 32px 90px rgba(15,23,42,0.08)",
    surface: isDark ? "#1B1815" : "#F8F4EE",
    softSurface: isDark ? "rgba(255,255,255,0.045)" : "rgba(15,23,42,0.04)",
    accentSurface: isDark ? "rgba(196,168,130,0.12)" : "rgba(163,138,112,0.1)",
    text: isDark ? "#F2EDE8" : "#171717",
    muted: isDark ? "rgba(242,237,232,0.62)" : "#525252",
    faint: isDark ? "rgba(242,237,232,0.34)" : "#A3A3A3",
    accentText: isDark ? "#E7D3BB" : "#8B6F52",
    success: "#7A8B76",
  };
}

function CopyButton({ text, tokens }: { text: string; tokens: Tokens }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button
      type="button"
      onClick={handleCopy}
      className="flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-medium transition-all duration-150 active:scale-95"
      style={{
        background: copied ? "rgba(122,139,118,0.14)" : tokens.softSurface,
        color: copied ? tokens.success : tokens.faint,
        border: `1px solid ${copied ? "rgba(122,139,118,0.3)" : tokens.panelBorder}`,
      }}
    >
      {copied ? <Check className="h-3 w-3" /> : <ClipboardCopy className="h-3 w-3" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

const SCENARIO_STATS: Record<ScenarioId, { label: string; value: string }[]> = {
  launch: [
    { label: "Accounts connected", value: "5 channels" },
    { label: "Launch assets ready", value: "17 queued" },
    { label: "Best slot today", value: "Thu 8:00 AM" },
  ],
  authority: [
    { label: "Core thesis mapped", value: "1 winner" },
    { label: "AI variations", value: "12 drafted" },
    { label: "Strongest outlet", value: "LinkedIn first" },
  ],
  ops: [
    { label: "Publishing gaps", value: "3 days open" },
    { label: "Fast wins ready", value: "6 assets" },
    { label: "Recovery target", value: "Daily cadence" },
  ],
};

function TopStats({ tokens, scenario }: { tokens: Tokens; scenario: ScenarioId }) {
  const stats = SCENARIO_STATS[scenario];

  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {stats.map((stat, index) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: index * 0.05, ease: EASE }}
          className="rounded-2xl px-4 py-4"
          style={{ background: tokens.softSurface, border: `1px solid ${tokens.panelBorder}` }}
        >
          <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>
            {stat.label}
          </div>
          <div className="mt-2 text-[22px] font-semibold tracking-[-0.03em]" style={{ color: tokens.text }}>
            {stat.value}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function WorkspaceIntro({ active, tokens }: { active: WorkspaceId; tokens: Tokens }) {
  const copy = {
    sync: ["Start here", "Connect the channels that already hold your signal.", "Ittera pulls post history, platform performance, and publishing cadence into one system before it suggests anything."],
    score: ["Then sharpen the message", "Score drafts before you spend a week publishing them.", "Ittera grades hook strength, clarity, and conversion angle, then rewrites the weak part instead of just telling you the score."],
    plan: ["Map the week", "Build a real content plan, not a pile of ideas.", "Click days, stage posts, and use AI timing guidance to turn scattered thoughts into a schedule your team can actually execute."],
    repurpose: ["Multiply what works", "One core idea becomes platform-native assets.", "Take a strong post and immediately spin out a carousel angle, an email hook, and a short-form script without losing the original thesis."],
    publish: ["Ship everywhere", "Queue, approve, and publish from one command center.", "The workflow stays visible across LinkedIn, X, Instagram, YouTube, and newsletter so the team knows what is live and what still needs review."],
    learn: ["Close the loop", "See what actually moved growth this week.", "Hover the data, compare channels, and spot momentum fast so the next plan is grounded in performance, not intuition."],
  }[active];

  return (
    <div
      className="rounded-[28px] p-6 lg:p-7"
      style={{
        background: tokens.isDark
          ? "linear-gradient(180deg, rgba(196,168,130,0.08), rgba(20,18,16,0.96))"
          : "linear-gradient(180deg, rgba(163,138,112,0.08), rgba(255,255,255,0.98))",
        border: `1px solid ${tokens.panelBorder}`,
      }}
    >
      <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.accentText }}>
        {copy[0]}
      </div>
      <h3 className="mt-3 text-[28px] font-semibold leading-[1.05] tracking-[-0.035em]" style={{ color: tokens.text }}>
        {copy[1]}
      </h3>
      <p className="mt-4 text-[14px] leading-7" style={{ color: tokens.muted }}>
        {copy[2]}
      </p>
      <a
        href="/#waitlist"
        className="mt-6 inline-flex items-center gap-2 rounded-full px-4 py-2 text-[12px] font-semibold transition-all duration-200 hover:-translate-y-0.5 hover:opacity-90 active:scale-95"
        style={{ background: tokens.text, color: tokens.panelBg }}
      >
        Join the private beta
        <ArrowRight className="h-3.5 w-3.5" />
      </a>
    </div>
  );
}

function WorkspaceRail({ active, setActive, tokens }: { active: WorkspaceId; setActive: (id: WorkspaceId) => void; tokens: Tokens }) {
  return (
    <div className="space-y-2">
      {WORKSPACES.map((workspace) => {
        const Icon = workspace.icon;
        const isActive = workspace.id === active;
        return (
          <button
            key={workspace.id}
            type="button"
            onClick={() => setActive(workspace.id)}
            className="flex w-full items-center justify-between rounded-2xl px-4 py-3 text-left transition-all duration-150 ease-out active:scale-[0.97]"
            style={{
              background: isActive ? tokens.accentSurface : "transparent",
              color: isActive ? tokens.text : tokens.muted,
              border: `1px solid ${isActive ? "rgba(163,138,112,0.22)" : "transparent"}`,
            }}
          >
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl" style={{ background: isActive ? tokens.panelBg : tokens.softSurface }}>
                <Icon className="h-4 w-4" />
              </div>
              <span className="text-[13px] font-medium">{workspace.label}</span>
            </div>
            <ChevronRight className="h-4 w-4 opacity-60" />
          </button>
        );
      })}
    </div>
  );
}

function ScenarioStrip({
  active,
  setActive,
  tokens,
}: {
  active: ScenarioId;
  setActive: (id: ScenarioId) => void;
  tokens: Tokens;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      {SCENARIOS.map((scenario) => {
        const isActive = scenario.id === active;
        // Light mode: use warm accent surface with accent text (not black-on-black)
        // Dark mode: invert to near-white bg with dark text
        const activeBg = tokens.isDark
          ? "linear-gradient(135deg, rgba(196,168,130,0.22) 0%, rgba(163,138,112,0.18) 100%)"
          : "linear-gradient(135deg, rgba(163,138,112,0.16) 0%, rgba(196,168,130,0.12) 100%)";
        const activeBorder = tokens.isDark ? "rgba(196,168,130,0.36)" : "rgba(163,138,112,0.4)";
        const activeLabelColor = tokens.isDark ? "#E7D3BB" : "#6B4F35";
        const activeBriefColor = tokens.isDark ? "rgba(231,211,187,0.62)" : "rgba(107,79,53,0.7)";
        return (
          <button
            key={scenario.id}
            type="button"
            onClick={() => setActive(scenario.id)}
            className="rounded-2xl px-4 py-3 text-left text-[11px] font-medium transition-all duration-200 ease-out active:scale-[0.97] hover:scale-[1.01]"
            style={{
              background: isActive ? activeBg : tokens.panelBg,
              border: `1px solid ${isActive ? activeBorder : tokens.panelBorder}`,
              boxShadow: isActive ? (tokens.isDark ? "0 0 0 1px rgba(196,168,130,0.18) inset" : "0 0 0 1px rgba(163,138,112,0.1) inset") : "none",
            }}
          >
            <div className="flex items-center gap-2">
              {isActive && (
                <span
                  className="h-1.5 w-1.5 rounded-full animate-pulse"
                  style={{ background: tokens.isDark ? "#C4A882" : "#A38A70" }}
                />
              )}
              <span style={{ color: isActive ? activeLabelColor : tokens.muted, fontWeight: isActive ? 600 : 500 }}>
                {scenario.label}
              </span>
            </div>
            <div className="mt-1.5 text-[10px] leading-[1.6]" style={{ color: isActive ? activeBriefColor : tokens.faint }}>
              {scenario.brief}
            </div>
          </button>
        );
      })}
    </div>
  );
}

function ChannelStrip({
  active,
  setActive,
  tokens,
}: {
  active: ChannelId;
  setActive: (id: ChannelId) => void;
  tokens: Tokens;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
      {CHANNELS.map((channel) => {
        const isActive = channel.id === active;
        const isSynced = channel.status === "Synced";
        return (
          <button
            key={channel.id}
            type="button"
            onClick={() => setActive(channel.id)}
            className="h-full rounded-2xl px-3 py-3 text-left transition-all duration-150 ease-out active:scale-[0.97]"
            style={{
              background: isActive ? tokens.accentSurface : tokens.panelBg,
              border: `1px solid ${isActive ? "rgba(163,138,112,0.28)" : tokens.panelBorder}`,
            }}
          >
            <div className="flex items-center gap-2 text-[11px]">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: isSynced ? tokens.success : tokens.accentText }} />
              <span style={{ color: isActive ? tokens.text : tokens.muted }}>{channel.label}</span>
              <span style={{ color: tokens.faint }}>{channel.status}</span>
            </div>
            <div className="mt-1 text-[10px]" style={{ color: tokens.faint }}>
              {channel.handle} · {channel.volume}
            </div>
          </button>
        );
      })}
    </div>
  );
}

function ControlDeck({
  activeWorkspace,
  activeScenario,
  activeChannel,
  tokens,
}: {
  activeWorkspace: WorkspaceId;
  activeScenario: ScenarioId;
  activeChannel: ChannelId;
  tokens: Tokens;
}) {
  const scenario = SCENARIOS.find((item) => item.id === activeScenario)!;
  const channel = CHANNELS.find((item) => item.id === activeChannel)!;
  const workspace = WORKSPACES.find((item) => item.id === activeWorkspace)!;

  return (
    <div className="grid gap-3 xl:grid-cols-[1.12fr_0.88fr]">
      <div className="rounded-[22px] p-4" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>
              Live scenario
            </div>
            <div className="mt-2 text-[20px] font-semibold tracking-[-0.03em]" style={{ color: tokens.text }}>
              {scenario.label}
            </div>
          </div>
          <div className="rounded-full px-3 py-1.5 text-[11px] font-medium" style={{ background: tokens.accentSurface, color: tokens.accentText }}>
            Focus: {workspace.label}
          </div>
        </div>
        <p className="mt-3 text-[13px] leading-6" style={{ color: tokens.muted }}>
          {scenario.brief}
        </p>
      </div>
      <div className="rounded-[22px] p-4" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>
              Next best action
            </div>
            <div className="mt-2 text-[14px] font-medium leading-6" style={{ color: tokens.text }}>
              {scenario.nextAction}
            </div>
          </div>
          <div className="rounded-2xl px-3 py-2 text-right" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
            <div className="text-[10px]" style={{ color: tokens.faint }}>
              Working set
            </div>
            <div className="mt-1 text-[12px] font-medium" style={{ color: tokens.text }}>
              {channel.label}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SyncPanel({ tokens, channel }: { tokens: Tokens; channel: ChannelId }) {
  const [syncing, setSyncing] = useState(false);
  const [syncDone, setSyncDone] = useState(false);

  const handleRefresh = () => {
    if (syncing) return;
    setSyncing(true);
    setSyncDone(false);
    window.setTimeout(() => {
      setSyncing(false);
      setSyncDone(true);
      window.setTimeout(() => setSyncDone(false), 2200);
    }, 1800);
  };

  const syncRows: Record<ChannelId, { label: string; progress: number; note: string }[]> = {
    linkedin: [
      { label: "LinkedIn post history", progress: 100, note: "Imported 94 posts and 18 top performers" },
      { label: "Comment momentum", progress: 91, note: "Reply patterns grouped by authority angle" },
      { label: "Profile conversion path", progress: 74, note: "CTA clicks now mapped to signup pages" },
    ],
    x: [
      { label: "Threads and replies", progress: 82, note: "Engagement patterns mapped by topic cluster" },
      { label: "Posting cadence", progress: 87, note: "Timing windows compared across weekdays" },
      { label: "Hook archive", progress: 69, note: "High-impression openers marked for reuse" },
    ],
    instagram: [
      { label: "Reels library", progress: 66, note: "Short-form watch-time now syncing" },
      { label: "Carousel saves", progress: 79, note: "High-save educational posts isolated" },
      { label: "Story tap-through", progress: 58, note: "Funnel exits need more capture data" },
    ],
    youtube: [
      { label: "Video metadata", progress: 54, note: "Titles, thumbnails, and upload windows mapped" },
      { label: "Watch-time import", progress: 32, note: "Audience-retention data still connecting" },
      { label: "Clip candidates", progress: 61, note: "Strong long-form moments marked for shorts" },
    ],
    newsletter: [
      { label: "Send history", progress: 72, note: "Recent editions and subject lines imported" },
      { label: "CTR patterns", progress: 48, note: "List performance needs provider sync" },
      { label: "Archive themes", progress: 84, note: "Recurring ideas grouped by conversion lift" },
    ],
  };

  const insights: Record<ChannelId, { label: string; value: string }[]> = {
    linkedin: [
      { label: "Peak audience hour", value: "Thu 8:00 AM" },
      { label: "Best performing angle", value: "Operational insight" },
      { label: "Content gap", value: "No founder story in 9 days" },
      { label: "Suggested next move", value: "Turn last launch lesson into carousel" },
    ],
    x: [
      { label: "Peak audience hour", value: "Tue 10:30 AM" },
      { label: "Best performing angle", value: "Contrarian thread" },
      { label: "Content gap", value: "No high-signal reply chain this week" },
      { label: "Suggested next move", value: "Break the core thesis into 5 short punches" },
    ],
    instagram: [
      { label: "Peak audience hour", value: "Sat 6:00 PM" },
      { label: "Best performing angle", value: "Tactical carousel" },
      { label: "Content gap", value: "No save-first educational post in 6 days" },
      { label: "Suggested next move", value: "Repurpose the winner into a 6-slide reel outline" },
    ],
    youtube: [
      { label: "Peak audience hour", value: "Sun 11:00 AM" },
      { label: "Best performing angle", value: "Build-in-public breakdown" },
      { label: "Content gap", value: "No follow-up short after the last long-form upload" },
      { label: "Suggested next move", value: "Cut one lesson into a 45-second short" },
    ],
    newsletter: [
      { label: "Peak audience hour", value: "Fri 7:30 AM" },
      { label: "Best performing angle", value: "System teardown" },
      { label: "Content gap", value: "No recap email tied to social wins" },
      { label: "Suggested next move", value: "Bundle the week into one authority email" },
    ],
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
      <div className="rounded-[24px] p-5" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Historical import</div>
            <div className="mt-2 text-[24px] font-semibold tracking-[-0.03em]" style={{ color: tokens.text }}>323 assets unified</div>
          </div>
          <button
            type="button"
            onClick={handleRefresh}
            disabled={syncing}
            className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-medium transition-all duration-150 ease-out active:scale-[0.97] disabled:opacity-70"
            style={{ background: syncDone ? "rgba(122,139,118,0.14)" : tokens.panelBg, border: `1px solid ${syncDone ? "rgba(122,139,118,0.4)" : tokens.panelBorder}`, color: syncDone ? tokens.success : tokens.muted }}
          >
            {syncing ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : syncDone ? (
              <Check className="h-3 w-3" />
            ) : (
              <RefreshCw className="h-3 w-3" />
            )}
            {syncing ? "Syncing..." : syncDone ? "Up to date" : "Refresh sources"}
          </button>
        </div>
        <div className="mt-5 space-y-3">
          {syncRows[channel].map((row) => (
            <div key={row.label}>
              <div className="mb-1.5 flex items-center justify-between text-[12px]">
                <span style={{ color: tokens.text }}>{row.label}</span>
                <span style={{ color: tokens.muted }}>{row.progress}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full" style={{ background: tokens.softSurface }}>
                <motion.div className="h-full rounded-full origin-left w-full" style={{ background: "linear-gradient(90deg, #A38A70, #7A8B76)" }} initial={{ scaleX: 0 }} animate={{ scaleX: row.progress / 100 }} transition={{ duration: 0.55, ease: EASE }} />
              </div>
              <div className="mt-2 text-[11px]" style={{ color: tokens.faint }}>{row.note}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="rounded-[24px] p-5" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Ittera sees</div>
        <div className="mt-4 grid gap-3">
          {insights[channel].map((item, i) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, delay: i * 0.06 }}
              className="rounded-2xl px-4 py-3"
              style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}
            >
              <div className="text-[11px]" style={{ color: tokens.faint }}>{item.label}</div>
              <div className="mt-1 text-[13px] font-medium" style={{ color: tokens.text }}>{item.value}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ScorePanel({
  tokens,
  channel,
  scenario,
}: {
  tokens: Tokens;
  channel: ChannelId;
  scenario: ScenarioId;
}) {
  const defaultPlatform = {
    linkedin: "LinkedIn",
    x: "X / Twitter",
    instagram: "Instagram",
    youtube: "YouTube",
    newsletter: "Newsletter",
  }[channel];
  const defaultDraft = {
    launch: "Most launches fail before distribution even begins. The problem is not the product. It is the broken content system around it.",
    authority: "Most creators do not need more ideas. They need a system that turns ideas into consistent output.",
    ops: "When consistency drops, the answer is not motivation. It is a workflow that makes publishing easier than procrastinating.",
  }[scenario];

  const [platform, setPlatform] = useState(defaultPlatform);
  const [content, setContent] = useState(defaultDraft);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<null | { score: number; verdict: string; rewrite: string; metrics: { label: string; value: number }[] }>(null);

  useEffect(() => {
    setPlatform(defaultPlatform);
  }, [defaultPlatform]);

  useEffect(() => {
    setContent(defaultDraft);
    setResult(null);
  }, [defaultDraft]);

  const runAnalysis = () => {
    if (!content.trim()) return;
    setLoading(true);
    setResult(null);
    window.setTimeout(() => {
      const platformBoost = platform === "LinkedIn" ? 3 : platform === "X / Twitter" ? 1 : 0;
      const scenarioBoost = scenario === "authority" ? 2 : scenario === "launch" ? 1 : 0;
      const score = 84 + platformBoost + scenarioBoost;
      setResult({
        score,
        verdict:
          scenario === "launch"
            ? "Clear promise, but the first line should create urgency faster for launch-week attention."
            : scenario === "ops"
              ? "Strong operational angle, but it needs a more concrete payoff in the first two lines."
              : "High authority, but the first line needs to stop the scroll faster.",
        rewrite:
          scenario === "launch"
            ? "Open with: 'Launches do not stall because the product is weak. They stall because the content engine breaks.' Then move into one proof point."
            : scenario === "ops"
              ? "Open with: 'Consistency is rarely a discipline problem. It is usually an operating-system problem.' Then show the workflow fix."
              : "Open with: 'The biggest creator bottleneck is not ideas. It is operating without a system.' Then support it with one concrete proof point.",
        metrics: [
          { label: "Hook strength", value: 79 + platformBoost + scenarioBoost },
          { label: "Clarity", value: 90 + scenarioBoost },
          { label: "Comment potential", value: 84 + platformBoost },
        ],
      });
      setLoading(false);
    }, 900);
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[1.02fr_0.98fr]">
      <div className="rounded-[24px] p-5" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="flex flex-wrap gap-2">
          {CHANNELS.map((item) => item.label).map((item) => {
            const active = item === platform;
            return (
              <button key={item} type="button" onClick={() => setPlatform(item)} className="rounded-full px-3 py-1.5 text-[12px] font-medium transition-all duration-150 ease-out active:scale-[0.97]" style={{ background: active ? tokens.accentSurface : "transparent", color: active ? tokens.text : tokens.muted, border: `1px solid ${active ? "rgba(163,138,112,0.24)" : tokens.panelBorder}` }}>
                {item}
              </button>
            );
          })}
        </div>
        <textarea value={content} onChange={(event) => setContent(event.target.value)} placeholder={`Paste your ${platform} draft`} className="mt-4 h-56 w-full resize-none rounded-[22px] p-4 text-[13px] leading-6 outline-none" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}`, color: tokens.text }} />
        <div className="mt-3 flex items-center justify-between">
          <span className="text-[11px]" style={{ color: tokens.faint }}>{content.length} characters</span>
          <button type="button" onClick={runAnalysis} disabled={loading || !content.trim()} className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-[12px] font-semibold transition-transform duration-150 ease-out active:scale-[0.97] disabled:opacity-40" style={{ background: tokens.text, color: tokens.panelBg }}>
            {loading ? "Analyzing..." : "Analyze draft"}
            {!loading && <ArrowRight className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>
      <div className="rounded-[24px] p-5" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>AI score</div>
            <div className="mt-2 text-[28px] font-semibold tracking-[-0.03em]" style={{ color: tokens.text }}>{result ? `${result.score}/100` : "--/100"}</div>
          </div>
          <div className="rounded-full px-3 py-1 text-[11px] font-medium" style={{ background: tokens.accentSurface, color: tokens.accentText }}>{result ? "Ready to refine" : "Waiting for draft"}</div>
        </div>
        <div className="mt-5 space-y-3">
          {(result?.metrics ?? [
            { label: "Hook strength", value: 0 },
            { label: "Clarity", value: 0 },
            { label: "Comment potential", value: 0 },
          ]).map((metric) => (
            <div key={metric.label}>
              <div className="mb-1.5 flex items-center justify-between text-[12px]">
                <span style={{ color: tokens.muted }}>{metric.label}</span>
                <span style={{ color: tokens.text }}>{metric.value || "--"}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full" style={{ background: tokens.softSurface }}>
                <motion.div className="h-full rounded-full origin-left w-full" style={{ background: "linear-gradient(90deg, #A38A70, #7A8B76)" }} initial={{ scaleX: 0 }} animate={{ scaleX: metric.value / 100 }} transition={{ duration: 0.55, ease: EASE }} />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-5 rounded-[20px] p-4" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
          <div className="flex items-center justify-between">
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Rewrite suggestion</div>
            {result && (
              <CopyButton text={result.rewrite} tokens={tokens} />
            )}
          </div>
          <p className="mt-3 text-[13px] leading-6" style={{ color: tokens.text }}>{result ? result.verdict : "Run a score to see what the draft gets right and where it is likely to lose attention."}</p>
          <p className="mt-3 text-[13px] leading-6" style={{ color: tokens.muted }}>{result ? result.rewrite : "Ittera will suggest a stronger first line, a clearer structure, and a better CTA based on platform fit."}</p>
        </div>
      </div>
    </div>
  );
}

function PlanPanel({ tokens, scenario }: { tokens: Tokens; scenario: ScenarioId }) {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const [events, setEvents] = useState([
    { day: 0, title: "Founder story" },
    { day: 1, title: "Twitter thread" },
    { day: 3, title: "Newsletter recap" },
    { day: 5, title: "Carousel draft" },
  ]);
  const [editingDay, setEditingDay] = useState<number | null>(null);
  const [newTitle, setNewTitle] = useState("");

  const saveEvent = (day: number) => {
    if (!newTitle.trim()) {
      setEditingDay(null);
      setNewTitle("");
      return;
    }
    setEvents((current) => [...current, { day, title: newTitle.trim() }]);
    setEditingDay(null);
    setNewTitle("");
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[1.16fr_0.84fr]">
      <div className="rounded-[24px] p-5" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Weekly planner</div>
            <div className="mt-2 text-[24px] font-semibold tracking-[-0.03em]" style={{ color: tokens.text }}>March 2026</div>
          </div>
          <div className="rounded-full px-3 py-1 text-[11px] font-medium" style={{ background: tokens.accentSurface, color: tokens.accentText }}>{events.length} posts staged</div>
        </div>
        <div className="grid grid-cols-7 gap-2">
          {days.map((day) => (
            <div key={day} className="pb-1 text-center text-[10px] font-medium" style={{ color: tokens.faint }}>{day}</div>
          ))}
          {Array.from({ length: 7 }).map((_, dayIndex) => {
            const dayEvents = events.filter((event) => event.day === dayIndex);
            const editing = editingDay === dayIndex;
            return (
              <div key={dayIndex} className="min-h-[128px] rounded-[18px] p-2" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
                <div className="mb-2 text-[11px]" style={{ color: tokens.faint }}>{dayIndex + 10}</div>
                <div className="space-y-2">
                  {dayEvents.map((event, index) => (
                    <motion.div key={`${event.title}-${index}`} initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} className="rounded-xl px-2 py-1.5 text-[10px] font-medium" style={{ background: tokens.accentSurface, color: tokens.accentText }}>
                      {event.title}
                    </motion.div>
                  ))}
                  {editing ? (
                    <div className="space-y-2">
                      <input
                        autoFocus
                        value={newTitle}
                        onChange={(event) => setNewTitle(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") saveEvent(dayIndex);
                          if (event.key === "Escape") {
                            setEditingDay(null);
                            setNewTitle("");
                          }
                        }}
                        className="w-full rounded-xl px-2 py-2 text-[10px] outline-none"
                        placeholder="Add post title"
                        style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}`, color: tokens.text }}
                      />
                      <div className="flex gap-2">
                        <button type="button" onClick={() => saveEvent(dayIndex)} className="flex-1 rounded-full px-2 py-1.5 text-[10px] font-semibold" style={{ background: tokens.text, color: tokens.panelBg }}>Save</button>
                        <button type="button" onClick={() => { setEditingDay(null); setNewTitle(""); }} className="flex-1 rounded-full px-2 py-1.5 text-[10px] font-medium" style={{ background: tokens.softSurface, color: tokens.muted }}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <button type="button" onClick={() => { setEditingDay(dayIndex); setNewTitle(""); }} className="w-full rounded-xl border border-dashed px-2 py-2 text-[10px]" style={{ borderColor: tokens.panelBorder, color: tokens.faint }}>
                      + Add post
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <div className="space-y-4">
        <div className="rounded-[24px] p-5" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
          <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Best slot</div>
          <div className="mt-3 text-[22px] font-semibold tracking-[-0.03em]" style={{ color: tokens.text }}>
            {scenario === "launch" ? "Thursday, 8:00 AM" : scenario === "authority" ? "Tuesday, 9:30 AM" : "Tomorrow, 7:45 AM"}
          </div>
          <p className="mt-3 text-[12px] leading-6" style={{ color: tokens.muted }}>
            {scenario === "launch"
              ? "This window historically outperforms your average launch-week reach by 2.8x."
              : scenario === "authority"
                ? "This slot gives your thought-leadership posts the strongest early engagement spike."
                : "This slot is the fastest way to repair cadence without overloading the team."}
          </p>
        </div>
        <div className="rounded-[24px] p-5" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
          <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Queue balance</div>
          <div className="mt-4 space-y-3">
            {(
              scenario === "launch"
                ? [
                    { label: "Launch proof", value: "3 posts" },
                    { label: "Behind-the-scenes", value: "2 posts" },
                    { label: "Waitlist CTA", value: "2 posts" },
                  ]
                : scenario === "authority"
                  ? [
                      { label: "Educational", value: "3 posts" },
                      { label: "Opinion", value: "2 posts" },
                      { label: "Personal story", value: "2 posts" },
                    ]
                  : [
                      { label: "Fast wins", value: "2 posts" },
                      { label: "Repurposed", value: "3 posts" },
                      { label: "Recovery cadence", value: "2 posts" },
                    ]
            ).map((item) => (
              <div key={item.label} className="flex items-center justify-between text-[12px]">
                <span style={{ color: tokens.muted }}>{item.label}</span>
                <span style={{ color: tokens.text }}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function RepurposePanel({ tokens, scenario }: { tokens: Tokens; scenario: ScenarioId }) {
  const assets =
    scenario === "launch"
      ? [
          { label: "Launch post", status: "Ready", preview: "A clearer launch promise with urgency-led CTA." },
          { label: "Instagram carousel", status: "Ready", preview: "Six-slide rollout sequence with feature proof." },
          { label: "Newsletter announcement", status: "Drafted", preview: "Opening note plus early-access hook." },
          { label: "Short-form teaser", status: "Ready", preview: "30-second launch script with visual beats." },
        ]
      : scenario === "ops"
        ? [
            { label: "LinkedIn post", status: "Ready", preview: "A tighter ops-led version with a simpler CTA." },
            { label: "Instagram carousel", status: "Ready", preview: "Five-slide workflow breakdown with one fix per card." },
            { label: "Newsletter hook", status: "Drafted", preview: "Lead paragraph plus recovery playbook angle." },
            { label: "Short-form video script", status: "Ready", preview: "45-second script with process-overlay cues." },
          ]
        : [
            { label: "LinkedIn post", status: "Ready", preview: "A tighter authority-led version with a clearer CTA." },
            { label: "Instagram carousel", status: "Ready", preview: "Six-slide outline with one insight per card." },
            { label: "Newsletter hook", status: "Drafted", preview: "Lead paragraph plus subject-line angle." },
            { label: "Short-form video script", status: "Ready", preview: "45-second script with text-overlay cues." },
          ];

  return (
    <div className="grid gap-4 xl:grid-cols-[0.96fr_1.04fr]">
      <div className="rounded-[24px] p-5" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Source asset</div>
        <div className="mt-3 rounded-[20px] p-4" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
          <div className="text-[12px] font-medium" style={{ color: tokens.text }}>Founder operating-system post</div>
          <p className="mt-3 text-[13px] leading-6" style={{ color: tokens.muted }}>&ldquo;Most creators do not need more ideas. They need a system that turns ideas into consistent output.&rdquo;</p>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {[
            { label: "Repurpose score", value: "9.1 / 10" },
            { label: "Assets generated", value: "4 outputs" },
          ].map((item) => (
            <div key={item.label} className="rounded-[18px] p-4" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
              <div className="text-[11px]" style={{ color: tokens.faint }}>{item.label}</div>
              <div className="mt-2 text-[20px] font-semibold tracking-[-0.03em]" style={{ color: tokens.text }}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="rounded-[24px] p-5" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Generated outputs</div>
        <div className="mt-4 space-y-3">
          {assets.map((asset) => (
            <div key={asset.label} className="rounded-[20px] p-4" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
              <div className="flex items-center justify-between gap-3">
                <div className="text-[13px] font-medium" style={{ color: tokens.text }}>{asset.label}</div>
                <div className="rounded-full px-2.5 py-1 text-[10px] font-medium" style={{ background: asset.status === "Ready" ? "rgba(122,139,118,0.14)" : tokens.softSurface, color: asset.status === "Ready" ? tokens.success : tokens.muted }}>{asset.status}</div>
              </div>
              <p className="mt-2 text-[12px] leading-6" style={{ color: tokens.muted }}>{asset.preview}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PublishPanel({ tokens, scenario }: { tokens: Tokens; scenario: ScenarioId }) {
  const initialQueue =
    scenario === "launch"
      ? [
          { label: "LinkedIn launch post", when: "Today, 8:00 AM", status: "Scheduled" },
          { label: "X launch thread", when: "Today, 9:30 AM", status: "Scheduled" },
          { label: "Instagram launch carousel", when: "Tomorrow, 6:00 PM", status: "In review" },
          { label: "Waitlist email", when: "Friday, 7:30 AM", status: "Queued" },
        ]
      : [
          { label: "LinkedIn founder post", when: "Today, 8:00 AM", status: "Scheduled" },
          { label: "X thread variant", when: "Today, 9:30 AM", status: "Scheduled" },
          { label: "Instagram carousel", when: "Tomorrow, 6:00 PM", status: "In review" },
          { label: "Newsletter recap", when: "Friday, 7:30 AM", status: "Queued" },
        ];

  const [queue, setQueue] = useState(initialQueue);

  // Reset queue when scenario changes
  useEffect(() => {
    setQueue(scenario === "launch"
      ? [
          { label: "LinkedIn launch post", when: "Today, 8:00 AM", status: "Scheduled" },
          { label: "X launch thread", when: "Today, 9:30 AM", status: "Scheduled" },
          { label: "Instagram launch carousel", when: "Tomorrow, 6:00 PM", status: "In review" },
          { label: "Waitlist email", when: "Friday, 7:30 AM", status: "Queued" },
        ]
      : [
          { label: "LinkedIn founder post", when: "Today, 8:00 AM", status: "Scheduled" },
          { label: "X thread variant", when: "Today, 9:30 AM", status: "Scheduled" },
          { label: "Instagram carousel", when: "Tomorrow, 6:00 PM", status: "In review" },
          { label: "Newsletter recap", when: "Friday, 7:30 AM", status: "Queued" },
        ]);
  }, [scenario]);

  const approve = (label: string) => {
    setQueue((q) => q.map((item) => item.label === label ? { ...item, status: "Scheduled" } : item));
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[1.02fr_0.98fr]">
      <div className="rounded-[24px] p-5" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Publishing queue</div>
        <div className="mt-4 space-y-3">
          {queue.map((item) => (
            <div key={item.label} className="rounded-[20px] p-4" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
              <div className="flex items-center justify-between gap-3">
                <div className="text-[13px] font-medium" style={{ color: tokens.text }}>{item.label}</div>
                <div className="rounded-full px-2.5 py-1 text-[10px] font-medium" style={{ background: item.status === "Scheduled" ? "rgba(122,139,118,0.14)" : tokens.softSurface, color: item.status === "Scheduled" ? tokens.success : tokens.muted }}>{item.status}</div>
              </div>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-[11px]" style={{ color: tokens.faint }}>{item.when}</span>
                {item.status !== "Scheduled" && (
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => approve(item.label)}
                      className="flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-semibold transition-all duration-150 active:scale-95"
                      style={{ background: "rgba(122,139,118,0.14)", color: tokens.success, border: "1px solid rgba(122,139,118,0.28)" }}
                    >
                      <ThumbsUp className="h-2.5 w-2.5" />
                      Approve
                    </button>
                    <button
                      type="button"
                      className="flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-medium transition-all duration-150 active:scale-95"
                      style={{ background: tokens.softSurface, color: tokens.muted, border: `1px solid ${tokens.panelBorder}` }}
                    >
                      <Edit3 className="h-2.5 w-2.5" />
                      Edit
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="space-y-4">
        <div className="rounded-[24px] p-5" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
          <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Coverage</div>
          <div className="mt-4 space-y-3">
            {[
              { label: "LinkedIn", value: "Ready" },
              { label: "X / Twitter", value: "Ready" },
              { label: "Instagram", value: "Needs asset review" },
              { label: "YouTube", value: "Awaiting sync" },
              { label: "Newsletter", value: "Ready" },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between text-[12px]">
                <span style={{ color: tokens.muted }}>{item.label}</span>
                <span style={{ color: tokens.text }}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-[24px] p-5" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
          <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Command center summary</div>
          <p className="mt-3 text-[13px] leading-6" style={{ color: tokens.muted }}>The team can see what is approved, what still needs assets, and what is already scheduled across every channel.</p>
        </div>
      </div>
    </div>
  );
}

function LearnPanel({ tokens, channel }: { tokens: Tokens; channel: ChannelId }) {
  const bars = {
    linkedin: [
      { day: "Mon", value: 34 },
      { day: "Tue", value: 46 },
      { day: "Wed", value: 39 },
      { day: "Thu", value: 74 },
      { day: "Fri", value: 59 },
      { day: "Sat", value: 88 },
      { day: "Sun", value: 63 },
    ],
    x: [
      { day: "Mon", value: 28 },
      { day: "Tue", value: 61 },
      { day: "Wed", value: 54 },
      { day: "Thu", value: 44 },
      { day: "Fri", value: 69 },
      { day: "Sat", value: 57 },
      { day: "Sun", value: 52 },
    ],
    instagram: [
      { day: "Mon", value: 41 },
      { day: "Tue", value: 36 },
      { day: "Wed", value: 48 },
      { day: "Thu", value: 63 },
      { day: "Fri", value: 71 },
      { day: "Sat", value: 92 },
      { day: "Sun", value: 77 },
    ],
    youtube: [
      { day: "Mon", value: 22 },
      { day: "Tue", value: 31 },
      { day: "Wed", value: 27 },
      { day: "Thu", value: 58 },
      { day: "Fri", value: 64 },
      { day: "Sat", value: 73 },
      { day: "Sun", value: 80 },
    ],
    newsletter: [
      { day: "Mon", value: 49 },
      { day: "Tue", value: 26 },
      { day: "Wed", value: 22 },
      { day: "Thu", value: 57 },
      { day: "Fri", value: 83 },
      { day: "Sat", value: 33 },
      { day: "Sun", value: 29 },
    ],
  }[channel];
  const [hovered, setHovered] = useState<number | null>(5);

  return (
    <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
      <div className="space-y-4">
        {[
          { label: "Total reach", value: "142K", delta: "+23%" },
          { label: "Average engagement", value: "8.4%", delta: "+3.1 pts" },
          { label: "Fastest growing channel", value: "Instagram", delta: "+65%" },
        ].map((item) => (
          <div key={item.label} className="rounded-[24px] p-5" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}` }}>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>{item.label}</div>
            <div className="mt-3 flex items-end justify-between gap-3">
              <div className="text-[24px] font-semibold tracking-[-0.03em]" style={{ color: tokens.text }}>{item.value}</div>
              <div className="text-[12px] font-medium" style={{ color: tokens.success }}>{item.delta}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-[24px] p-5" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}` }}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>Weekly momentum</div>
            <div className="mt-2 text-[24px] font-semibold tracking-[-0.03em]" style={{ color: tokens.text }}>Hover the week</div>
          </div>
          <div className="rounded-full px-3 py-1 text-[11px] font-medium" style={{ background: tokens.accentSurface, color: tokens.accentText }}>Saturday peaked</div>
        </div>
        <div className="mt-8 flex h-64 items-end gap-3">
          {bars.map((bar, index) => {
            const active = hovered === index;
            return (
              <div key={bar.day} className="relative flex flex-1 items-end" onMouseEnter={() => setHovered(index)} onMouseLeave={() => setHovered(5)}>
                <AnimatePresence>
                  {active && (
                    <motion.div initial={{ opacity: 0, y: -6, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -6, scale: 0.96 }} className="absolute left-1/2 top-0 -translate-x-1/2 rounded-xl px-3 py-2 text-[11px] origin-bottom" style={{ background: tokens.surface, border: `1px solid ${tokens.panelBorder}`, color: tokens.text }}>
                      {bar.day}: {bar.value}K reach
                    </motion.div>
                  )}
                </AnimatePresence>
                <motion.div className="w-full rounded-t-[18px]" style={{ height: `${bar.value}%`, background: active ? "linear-gradient(180deg, rgba(163,138,112,0.95), rgba(122,139,118,0.82))" : "linear-gradient(180deg, rgba(163,138,112,0.55), rgba(163,138,112,0.22))" }} initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ duration: 0.45, delay: index * 0.06, ease: EASE }} />
              </div>
            );
          })}
        </div>
        <div className="mt-3 flex gap-3">
          {bars.map((bar) => (
            <div key={bar.day} className="flex-1 text-center text-[11px]" style={{ color: tokens.faint }}>{bar.day}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

const PANELS: Record<
  WorkspaceId,
  (props: { tokens: Tokens; channel: ChannelId; scenario: ScenarioId }) => JSX.Element
> = {
  sync: SyncPanel,
  score: ScorePanel,
  plan: PlanPanel,
  repurpose: RepurposePanel,
  publish: PublishPanel,
  learn: LearnPanel,
};

export default function ProductShowcase() {
  const shouldReduceMotion = useReducedMotion();
  const tokens = useTokens();
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId>("sync");
  const [activeChannel, setActiveChannel] = useState<ChannelId>("linkedin");
  const [activeScenario, setActiveScenario] = useState<ScenarioId>("authority");
  const ActivePanel = PANELS[activeWorkspace];

  return (
    <section id="showcase" className="relative overflow-hidden py-12 sm:py-24" style={{ background: tokens.isDark ? "#0C0B09" : "#F9F8F6" }}>
      <div className="pointer-events-none absolute left-0 top-10 h-[420px] w-[520px]" style={{ background: tokens.pageGlow }} />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[420px] w-[520px]" style={{ background: "radial-gradient(circle, rgba(15,23,42,0.05) 0%, transparent 72%)" }} />
      <div className="relative z-10 mx-auto max-w-7xl px-6 lg:px-10">
        <div className="max-w-xl">
          <motion.div initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.45 }} className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-[#A38A70]/70" />
            <span className="eyebrow">Product Experience</span>
          </motion.div>
          <motion.h2 initial={shouldReduceMotion ? false : { opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.52, delay: 0.05 }} className="mt-6 text-[28px] sm:text-[42px] lg:text-[58px] font-bold leading-[1.03] tracking-[-0.045em]" style={{ color: tokens.text }}>
            The moment the stack <span className="gradient-text">clicks</span>
          </motion.h2>
          <motion.p initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.45, delay: 0.1 }} className="mt-5 text-[15px] leading-8" style={{ color: tokens.muted }}>
            Connect accounts, score drafts, map the calendar, repurpose winners, publish everywhere, and learn from real performance in one continuous workflow.
          </motion.p>
        </div>
        <motion.div initial={shouldReduceMotion ? false : { opacity: 0, y: 28 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }} transition={{ duration: 0.68, ease: EASE }} className="mt-10">
          <div className="overflow-hidden rounded-[30px]" style={{ background: tokens.panelBg, border: `1px solid ${tokens.panelBorder}`, boxShadow: tokens.panelShadow }}>
            <div className="flex items-center gap-2 px-4 py-3" style={{ background: tokens.surface, borderBottom: `1px solid ${tokens.panelBorder}` }}>
              <div className="flex gap-1.5">
                <div className="h-2.5 w-2.5 rounded-full bg-[rgba(255,95,87,0.7)]" />
                <div className="h-2.5 w-2.5 rounded-full bg-[rgba(254,188,46,0.7)]" />
                <div className="h-2.5 w-2.5 rounded-full bg-[rgba(40,200,64,0.7)]" />
              </div>
              <div className="mx-3 flex h-8 flex-1 items-center justify-center rounded-full px-4" style={{ background: tokens.softSurface, color: tokens.faint }}>
                <span className="text-[10px] tracking-[0.18em]">app.ittera.ai / creator-os</span>
              </div>
              <div className="text-[11px]" style={{ color: tokens.muted }}>Interactive workspace</div>
            </div>
            <div className="border-b px-4 py-4 sm:px-5" style={{ borderColor: tokens.panelBorder, background: tokens.surface }}>
              <TopStats tokens={tokens} scenario={activeScenario} />
              <div className="mt-4 space-y-4">
                <div>
                  <div className="mb-2 text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>
                    Choose a scenario
                  </div>
                  <ScenarioStrip active={activeScenario} setActive={setActiveScenario} tokens={tokens} />
                </div>
                <div>
                  <div className="mb-2 text-[11px] uppercase tracking-[0.18em]" style={{ color: tokens.faint }}>
                    Focus a channel
                  </div>
                  <ChannelStrip active={activeChannel} setActive={setActiveChannel} tokens={tokens} />
                </div>
              </div>
            </div>
            <div className="flex xl:flex-row flex-col">
              {/* Sidebar: Try the workflow */}
              <div
                className="xl:w-[220px] flex-shrink-0 p-4 xl:border-r border-b xl:border-b-0 xl:self-stretch"
                style={{ borderColor: tokens.panelBorder, background: tokens.surface }}
              >
                <div className="text-[11px] uppercase tracking-[0.18em] mb-1" style={{ color: tokens.faint }}>Try the workflow</div>
                <div className="text-[10px] mb-4" style={{ color: tokens.faint, opacity: 0.7 }}>Select a workspace module</div>
                <WorkspaceRail active={activeWorkspace} setActive={setActiveWorkspace} tokens={tokens} />
              </div>
              {/* Main content area */}
              <div className="flex-1 min-w-0 p-4 sm:p-5">
                <ControlDeck activeWorkspace={activeWorkspace} activeScenario={activeScenario} activeChannel={activeChannel} tokens={tokens} />
                <AnimatePresence mode="wait">
                  <motion.div key={`${activeWorkspace}-${activeChannel}-${activeScenario}`} initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={shouldReduceMotion ? undefined : { opacity: 0, y: -8 }} transition={{ duration: 0.2, ease: "easeOut" }} className="mt-4">
                    <ActivePanel tokens={tokens} channel={activeChannel} scenario={activeScenario} />
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </div>
        </motion.div>
        <motion.div initial={shouldReduceMotion ? false : { opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5, delay: 0.08 }} className="mt-5">
          <WorkspaceIntro active={activeWorkspace} tokens={tokens} />
        </motion.div>
      </div>
    </section>
  );
}
