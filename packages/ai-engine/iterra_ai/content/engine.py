import os

from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.content.schemas import ContentGenerationInput, ContentGenerationOutput
from iterra_ai.prompts.content import CONTENT_GENERATION_USER_PROMPT
from iterra_ai.content.platform_rules import format_content


class ContentGenerationEngine(BaseEngine[ContentGenerationInput, ContentGenerationOutput]):
    """Generates context-aware social media posts."""

    def generate(self, input: ContentGenerationInput) -> ContentGenerationOutput:
        hook_line = f"Hook: {input.hook}" if input.hook else ""
        
        user_prompt = CONTENT_GENERATION_USER_PROMPT.format(
            platform=input.platform,
            prompt=input.prompt,
            hook_line=hook_line,
            target_chars=input.platform_rules.get("target_chars", 1000),
            max_chars=input.platform_rules.get("max_chars", 2000),
            hook_style=input.platform_rules.get("hook_style", "engaging"),
            cta_style=input.platform_rules.get("cta_style", "none"),
            hashtag_count_min=input.platform_rules.get("hashtag_count_min", 0),
            hashtag_count_max=input.platform_rules.get("hashtag_count_max", 3),
            line_break_style=input.platform_rules.get("line_break_style", "readable"),
            emoji=input.platform_rules.get("emoji", "minimal"),
        )
        
        # Mock fallback if no API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            return self._mock_generate(input)
        
        # Real generation
        raw = self._call_llm(system=input.system_prompt, user=user_prompt, max_tokens=1000)
        final_content = format_content(raw, input.platform)
        
        return ContentGenerationOutput(
            content=final_content,
            model=self._get_model(),
            is_mock=False,
            word_count=len(final_content.split()),
            char_count=len(final_content),
        )

    def _mock_generate(self, input: ContentGenerationInput) -> ContentGenerationOutput:
        """Structured mock when API key is missing."""
        seed = input.hook if input.hook else input.prompt
        content = (
            f"{seed}\n\n"
            f"Here is the practical version: {input.prompt.strip()}\n\n"
            "The best content systems do three things well:\n"
            "1. Notice the signal before it becomes noisy.\n"
            "2. Shape the idea through a clear point of view.\n"
            "3. Review performance without losing the voice that made it work.\n\n"
            "That is how a content loop compounds."
        )
        
        final_content = format_content(content, input.platform)
        return ContentGenerationOutput(
            content=final_content,
            model="mock-local",
            is_mock=True,
            word_count=len(final_content.split()),
            char_count=len(final_content),
        )
