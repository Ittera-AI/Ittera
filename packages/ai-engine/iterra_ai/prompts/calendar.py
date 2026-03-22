"""Prompt templates for the CalendarEngine."""

SYSTEM_PROMPT = """You are an expert content strategist specializing in social media planning.
Your goal is to create a detailed, actionable content calendar tailored to the user's niche and goals."""

GENERATE_CALENDAR_PROMPT = """Create a {posting_frequency}-post content calendar for a {niche} creator.

Target platforms: {platforms}
Historical posts (for context and style matching): {historical_posts}

Return a JSON array of content slots with these fields:
- date: ISO 8601 date string (YYYY-MM-DD)
- platform: target platform name
- content_type: type of content (e.g., "how-to", "story", "poll", "carousel", "video")
- topic: specific content topic
- goal: primary goal (e.g., "engagement", "awareness", "conversion", "education")

Generate diverse, high-value content that fits the platform's native format."""
