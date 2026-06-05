"""EXPERIMENTAL — template repurposing until LLM path is production-hardened."""

import json
import os
from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.repurpose.schemas import RepurposedItem, RepurposeInput, RepurposeOutput
from iterra_ai.prompts.repurpose import SYSTEM_PROMPT, REPURPOSE_PROMPT, REPURPOSE_PROMPT_WITH_LIMIT


class RepurposeEngine(BaseEngine[RepurposeInput, RepurposeOutput]):
    """Repurposes content across different social platforms."""

    def repurpose(self, input: RepurposeInput) -> RepurposeOutput:
        return self.generate(input)

    def generate(self, input: RepurposeInput) -> RepurposeOutput:
        if not self._client and not os.getenv("AIML_API_KEY"):
            return self._mock_repurpose(input)
        
        # Use brand voice system prompt if provided, otherwise default
        system = input.system_prompt if input.system_prompt else SYSTEM_PROMPT
        
        # Use limit-aware prompt template when max_chars is specified
        if input.max_chars:
            user_prompt = REPURPOSE_PROMPT_WITH_LIMIT.format(
                source_platform=input.source_platform,
                target_platforms=", ".join(input.target_platforms),
                original_content=input.original_content,
                max_chars=input.max_chars,
            )
        else:
            user_prompt = REPURPOSE_PROMPT.format(
                source_platform=input.source_platform,
                target_platforms=", ".join(input.target_platforms),
                original_content=input.original_content,
            )
        
        raw_output = self._call_llm(system=system, user=user_prompt, max_tokens=2000)
        
        # We asked for a JSON array in the prompt.
        try:
            # strip possible fences or non-json prefixes
            cleaned = self._strip_json_fence(raw_output)
            data = json.loads(cleaned)
            items = []
            for item in data:
                items.append(
                    RepurposedItem(
                        platform=item.get("platform", "unknown"),
                        content=item.get("content", ""),
                        format=item.get("format", "post")
                    )
                )
            return RepurposeOutput(repurposed=items)
        except Exception as e:
            # Fallback if parsing fails
            return self._mock_repurpose(input)

    def _mock_repurpose(self, input: RepurposeInput) -> RepurposeOutput:
        items = []
        max_chars = input.max_chars or 280
        for platform in input.target_platforms:
            if platform == "instagram":
                content = f"{input.original_content}\n\nSave this for your next planning sprint."
                fmt = "caption"
            elif platform == "twitter" and max_chars <= 280:
                # Respect character limit in mock output
                truncated = input.original_content[:max_chars - 3] + "..." if len(input.original_content) > max_chars else input.original_content
                content = truncated[:max_chars]
                fmt = "tweet"
            else:
                # Premium Twitter or other — fit within limit
                content = input.original_content[:max_chars] if len(input.original_content) > max_chars else input.original_content
                fmt = "post"
            items.append(RepurposedItem(platform=platform, content=content, format=fmt))
        return RepurposeOutput(repurposed=items)
