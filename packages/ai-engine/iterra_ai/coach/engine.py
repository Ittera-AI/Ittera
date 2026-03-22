from iterra_ai.coach.schemas import CoachInput, CoachOutput


class EngagementCoach:
    """Analyzes content and provides engagement improvement suggestions.

    TODO: Implement using LangChain or raw OpenAI SDK.
    See prompts/coach.py for prompt templates.
    """

    def analyze(self, input: CoachInput) -> CoachOutput:
        """Analyze content and return engagement coaching feedback.

        Args:
            input: Content and platform context.

        Returns:
            CoachOutput with score, suggestions, and summary.

        Raises:
            NotImplementedError: Until the engine is implemented.
        """
        # TODO: implement engagement analysis using LLM
        raise NotImplementedError(
            "EngagementCoach.analyze is not yet implemented. "
            "See iterra_ai/coach/engine.py to implement."
        )
