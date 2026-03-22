import pytest

from iterra_ai.calendar.engine import CalendarEngine
from iterra_ai.calendar.schemas import CalendarInput


def test_calendar_engine_raises_not_implemented(calendar_input):
    engine = CalendarEngine()
    with pytest.raises(NotImplementedError):
        engine.generate(calendar_input)


def test_calendar_input_schema_validation():
    with pytest.raises(Exception):
        CalendarInput(niche=123, platforms="not-a-list", posting_frequency="five")


def test_calendar_input_valid():
    inp = CalendarInput(niche="tech", platforms=["twitter"], posting_frequency=3)
    assert inp.niche == "tech"
    assert inp.posting_frequency == 3
