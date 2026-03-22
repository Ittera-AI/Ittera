import pytest


@pytest.fixture()
def calendar_input():
    from iterra_ai.calendar.schemas import CalendarInput
    return CalendarInput(
        niche="technology",
        platforms=["twitter", "linkedin"],
        posting_frequency=5,
        historical_posts=["Thread on AI trends", "LinkedIn post about Python tips"],
    )


@pytest.fixture()
def repurpose_input():
    from iterra_ai.repurpose.schemas import RepurposeInput
    return RepurposeInput(
        original_content="10 things I learned about Python this year...",
        source_platform="twitter",
        target_platforms=["linkedin", "instagram"],
    )


@pytest.fixture()
def coach_input():
    from iterra_ai.coach.schemas import CoachInput
    return CoachInput(content="Check out my new post!", platform="twitter")


@pytest.fixture()
def radar_input():
    from iterra_ai.radar.schemas import RadarInput
    return RadarInput(niche="technology", platforms=["twitter", "linkedin"])
