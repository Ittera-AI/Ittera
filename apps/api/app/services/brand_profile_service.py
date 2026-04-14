from datetime import datetime

from sqlalchemy.orm import Session

from app.models.brand_profile import BrandProfile
from app.models.post import Post
from app.models.user import User
from app.schemas.brand_profile import BrandProfileData, normalize_profile
from app.services.mock_data import topics_for_niche


def get_profile(db: Session, user: User) -> dict:
    profile = _profile(db, user)
    return _response(profile)


def generate_profile(db: Session, user: User) -> dict:
    posts = db.query(Post).filter(Post.user_id == user.id, Post.platform == "linkedin").all()
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
        content_pillars=[
            "Strategic clarity",
            "Repeatable systems",
            "Performance learning",
        ],
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
    profile.ai_confidence_score = 0.86 if posts else 0.68
    profile.analysis_based_on_posts = len(posts)
    profile.generated_at = datetime.utcnow()
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return _response(profile)


def update_profile(db: Session, user: User, payload: BrandProfileData) -> dict:
    profile = _profile(db, user)
    if profile is None:
        profile = BrandProfile(user_id=user.id)
        db.add(profile)
    profile.profile = payload.model_dump()
    profile.is_confirmed = False
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return _response(profile)


def confirm_profile(db: Session, user: User) -> dict:
    profile = _profile(db, user)
    if profile is None:
        return generate_profile(db, user)
    profile.is_confirmed = True
    profile.confirmed_at = datetime.utcnow()
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return _response(profile)


def ensure_confirmed_profile(db: Session, user: User) -> BrandProfile | None:
    profile = _profile(db, user)
    return profile if profile and profile.is_confirmed else None


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
        "generated_at": profile.generated_at,
        "confirmed_at": profile.confirmed_at,
        "updated_at": profile.updated_at,
    }
