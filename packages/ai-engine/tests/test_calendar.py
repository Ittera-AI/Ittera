from types import SimpleNamespace

import pytest

from iterra_ai.calendar.engine import CalendarEngine
from iterra_ai.calendar.schemas import CalendarInput
from iterra_ai.core.exceptions import EngineError, ParseError


class FakeMessages:
    def __init__(self, raw: str, should_raise: bool = False) -> None:
        self.raw = raw
        self.should_raise = should_raise

    def create(self, **kwargs):
        if self.should_raise:
            raise RuntimeError("provider unavailable")
        return SimpleNamespace(
            content=[SimpleNamespace(text=self.raw)],
            usage=SimpleNamespace(input_tokens=100, output_tokens=50),
        )


class FakeClient:
    def __init__(self, raw: str, should_raise: bool = False) -> None:
        self.messages = FakeMessages(raw, should_raise=should_raise)


def test_calendar_engine_parses_mocked_llm_response(calendar_input):
    raw = """
    ```json
    {
      "content_plan": [
        {
          "date": "2026-04-15",
          "platform": "linkedin",
          "content_type": "how-to",
          "topic": "AI workflow audits",
          "goal": "education"
        }
      ]
    }
    ```
    """
    engine = CalendarEngine(client=FakeClient(raw))

    output = engine.generate(calendar_input)

    assert output.content_plan[0].topic == "AI workflow audits"


def test_calendar_engine_wraps_provider_errors(calendar_input):
    engine = CalendarEngine(client=FakeClient("{}", should_raise=True))
    with pytest.raises(EngineError):
        engine.generate(calendar_input)


def test_calendar_engine_raises_parse_error(calendar_input):
    engine = CalendarEngine(client=FakeClient("not json"))
    with pytest.raises(ParseError):
        engine.generate(calendar_input)


def test_calendar_input_schema_validation():
    with pytest.raises(Exception):
        CalendarInput(niche=123, platforms="not-a-list", posting_frequency="five")


def test_calendar_input_valid():
    inp = CalendarInput(niche="tech", platforms=["twitter"], posting_frequency=3)
    assert inp.niche == "tech"
    assert inp.posting_frequency == 3
