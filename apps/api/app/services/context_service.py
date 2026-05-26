"""
ContextAssembler — builds the 3-layer context for every LLM content generation call.

Layer 1: PermanentContext  — brand identity + user-approved platform facts
Layer 2: PersonaContext    — AI-derived writing style from post analysis
Layer 3: ReportContext     — current engagement insights from analytics

Usage:
    from app.services import context_service
    ctx = context_service.assemble(db=db, user=user, platform="linkedin")
    # ctx.system_prompt → inject into LLM as the system message
    # ctx.missing_layers → warn the user if context is incomplete
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.brand_profile import BrandProfile
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.user import User
from app.models.user_context import UserContext
from app.schemas.context import (
    AssembledContext,
    PersonaContext,
    PermanentContext,
    PlatformFactEntry,
    ReportContext,
)


# ── Public API ────────────────────────────────────────────────────────────────

def assemble(db: Session, user: User, platform: str = "linkedin") -> AssembledContext:
    """
    Reads all three context layers and returns a single AssembledContext whose
    .system_prompt is ready to be injected into any LLM call.
    """
    permanent = _get_permanent_context(db, user)
    persona = _get_persona_context(db, user)
    report = _get_report_context(db, user, platform)
    missing = _missing_layers(permanent, persona, report)
    system_prompt = _build_system_prompt(permanent, persona, report, platform)

    return AssembledContext(
        system_prompt=system_prompt,
        permanent=permanent,
        persona=persona,
        report=report,
        platform=platform,
        missing_layers=missing,
    )


def get_active_user_context(db: Session, user: User) -> UserContext | None:
    """Returns the single active UserContext snapshot for this user."""
    return (
        db.query(UserContext)
        .filter(UserContext.user_id == user.id, UserContext.is_active == True)  # noqa: E712
        .first()
    )


# ── Layer 1: Permanent Context ────────────────────────────────────────────────

def _get_permanent_context(db: Session, user: User) -> PermanentContext:
    uctx = get_active_user_context(db, user)

    # Platform facts from the active UserContext snapshot
    raw_facts: dict = uctx.platform_facts if uctx else {}
    platform_facts: dict[str, PlatformFactEntry] = {}
    for platform_key, facts in raw_facts.items():
        try:
            platform_facts[platform_key] = PlatformFactEntry(**facts)
        except Exception:
            pass  # Tolerate schema drift in stored JSON

    return PermanentContext(
        brand_name=user.brand_name,
        bio=user.bio,
        target_audience=user.target_audience,
        content_mission=user.content_mission,
        niche=user.niche,
        primary_platform=user.primary_platform,
        platform_facts=platform_facts,
        context_version=uctx.version if uctx else 0,
    )


# ── Layer 2: Persona Context ──────────────────────────────────────────────────

def _get_persona_context(db: Session, user: User) -> PersonaContext:
    """
    Reads the BrandProfile (AI-derived writing style analysis).
    Falls back to a zero-confidence PersonaContext if no profile exists yet.
    """
    profile: BrandProfile | None = (
        db.query(BrandProfile)
        .filter(BrandProfile.user_id == user.id, BrandProfile.is_confirmed == True)  # noqa: E712
        .first()
    )
    if not profile or not profile.profile:
        return PersonaContext()

    p = profile.profile  # JSON dict from BrandProfileData

    return PersonaContext(
        voice_tone=p.get("voice_tone"),
        sentence_style=None,  # Not yet in BrandProfileData — future field
        hook_patterns=p.get("writing_patterns", []),
        content_pillars=p.get("content_pillars", []),
        hashtag_style=p.get("hashtag_strategy"),
        emoji_usage=p.get("emoji_usage"),
        avg_post_length=p.get("avg_post_length"),
        analysis_based_on_posts=profile.analysis_based_on_posts,
        confidence_score=profile.ai_confidence_score,
    )


# ── Layer 3: Report Context ───────────────────────────────────────────────────

def _get_report_context(db: Session, user: User, platform: str) -> ReportContext:
    """
    Derives the report context from the last 30 days of post + analysis data.
    Falls back to an empty ReportContext if no data exists yet.
    """
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    posts = (
        db.query(Post)
        .filter(
            Post.user_id == user.id,
            Post.platform == platform,
            Post.published_at >= cutoff,
        )
        .order_by(Post.engagement_rate.desc())
        .all()
    )

    if not posts:
        return ReportContext()

    # Top topics from highest-engagement posts
    top_topics: list[str] = []
    for p in posts[:5]:
        if p.topics:
            topics = p.topics if isinstance(p.topics, list) else [p.topics]
            top_topics.extend(t for t in topics if t not in top_topics)

    avg_er = (
        sum(p.engagement_rate for p in posts if p.engagement_rate) / len(posts)
        if posts else None
    )

    best_hook: str | None = None
    top_post = posts[0] if posts else None
    if top_post:
        lines = (top_post.content or "").strip().splitlines()
        best_hook = lines[0][:150] if lines else None

    return ReportContext(
        top_performing_topics=top_topics[:5],
        avg_engagement_rate=round(avg_er, 4) if avg_er else None,
        best_hook_last_cycle=best_hook,
        posts_analysed=len(posts),
        period_days=30,
    )


# ── System Prompt Builder ─────────────────────────────────────────────────────

def _build_system_prompt(
    permanent: PermanentContext,
    persona: PersonaContext,
    report: ReportContext,
    platform: str,
) -> str:
    """
    Composes the three context layers into a single LLM system prompt.
    Each section is labelled so the model can weight them appropriately.
    """
    parts: list[str] = [
        "You are an expert content strategist generating a post for a specific creator.",
        f"Platform: {platform.upper()}",
        "",
    ]

    # Layer 1
    parts.append("## Creator Identity (Permanent — highest priority)")
    if permanent.brand_name:
        parts.append(f"- Name / Brand: {permanent.brand_name}")
    if permanent.bio:
        parts.append(f"- Bio: {permanent.bio}")
    if permanent.target_audience:
        parts.append(f"- Target Audience: {permanent.target_audience}")
    if permanent.content_mission:
        parts.append(f"- Content Mission: {permanent.content_mission}")
    if permanent.niche:
        parts.append(f"- Niche: {permanent.niche}")

    # Platform-specific facts
    facts = permanent.platform_facts.get(platform)
    if facts:
        if facts.best_post_times:
            parts.append(f"- Default Post Times ({platform}): {', '.join(facts.best_post_times)}")
        if facts.best_formats:
            parts.append(f"- Best Performing Formats ({platform}): {', '.join(facts.best_formats)}")
        if facts.avoid:
            parts.append(f"- Avoid ({platform}): {', '.join(facts.avoid)}")

    parts.append("")

    # Layer 2
    if persona.voice_tone or persona.hook_patterns:
        parts.append("## Writing Style (Persona — match this voice exactly)")
        if persona.voice_tone:
            parts.append(f"- Voice & Tone: {persona.voice_tone}")
        if persona.hook_patterns:
            parts.append(f"- Typical Opening Patterns: {'; '.join(persona.hook_patterns)}")
        if persona.content_pillars:
            parts.append(f"- Content Pillars: {', '.join(persona.content_pillars)}")
        if persona.hashtag_style:
            parts.append(f"- Hashtag Style: {persona.hashtag_style}")
        if persona.confidence_score < 0.6:
            parts.append(
                f"  ⚠ Low-confidence persona (based on {persona.analysis_based_on_posts} posts). "
                "Use as a soft guide, not a hard rule."
            )
        parts.append("")

    # Layer 3
    if report.posts_analysed > 0:
        parts.append("## Current Performance Insights (Report — recent signal)")
        if report.top_performing_topics:
            parts.append(f"- Top Topics Right Now: {', '.join(report.top_performing_topics)}")
        if report.avg_engagement_rate:
            parts.append(f"- Avg Engagement Rate (last {report.period_days}d): {report.avg_engagement_rate:.2%}")
        if report.best_hook_last_cycle:
            parts.append(f"- Best-Performing Hook Recently: \"{report.best_hook_last_cycle}\"")
        parts.append("")

    parts.append(
        "Generate content that is authentic to this creator's identity, matches their voice, "
        "and is informed by what has worked recently. Do not add facts not in this context."
    )

    return "\n".join(parts)


# ── Missing Layer Detection ───────────────────────────────────────────────────

def _missing_layers(
    permanent: PermanentContext,
    persona: PersonaContext,
    report: ReportContext,
) -> list[str]:
    missing = []
    if not permanent.is_complete():
        missing.append("permanent_context")
    if persona.confidence_score < 0.6:
        missing.append("persona_context")
    if report.posts_analysed == 0:
        missing.append("report_context")
    return missing
