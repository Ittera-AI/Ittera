class EngineError(RuntimeError):
    """Raised when an AI engine cannot complete a generation."""


class ParseError(EngineError):
    """Raised when an LLM response cannot be parsed into the expected schema."""


class RateLimitError(EngineError):
    """Raised when an upstream LLM provider rate-limits the request."""
