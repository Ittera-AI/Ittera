"""Competitive intelligence API endpoints.

Provides endpoints for:
- Managing competitors to track
- Running competitive analyses
- Viewing content gaps
- Benchmarking trend performance
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.dependencies.workspace import can_view_competitors
from app.models.organization import (
    Competitor,
    CompetitorAnalysis,
    CompetitorPost,
    Workspace,
)
from app.models.user import User

router = APIRouter(tags=["competitors"])


# ---------------------------------------------------------------------------
# Request/Response Schemas
# ---------------------------------------------------------------------------

class CompetitorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    platform: Literal["linkedin", "twitter", "instagram", "facebook"] = "linkedin"
    handle: str = Field(..., min_length=1, max_length=255)
    profile_url: str | None = Field(None, max_length=500)
    niche_tags: list[str] = Field(default_factory=list)


class CompetitorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None
    niche_tags: list[str] | None = None


class CompetitorResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    platform: str
    handle: str
    profile_url: str | None
    follower_count: int | None
    niche_tags: list[str]
    is_active: bool
    last_synced_at: str | None
    created_at: str
    
    class Config:
        from_attributes = True


class CompetitorDetailResponse(CompetitorResponse):
    recent_posts_count: int
    recent_analyses: list[dict]


class CompetitorWithStats(BaseModel):
    competitor: CompetitorResponse
    post_count: int
    avg_engagement: float | None
    top_post: dict | None


class StrategyAnalysisRequest(BaseModel):
    posts_to_analyze: int = Field(default=10, ge=5, le=50)
    force_refresh: bool = Field(default=False)


class ContentGapRequest(BaseModel):
    competitor_ids: list[str] | None = None  # None = all active competitors
    include_underserved: bool = Field(default=True)


class TrendBenchmarkRequest(BaseModel):
    trend_topic: str = Field(..., min_length=3, max_length=200)
    competitor_ids: list[str] | None = None


class AnalysisResponse(BaseModel):
    analysis_id: str
    analysis_type: str
    competitor_id: str | None
    created_at: str
    findings_summary: dict


class StrategyAnalysisResponse(AnalysisResponse):
    content_strategy: dict
    posting_patterns: dict
    engagement_tactics: list[str]
    top_performing_themes: list[dict]
    opportunities: list[dict]
    recommended_actions: list[str]
    content_ideas: list[str]
    confidence_score: float


class ContentGapResponse(AnalysisResponse):
    covered_topics: list[dict]
    gap_topics: list[dict]
    format_gaps: list[dict]
    high_impact_opportunities: list[dict]
    quick_wins: list[str]
    suggested_content_calendar: list[dict]


class TrendBenchmarkResponse(AnalysisResponse):
    trend_topic: str
    your_rank: int | None
    total_competitors: int
    why_top_performers_succeeded: list[str]
    your_gaps_vs_top: list[str]
    trend_lifecycle: str
    how_to_improve: list[str]


# ---------------------------------------------------------------------------
# Competitor Management
# ---------------------------------------------------------------------------

@router.get("", response_model=list[CompetitorResponse])
async def list_competitors(
    workspace: Workspace | None = Depends(can_view_competitors),
    db: Session = Depends(get_db),
):
    """List all competitors for the workspace."""
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    competitors = (
        db.query(Competitor)
        .filter(Competitor.workspace_id == workspace.id, Competitor.is_active.is_(True))
        .all()
    )
    
    return competitors


@router.post("", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def create_competitor(
    data: CompetitorCreate,
    workspace: Workspace | None = Depends(can_view_competitors),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a new competitor to track.
    
    Requires: ai:competitor_analysis permission
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    # Check not already tracking
    existing = (
        db.query(Competitor)
        .filter(
            Competitor.workspace_id == workspace.id,
            Competitor.platform == data.platform,
            Competitor.handle == data.handle,
        )
        .first()
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Already tracking {data.handle} on {data.platform}",
        )
    
    competitor = Competitor(
        workspace_id=workspace.id,
        name=data.name,
        platform=data.platform,
        handle=data.handle,
        profile_url=data.profile_url,
        niche_tags=data.niche_tags,
    )
    
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    
    return competitor


@router.get("/{competitor_id}", response_model=CompetitorDetailResponse)
async def get_competitor(
    competitor_id: str,
    workspace: Workspace | None = Depends(can_view_competitors),
    db: Session = Depends(get_db),
):
    """Get detailed competitor information with recent activity."""
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    competitor = (
        db.query(Competitor)
        .filter(
            Competitor.id == competitor_id,
            Competitor.workspace_id == workspace.id,
        )
        .first()
    )
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    # Get recent analyses
    recent_analyses = (
        db.query(CompetitorAnalysis)
        .filter(CompetitorAnalysis.competitor_id == competitor_id)
        .order_by(CompetitorAnalysis.created_at.desc())
        .limit(5)
        .all()
    )
    
    return {
        "id": competitor.id,
        "workspace_id": competitor.workspace_id,
        "name": competitor.name,
        "platform": competitor.platform,
        "handle": competitor.handle,
        "profile_url": competitor.profile_url,
        "follower_count": competitor.follower_count,
        "niche_tags": competitor.niche_tags or [],
        "is_active": competitor.is_active,
        "last_synced_at": competitor.last_synced_at.isoformat() if competitor.last_synced_at else None,
        "created_at": competitor.created_at.isoformat() if competitor.created_at else None,
        "recent_posts_count": len(competitor.posts),
        "recent_analyses": [
            {
                "id": a.id,
                "type": a.analysis_type,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent_analyses
        ],
    }


@router.patch("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: str,
    data: CompetitorUpdate,
    workspace: Workspace | None = Depends(can_view_competitors),
    db: Session = Depends(get_db),
):
    """Update competitor information."""
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    competitor = (
        db.query(Competitor)
        .filter(
            Competitor.id == competitor_id,
            Competitor.workspace_id == workspace.id,
        )
        .first()
    )
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    if data.name is not None:
        competitor.name = data.name
    if data.is_active is not None:
        competitor.is_active = data.is_active
    if data.niche_tags is not None:
        competitor.niche_tags = data.niche_tags
    
    db.commit()
    db.refresh(competitor)
    
    return competitor


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(
    competitor_id: str,
    workspace: Workspace | None = Depends(can_view_competitors),
    db: Session = Depends(get_db),
):
    """Remove a competitor from tracking."""
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    competitor = (
        db.query(Competitor)
        .filter(
            Competitor.id == competitor_id,
            Competitor.workspace_id == workspace.id,
        )
        .first()
    )
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    db.delete(competitor)
    db.commit()
    
    return None


# ---------------------------------------------------------------------------
# Competitive Analyses
# ---------------------------------------------------------------------------

@router.post("/{competitor_id}/analyze/strategy", response_model=StrategyAnalysisResponse)
async def analyze_competitor_strategy(
    competitor_id: str,
    request: StrategyAnalysisRequest,
    workspace: Workspace | None = Depends(can_view_competitors),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run AI strategy analysis on a competitor.
    
    Analyzes their content patterns, engagement tactics, and identifies opportunities.
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    # Get competitor
    competitor = (
        db.query(Competitor)
        .filter(
            Competitor.id == competitor_id,
            Competitor.workspace_id == workspace.id,
        )
        .first()
    )
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    # Check for recent analysis
    if not request.force_refresh:
        recent = (
            db.query(CompetitorAnalysis)
            .filter(
                CompetitorAnalysis.competitor_id == competitor_id,
                CompetitorAnalysis.analysis_type == "strategy",
                CompetitorAnalysis.created_at > datetime.utcnow().replace(
                    day=datetime.utcnow().day - 7
                ),
            )
            .first()
        )
        if recent:
            # Return cached analysis
            return recent.findings.get("strategy_analysis", {})
    
    # Get recent posts for analysis
    recent_posts = (
        db.query(CompetitorPost)
        .filter(CompetitorPost.competitor_id == competitor_id)
        .order_by(CompetitorPost.published_at.desc().nullslast())
        .limit(request.posts_to_analyze)
        .all()
    )
    
    if len(recent_posts) < 5:
        # Scrape competitor posts (background task)
        from workers.celery.tasks import scrape_competitor_posts
        scrape_competitor_posts.delay(
            competitor_id=competitor_id,
            platform=competitor.platform,
            handle=competitor.handle,
        )
        
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Competitor data being fetched. Retry analysis in a few minutes.",
        )
    
    # Run AI analysis
    from iterra_ai.competitive import (
        CompetitorProfileInput,
        get_competitive_engine,
    )
    
    # Get author context
    from app.services.analytics_service import get_author_historical_metrics
    author_metrics = get_author_historical_metrics(db, current_user.id, limit=50)
    
    engine = get_competitive_engine()
    analysis = engine.analyze_competitor_strategy(
        CompetitorProfileInput(
            competitor_id=competitor_id,
            competitor_name=competitor.name,
            platform=competitor.platform,
            handle=competitor.handle,
            follower_count=competitor.follower_count,
            niche_tags=competitor.niche_tags or [],
            recent_posts=[
                {
                    "content": p.content,
                    "engagement_rate": float(p.engagement_rate) if p.engagement_rate else 0,
                    "published_at": p.published_at.isoformat() if p.published_at else None,
                    "likes": p.likes,
                    "comments": p.comments,
                }
                for p in recent_posts
            ],
            author_niche=workspace.settings.get("niche") if workspace else None,
            author_avg_engagement=author_metrics.get("avg_engagement_rate") * 100 if author_metrics else None,
        )
    )
    
    # Store analysis
    analysis_record = CompetitorAnalysis(
        workspace_id=workspace.id,
        competitor_id=competitor_id,
        analysis_type="strategy",
        findings={"strategy_analysis": analysis.model_dump()},
        ai_model_used=analysis.model_version,
    )
    db.add(analysis_record)
    db.commit()
    
    return {
        **analysis.model_dump(),
        "analysis_id": analysis_record.id,
    }


@router.post("/analyze/gaps", response_model=ContentGapResponse)
async def analyze_content_gaps(
    request: ContentGapRequest,
    workspace: Workspace | None = Depends(can_view_competitors),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze content gaps between author and competitors.
    
    Identifies topics, formats, and approaches competitors use
    that the author doesn't.
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    # Get author's recent content themes
    from app.models.post import Post
    
    author_posts = (
        db.query(Post)
        .filter(Post.user_id == current_user.id)
        .order_by(Post.published_at.desc())
        .limit(20)
        .all()
    )
    
    author_topics = set()
    for post in author_posts:
        if post.topics:
            author_topics.update(post.topics)
    
    # Get competitor data
    query = db.query(Competitor).filter(
        Competitor.workspace_id == workspace.id,
        Competitor.is_active.is_(True),
    )
    
    if request.competitor_ids:
        query = query.filter(Competitor.id.in_(request.competitor_ids))
    
    competitors = query.all()
    
    if not competitors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No competitors found to analyze",
        )
    
    # Collect competitor data
    competitor_posts = []
    competitor_themes = set()
    
    for comp in competitors:
        for niche in (comp.niche_tags or []):
            competitor_themes.add(niche)
        
        posts = (
            db.query(CompetitorPost)
            .filter(CompetitorPost.competitor_id == comp.id)
            .order_by(CompetitorPost.published_at.desc().nullslast())
            .limit(10)
            .all()
        )
        
        for p in posts:
            competitor_posts.append({
                "content": p.content,
                "topics": p.topics,
                "engagement_rate": float(p.engagement_rate) if p.engagement_rate else 0,
            })
            if p.topics:
                competitor_themes.update(p.topics)
    
    # Run gap analysis
    from iterra_ai.competitive import (
        ContentGapAnalysisInput,
        get_competitive_engine,
    )
    
    engine = get_competitive_engine()
    gaps = engine.analyze_content_gaps(
        ContentGapAnalysisInput(
            author_content_pillars=list(author_topics),
            author_recent_topics=list(author_topics)[:10],
            competitor_posts=competitor_posts[:20],
            competitor_content_themes=list(competitor_themes),
            industry_trends=[],  # TODO: Add trend data
        )
    )
    
    # Store analysis
    analysis_record = CompetitorAnalysis(
        workspace_id=workspace.id,
        competitor_id=None,  # Multi-competitor analysis
        analysis_type="content_gaps",
        findings={"gap_analysis": gaps.model_dump()},
        ai_model_used=gaps.model_version,
    )
    db.add(analysis_record)
    db.commit()
    
    return {
        **gaps.model_dump(),
        "analysis_id": analysis_record.id,
        "competitor_id": None,
        "created_at": analysis_record.created_at.isoformat() if analysis_record.created_at else None,
    }


@router.post("/analyze/trend", response_model=TrendBenchmarkResponse)
async def benchmark_trend(
    request: TrendBenchmarkRequest,
    workspace: Workspace | None = Depends(can_view_competitors),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Benchmark author vs competitors on a specific trend/topic.
    
    Identifies why some creators succeed more than others on the same topic.
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    # Get author's posts on this trend
    from app.models.post import Post
    
    author_posts = (
        db.query(Post)
        .filter(
            Post.user_id == current_user.id,
            Post.content.ilike(f"%{request.trend_topic}%"),
        )
        .order_by(Post.published_at.desc())
        .limit(10)
        .all()
    )
    
    author_performance = None
    if author_posts:
        avg_engagement = sum(p.engagement_rate for p in author_posts) / len(author_posts)
        best_post = max(author_posts, key=lambda p: p.engagement_rate)
        author_performance = {
            "engagement_rate": avg_engagement * 100,
            "posts_count": len(author_posts),
            "best_post_content": best_post.content[:200] if best_post.content else None,
        }
    
    # Get competitor posts on trend
    query = db.query(Competitor).filter(
        Competitor.workspace_id == workspace.id,
        Competitor.is_active.is_(True),
    )
    
    if request.competitor_ids:
        query = query.filter(Competitor.id.in_(request.competitor_ids))
    
    competitors = query.all()
    
    competitor_performances = []
    for comp in competitors:
        posts = (
            db.query(CompetitorPost)
            .filter(
                CompetitorPost.competitor_id == comp.id,
                CompetitorPost.content.ilike(f"%{request.trend_topic}%"),
            )
            .order_by(CompetitorPost.published_at.desc())
            .limit(5)
            .all()
        )
        
        if posts:
            avg_engagement = sum(
                float(p.engagement_rate) if p.engagement_rate else 0
                for p in posts
            ) / len(posts)
            best_post = max(posts, key=lambda p: p.engagement_rate or 0)
            
            competitor_performances.append({
                "competitor_name": comp.name,
                "engagement_rate": avg_engagement,
                "posts_count": len(posts),
                "best_post": best_post.content[:200] if best_post.content else None,
            })
    
    # Run benchmark analysis
    from iterra_ai.competitive import (
        TrendBenchmarkInput,
        get_competitive_engine,
    )
    
    engine = get_competitive_engine()
    benchmark = engine.benchmark_trend(
        TrendBenchmarkInput(
            trend_topic=request.trend_topic,
            author_performance=author_performance,
            competitor_performances=competitor_performances,
        )
    )
    
    # Store analysis
    analysis_record = CompetitorAnalysis(
        workspace_id=workspace.id,
        competitor_id=None,
        analysis_type="trend_benchmark",
        findings={"trend_benchmark": benchmark.model_dump()},
        ai_model_used=benchmark.model_version,
    )
    db.add(analysis_record)
    db.commit()
    
    return {
        **benchmark.model_dump(),
        "analysis_id": analysis_record.id,
        "competitor_id": None,
        "created_at": analysis_record.created_at.isoformat() if analysis_record.created_at else None,
    }


@router.get("/analyses/history", response_model=list[AnalysisResponse])
async def list_analyses(
    analysis_type: str | None = None,
    limit: int = 20,
    workspace: Workspace | None = Depends(can_view_competitors),
    db: Session = Depends(get_db),
):
    """List recent competitive analyses."""
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    query = db.query(CompetitorAnalysis).filter(
        CompetitorAnalysis.workspace_id == workspace.id,
    )
    
    if analysis_type:
        query = query.filter(CompetitorAnalysis.analysis_type == analysis_type)
    
    analyses = query.order_by(CompetitorAnalysis.created_at.desc()).limit(limit).all()
    
    return [
        {
            "analysis_id": a.id,
            "analysis_type": a.analysis_type,
            "competitor_id": a.competitor_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "findings_summary": {
                "model": a.ai_model_used,
                "has_data": bool(a.findings),
            },
        }
        for a in analyses
    ]
