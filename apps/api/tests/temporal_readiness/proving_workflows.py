"""Harmless proving workflows for the shared Temporal readiness exercise.

These workflows are conformance fixtures only. They do not implement publishing,
provider synchronization, target tenancy, or any other production workflow.
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError


@dataclass(frozen=True)
class ReadinessInput:
    """Only stable, non-sensitive references and bounded timing enter history."""

    operation_id: str
    timer_seconds: int
    approval_timeout_seconds: int


@dataclass(frozen=True)
class ReadinessResult:
    status: str
    operation_id: str
    approval_id: str | None
    approval_signal_count: int
    remote_id: str | None


class SimulatedRemoteService:
    """In-memory remote-effect simulator with an idempotency key.

    The first call commits one logical remote effect and then loses its response.
    A retry with the same operation ID reconciles to the existing remote ID.
    """

    def __init__(self) -> None:
        self.attempt_count = 0
        self.effects: dict[str, str] = {}
        self.response_recovered = asyncio.Event()

    @activity.defn(name="temporal_readiness_remote_operation")
    async def execute(self, operation_id: str) -> str:
        self.attempt_count += 1
        existing_remote_id = self.effects.get(operation_id)
        if existing_remote_id is not None:
            self.response_recovered.set()
            return existing_remote_id

        self.effects[operation_id] = f"remote:{operation_id}"
        raise ApplicationError(
            "The simulated remote effect succeeded before its response was lost",
            type="SimulatedResponseLost",
        )


@workflow.defn(name="TemporalReadinessWorkflow")
class TemporalReadinessWorkflow:
    """Exercise timer, Signals, retry, timeout, restart, and ambiguous effects."""

    def __init__(self) -> None:
        self._approval_id: str | None = None
        self._approval_signal_count = 0
        self._finish_requested = False

    @workflow.signal(name="approve")
    def approve(self, approval_id: str) -> None:
        self._approval_signal_count += 1
        if self._approval_id is None:
            self._approval_id = approval_id

    @workflow.signal(name="finish")
    def finish(self) -> None:
        self._finish_requested = True

    @workflow.run
    async def run(self, readiness_input: ReadinessInput) -> ReadinessResult:
        await workflow.sleep(timedelta(seconds=readiness_input.timer_seconds))

        try:
            await workflow.wait_condition(
                lambda: self._approval_id is not None,
                timeout=timedelta(
                    seconds=readiness_input.approval_timeout_seconds
                ),
                timeout_summary="wait-for-readiness-approval",
            )
        except asyncio.TimeoutError:
            return ReadinessResult(
                status="approval_timed_out",
                operation_id=readiness_input.operation_id,
                approval_id=None,
                approval_signal_count=self._approval_signal_count,
                remote_id=None,
            )

        remote_id = await workflow.execute_activity(
            "temporal_readiness_remote_operation",
            readiness_input.operation_id,
            result_type=str,
            start_to_close_timeout=timedelta(seconds=5),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(milliseconds=10),
                maximum_attempts=3,
            ),
        )
        await workflow.wait_condition(lambda: self._finish_requested)

        return ReadinessResult(
            status="completed",
            operation_id=readiness_input.operation_id,
            approval_id=self._approval_id,
            approval_signal_count=self._approval_signal_count,
            remote_id=remote_id,
        )


@workflow.defn(name="TemporalReadinessEvolution")
class TemporalReadinessEvolutionV1:
    """Original workflow retained only to produce pre-change replay history."""

    @workflow.run
    async def run(self) -> str:
        await workflow.sleep(timedelta(seconds=1))
        return "v1"


@workflow.defn(name="TemporalReadinessEvolution")
class TemporalReadinessEvolutionV2:
    """Compatible evolution that preserves the old replay branch."""

    @workflow.run
    async def run(self) -> str:
        await workflow.sleep(timedelta(seconds=1))
        if workflow.patched("temporal-readiness-evolution-v2"):
            return "v2"
        return "v1"
