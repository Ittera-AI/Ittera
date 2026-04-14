from iterra_ai.coach.schemas import CoachInput, CoachOutput
from iterra_ai.core.base_engine import BaseEngine


class EngagementCoach(BaseEngine[CoachInput, CoachOutput]):
    """Analyzes content and provides engagement improvement suggestions.

    TODO: Implement using LangChain or raw OpenAI SDK.
    See prompts/coach.py for prompt templates.
    """

    def analyze(self, input: CoachInput) -> CoachOutput:
        return CoachOutput(
            score=8.4,
            suggestions=[
                "Open with a sharper tension line.",
                "Add one concrete example before the final insight.",
                "End with a question that invites replies.",
            ],
            summary="Strong strategic clarity with room for a more conversational ending.",
        )

    def generate(self, input: CoachInput) -> CoachOutput:
        return self.analyze(input)
