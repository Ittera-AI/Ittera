"""
BrandProfileService — manages the AI-derived persona layer (Layer 2 context).

Two generation paths:
  generate_profile()           — API-triggered, runs the BrandProfileEngine synchronously
                                 (used for manual "re-analyse" calls from the frontend).
  generate_profile_from_data() — called by the Celery analyze_brand_profile task after
                                 a background post sync; accepts a pre-computed
                                 BrandProfileOutput so the Celery task can run the LLM
                                 in the worker process.

Both paths persist to the same brand_profiles table row.
"""

from __future__ import annotations

import logging
from collections import Counter

from sqlalchemy.orm import Session

from app.db.datetime_helpers import utc_now
from app.models.brand_profile import BrandProfile
from app.models.post import Post
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.schemas.brand_profile import BrandProfileData, normalize_profile
from app.services.mock_data import topics_for_niche
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

# Minimum number of posts (across all platforms) before triggering AI analysis
MIN_POSTS_FOR_ANALYSIS = 5


# ── Public API ────────────────────────────────────────────────────────────────

def get_profile(db: Session, user: User) -> dict:
    profile = _profile(db, user)
    return _response(profile)


def generate_profile(db: Session, user: User) -> dict:
    """
    Synchronous generation path — calls BrandProfileEngine with the user's real posts
    from ALL connected platforms.
    Falls back to hardcoded mock data if fewer than MIN_POSTS_FOR_ANALYSIS posts exist
    or no AI key is set.
    Called by the frontend via POST /brand-profile/generate.
    """
    # Pull posts from all platforms (not just LinkedIn)
    posts = db.query(Post).filter(Post.user_id == user.id).all()

    if len(posts) >= MIN_POSTS_FOR_ANALYSIS:
        try:
            engine_output = _run_engine(user, posts)
            return generate_profile_from_data(db, user, engine_output, posts=posts)
        except Exception:
            logger.exception("generate_profile: BrandProfileEngine failed — using mock user_id=%s", user.id)

    # Fallback: hardcoded mock profile (insufficient posts or engine error)
    return _generate_mock_profile(db, user, posts)


def generate_profile_from_data(
    db: Session,
    user: User,
    engine_output: "BrandProfileOutput",  # noqa: F821 — forward ref
    *,
    posts: list[Post] | None = None,
) -> dict:
    """
    Persists a BrandProfileOutput (from BrandProfileEngine) to the brand_profiles table.
    Called by the Celery analyze_brand_profile task after a background sync.
    """
    if posts is None:
        posts = db.query(Post).filter(Post.user_id == user.id).all()

    data = BrandProfileData(
        voice_tone=engine_output.voice_tone,
        audience=engine_output.audience,
        core_topics=engine_output.core_topics,
        writing_patterns=engine_output.writing_patterns,
        content_pillars=engine_output.content_pillars,
        hashtag_strategy=engine_output.hashtag_strategy,
        summary=engine_output.summary,
    )

    # Store the extra fields in the JSON blob under extended_data
    extended: dict = {}
    if engine_output.avg_post_length is not None:
        extended["avg_post_length"] = engine_output.avg_post_length
    if engine_output.emoji_usage is not None:
        extended["emoji_usage"] = engine_output.emoji_usage

    profile = _profile(db, user)
    if profile is None:
        profile = BrandProfile(user_id=user.id)
        db.add(profile)

    profile_dict = data.model_dump()
    profile_dict.update(extended)

    profile.profile = profile_dict
    profile.version = (profile.version or 0) + 1
    profile.ai_confidence_score = _confidence_score(len(posts))
    profile.analysis_based_on_posts = len(posts)
    profile.generated_at = utc_now()
    profile.updated_at = utc_now()

    db.commit()
    db.refresh(profile)

    # Save to Google Drive if user has Drive connected
    try:
        _save_brand_analysis_to_drive_if_connected(db, user, profile, profile_dict)
    except Exception as e:
        # Don't fail the profile generation if Drive save fails
        logger.warning("Failed to save brand analysis to Drive: %s", e)

    logger.info(
        "generate_profile_from_data: saved profile v%d confidence=%.2f posts=%d user_id=%s",
        profile.version,
        profile.ai_confidence_score,
        len(posts),
        user.id,
    )
    return _response(profile)


