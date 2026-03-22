"""Prompt templates for the EngagementCoach."""

SYSTEM_PROMPT = """You are an expert social media engagement coach.
You analyze content and provide actionable, specific suggestions to improve engagement."""

ANALYZE_PROMPT = """Analyze this {platform} post for engagement potential{goal_context}.

Content:
{content}

Evaluate and respond with JSON containing:
- score: engagement score from 0.0 to 10.0
- suggestions: list of 3-5 specific, actionable improvement suggestions
- summary: 1-2 sentence overall assessment

Focus on: hook strength, clarity, call-to-action, emotional resonance, platform fit."""
