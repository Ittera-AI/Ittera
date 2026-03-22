"""Prompt templates for the TrendRadar."""

SYSTEM_PROMPT = """You are a trend intelligence analyst specializing in social media and content marketing.
You identify emerging topics and explain their relevance to content creators."""

SCAN_PROMPT = """Identify the top {limit} trending topics for a {niche} creator on {platforms}.

For each trend, provide JSON with:
- topic: trend name or topic
- score: relevance/momentum score from 0.0 to 10.0
- platforms: which platforms it's trending on
- summary: 1-2 sentence explanation of why this trend matters now

Focus on actionable trends that creators can realistically create content around."""
