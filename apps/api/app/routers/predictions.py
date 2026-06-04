"""Prediction API endpoints for AI-powered content analysis.

Provides endpoints for:
- Performance prediction (with confidence intervals)
- Viral potential scoring
- Optimal timing prediction
- Caching and storage of predictions
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.dependencies.workspace import can_use_ai_predict, get_current_workspace
from app.models.organization import Prediction, Workspace
from app.models.user import User

router = APIRouter(prefix="/predictions", tags=["predictions"])


# ---------------------------------------------------------------------------
# Request/Response Schemas
# ---------------------------------------------------------------------------

class PerformancePredictionRequest(BaseModel):
    """Request to predict content performance."""
    content: str = Field(..., min_length=10, description="Content to analyze")
    platform: Literal["linkedin", "twitter", "instagram", "facebook"] = Field(
        default="linkedin",
    )
    content_type: Literal["post", "article", "video", "image", "poll"] = Field(
        default="post",
    )
    hashtags: list[str] = Field(default_factory=list)
    mentioned_accounts: list[str] = Field(default_factory=list)
    use_cache: bool = Field(default=True, description="Use cached prediction if available")


class ViralPredictionRequest(BaseModel):
    """Request to analyze viral potential."""
    content: str = Field(..., min_length=10)
    platform: Literal["linkedin", "twitter", "instagram", "facebook"] = Field(
        default="linkedin",
    )
    use_cache: bool = Field(default=True)


class TimingPredictionRequest(BaseModel):
    """Request to predict optimal posting time."""
    content: str = Field(..., min_length=10)
    platform: Literal["linkedin", "twitter", "instagram", "facebook"] = Field(
        default="linkedin",
    )
    timezone: str = Field(default="UTC")
    allowed_days: list[Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]] = Field(
        default_factory=lambda: ["mon", "tue", "wed", "thu", "fri"],
    )
    allowed_hours_start: int = Field(default=8, ge=0, le=23)
    allowed_hours_end: int = Field(default=18, ge=0, le=23)
    use_cache: bool = Field(default=True)


class ConfidenceIntervalResponse(BaseModel):
    lower: float
    upper: float
    confidence: float


class PredictionConfidenceResponse(BaseModel):
    overall_confidence: float
    engagement_rate_ci: ConfidenceIntervalResponse
    impressions_ci: ConfidenceIntervalResponse | None
    data_quality_score: float
    historical_alignment: float
    model_confidence: float


class PredictionMetricsResponse(BaseModel):
    likes: int
    comments: int
    shares: int
    impressions: int
    engagement_rate: float
    reach: int | None
    click_through_rate: float | None


class FeatureImportanceResponse(BaseModel):
    feature: str
    importance: float
    impact: Literal["positive", "negative", "neutral"]
    explanation: str


class PerformancePredictionResponse(BaseModel):
    prediction_id: str
    content_hash: str
    metrics: PredictionMetricsResponse
    confidence: PredictionConfidenceResponse
    feature_importance: list[FeatureImportanceResponse]
    improvement_suggestions: list[str]
    comparative_analysis: str | None
    model_version: str
    prediction_time: str
    processing_time_ms: int
    cached: bool = False


class ViralPatternResponse(BaseModel):
    pattern_type: str
    score: float
    detected: bool
    explanation: str
    examples: list[str]


class ViralPredictionResponse(BaseModel):
    prediction_id: str
    content_hash: str
    viral_probability: float
    viral_score: float
    category: str
    patterns: list[ViralPatternResponse]
    percentile_rank: float
    comparison_to_top_performers: str | None
    viral_triggers: list[str]
    amplification_suggestions: list[str]
    model_version: str
    prediction_time: str
    processing_time_ms: int
    cached: bool = False


class TimeSlotResponse(BaseModel):
    day: str
    hour: int
    score: float
    predicted_engagement_rate: float
    predicted_reach: int
    audience_availability: float
    competition_level: str
    reasoning: str


class TimingPatternResponse(BaseModel):
    pattern_type: str
    description: str
    confidence: float
    recommended_action: str | None


class TimingPredictionResponse(BaseModel):
    prediction_id: str
    content_hash: str
    optimal_time: str
    confidence_score: float
    alternative_slots: list[TimeSlotResponse]
    detected_patterns: list[TimingPatternResponse]
    best_days: list[str]
    best_hours: list[int]
    worst_times_to_post: list[str]
    platform_insights: str | None
    model_version: str
    prediction_time: str
    processing_time_ms: int
    cached: bool = False


class PredictionCacheEntry(BaseModel):
    prediction_id: str
    prediction_type: str
    content_hash: str
    created_at: str
    expires_at: str | None
    confidence_score: float | None
    model_used: str | None


class PredictionListResponse(BaseModel):
    predictions: list[PredictionCacheEntry]
    total: int


# ---------------------------------------------------------------------------
# Prediction Endpoints
# ---------------------------------------------------------------------------

@router.post("/performance", response_model=PerformancePredictionResponse)
async def predict_performance(
    request: PerformancePredictionRequest,
    workspace: Workspace | None = Depends(can_use_ai_predict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Predict content performance with confidence intervals.
    
    Analyzes content and predicts:
    - Likes, comments, shares, impressions
    - Engagement rate with 95% confidence intervals
    - Key factors affecting performance
    - Improvement suggestions
    """
    # Import here to avoid circular imports
    from iterra_ai.predictions import (
        ContentInput,
        PredictorEngine,
    )
    from app.services.analytics_service import get_author_historical_metrics
    
    # Check cache first
    if request.use_cache and workspace:
        import hashlib
        import json
        
        cache_key_input = {
            "content": request.content.strip().lower()[:500],
            "platform": request.platform,
        }
        input_hash = hashlib.sha256(
            json.dumps(cache_key_input, sort_keys=True).encode()
        ).hexdigest()[:32]
        
        cached = (
            db.query(Prediction)
            .filter(
                Prediction.workspace_id == workspace.id,
                Prediction.input_hash == input_hash,
                Prediction.prediction_type == "performance",
            )
            .first()
        )
        
        if cached:
            # Check not expired
            from datetime import datetime
            if cached.expires_at is None or cached.expires_at > datetime.utcnow():
                # Return cached result
                return cached.prediction_data
    
    # Get historical metrics for context
    historical = get_author_historical_metrics(db, current_user.id, limit=100)
    avg_engagement = historical.get("avg_engagement_rate") if historical else None
    follower_count = None  # TODO: Get from social connections
    
    # Generate prediction
    predictor = PredictorEngine()
    prediction = predictor.predict(ContentInput(
        content=request.content,
        platform=request.platform,
        content_type=request.content_type,
        hashtags=request.hashtags,
        mentioned_accounts=request.mentioned_accounts,
        industry=workspace.settings.get("industry") if workspace else None,
        target_audience=workspace.settings.get("target_audience") if workspace else None,
        author_avg_engagement=avg_engagement,
        author_follower_count=follower_count,
    ))
    
    # Store in cache if workspace context
    if workspace:
        cache_entry = Prediction(
            workspace_id=workspace.id,
            content_type=request.content_type,
            prediction_type="performance",
            input_hash=prediction.content_hash,
            prediction_data=prediction.model_dump(),
            confidence_score=prediction.confidence.overall_confidence,
            model_used=prediction.model_version,
            expires_at=None,  # Performance predictions don't expire
        )
        db.add(cache_entry)
        db.commit()
    
    return {
        **prediction.model_dump(),
        "cached": False,
    }


