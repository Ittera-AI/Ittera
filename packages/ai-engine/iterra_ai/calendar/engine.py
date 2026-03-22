from iterra_ai.calendar.schemas import CalendarInput, CalendarOutput


class CalendarEngine:
    """Generates AI-powered content calendars.

    TODO: Implement using LangChain or raw OpenAI SDK.
    See prompts/calendar.py for prompt templates.
    """

    def generate(self, input: CalendarInput) -> CalendarOutput:
        """Generate a content calendar from the given input.

        Args:
            input: Structured calendar generation parameters.

        Returns:
            CalendarOutput with a list of ContentSlot items.

        Raises:
            NotImplementedError: Until the engine is implemented.
        """
        # TODO: implement calendar generation using LLM
        raise NotImplementedError(
            "CalendarEngine.generate is not yet implemented. "
            "See iterra_ai/calendar/engine.py to implement."
        )
