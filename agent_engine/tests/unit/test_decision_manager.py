"""
===============================================================================
File Name   : test_decision_manager.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase D-1:
    Tests for the Decision Manager entry point.

Phase D-4:
    Tests for dependency-based skip decisions.

Phase D-5:
    Tests for fallback/recovery decisions.
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus, ToolType
from agent_engine.contracts.task import Task

from agent_engine.decision_manager import (
    DecisionAction,
    DecisionManager,
    DecisionResult,
    ExecutionOutcome,
    FailureType,
)
from agent_engine.decision_manager.models.fallback import FallbackOption


def test_decision_manager_delegates_retry_decision() -> None:
    manager = DecisionManager()

    outcome = ExecutionOutcome(
        task_id=10,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=2,
        failure_type=FailureType.TRANSIENT,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.RETRY
    assert result.task_id == 10


def test_decision_manager_returns_failure_for_non_retryable_error() -> None:
    manager = DecisionManager()

    outcome = ExecutionOutcome(
        task_id=11,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=3,
        failure_type=FailureType.PERMANENT,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.FAIL


def test_timeout_with_retry_available_returns_retry() -> None:
    manager = DecisionManager()

    outcome = ExecutionOutcome(
        task_id=20,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=3,
        timeout_seconds=30,
        execution_time=45,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.RETRY
    assert result.task_id == 20
    assert result.failure_type == FailureType.TIMEOUT


def test_timeout_after_retries_exhausted_returns_fail() -> None:
    manager = DecisionManager()

    outcome = ExecutionOutcome(
        task_id=21,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=4,
        retry_count=3,
        max_retries=3,
        timeout_seconds=30,
        execution_time=45,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.FAIL
    assert result.task_id == 21
    assert result.failure_type == FailureType.TIMEOUT


def test_explicit_timeout_returns_retry() -> None:
    manager = DecisionManager()

    outcome = ExecutionOutcome(
        task_id=22,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=2,
        retry_count=1,
        max_retries=3,
        timeout_seconds=60,
        execution_time=40,
        timed_out=True,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.RETRY
    assert result.failure_type == FailureType.TIMEOUT


def test_permanent_failure_is_not_retried() -> None:
    manager = DecisionManager()

    outcome = ExecutionOutcome(
        task_id=30,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=3,
        failure_type=FailureType.PERMANENT,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.FAIL


def test_validation_failure_is_not_retried() -> None:
    manager = DecisionManager()

    outcome = ExecutionOutcome(
        task_id=31,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=3,
        failure_type=FailureType.VALIDATION,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.FAIL


def test_dependency_failure_results_in_skip() -> None:
    manager = DecisionManager()

    outcome = ExecutionOutcome(
        task_id=32,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=3,
        failure_type=FailureType.DEPENDENCY,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.SKIP


def test_decision_manager_skips_task_with_failed_dependency() -> None:
    manager = DecisionManager()

    task = Task(
        id=40,
        description="Dependent task",
        action="test_action",
        tool=list(ToolType)[0],
        depends_on=[10],
    )

    states = {
        10: ExecutionStatus.FAILED,
    }

    result = manager.evaluate_dependencies(
        task,
        states,
    )

    assert result.action == DecisionAction.SKIP
    assert result.task_id == 40
    assert result.failure_type == FailureType.DEPENDENCY


def test_decision_manager_selects_fallback() -> None:
    manager = DecisionManager()

    task = Task(
        id=50,
        description="Fallback test task",
        action="primary_action",
        tool=list(ToolType)[0],
    )

    fallback = FallbackOption(
        id="fallback_1",
        action="alternative_action",
        priority=1,
    )

    result = manager.evaluate_fallback(
        task,
        [fallback],
    )

    assert result.task_id == 50
    assert result.action == DecisionAction.FALLBACK
    assert result.selected_fallback is not None
    assert result.selected_fallback.id == "fallback_1"
    assert result.selected_fallback.action == "alternative_action"

# =============================================================================
# D-7: Decision Priority
# =============================================================================


def test_decision_manager_prioritizes_retry_over_failure() -> None:
    manager = DecisionManager()

    retry = DecisionResult(
        action=DecisionAction.RETRY,
        task_id=60,
        reason="Retryable failure.",
        attempt=1,
        max_retries=3,
        failure_type=FailureType.TRANSIENT,
    )

    fail = DecisionResult(
        action=DecisionAction.FAIL,
        task_id=60,
        reason="Permanent failure.",
        attempt=1,
        max_retries=3,
        failure_type=FailureType.PERMANENT,
    )

    result = manager.prioritize(
        [fail, retry],
    )

    assert result is retry
    assert result.action == DecisionAction.RETRY


def test_decision_manager_prioritizes_fallback_over_failure() -> None:
    manager = DecisionManager()

    fallback = DecisionResult(
        action=DecisionAction.FALLBACK,
        task_id=61,
        reason="Fallback available.",
        attempt=1,
        max_retries=3,
        failure_type=FailureType.NONE,
    )

    fail = DecisionResult(
        action=DecisionAction.FAIL,
        task_id=61,
        reason="Task failed.",
        attempt=1,
        max_retries=3,
        failure_type=FailureType.PERMANENT,
    )

    result = manager.prioritize(
        [fail, fallback],
    )

    assert result is fallback
    assert result.action == DecisionAction.FALLBACK


def test_decision_manager_prioritizes_abort_over_all_decisions() -> None:
    manager = DecisionManager()

    decisions = [
        DecisionResult(
            action=DecisionAction.FAIL,
            task_id=62,
            reason="Failure.",
            attempt=1,
            max_retries=3,
            failure_type=FailureType.PERMANENT,
        ),
        DecisionResult(
            action=DecisionAction.FALLBACK,
            task_id=62,
            reason="Fallback.",
            attempt=1,
            max_retries=3,
            failure_type=FailureType.NONE,
        ),
        DecisionResult(
            action=DecisionAction.RETRY,
            task_id=62,
            reason="Retry.",
            attempt=1,
            max_retries=3,
            failure_type=FailureType.TRANSIENT,
        ),
        DecisionResult(
            action=DecisionAction.COMPLETE,
            task_id=62,
            reason="Completed.",
            attempt=1,
            max_retries=3,
            failure_type=FailureType.NONE,
        ),
        DecisionResult(
            action=DecisionAction.SKIP,
            task_id=62,
            reason="Dependency failed.",
            attempt=1,
            max_retries=3,
            failure_type=FailureType.DEPENDENCY,
        ),
        DecisionResult(
            action=DecisionAction.ABORT,
            task_id=62,
            reason="Explicit abort.",
            attempt=1,
            max_retries=3,
            failure_type=FailureType.NONE,
        ),
    ]

    result = manager.prioritize(
        decisions,
    )

    assert result.action == DecisionAction.ABORT


def test_decision_manager_priority_is_independent_of_input_order() -> None:
    manager = DecisionManager()

    fail = DecisionResult(
        action=DecisionAction.FAIL,
        task_id=63,
        reason="Failure.",
        attempt=1,
        max_retries=3,
        failure_type=FailureType.PERMANENT,
    )

    fallback = DecisionResult(
        action=DecisionAction.FALLBACK,
        task_id=63,
        reason="Fallback.",
        attempt=1,
        max_retries=3,
        failure_type=FailureType.NONE,
    )

    retry = DecisionResult(
        action=DecisionAction.RETRY,
        task_id=63,
        reason="Retry.",
        attempt=1,
        max_retries=3,
        failure_type=FailureType.TRANSIENT,
    )

    result_1 = manager.prioritize(
        [fail, fallback, retry],
    )

    result_2 = manager.prioritize(
        [retry, fail, fallback],
    )

    result_3 = manager.prioritize(
        [fallback, retry, fail],
    )

    assert result_1.action == DecisionAction.RETRY
    assert result_2.action == DecisionAction.RETRY
    assert result_3.action == DecisionAction.RETRY