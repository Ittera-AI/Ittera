import json
import os
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from iterra_ai.core.cost_tracker import CostTracker, get_request_id
from iterra_ai.core.exceptions import EngineError, ParseError

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseEngine(ABC, Generic[InputT, OutputT]):
    """Base class for typed Iterra AI engines."""

    def __init__(self, client: Any = None, tracker: CostTracker | None = None) -> None:
        self._client = client
        self._tracker = tracker or CostTracker()

    @abstractmethod
    def generate(self, input: InputT) -> OutputT:
        """Generate a typed output for a typed input."""

    def _call_llm(
        self,
        system: str,
        user: str,
        max_tokens: int = 2000,
        temperature: float | None = None,
    ) -> str:
        try:
            if self._client is None:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=os.getenv("AIML_API_KEY"),
                    base_url=os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1"),
                )
            request = {
                "model": self._get_model(),
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
            if temperature is not None:
                request["temperature"] = temperature
            if hasattr(self._client, "chat"):
                response = self._client.chat.completions.create(**request)
                usage = getattr(response, "usage", None)
                message = response.choices[0].message if response.choices else None
                raw_response_text = getattr(message, "content", "")
                response_text = (
                    raw_response_text if isinstance(raw_response_text, str) else ""
                )
                input_tokens = getattr(usage, "prompt_tokens", 0)
                output_tokens = getattr(usage, "completion_tokens", 0)
            else:
                response = self._client.messages.create(
                    model=request["model"],
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                usage = getattr(response, "usage", None)
                raw_response_text = (
                    response.content[0].text
                    if getattr(response, "content", None)
                    else ""
                )
                response_text = (
                    raw_response_text if isinstance(raw_response_text, str) else ""
                )
                input_tokens = getattr(usage, "input_tokens", 0)
                output_tokens = getattr(usage, "output_tokens", 0)
            self._tracker.log(
                engine=self.__class__.__name__,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_id=get_request_id(),
            )
            return response_text
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
        configured_model = getattr(self, "model", None)
        if isinstance(configured_model, str) and configured_model:
            return configured_model
        return os.getenv("AIML_MODEL") or "gpt-4o-mini"
