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

from sqlalchemy.orm import Session

from app.db.datetime_helpers import utc_now
from app.models.brand_profile import BrandProfile
from app.models.post import Post
from app.models.user import User
from app.schemas.brand_profile import BrandProfileData, normalize_profile
from app.services.mock_data import topics_for_niche

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────────────────────

def get_profile(db: Session, user: User) -> dict:
    profile = _profile(db, user)
    return _response(profile)


def generate_profile(db: Session, user: User) -> dict:
    """
    Synchronous generation path — calls BrandProfileEngine with the user's real posts.
    Falls back to hardcoded mock data if fewer than 3 posts exist or no AI key is set.
    Called by the frontend via POST /brand-profile/generate.
    """
    posts = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").all()

    if len(posts) >= 3:
        try:
            engine_output = _run_engine(user, posts)
            return generate_profile_from_data(db, user, engine_output, posts=posts)
        except Exception:
            logger.exception("generate_profile: BrandProfileEngine failed — using mock user_id=%s", user.id)

    # Fallback: hardcoded mock profile (no posts or engine error)
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
        posts = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").all()

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


# ── Internal helpers ──────────────────────────────────────────────────────────

def _run_engine(user: User, posts: list[Post]):
    """Imports and runs BrandProfileEngine. Import is deferred to avoid circular deps."""
    from iterra_ai.brand_profile.engine import BrandProfileEngine
    from iterra_ai.brand_profile.schemas import BrandProfileInput

    formatted = _format_posts_for_engine(posts)
    engine_input = BrandProfileInput(niche=user.niche or "content creation", posts=formatted)
    return BrandProfileEngine().generate(engine_input)


def _format_posts_for_engine(posts: list[Post]) -> list[str]:
    """
    Formats posts as annotated strings for the LLM:
    "Post #N | YYYY-MM-DD | Engagement: X.X%\n{content}"
    """
    sorted_posts = sorted(posts, key=lambda p: p.published_at or utc_now(), reverse=True)
    result = []
    for i, p in enumerate(sorted_posts, 1):
        date_str = p.published_at.strftime("%Y-%m-%d") if p.published_at else "unknown date"
        er_str = f"{p.engagement_rate:.1%}" if p.engagement_rate else "0.0%"
        header = f"Post #{i} | {date_str} | Engagement: {er_str}"
        result.append(f"{header}\n{p.content or ''}")
    return result


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
