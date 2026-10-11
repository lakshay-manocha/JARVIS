import pytest

from agent_engine.contracts.enums import ExecutionStatus

from agent_engine.decision_manager.failure_handler import (
    FailureHandler,
)

from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)


@pytest.fixture
def handler() -> FailureHandler:
    return FailureHandler()


def test_generic_exception_becomes_unknown_failure(
    handler: FailureHandler,
) -> None:

    outcome = handler.handle_exception(
        task_id=1,
        exception=RuntimeError("Automation failed"),
    )

    assert outcome.task_id == 1
    assert outcome.status == ExecutionStatus.FAILED
    assert outcome.success is False
    assert outcome.failure_type == FailureType.UNKNOWN
    assert outcome.error_message == "Automation failed"
    assert outcome.attempt == 1
    assert outcome.retry_count == 0
    assert outcome.max_retries == 0


def test_timeout_exception_becomes_timeout_failure(
    handler: FailureHandler,
) -> None:

    outcome = handler.handle_exception(
        task_id=2,
        exception=TimeoutError("Execution timed out"),
        attempt=2,
        retry_count=1,
        max_retries=3,
        timeout_seconds=30.0,
        execution_time=31.2,
    )

    assert outcome.task_id == 2
    assert outcome.status == ExecutionStatus.FAILED
    assert outcome.success is False
    assert outcome.failure_type == FailureType.TIMEOUT
    assert outcome.timed_out is True
    assert outcome.attempt == 2
    assert outcome.retry_count == 1
    assert outcome.max_retries == 3
    assert outcome.timeout_seconds == 30.0
    assert outcome.execution_time == 31.2


def test_existing_successful_outcome_is_preserved(
    handler: FailureHandler,
) -> None:

    outcome = ExecutionOutcome(
        task_id=3,
        status=ExecutionStatus.COMPLETED,
        success=True,
        attempt=1,
        failure_type=FailureType.NONE,
    )

    normalized = handler.normalize_outcome(outcome)

    assert normalized.task_id == 3
    assert normalized.status == ExecutionStatus.COMPLETED
    assert normalized.success is True
    assert normalized.failure_type == FailureType.NONE


def test_unclassified_failed_outcome_becomes_unknown(
    handler: FailureHandler,
) -> None:

    outcome = ExecutionOutcome(
        task_id=4,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        failure_type=FailureType.NONE,
    )

    normalized = handler.normalize_outcome(outcome)

    assert normalized.status == ExecutionStatus.FAILED
    assert normalized.success is False
    assert normalized.failure_type == FailureType.UNKNOWN


def test_timeout_is_detected_from_execution_time(
    handler: FailureHandler,
) -> None:

    outcome = ExecutionOutcome(
        task_id=5,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        timeout_seconds=10.0,
        execution_time=12.5,
        failure_type=FailureType.UNKNOWN,
    )

    normalized = handler.normalize_outcome(outcome)

    assert normalized.status == ExecutionStatus.FAILED
    assert normalized.success is False
    assert normalized.timed_out is True
    assert normalized.failure_type == FailureType.TIMEOUT


def test_original_outcome_is_not_mutated(
    handler: FailureHandler,
) -> None:

    outcome = ExecutionOutcome(
        task_id=6,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        failure_type=FailureType.NONE,
    )

    normalized = handler.normalize_outcome(outcome)

    assert outcome.failure_type == FailureType.NONE
    assert normalized.failure_type == FailureType.UNKNOWN