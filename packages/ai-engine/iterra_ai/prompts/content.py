CONTENT_GENERATION_USER_PROMPT = """Write a {platform} post.

Request: {prompt}
{hook_line}

Platform formatting rules:
- Target length: ~{target_chars} characters (hard max: {max_chars})
- Hook style: {hook_style}
- CTA style: {cta_style}
- Hashtag density: {hashtag_count_min}–{hashtag_count_max} hashtags
- Paragraph style: {line_break_style}
- Emoji usage: {emoji}

Return only the post text. No explanation, no markdown, no quotes."""
