from iterra_ai.coach.engine import EngagementCoach
from iterra_ai.coach.schemas import CoachInput


def test_coach_engine_returns_mock_analysis(coach_input):
    engine = EngagementCoach()
    output = engine.analyze(coach_input)
    assert output.score > 0
    assert output.suggestions


def test_coach_input_valid():
    inp = CoachInput(content="Great content!", platform="linkedin", goal="engagement")
    assert inp.platform == "linkedin"
    assert inp.goal == "engagement"
