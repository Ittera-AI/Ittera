"""Shared Checkpoint 1 Temporal readiness conformance tests."""

import asyncio
import uuid
from datetime import timedelta

import pytest
from google.protobuf.message import Message
from temporalio.client import WorkflowFailureError
from temporalio.exceptions import CancelledError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker

from tests.temporal_readiness.proving_workflows import (
    ReadinessInput,
    SimulatedRemoteService,
    TemporalReadinessEvolutionV1,
    TemporalReadinessEvolutionV2,
    TemporalReadinessWorkflow,
)


def _task_queue() -> str:
    return f"temporal-readiness-{uuid.uuid4()}"


def _workflow_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _payload_data(message: Message):
    """Yield serialized payload bytes from an arbitrary history protobuf."""
    if message.DESCRIPTOR.full_name == "temporal.api.common.v1.Payload":
        yield message.data
        return

    for field, value in message.ListFields():
        if field.message_type is None:
            continue
        if field.label == field.LABEL_REPEATED:
            for item in value:
                if isinstance(item, Message):
                    yield from _payload_data(item)
        elif isinstance(value, Message):
            yield from _payload_data(value)


@pytest.mark.asyncio
async def test_retry_restart_replay_signal_timer_and_safe_history() -> None:
    """One scenario proves the high-risk failure/recovery readiness cases."""
    service = SimulatedRemoteService()
    queue = _task_queue()
    operation_id = "readiness-operation-001"

    async with await WorkflowEnvironment.start_time_skipping() as environment:
        first_worker = Worker(
            environment.client,
            task_queue=queue,
            workflows=[TemporalReadinessWorkflow],
            activities=[service.execute],
            max_cached_workflows=0,
        )
        async with first_worker:
            handle = await environment.client.start_workflow(
                TemporalReadinessWorkflow.run,
                ReadinessInput(
                    operation_id=operation_id,
                    timer_seconds=3600,
                    approval_timeout_seconds=7200,
                ),
                id=_workflow_id("restart"),
                task_queue=queue,
            )
            await handle.signal("approve", "approval-001")
            await handle.signal("approve", "approval-001")
            await environment.sleep(timedelta(hours=1))
            await asyncio.wait_for(service.response_recovered.wait(), timeout=10)

            assert service.attempt_count == 2
            assert service.effects == {operation_id: f"remote:{operation_id}"}

        # The workflow is still open while no worker polls its queue. A second
        # worker must recover from history rather than repeat the remote effect.
        second_worker = Worker(
            environment.client,
            task_queue=queue,
            workflows=[TemporalReadinessWorkflow],
            activities=[service.execute],
            max_cached_workflows=0,
        )
        async with second_worker:
            await handle.signal("finish")
            result = await handle.result()

        assert result.status == "completed"
        assert result.approval_id == "approval-001"
        assert result.approval_signal_count == 2
        assert result.remote_id == f"remote:{operation_id}"
        assert service.attempt_count == 2
        assert len(service.effects) == 1

        history = await handle.fetch_history()
        replay = await Replayer(
            workflows=[TemporalReadinessWorkflow]
        ).replay_workflow(history)
        assert replay.replay_failure is None

        payloads = [
            payload
            for event in history.events
            for payload in _payload_data(event)
        ]
        assert payloads
        assert max(map(len, payloads)) < 4096
        serialized_payloads = b"".join(payloads).lower()
        for forbidden in (
            b"access_token",
            b"refresh_token",
            b"client_secret",
            b"password",
            b"credential",
        ):
            assert forbidden not in serialized_payloads


@pytest.mark.asyncio
async def test_approval_timeout_is_typed_and_has_no_remote_effect() -> None:
    service = SimulatedRemoteService()
    queue = _task_queue()

    async with await WorkflowEnvironment.start_time_skipping() as environment:
        async with Worker(
            environment.client,
            task_queue=queue,
            workflows=[TemporalReadinessWorkflow],
            activities=[service.execute],
        ):
            result = await environment.client.execute_workflow(
                TemporalReadinessWorkflow.run,
                ReadinessInput(
                    operation_id="timed-out-operation",
                    timer_seconds=1,
                    approval_timeout_seconds=60,
                ),
                id=_workflow_id("timeout"),
                task_queue=queue,
            )

    assert result.status == "approval_timed_out"
    assert result.remote_id is None
    assert service.attempt_count == 0
    assert service.effects == {}


@pytest.mark.asyncio
async def test_cancellation_stops_before_remote_effect() -> None:
    service = SimulatedRemoteService()
    queue = _task_queue()

    async with await WorkflowEnvironment.start_time_skipping() as environment:
        async with Worker(
            environment.client,
            task_queue=queue,
            workflows=[TemporalReadinessWorkflow],
            activities=[service.execute],
        ):
            handle = await environment.client.start_workflow(
                TemporalReadinessWorkflow.run,
                ReadinessInput(
                    operation_id="cancelled-operation",
                    timer_seconds=86400,
                    approval_timeout_seconds=60,
                ),
                id=_workflow_id("cancel"),
                task_queue=queue,
            )
            await handle.cancel(reason="readiness cancellation exercise")
            with pytest.raises(WorkflowFailureError) as exc_info:
                await handle.result()

    assert isinstance(exc_info.value.cause, CancelledError)
    assert service.attempt_count == 0
    assert service.effects == {}


@pytest.mark.asyncio
async def test_patched_code_replays_old_history_and_runs_new_branch() -> None:
    queue = _task_queue()

    async with await WorkflowEnvironment.start_time_skipping() as environment:
        async with Worker(
            environment.client,
            task_queue=queue,
            workflows=[TemporalReadinessEvolutionV1],
        ):
            old_handle = await environment.client.start_workflow(
                TemporalReadinessEvolutionV1.run,
                id=_workflow_id("evolution-v1"),
                task_queue=queue,
            )
            assert await old_handle.result() == "v1"

        old_history = await old_handle.fetch_history()
        replay = await Replayer(
            workflows=[TemporalReadinessEvolutionV2]
        ).replay_workflow(old_history)
        assert replay.replay_failure is None

        async with Worker(
            environment.client,
            task_queue=queue,
            workflows=[TemporalReadinessEvolutionV2],
        ):
            assert (
                await environment.client.execute_workflow(
                    TemporalReadinessEvolutionV2.run,
                    id=_workflow_id("evolution-v2"),
                    task_queue=queue,
                )
                == "v2"
            )
