PLATFORM_RULES = {
    "linkedin": {
        "max_chars": 3000,
        "target_chars": 1200,
        "hook_style": "direct_statement_or_question",
        "cta_style": "soft_question",
        "hashtag_count_min": 3,
        "hashtag_count_max": 5,
        "line_break_style": "short_paragraphs",
        "emoji": "minimal",
    },
    "instagram": {
        "max_chars": 2200,
        "target_chars": 800,
        "hook_style": "lifestyle_opener",
        "cta_style": "save_or_share",
        "hashtag_count_min": 5,
        "hashtag_count_max": 15,
        "line_break_style": "visual_spacing",
        "emoji": "moderate",
    },
    "twitter": {
        "max_chars": 280,
        "target_chars": 240,
        "hook_style": "punchy_claim",
        "cta_style": "none",
        "hashtag_count_min": 0,
        "hashtag_count_max": 2,
        "line_break_style": "single_line",
        "emoji": "none",
    },
}

def get_rules(platform: str) -> dict:
    return PLATFORM_RULES.get(platform, PLATFORM_RULES["linkedin"])

def format_content(content: str, platform: str, ctx=None) -> str:
    """Post-processes LLM output according to platform rules."""
    rules = get_rules(platform)
    max_chars = rules["max_chars"]
    
    cleaned = content.strip()
    
    # 1. Enforce hard character limit by truncating at last sentence boundary if needed
    if len(cleaned) > max_chars:
        truncated = cleaned[:max_chars]
        last_period = truncated.rfind(".")
        last_question = truncated.rfind("?")
        last_exclamation = truncated.rfind("!")
        
        last_boundary = max(last_period, last_question, last_exclamation)
        
        if last_boundary > 0:
            cleaned = truncated[:last_boundary + 1]
        else:
            # Fallback to word boundary
            last_space = truncated.rfind(" ")
            if last_space > 0:
                cleaned = truncated[:last_space] + "..."
            else:
                cleaned = truncated
    
    return cleaned