def update_profile(db: Session, user: User, payload: BrandProfileData) -> dict:
    profile = _profile(db, user)
    if profile is None:
        profile = BrandProfile(user_id=user.id)
        db.add(profile)
    profile.profile = payload.model_dump()
    profile.is_confirmed = False
    profile.updated_at = utc_now()
    db.commit()
    db.refresh(profile)
    return _response(profile)


def confirm_profile(db: Session, user: User) -> dict:
    profile = _profile(db, user)
    if profile is None:
        return generate_profile(db, user)
    profile.is_confirmed = True
    profile.confirmed_at = utc_now()
    profile.updated_at = utc_now()
    db.commit()
    db.refresh(profile)
    return _response(profile)


def ensure_confirmed_profile(db: Session, user: User) -> BrandProfile | None:
    profile = _profile(db, user)
    return profile if profile and profile.is_confirmed else None


def ready_for_analysis(db: Session, user: User) -> bool:
    """
    Check whether a user has enough posts across all platforms to trigger
    brand profile generation. Returns True if total_posts >= MIN_POSTS_FOR_ANALYSIS.
    """
    total_posts = db.query(Post).filter(Post.user_id == user.id).count()
    return total_posts >= MIN_POSTS_FOR_ANALYSIS


# ── Internal helpers ──────────────────────────────────────────────────────────

def _run_engine(user: User, posts: list[Post]):
    """Imports and runs BrandProfileEngine. Import is deferred to avoid circular deps."""
    from iterra_ai.brand_profile.engine import BrandProfileEngine
    from iterra_ai.brand_profile.schemas import BrandProfileInput

    formatted = _format_posts_for_engine(posts)

    # Add platform-specific style variation notes if posts span multiple platforms
    platform_notes = _build_platform_style_notes(posts)
    niche = user.niche or "content creation"
    if platform_notes:
        niche = f"{niche}\n\n{platform_notes}"

    engine_input = BrandProfileInput(niche=niche, posts=formatted)
    return BrandProfileEngine().generate(engine_input)


def _format_posts_for_engine(posts: list[Post]) -> list[str]:
    """
    Formats posts as annotated strings for the LLM:
    "Post #N | PLATFORM | YYYY-MM-DD | Engagement: X.X%\n{content}"
    """
    sorted_posts = sorted(posts, key=lambda p: p.published_at or utc_now(), reverse=True)
    result = []
    for i, p in enumerate(sorted_posts, 1):
        date_str = p.published_at.strftime("%Y-%m-%d") if p.published_at else "unknown date"
        er_str = f"{p.engagement_rate:.1%}" if p.engagement_rate else "0.0%"
        platform_label = p.platform.upper() if p.platform else "UNKNOWN"
        header = f"Post #{i} | {platform_label} | {date_str} | Engagement: {er_str}"
        result.append(f"{header}\n{p.content or ''}")
    return result


def _build_platform_style_notes(posts: list[Post]) -> str:
    """
    Build platform-specific style variation notes for the AI engine prompt.
    Only included when posts span multiple platforms.
    """
    platform_counts = Counter(p.platform for p in posts if p.platform)
    platforms = sorted(platform_counts.keys())

    if len(platforms) <= 1:
        return ""

    notes_lines = [
        "Platform-specific style notes (posts are tagged by platform):",
    ]

    platform_guidance = {
        "twitter": "TWITTER posts tend to be shorter, punchier, and more conversational. Look for concise hooks, thread structures, and hashtag usage patterns.",
        "linkedin": "LINKEDIN posts tend to be longer-form, more narrative and professional. Look for storytelling, thought leadership patterns, and structured formatting.",
        "instagram": "INSTAGRAM posts tend to be visual-first with shorter captions, emoji-heavy, and hashtag-rich. Look for lifestyle tone and call-to-action patterns.",
    }

    for platform in platforms:
        count = platform_counts[platform]
        guidance = platform_guidance.get(platform, f"{platform.upper()} posts may have distinct style conventions.")
        notes_lines.append(f"- {platform.upper()} ({count} posts): {guidance}")

    notes_lines.append(
        "Identify cross-platform patterns (consistent voice) AND platform-specific adaptations (format/length differences)."
    )

    return "\n".join(notes_lines)


