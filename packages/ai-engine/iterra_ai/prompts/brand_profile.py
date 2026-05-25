"""Prompt templates for the BrandProfileEngine."""

SYSTEM_PROMPT = """You are a brand strategist for an AI content strategy platform.
Analyse the creator's posts, weighting higher-engagement posts more heavily.
Return only valid JSON matching the requested schema. Do not include markdown fences."""

BRAND_PROFILE_V1 = """Analyse this creator's niche and posts.

Niche:
{niche}

Posts (ordered by recency, annotated with engagement rate):
{posts}

Instructions:
- voice_tone: Describe their writing voice in 10-15 words (e.g. "Analytical, direct, uses data to challenge assumptions")
- audience: Describe their ideal reader in one sentence
- core_topics: 3-5 recurring themes as short strings
- writing_patterns: 3-4 structural patterns they use (e.g. "Opens with a question", "Bullet-heavy breakdown")
- content_pillars: 3-4 strategic pillars (e.g. "Thought leadership", "How-to systems", "Industry critique")
- hashtag_strategy: A short description of how they use hashtags (or suggest one if none visible)
- summary: 1-2 sentences summarising their content brand
- avg_post_length: The median character count of the posts (integer)
- emoji_usage: One of "none", "occasional" (1-3 per post), "moderate" (4-8), "frequent" (9+)

Return JSON with all keys above."""
