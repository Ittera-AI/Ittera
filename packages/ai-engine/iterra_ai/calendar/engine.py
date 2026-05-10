"""Calendar engine — LLM-backed when keys are configured; keep evals in sync with prompt changes."""

from iterra_ai.calendar.schemas import CalendarInput, CalendarOutput
from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.prompts.calendar import GENERATE_CALENDAR_PROMPT, SYSTEM_PROMPT


class CalendarEngine(BaseEngine[CalendarInput, CalendarOutput]):
    """Generates AI-powered content calendars.

    TODO: Implement using LangChain or raw OpenAI SDK.
    See prompts/calendar.py for prompt templates.
    """

    def generate(self, input: CalendarInput) -> CalendarOutput:
        prompt = GENERATE_CALENDAR_PROMPT.format(
            niche=input.niche,
            platforms=", ".join(input.platforms),
            posting_frequency=input.posting_frequency,
            historical_posts="\n".join(input.historical_posts) or "None provided",
        )
        raw = self._call_llm(system=SYSTEM_PROMPT, user=prompt)
        return self._parse_json_output(raw, CalendarOutput)
