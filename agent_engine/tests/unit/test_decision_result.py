"""
===============================================================================
File Name   : test_decision_result.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase D-6:
    Tests for the unified DecisionResult contract.
===============================================================================
"""

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)

from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)

from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)


def test_decision_result_supports_complete_decision() -> None:
    result = DecisionResult(
        action=DecisionAction.COMPLETE,
        task_id=1,
        reason="Task completed successfully.",
        attempt=1,
        max_retries=0,
        failure_type=FailureType.NONE,
    )

    assert result.action == DecisionAction.COMPLETE
    assert result.task_id == 1
    assert result.failure_type == FailureType.NONE


def test_decision_result_supports_retry_decision() -> None:
    result = DecisionResult(
        action=DecisionAction.RETRY,
        task_id=2,
        reason="Retry is available.",
        attempt=1,
        max_retries=3,
        failure_type=FailureType.TRANSIENT,
    )

    assert result.action == DecisionAction.RETRY
    assert result.task_id == 2
    assert result.max_retries == 3


def test_decision_result_supports_skip_decision() -> None:
    result = DecisionResult(
        action=DecisionAction.SKIP,
        task_id=3,
        reason="Dependency failed.",
        attempt=1,
        max_retries=0,
        failure_type=FailureType.DEPENDENCY,
    )

    assert result.action == DecisionAction.SKIP
    assert result.failure_type == FailureType.DEPENDENCY


def test_decision_result_supports_fallback_decision() -> None:
    fallback = FallbackOption(
        id="fallback_1",
        action="alternative_action",
        tool="alternative_tool",
        parameters={
            "mode": "safe",
        },
        priority=1,
    )

    result = DecisionResult(
        action=DecisionAction.FALLBACK,
        task_id=4,
        reason="Fallback selected.",
        attempt=1,
        max_retries=0,
        selected_fallback=fallback,
        failure_type=FailureType.NONE,
    )

    assert result.action == DecisionAction.FALLBACK
    assert result.selected_fallback is not None
    assert result.selected_fallback.id == "fallback_1"
    assert result.selected_fallback.action == "alternative_action"
    assert result.selected_fallback.tool == "alternative_tool"
    assert result.selected_fallback.parameters == {
        "mode": "safe",
    }


def test_decision_result_supports_fail_decision() -> None:
    result = DecisionResult(
        action=DecisionAction.FAIL,
        task_id=5,
        reason="Task failure is not recoverable.",
        attempt=1,
        max_retries=0,
        failure_type=FailureType.PERMANENT,
    )

    assert result.action == DecisionAction.FAIL
    assert result.failure_type == FailureType.PERMANENT
    assert result.selected_fallback is None