def _generate_mock_profile(db: Session, user: User, posts: list[Post]) -> dict:
    """Hardcoded fallback profile used when posts < 3 or engine unavailable."""
    topics = topics_for_niche(user.niche)
    data = BrandProfileData(
        voice_tone="Clear, analytical, and calmly opinionated",
        audience=f"Professionals interested in {user.niche or 'AI-powered content systems'}",
        core_topics=topics,
        writing_patterns=[
            "Opens with a direct observation",
            "Uses short paragraphs for pace",
            "Connects strategy to operating habits",
        ],
        content_pillars=["Strategic clarity", "Repeatable systems", "Performance learning"],
        hashtag_strategy="#ContentStrategy #LinkedInGrowth #AIWorkflow",
        summary=(
            "Your strongest lane is practical strategy: taking noisy market signals and turning "
            "them into calm, useful content decisions."
        ),
    )
    profile = _profile(db, user)
    if profile is None:
        profile = BrandProfile(user_id=user.id)
        db.add(profile)
    profile.profile = data.model_dump()
    profile.version = (profile.version or 0) + 1
    profile.ai_confidence_score = 0.45 if posts else 0.30  # Low — this is mock output
    profile.analysis_based_on_posts = len(posts)
    profile.generated_at = utc_now()
    profile.updated_at = utc_now()
    db.commit()
    db.refresh(profile)
    return _response(profile)


def _confidence_score(post_count: int) -> float:
    """
    Confidence increases with more posts up to a ceiling of 0.95.
    Formula: 0.40 base + 0.01 per post, capped at 0.95.
    - 5  posts → 0.45
    - 20 posts → 0.60
    - 40 posts → 0.80
    - 55+ posts → 0.95
    """
    return round(min(0.40 + post_count * 0.01, 0.95), 2)


def _profile(db: Session, user: User) -> BrandProfile | None:
    return db.query(BrandProfile).filter(BrandProfile.user_id == user.id).first()


def _response(profile: BrandProfile | None) -> dict:
    if profile is None:
        return {}
    return {
        "id": profile.id,
        "profile": normalize_profile(profile.profile),
        "version": profile.version,
        "ai_confidence_score": profile.ai_confidence_score,
        "is_confirmed": profile.is_confirmed,
        "analysis_based_on_posts": profile.analysis_based_on_posts,
        "drive_analysis_file_id": profile.drive_analysis_file_id,
        "generated_at": profile.generated_at,
        "confirmed_at": profile.confirmed_at,
        "updated_at": profile.updated_at,
    }


def _save_brand_analysis_to_drive_if_connected(
    db: Session, user: User, profile: BrandProfile, analysis_data: dict
) -> None:
    """
    Save brand analysis to Google Drive if user has Drive connected.
    Updates profile.drive_analysis_file_id with the Drive file ID.
    """
    # Check storage preference
    if user.storage_preference != "google_drive":
        return

    # Get Google Drive connection
    drive_connection = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.user_id == user.id,
            SocialConnection.platform == "google_drive",
            SocialConnection.is_active == True,
        )
        .first()
    )

    if not drive_connection:
        logger.debug("User %s has no Google Drive connection, skipping Drive save", user.id)
        return

    # Get folder ID from metadata
    meta = drive_connection.connection_metadata or {}
    iterra_folder_id = meta.get("iterra_folder_id")

    if not iterra_folder_id:
        logger.warning("User %s has Drive connection but no Iterra folder ID", user.id)
        return

    # Prepare analysis data for Drive
    drive_data = {
        "version": profile.version,
        "generated_at": profile.generated_at.isoformat() if profile.generated_at else None,
        "ai_confidence_score": profile.ai_confidence_score,
        "analysis_based_on_posts": profile.analysis_based_on_posts,
        "profile": analysis_data,
    }

    # Save to Drive
    storage = StorageService(
        access_token=drive_connection.access_token,
        refresh_token=drive_connection.refresh_token,
    )

    # Use existing file ID if available (update), else create new
    file_id = storage.save_brand_analysis(
        folder_id=iterra_folder_id,
        analysis_data=drive_data,
        existing_file_id=profile.drive_analysis_file_id,
    )

    # Update profile with Drive file ID
    profile.drive_analysis_file_id = file_id
    db.commit()

    logger.info("Saved brand analysis v%d to Drive with file ID %s", profile.version, file_id)
