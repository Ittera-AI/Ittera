from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.models.user import User


def posts_with_analysis(db: Session, user: User, limit: int = 20, platform: str = "linkedin") -> list[dict]:
    posts = (
        db.query(Post)
        .filter(Post.user_id == user.id, Post.platform == platform)
        .order_by(Post.published_at.desc().nullslast())
        .limit(limit)
        .all()
    )
    return [_post_payload(post) for post in posts]


def analyze_post(db: Session, user: User, post_id: str) -> dict:
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if post is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    analysis = post.analysis
    if analysis is None:
        analysis = PostAnalysis(
            post_id=post.id,
            hook_score=8,
            tone_match_score=9,
            structure_score=8,
            cta_effectiveness="strong" if "?" in post.content else "weak",
            coach_feedback={
                "top_strength": "Clear strategic point of view",
                "top_improvement": "Add a sharper closing question to invite replies",
                "predicted_engagement": "high" if post.engagement_rate >= 0.05 else "medium",
            },
            rewrite_suggestion="Start with the tradeoff, then show the operating principle in one line.",
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
    return _analysis_payload(post.id, analysis)


def _post_payload(post: Post) -> dict:
    return {
        "id": post.id,
        "platform": post.platform,
        "content": post.content,
        "published_at": post.published_at,
        "likes": post.likes,
        "comments": post.comments,
        "shares": post.shares,
        "engagement_rate": post.engagement_rate,
        "analysis": _analysis_payload(post.id, post.analysis) if post.analysis else None,
    }


def _analysis_payload(post_id: str, analysis: PostAnalysis) -> dict:
    feedback = analysis.coach_feedback or {}
    return {
        "post_id": post_id,
        "hook_score": analysis.hook_score,
        "tone_match_score": analysis.tone_match_score,
        "structure_score": analysis.structure_score,
        "cta_effectiveness": analysis.cta_effectiveness,
        "top_strength": feedback.get("top_strength", "Clear point of view"),
        "top_improvement": feedback.get("top_improvement", "Make the ending more actionable"),
        "predicted_engagement": feedback.get("predicted_engagement", "medium"),
        "rewrite_suggestion": analysis.rewrite_suggestion,
    }