@router.post("/viral", response_model=ViralPredictionResponse)
async def predict_viral_potential(
    request: ViralPredictionRequest,
    workspace: Workspace | None = Depends(can_use_ai_predict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze content for viral potential.
    
    Detects viral patterns:
    - Hook strength
    - Emotional resonance
    - Shareability
    - Timeliness
    - Uniqueness
    
    Returns viral probability score (0-1) and amplification suggestions.
    """
    from iterra_ai.predictions import ViralPredictionEngine, ViralScoreInput
    
    # Check cache
    if request.use_cache and workspace:
        import hashlib
        import json
        
        cache_key_input = {
            "content": request.content.strip().lower()[:500],
            "platform": request.platform,
        }
        input_hash = hashlib.sha256(
            json.dumps(cache_key_input, sort_keys=True).encode()
        ).hexdigest()[:32]
        
        cached = (
            db.query(Prediction)
            .filter(
                Prediction.workspace_id == workspace.id,
                Prediction.input_hash == input_hash,
                Prediction.prediction_type == "viral",
            )
            .first()
        )
        
        if cached:
            from datetime import datetime
            if cached.expires_at is None or cached.expires_at > datetime.utcnow():
                return cached.prediction_data
    
    # Generate viral analysis
    viral_engine = ViralPredictionEngine()
    result = viral_engine.analyze(ViralScoreInput(
        content=request.content,
        platform=request.platform,
    ))
    
    # Cache result
    if workspace:
        cache_entry = Prediction(
            workspace_id=workspace.id,
            content_type="post",
            prediction_type="viral",
            input_hash=result.content_hash,
            prediction_data=result.model_dump(),
            confidence_score=result.viral_probability,
            model_used=result.model_version,
            expires_at=None,
        )
        db.add(cache_entry)
        db.commit()
    
    return {
        **result.model_dump(),
        "cached": False,
    }


@router.post("/timing", response_model=TimingPredictionResponse)
async def predict_optimal_timing(
    request: TimingPredictionRequest,
    workspace: Workspace | None = Depends(can_use_ai_predict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Predict optimal posting time for content.
    
    Analyzes:
    - Historical post performance patterns
    - Platform-specific audience behavior
    - Content type and complexity
    - Competition analysis
    
    Returns optimal time, alternative slots, and timing insights.
    """
    from iterra_ai.predictions import TimingPredictionEngine, TimingInput
    from app.services.analytics_service import get_post_timing_history
    
    # Get historical timing data
    historical = get_post_timing_history(db, current_user.id, limit=100)
    
    # Check cache (timing predictions are more stable)
    if request.use_cache and workspace:
        import hashlib
        import json
        from datetime import datetime, timedelta
        
        cache_key_input = {
            "content": request.content.strip().lower()[:200],
            "platform": request.platform,
            "timezone": request.timezone,
        }
        input_hash = hashlib.sha256(
            json.dumps(cache_key_input, sort_keys=True).encode()
        ).hexdigest()[:32]
        
        cached = (
            db.query(Prediction)
            .filter(
                Prediction.workspace_id == workspace.id,
                Prediction.input_hash == input_hash,
                Prediction.prediction_type == "timing",
                Prediction.created_at > (datetime.utcnow() - timedelta(days=7)),
            )
            .first()
        )
        
        if cached:
            return cached.prediction_data
    
    # Generate timing prediction
    timing_engine = TimingPredictionEngine()
    result = timing_engine.predict(TimingInput(
        content=request.content,
        platform=request.platform,
        timezone=request.timezone,
        allowed_days=request.allowed_days,
        allowed_hours_start=request.allowed_hours_start,
        allowed_hours_end=request.allowed_hours_end,
        author_historical_posts=historical,
    ))
    
    # Cache with weekly expiration
    if workspace:
        from datetime import datetime, timedelta
        
        cache_entry = Prediction(
            workspace_id=workspace.id,
            content_type="post",
            prediction_type="timing",
            input_hash=result.content_hash,
            prediction_data=result.model_dump(),
            confidence_score=result.confidence_score,
            model_used=result.model_version,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db.add(cache_entry)
        db.commit()
    
    return {
        **result.model_dump(),
        "cached": False,
    }


@router.post("/all")
async def predict_all(
    content: str = Query(..., min_length=10),
    platform: Literal["linkedin", "twitter", "instagram", "facebook"] = Query(default="linkedin"),
    workspace: Workspace | None = Depends(can_use_ai_predict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all predictions (performance, viral, timing) in one call.
    
    Efficient for clients that want a complete analysis.
    """
    from iterra_ai.predictions import (
        PredictorEngine,
        ViralPredictionEngine,
        TimingPredictionEngine,
        ContentInput,
        ViralScoreInput,
        TimingInput,
    )
    from app.services.analytics_service import get_author_historical_metrics, get_post_timing_history
    
    # Get historical data
    historical_metrics = get_author_historical_metrics(db, current_user.id, limit=100)
    historical_timing = get_post_timing_history(db, current_user.id, limit=100)
    
    # Generate all predictions in parallel would be better, but sequential for now
    predictor = PredictorEngine()
    performance = predictor.predict(ContentInput(
        content=content,
        platform=platform,
        author_avg_engagement=historical_metrics.get("avg_engagement_rate") if historical_metrics else None,
    ))
    
    viral = ViralPredictionEngine()
    viral_result = viral.analyze(ViralScoreInput(
        content=content,
        platform=platform,
    ))
    
    timing = TimingPredictionEngine()
    timing_result = timing.predict(TimingInput(
        content=content,
        platform=platform,
        author_historical_posts=historical_timing,
    ))
    
    return {
        "performance": performance.model_dump(),
        "viral": viral_result.model_dump(),
        "timing": timing_result.model_dump(),
    }


# ---------------------------------------------------------------------------
# Cache Management
# ---------------------------------------------------------------------------

@router.get("/cache", response_model=PredictionListResponse)
async def list_cached_predictions(
    prediction_type: str | None = None,
    limit: int = 50,
    workspace: Workspace | None = Depends(can_use_ai_predict),
    db: Session = Depends(get_db),
):
    """List cached predictions for the workspace."""
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    query = db.query(Prediction).filter(Prediction.workspace_id == workspace.id)
    
    if prediction_type:
        query = query.filter(Prediction.prediction_type == prediction_type)
    
    predictions = query.order_by(Prediction.created_at.desc()).limit(limit).all()
    
    return {
        "predictions": [
            {
                "prediction_id": p.id,
                "prediction_type": p.prediction_type,
                "content_hash": p.input_hash,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "expires_at": p.expires_at.isoformat() if p.expires_at else None,
                "confidence_score": float(p.confidence_score) if p.confidence_score else None,
                "model_used": p.model_used,
            }
            for p in predictions
        ],
        "total": len(predictions),
    }


@router.delete("/cache/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cached_prediction(
    prediction_id: str,
    workspace: Workspace | None = Depends(can_use_ai_predict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a cached prediction."""
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    prediction = (
        db.query(Prediction)
        .filter(Prediction.id == prediction_id, Prediction.workspace_id == workspace.id)
        .first()
    )
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    db.delete(prediction)
    db.commit()
    
    return None
