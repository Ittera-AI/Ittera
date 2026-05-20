import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_anthropic_client():
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("Install the anthropic package to use Iterra AI engines.") from exc

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
    return Anthropic(api_key=api_key)
