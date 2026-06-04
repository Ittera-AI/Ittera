"""Competitive intelligence module for content strategy analysis.

Provides AI-powered competitor analysis:
1. CompetitiveAnalysisEngine - Main engine for all competitive analysis
2. Strategy Analysis - Deep dive into competitor content strategy
3. Content Gap Analysis - Identify topics and formats you're missing
4. Trend Benchmarking - Compare performance on specific trends

Usage:
    from iterra_ai.competitive import (
        CompetitiveAnalysisEngine,
        CompetitorProfileInput,
        ContentGapAnalysisInput,
        TrendBenchmarkInput,
        get_competitive_engine,
    )
    
    # Analyze competitor strategy
    engine = CompetitiveAnalysisEngine()
    strategy = engine.analyze_competitor_strategy(
        CompetitorProfileInput(
            competitor_id="comp123",
            competitor_name="Competitor Inc",
            platform="linkedin",
            handle="competitor",
            recent_posts=[...],
        )
    )
    
    # Find content gaps
    gaps = engine.analyze_content_gaps(
        ContentGapAnalysisInput(
            author_content_pillars=["AI", "Marketing"],
            competitor_content_themes=["AI", "Marketing", "Sales"],
        )
    )
"""

from iterra_ai.competitive.engine import (
    CompetitiveAnalysisEngine,
    get_competitive_engine,
)
from iterra_ai.competitive.schemas import (
    CompetitorProfileInput,
    CompetitorStrategyOutput,
    ContentGapAnalysisInput,
    ContentGapOutput,
    TrendBenchmarkInput,
    TrendBenchmarkOutput,
)

__all__ = [
    # Engine
    "CompetitiveAnalysisEngine",
    "get_competitive_engine",
    # Input schemas
    "CompetitorProfileInput",
    "ContentGapAnalysisInput",
    "TrendBenchmarkInput",
    # Output schemas
    "CompetitorStrategyOutput",
    "ContentGapOutput",
    "TrendBenchmarkOutput",
]
