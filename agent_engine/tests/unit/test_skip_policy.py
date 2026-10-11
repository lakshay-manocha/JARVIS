"""
===============================================================================
File Name   : test_skip_policy.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase D-4:
    Dependency-aware skip policy tests.
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus, ToolType
from agent_engine.contracts.task import Task

from agent_engine.decision_manager import (
    DecisionAction,
    FailureType,
)

from agent_engine.decision_manager.skip_policy import (
    SkipPolicy,
)


policy = SkipPolicy()


def make_task(
    task_id: int,
    depends_on: list[int] | None = None,
) -> Task:
    """
    Create a minimal valid Task for dependency testing.
    """

    return Task(
        id=task_id,
        description=f"Task {task_id}",
        action="test_action",
        tool=list(ToolType)[0],
        depends_on=depends_on or [],
    )

# =============================================================================
# No dependencies
# =============================================================================


def test_task_without_dependencies_is_not_skipped() -> None:

    task = make_task(1)

    states = {}

    assert policy.should_skip(task, states) is False


# =============================================================================
# Dependency pending
# =============================================================================


def test_pending_dependency_does_not_skip_task() -> None:

    task = make_task(
        2,
        depends_on=[1],
    )

    states = {
        1: ExecutionStatus.PENDING,
    }

    assert policy.should_skip(task, states) is False


# =============================================================================
# Dependency running
# =============================================================================


def test_running_dependency_does_not_skip_task() -> None:

    task = make_task(
        2,
        depends_on=[1],
    )

    states = {
        1: ExecutionStatus.RUNNING,
    }

    assert policy.should_skip(task, states) is False


# =============================================================================
# Successful dependency
# =============================================================================


def test_completed_dependency_does_not_skip_task() -> None:

    task = make_task(
        2,
        depends_on=[1],
    )

    states = {
        1: ExecutionStatus.COMPLETED,
    }

    assert policy.should_skip(task, states) is False


# =============================================================================
# Failed dependency
# =============================================================================


def test_failed_dependency_skips_task() -> None:

    task = make_task(
        2,
        depends_on=[1],
    )

    states = {
        1: ExecutionStatus.FAILED,
    }

    assert policy.should_skip(task, states) is True


def test_failed_dependency_is_reported() -> None:

    task = make_task(
        3,
        depends_on=[1, 2],
    )

    states = {
        1: ExecutionStatus.COMPLETED,
        2: ExecutionStatus.FAILED,
    }

    blocking = policy.get_blocking_dependencies(
        task,
        states,
    )

    assert blocking == [2]


# =============================================================================
# Multiple failed dependencies
# =============================================================================


def test_multiple_failed_dependencies_are_detected() -> None:

    task = make_task(
        4,
        depends_on=[1, 2, 3],
    )

    states = {
        1: ExecutionStatus.FAILED,
        2: ExecutionStatus.COMPLETED,
        3: ExecutionStatus.FAILED,
    }

    blocking = policy.get_blocking_dependencies(
        task,
        states,
    )

    assert blocking == [1, 3]


# =============================================================================
# Decision generation
# =============================================================================


def test_dependency_failure_returns_skip_decision() -> None:

    task = make_task(
        5,
        depends_on=[1],
    )

    states = {
        1: ExecutionStatus.FAILED,
    }

    result = policy.evaluate(
        task,
        states,
    )

    assert result.action == DecisionAction.SKIP
    assert result.task_id == 5
    assert result.failure_type == FailureType.DEPENDENCY


def test_clear_dependencies_do_not_return_skip() -> None:

    task = make_task(
        6,
        depends_on=[1, 2],
    )

    states = {
        1: ExecutionStatus.COMPLETED,
        2: ExecutionStatus.COMPLETED,
    }

    result = policy.evaluate(
        task,
        states,
    )

    assert result.action == DecisionAction.COMPLETE
    assert result.failure_type == FailureType.NONE

def test_missing_dependency_state_does_not_skip_task() -> None:

    task = make_task(
        7,
        depends_on=[2],
    )

    states = {}

    assert policy.should_skip(task, states) is False