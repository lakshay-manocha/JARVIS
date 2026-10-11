"""
===============================================================================
File Name   : test_timeout_policy.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase D-2:
    Tests for timeout detection and normalization.
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus

from agent_engine.decision_manager import (
    ExecutionOutcome,
    FailureType,
    TimeoutPolicy,
)


policy = TimeoutPolicy()


# =============================================================================
# Explicit timeout
# =============================================================================


def test_explicit_timeout_is_detected() -> None:
    outcome = ExecutionOutcome(
        task_id=1,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=3,
        timeout_seconds=30,
        execution_time=25,
        timed_out=True,
    )

    assert policy.is_timeout(outcome) is True


def test_explicit_timeout_is_normalized() -> None:
    outcome = ExecutionOutcome(
        task_id=1,
        status=ExecutionStatus.RUNNING,
        success=True,
        attempt=1,
        retry_count=0,
        max_retries=3,
        timeout_seconds=30,
        execution_time=35,
        timed_out=True,
    )

    normalized = policy.normalize(outcome)

    assert normalized.timed_out is True
    assert normalized.success is False
    assert normalized.status == ExecutionStatus.FAILED
    assert normalized.failure_type == FailureType.TIMEOUT


# =============================================================================
# Timeout based on execution duration
# =============================================================================


def test_execution_time_exceeding_timeout_is_detected() -> None:
    outcome = ExecutionOutcome(
        task_id=2,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=3,
        timeout_seconds=30,
        execution_time=31,
    )

    assert policy.is_timeout(outcome) is True


def test_execution_time_exceeding_timeout_is_normalized() -> None:
    outcome = ExecutionOutcome(
        task_id=2,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=3,
        timeout_seconds=30,
        execution_time=31,
        failure_type=FailureType.UNKNOWN,
    )

    normalized = policy.normalize(outcome)

    assert normalized.timed_out is True
    assert normalized.failure_type == FailureType.TIMEOUT
    assert normalized.success is False
    assert normalized.status == ExecutionStatus.FAILED


# =============================================================================
# Boundary condition
# =============================================================================


def test_execution_time_equal_to_timeout_is_not_timeout() -> None:
    outcome = ExecutionOutcome(
        task_id=3,
        status=ExecutionStatus.COMPLETED,
        success=True,
        attempt=1,
        retry_count=0,
        max_retries=3,
        timeout_seconds=30,
        execution_time=30,
    )

    assert policy.is_timeout(outcome) is False


# =============================================================================
# Normal execution
# =============================================================================


def test_execution_within_timeout_is_not_timeout() -> None:
    outcome = ExecutionOutcome(
        task_id=4,
        status=ExecutionStatus.COMPLETED,
        success=True,
        attempt=1,
        retry_count=0,
        max_retries=3,
        timeout_seconds=30,
        execution_time=12,
    )

    assert policy.is_timeout(outcome) is False


def test_non_timeout_outcome_is_not_modified() -> None:
    outcome = ExecutionOutcome(
        task_id=5,
        status=ExecutionStatus.COMPLETED,
        success=True,
        attempt=1,
        retry_count=0,
        max_retries=3,
        timeout_seconds=30,
        execution_time=20,
        failure_type=FailureType.NONE,
    )

    normalized = policy.normalize(outcome)

    assert normalized == outcome
    assert normalized is not outcome