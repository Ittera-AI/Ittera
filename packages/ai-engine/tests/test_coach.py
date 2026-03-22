import pytest

from iterra_ai.coach.engine import EngagementCoach
from iterra_ai.coach.schemas import CoachInput


def test_coach_engine_raises_not_implemented(coach_input):
    engine = EngagementCoach()
    with pytest.raises(NotImplementedError):
        engine.analyze(coach_input)


def test_coach_input_valid():
    inp = CoachInput(content="Great content!", platform="linkedin", goal="engagement")
    assert inp.platform == "linkedin"
    assert inp.goal == "engagement"
