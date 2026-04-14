from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.repurpose.schemas import RepurposedItem, RepurposeInput, RepurposeOutput


class RepurposeEngine(BaseEngine[RepurposeInput, RepurposeOutput]):
    """Repurposes content across different social platforms.

    TODO: Implement using LangChain or raw OpenAI SDK.
    See prompts/repurpose.py for prompt templates.
    """

    def repurpose(self, input: RepurposeInput) -> RepurposeOutput:
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

    def generate(self, input: RepurposeInput) -> RepurposeOutput:
        return self.repurpose(input)
