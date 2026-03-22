from iterra_ai.repurpose.schemas import RepurposeInput, RepurposeOutput


class RepurposeEngine:
    """Repurposes content across different social platforms.

    TODO: Implement using LangChain or raw OpenAI SDK.
    See prompts/repurpose.py for prompt templates.
    """

    def repurpose(self, input: RepurposeInput) -> RepurposeOutput:
        """Repurpose content for target platforms.

        Args:
            input: Source content and target platform list.

        Returns:
            RepurposeOutput with platform-adapted content.

        Raises:
            NotImplementedError: Until the engine is implemented.
        """
        # TODO: implement content repurposing using LLM
        raise NotImplementedError(
            "RepurposeEngine.repurpose is not yet implemented. "
            "See iterra_ai/repurpose/engine.py to implement."
        )
