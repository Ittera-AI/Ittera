import json
import os
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from iterra_ai.core.cost_tracker import CostTracker
from iterra_ai.core.exceptions import EngineError, ParseError

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseEngine(ABC, Generic[InputT, OutputT]):
    """Base class for typed Iterra AI engines."""

    def __init__(self, client=None, tracker: CostTracker | None = None) -> None:
        self._client = client
        self._tracker = tracker or CostTracker()

    @abstractmethod
    def generate(self, input: InputT) -> OutputT:
        """Generate a typed output for a typed input."""

    def _call_llm(self, system: str, user: str, max_tokens: int = 2000) -> str:
        try:
            if self._client is None:
                from iterra_ai.core.client import get_anthropic_client

                self._client = get_anthropic_client()
            response = self._client.messages.create(
                model=self._get_model(),
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            usage = getattr(response, "usage", None)
            self._tracker.log(
                engine=self.__class__.__name__,
                input_tokens=getattr(usage, "input_tokens", 0),
                output_tokens=getattr(usage, "output_tokens", 0),
            )
            return response.content[0].text
        except Exception as exc:
            raise EngineError(f"{self.__class__.__name__} failed: {exc}") from exc

    def _parse_json_output(self, raw: str, schema: type[OutputT]) -> OutputT:
        cleaned = self._strip_json_fence(raw)
        try:
            return schema.model_validate_json(cleaned)
        except Exception as exc:
            raise ParseError(f"Failed to parse {schema.__name__}: {exc}\nRaw: {raw}") from exc

    @staticmethod
    def _strip_json_fence(raw: str) -> str:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # Normalizes accidental top-level arrays when a schema expects an object with content_plan.
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return cleaned
        return json.dumps(parsed)

    def _get_model(self) -> str:
        return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
