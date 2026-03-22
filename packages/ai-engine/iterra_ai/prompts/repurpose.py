"""Prompt templates for the RepurposeEngine."""

SYSTEM_PROMPT = """You are an expert content repurposing specialist.
You adapt content for different social platforms while preserving the core message and value."""

REPURPOSE_PROMPT = """Repurpose the following {source_platform} content for {target_platforms}.

Original content:
{original_content}

For each target platform, adapt the content to match:
- Character/word limits
- Tone and format expectations
- Platform-specific features (hashtags, threads, carousels, etc.)
- Native engagement patterns

Return a JSON array with: platform, content (adapted text), format (e.g., "tweet-thread", "linkedin-post")."""
