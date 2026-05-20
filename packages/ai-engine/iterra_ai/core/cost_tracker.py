import logging
from dataclasses import dataclass

logger = logging.getLogger("iterra_ai.cost")

INPUT_COST_PER_1K = 0.003
OUTPUT_COST_PER_1K = 0.015


@dataclass(frozen=True)
class UsageLog:
    engine: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


class CostTracker:
    def log(self, engine: str, input_tokens: int, output_tokens: int) -> UsageLog:
        cost = (input_tokens / 1000 * INPUT_COST_PER_1K) + (
            output_tokens / 1000 * OUTPUT_COST_PER_1K
        )
        entry = UsageLog(
            engine=engine,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
        logger.info(
            "LLM_USAGE engine=%s input_tokens=%d output_tokens=%d cost_usd=%.6f",
            engine,
            input_tokens,
            output_tokens,
            cost,
        )
        return entry
