"""
===============================================================================
File Name   : test_decision_manager_integration.py
Module      : Decision Manager Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase F:
    F.5 - DecisionManager Integration

Purpose:
    Verify that DecisionManager correctly coordinates the different
    decision policies and produces a unified DecisionResult.
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus, ToolType
from agent_engine.contracts.task import Task

from agent_engine.decision_manager import (
    DecisionAction,
    DecisionManager,
    ExecutionOutcome,
    FailureType,
)

from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)


# =============================================================================
# Helpers
# =============================================================================


def build_outcome(
    *,
    task_id: int = 1,
    success: bool = False,
    failure_type: FailureType = FailureType.NONE,
    attempt: int = 1,
    retry_count: int = 0,
    max_retries: int = 0,
    timeout_seconds: float | None = None,
    execution_time: float | None = None,
    timed_out: bool = False,
) -> ExecutionOutcome:
    """
    Build a controlled ExecutionOutcome for integration testing.
    """

    return ExecutionOutcome(
        task_id=task_id,
        status=(
            ExecutionStatus.COMPLETED
            if success
            else ExecutionStatus.FAILED
        ),
        success=success,
        attempt=attempt,
        retry_count=retry_count,
        max_retries=max_retries,
        failure_type=failure_type,
        timeout_seconds=timeout_seconds,
        execution_time=execution_time,
        timed_out=timed_out,
    )


def build_task(task_id: int = 1) -> Task:
    """
    Build a minimal valid task for dependency/fallback evaluation.
    """

    return Task(
        id=task_id,
        description="Integration test task",
        action="open",
        tool=list(ToolType)[0],
    )


# =============================================================================
# F.5.1 - Unified execution decision flow
# =============================================================================


def test_successful_execution_produces_complete_decision() -> None:
    manager = DecisionManager()

    outcome = build_outcome(
        task_id=10,
        success=True,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.COMPLETE
    assert result.task_id == 10
    assert result.failure_type == FailureType.NONE


def test_transient_failure_uses_retry_policy() -> None:
    manager = DecisionManager()

    outcome = build_outcome(
        task_id=11,
        failure_type=FailureType.TRANSIENT,
        retry_count=0,
        max_retries=2,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.RETRY
    assert result.task_id == 11
    assert result.failure_type == FailureType.TRANSIENT


def test_timeout_uses_retry_policy() -> None:
    manager = DecisionManager()

    outcome = build_outcome(
        task_id=12,
        failure_type=FailureType.NONE,
        retry_count=0,
        max_retries=2,
        timeout_seconds=10,
        execution_time=20,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.RETRY
    assert result.task_id == 12
    assert result.failure_type == FailureType.TIMEOUT


def test_exhausted_retry_produces_fail_decision() -> None:
    manager = DecisionManager()

    outcome = build_outcome(
        task_id=13,
        failure_type=FailureType.TRANSIENT,
        retry_count=2,
        max_retries=2,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.FAIL
    assert result.task_id == 13
    assert result.failure_type == FailureType.TRANSIENT


def test_permanent_failure_uses_failure_strategy() -> None:
    manager = DecisionManager()

    outcome = build_outcome(
        task_id=14,
        failure_type=FailureType.PERMANENT,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.FAIL
    assert result.task_id == 14


def test_dependency_failure_produces_skip_decision() -> None:
    manager = DecisionManager()

    outcome = build_outcome(
        task_id=15,
        failure_type=FailureType.DEPENDENCY,
    )

    result = manager.decide(outcome)

    assert result.action == DecisionAction.SKIP
    assert result.task_id == 15


# =============================================================================
# F.5.2 - Dependency decision integration
# =============================================================================


def test_dependency_evaluation_uses_skip_policy() -> None:
    manager = DecisionManager()

    task = build_task(20)

    states = {
        100: ExecutionStatus.FAILED,
    }

    task.depends_on = [100]

    result = manager.evaluate_dependencies(
        task,
        states,
    )

    assert result.action == DecisionAction.SKIP
    assert result.task_id == 20
    assert result.failure_type == FailureType.DEPENDENCY


# =============================================================================
# F.5.3 - Fallback decision integration
# =============================================================================


def test_fallback_evaluation_returns_unified_decision_result() -> None:
    manager = DecisionManager()

    task = build_task(30)

    fallback = FallbackOption(
        id="fallback_browser",
        action="open",
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
        priority=1,
    )

    result = manager.evaluate_fallback(
        task,
        [fallback],
    )

    assert isinstance(result.task_id, int)
    assert result.task_id == 30
    assert result.action == DecisionAction.FALLBACK
    assert result.selected_fallback is not None
    assert result.selected_fallback.id == "fallback_browser"


# =============================================================================
# F.5.4 - Decision priority integration
# =============================================================================


def test_priority_resolves_retry_over_fallback_and_failure() -> None:
    manager = DecisionManager()

    retry = manager.decide(
        build_outcome(
            task_id=40,
            failure_type=FailureType.TRANSIENT,
            retry_count=0,
            max_retries=2,
        )
    )

    fallback = manager.evaluate_fallback(
        build_task(40),
        [
            FallbackOption(
                id="fallback_1",
                action="alternative_action",
                priority=1,
            )
        ],
    )

    fail = manager.decide(
        build_outcome(
            task_id=40,
            failure_type=FailureType.PERMANENT,
        )
    )

    result = manager.prioritize(
        [
            fail,
            fallback,
            retry,
        ]
    )

    assert result.action == DecisionAction.RETRY
    assert result is retry


def test_priority_resolves_fallback_over_failure() -> None:
    manager = DecisionManager()

    fallback = manager.evaluate_fallback(
        build_task(41),
        [
            FallbackOption(
                id="fallback_1",
                action="alternative_action",
                priority=1,
            )
        ],
    )

    fail = manager.decide(
        build_outcome(
            task_id=41,
            failure_type=FailureType.PERMANENT,
        )
    )

    result = manager.prioritize(
        [
            fail,
            fallback,
        ]
    )

    assert result.action == DecisionAction.FALLBACK
    assert result is fallback


# =============================================================================
# F.5.5 - DecisionResult contract
# =============================================================================


def test_all_decision_paths_return_decision_result() -> None:
    manager = DecisionManager()

    outcomes = [
        build_outcome(
            task_id=50,
            success=True,
        ),
        build_outcome(
            task_id=51,
            failure_type=FailureType.TRANSIENT,
            max_retries=1,
        ),
        build_outcome(
            task_id=52,
            failure_type=FailureType.PERMANENT,
        ),
        build_outcome(
            task_id=53,
            failure_type=FailureType.DEPENDENCY,
        ),
    ]

    for outcome in outcomes:
        result = manager.decide(outcome)

        assert result.task_id == outcome.task_id
        assert isinstance(result.action, DecisionAction)
        assert result.reason
        assert result.attempt == outcome.attempt