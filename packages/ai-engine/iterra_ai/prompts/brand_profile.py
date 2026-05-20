"""Prompt templates for the BrandProfileEngine."""

SYSTEM_PROMPT = """You are a brand strategist for an AI content strategy platform.
Return only valid JSON matching the requested schema."""

BRAND_PROFILE_V1 = """Analyze this creator's niche and posts.

Niche:
{niche}

Posts:
{posts}

Return JSON with: voice_tone, audience, core_topics, writing_patterns,
content_pillars, hashtag_strategy, summary."""
