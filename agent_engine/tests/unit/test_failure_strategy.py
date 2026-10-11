"""
===============================================================================
File Name   : test_failure_strategy.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase D-3:
    Tests for failure handling strategy.
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus

from agent_engine.decision_manager import (
    DecisionAction,
    ExecutionOutcome,
    FailureType,
)

from agent_engine.decision_manager.failure_strategy import (
    FailureStrategy,
)


strategy = FailureStrategy()


def make_outcome(
    failure_type: FailureType,
) -> ExecutionOutcome:

    return ExecutionOutcome(
        task_id=1,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=3,
        failure_type=failure_type,
        error_message="test failure",
    )


def test_permanent_failure_returns_fail() -> None:

    result = strategy.evaluate(
        make_outcome(FailureType.PERMANENT)
    )

    assert result.action == DecisionAction.FAIL
    assert result.failure_type == FailureType.PERMANENT


def test_validation_failure_returns_fail() -> None:

    result = strategy.evaluate(
        make_outcome(FailureType.VALIDATION)
    )

    assert result.action == DecisionAction.FAIL
    assert result.failure_type == FailureType.VALIDATION


def test_dependency_failure_returns_skip() -> None:

    result = strategy.evaluate(
        make_outcome(FailureType.DEPENDENCY)
    )

    assert result.action == DecisionAction.SKIP
    assert result.failure_type == FailureType.DEPENDENCY


def test_unknown_failure_returns_fail() -> None:

    result = strategy.evaluate(
        make_outcome(FailureType.UNKNOWN)
    )

    assert result.action == DecisionAction.FAIL
    assert result.failure_type == FailureType.UNKNOWN