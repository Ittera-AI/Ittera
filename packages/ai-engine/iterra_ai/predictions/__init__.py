"""AI-powered prediction engines for content performance.

This module provides three AI engines for advanced content analysis:

1. PredictorEngine - Content performance prediction with confidence intervals
2. ViralPredictionEngine - Viral potential scoring with pattern detection
3. TimingPredictionEngine - ML-based optimal posting time prediction

Usage:
    from iterra_ai.predictions import (
        ContentInput,
        ContentPredictionOutput,
        PredictorEngine,
        ViralScoreInput,
        ViralPotentialOutput,
        ViralPredictionEngine,
        TimingInput,
        TimingOutput,
        TimingPredictionEngine,
    )
    
    # Performance prediction
    predictor = PredictorEngine()
    prediction = predictor.predict(ContentInput(
        content="Your content here...",
        platform="linkedin",
    ))
    print(f"Predicted engagement rate: {prediction.metrics.engagement_rate}%")
    print(f"Confidence: {prediction.confidence.overall_confidence}")
    
    # Viral analysis
    viral = ViralPredictionEngine()
    viral_score = viral.analyze(ViralScoreInput(
        content="Your content here...",
        platform="linkedin",
    ))
    print(f"Viral probability: {viral_score.viral_probability}")
    print(f"Category: {viral_score.category}")
    
    # Optimal timing
    timing = TimingPredictionEngine()
    best_time = timing.predict(TimingInput(
        content="Your content here...",
        platform="linkedin",
        timezone="America/New_York",
    ))
    print(f"Optimal time: {best_time.optimal_time}")
"""

from iterra_ai.predictions.predictor_engine import (
    PredictorEngine,
    get_predictor_engine,
)
from iterra_ai.predictions.schemas import (
    ConfidenceInterval,
    # Input schemas
    ContentInput,
    # Output schemas
    ContentPredictionOutput,
    FeatureImportance,
    PredictionConfidence,
    # Metric schemas
    PredictionMetrics,
    TimeSlotScore,
    TimingInput,
    TimingOutput,
    TimingPattern,
    ViralPattern,
    ViralPotentialOutput,
    ViralScoreInput,
)
from iterra_ai.predictions.timing_engine import (
    TimingPredictionEngine,
    get_timing_engine,
)
from iterra_ai.predictions.viral_engine import (
    ViralPredictionEngine,
    get_viral_engine,
)

__all__ = [
    # Engines
    "PredictorEngine",
    "ViralPredictionEngine",
    "TimingPredictionEngine",
    # Engine getters
    "get_predictor_engine",
    "get_viral_engine",
    "get_timing_engine",
    # Input schemas
    "ContentInput",
    "ViralScoreInput",
    "TimingInput",
    # Output schemas
    "ContentPredictionOutput",
    "ViralPotentialOutput",
    "TimingOutput",
    # Supporting schemas
    "ViralPattern",
    "TimeSlotScore",
    "TimingPattern",
    "PredictionMetrics",
    "ConfidenceInterval",
    "PredictionConfidence",
    "FeatureImportance",
]
