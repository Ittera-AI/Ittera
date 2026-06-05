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

Return a JSON array with: platform, content (adapted text), format
(e.g., "tweet-thread", "linkedin-post")."""

REPURPOSE_PROMPT_WITH_LIMIT = """Repurpose the following {source_platform} content for {target_platforms}.

IMPORTANT: The target platform has a strict character limit of {max_chars} characters.
The repurposed content MUST be {max_chars} characters or fewer. Do NOT exceed this limit.

Original content:
{original_content}

For each target platform, adapt the content to match:
- Character limit: {max_chars} characters maximum
- Tone and format expectations
- Platform-specific features (hashtags, threads, carousels, etc.)
- Native engagement patterns
- Preserve the core message while fitting within the character constraint

Return a JSON array with: platform, content (adapted text), format
(e.g., "tweet", "tweet-thread", "linkedin-post")."""
