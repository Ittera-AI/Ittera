"""EXPERIMENTAL — template repurposing until LLM path is production-hardened."""

import os
import json
from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.repurpose.schemas import RepurposedItem, RepurposeInput, RepurposeOutput
from iterra_ai.prompts.repurpose import SYSTEM_PROMPT, REPURPOSE_PROMPT


class RepurposeEngine(BaseEngine[RepurposeInput, RepurposeOutput]):
    """Repurposes content across different social platforms."""

    def generate(self, input: RepurposeInput) -> RepurposeOutput:
        if not os.getenv("ANTHROPIC_API_KEY"):
            return self._mock_repurpose(input)
        
        user_prompt = REPURPOSE_PROMPT.format(
            source_platform=input.source_platform,
            target_platforms=", ".join(input.target_platforms),
            original_content=input.original_content
        )
        
        raw_output = self._call_llm(system=SYSTEM_PROMPT, user=user_prompt, max_tokens=2000)
        
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
        for platform in input.target_platforms:
            if platform == "instagram":
                content = f"{input.original_content}\n\nSave this for your next planning sprint."
                fmt = "caption"
            else:
                content = (
                    f"1/3 {input.original_content[:220]}\n\n"
                    "2/3 Build the loop before chasing volume."
                )
                fmt = "thread"
            items.append(RepurposedItem(platform=platform, content=content, format=fmt))
        return RepurposeOutput(repurposed=items)
