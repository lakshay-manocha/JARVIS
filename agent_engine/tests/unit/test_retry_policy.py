"""
===============================================================================
File Name   : test_retry_policy.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase D-1:
    Tests for deterministic retry behaviour.
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus

from agent_engine.decision_manager.models import (
    DecisionAction,
    ExecutionOutcome,
    FailureType,
)

from agent_engine.decision_manager.retry_policy import (
    RetryPolicy,
)


policy = RetryPolicy()


def make_failed_outcome(
    *,
    failure_type: FailureType,
    attempt: int = 1,
    retry_count: int = 0,
    max_retries: int = 3,
) -> ExecutionOutcome:
    """
    Helper for constructing failed execution outcomes.
    """

    return ExecutionOutcome(
        task_id=1,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=attempt,
        retry_count=retry_count,
        max_retries=max_retries,
        failure_type=failure_type,
        error_message="test failure",
    )


# =============================================================================
# Retryable failures
# =============================================================================


def test_retry_transient_failure() -> None:
    outcome = make_failed_outcome(
        failure_type=FailureType.TRANSIENT,
    )

    result = policy.evaluate(outcome)

    assert result.action == DecisionAction.RETRY
    assert result.task_id == 1
    assert result.attempt == 1
    assert result.max_retries == 3
    assert result.failure_type == FailureType.TRANSIENT


def test_retry_timeout() -> None:
    outcome = make_failed_outcome(
        failure_type=FailureType.TIMEOUT,
        attempt=2,
        retry_count=1,
    )

    result = policy.evaluate(outcome)

    assert result.action == DecisionAction.RETRY
    assert result.failure_type == FailureType.TIMEOUT


# =============================================================================
# Retry limit
# =============================================================================


def test_fail_after_max_retries() -> None:
    outcome = make_failed_outcome(
        failure_type=FailureType.TRANSIENT,
        attempt=4,
        retry_count=3,
        max_retries=3,
    )

    result = policy.evaluate(outcome)

    assert result.action == DecisionAction.FAIL
    assert result.reason == "Maximum retry attempts exhausted."


def test_zero_retries_fails_immediately() -> None:
    outcome = make_failed_outcome(
        failure_type=FailureType.TRANSIENT,
        max_retries=0,
    )

    result = policy.evaluate(outcome)

    assert result.action == DecisionAction.FAIL


# =============================================================================
# Non-retryable failures
# =============================================================================


def test_permanent_failure_does_not_retry() -> None:
    outcome = make_failed_outcome(
        failure_type=FailureType.PERMANENT,
    )

    result = policy.evaluate(outcome)

    assert result.action == DecisionAction.FAIL


def test_validation_failure_does_not_retry() -> None:
    outcome = make_failed_outcome(
        failure_type=FailureType.VALIDATION,
    )

    result = policy.evaluate(outcome)

    assert result.action == DecisionAction.FAIL


def test_dependency_failure_does_not_retry() -> None:
    outcome = make_failed_outcome(
        failure_type=FailureType.DEPENDENCY,
    )

    result = policy.evaluate(outcome)

    assert result.action == DecisionAction.FAIL


def test_unknown_failure_does_not_retry() -> None:
    outcome = make_failed_outcome(
        failure_type=FailureType.UNKNOWN,
    )

    result = policy.evaluate(outcome)

    assert result.action == DecisionAction.FAIL


# =============================================================================
# Successful execution
# =============================================================================


def test_success_returns_complete() -> None:
    outcome = ExecutionOutcome(
        task_id=2,
        status=ExecutionStatus.COMPLETED,
        success=True,
        attempt=1,
        retry_count=0,
        max_retries=3,
    )

    result = policy.evaluate(outcome)

    assert result.action == DecisionAction.COMPLETE
    assert result.failure_type == FailureType.NONE


# =============================================================================
# Determinism
# =============================================================================


def test_decision_is_deterministic() -> None:
    outcome = make_failed_outcome(
        failure_type=FailureType.TRANSIENT,
        attempt=2,
        retry_count=1,
    )

    first = policy.evaluate(outcome)
    second = policy.evaluate(outcome)

    assert first == second