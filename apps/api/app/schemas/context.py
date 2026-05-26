"""
Context schemas — the three context layers that feed into every LLM call.

PermanentContext  — brand identity + user-approved platform facts (never volatile)
PersonaContext    — AI-derived writing style, tone, patterns (from post analysis)
ReportContext     — current engagement insights (recent, from analytics)
AssembledContext  — all three merged into a single system prompt string

These are the contracts between context_service.py and every AI service.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Platform Facts (inside PermanentContext) ──────────────────────────────────

class PlatformFactEntry(BaseModel):
    """A single user-approved learned fact for one platform."""
    best_post_times: list[str] = Field(
        default_factory=list,
        description="UTC times in HH:MM format when posts perform best, e.g. ['17:00']",
    )
    best_formats: list[str] = Field(
        default_factory=list,
        description="Post formats that consistently perform well, e.g. ['listicle', 'story']",
    )
    avoid: list[str] = Field(
        default_factory=list,
        description="Formats or topics that consistently underperform",
    )
    confirmed_at: str | None = Field(
        default=None,
        description="ISO datetime when the user approved these facts",
    )


# ── Layer 1: Permanent Context ────────────────────────────────────────────────

class PermanentContext(BaseModel):
    """
    Layer 1 — never volatile. Set at onboarding, only updated when the user
    confirms a change (manual edit) or approves a learning-loop fact promotion.
    """
    brand_name: str | None = None
    bio: str | None = None
    target_audience: str | None = None
    content_mission: str | None = None
    niche: str | None = None
    primary_platform: str = "linkedin"
    platform_facts: dict[str, PlatformFactEntry] = Field(
        default_factory=dict,
        description="Keyed by platform slug: 'linkedin', 'twitter', 'instagram'",
    )
    context_version: int = 1

    def is_complete(self) -> bool:
        """True when enough identity fields exist to generate meaningful content."""
        return bool(self.bio and self.target_audience)


# ── Layer 2: Persona Context ──────────────────────────────────────────────────

class PersonaContext(BaseModel):
    """
    Layer 2 — AI-derived from post analysis. Updated whenever new posts are
    scraped and analysed. Represents *how* the user writes, not *who* they are.
    """
    voice_tone: str | None = None              # e.g. "Direct, analytical, calmly opinionated"
    sentence_style: str | None = None          # e.g. "Short paragraphs, punchy openers"
    hook_patterns: list[str] = Field(default_factory=list)  # Recurring opening moves
    content_pillars: list[str] = Field(default_factory=list)
    hashtag_style: str | None = None           # e.g. "3-5 professional hashtags at end"
    emoji_usage: str | None = None             # e.g. "Minimal — one per post max"
    avg_post_length: int | None = None         # words
    analysis_based_on_posts: int = 0
    confidence_score: float = 0.0              # 0.0–1.0; below 0.6 = treat as low-confidence


# ── Layer 3: Report Context ───────────────────────────────────────────────────

class ReportContext(BaseModel):
    """
    Layer 3 — current cycle insights. Volatile; refreshed after every analytics
    sync. Represents *what's working right now* for this user's content.
    """
    top_performing_topics: list[str] = Field(default_factory=list)
    avg_engagement_rate: float | None = None
    best_hook_last_cycle: str | None = None    # Hook text of the top post
    content_gaps: list[str] = Field(default_factory=list)  # Topics the niche is discussing but user hasn't
    posts_analysed: int = 0
    period_days: int = 30                      # Window this report covers


# ── Assembled Context (output of ContextAssembler) ───────────────────────────

class AssembledContext(BaseModel):
    """
    The fully assembled context passed to every LLM content generation call.
    system_prompt is injected as the system message; the three source objects
    are retained for debugging, logging, and cost attribution.
    """
    system_prompt: str
    permanent: PermanentContext
    persona: PersonaContext
    report: ReportContext
    platform: str                              # Target platform for this generation call
    missing_layers: list[str] = Field(
        default_factory=list,
        description="Layers that were absent / low-confidence — for UI warnings",
    )

    def has_full_context(self) -> bool:
        return len(self.missing_layers) == 0


# ── Onboarding update schema ──────────────────────────────────────────────────

class UpdatePermanentContextRequest(BaseModel):
    """User-initiated edit of their permanent context."""
    brand_name: str | None = None
    bio: str | None = None
    target_audience: str | None = None
    content_mission: str | None = None
    niche: str | None = None
    primary_platform: str | None = None


class PlatformFactProposal(BaseModel):
    """
    Proposed fact from the learning loop, awaiting user approval.
    The system proposes; the user approves; only then does it enter
    permanent context.
    """
    platform: str
    fact_type: str   # "best_post_time" | "best_format" | "avoid_format"
    value: Any
    evidence_summary: str    # Plain-English explanation of the evidence
    posts_analysed: int
    confidence: float        # 0.0–1.0
