from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalCase:
    name: str
    input: Any
    expected: Any
    scorer: Callable[[Any, Any], float] | None = None


@dataclass
class EvalResult:
    case: EvalCase
    actual: Any
    score: float
    passed: bool
    error: str | None = None


@dataclass
class EvalReport:
    results: list[EvalResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    @property
    def avg_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)


class EvalRunner:
    """Run evaluation cases against an AI engine function."""

    def __init__(self, engine_fn: Callable[..., Any], pass_threshold: float = 0.7) -> None:
        self.engine_fn = engine_fn
        self.pass_threshold = pass_threshold

    def run(self, cases: list[EvalCase]) -> EvalReport:
        report = EvalReport()
        for case in cases:
            try:
                actual = self.engine_fn(case.input)
                score = case.scorer(actual, case.expected) if case.scorer else 1.0
                report.results.append(
                    EvalResult(case=case, actual=actual, score=score, passed=score >= self.pass_threshold)
                )
            except Exception as exc:
                report.results.append(
                    EvalResult(case=case, actual=None, score=0.0, passed=False, error=str(exc))
                )
        return report
