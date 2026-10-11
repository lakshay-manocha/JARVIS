"""
===============================================================================
File Name   : test_fallback_policy.py
Module      : Decision Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase D-5:
    Fallback / Recovery.

Phase D-6:
    Verify that fallback decisions use the unified DecisionResult contract.
===============================================================================
"""

from agent_engine.contracts.enums import ToolType
from agent_engine.contracts.task import Task

from agent_engine.decision_manager.fallback_policy import (
    FallbackPolicy,
)

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
)

from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)


policy = FallbackPolicy()


def make_task(task_id: int = 1) -> Task:
    """
    Create a valid JARVIS Task.
    """

    return Task(
        id=task_id,
        description=f"Task {task_id}",
        action="test_action",
        tool=list(ToolType)[0],
    )


# =============================================================================
# No fallback
# =============================================================================


def test_no_fallback_available() -> None:
    """
    D-5:
        No fallback options should result in failure.

    D-6:
        The result must use the unified DecisionResult contract.
    """

    task = make_task()

    result = policy.select_fallback(task)

    assert result.task_id == task.id
    assert result.action == DecisionAction.FAIL
    assert result.selected_fallback is None
    assert result.failure_type.value == "NONE"


# =============================================================================
# Single fallback
# =============================================================================


def test_single_fallback_is_selected() -> None:
    """
    One available fallback should produce a FALLBACK decision.
    """

    task = make_task()

    fallback = FallbackOption(
        id="fallback_1",
        action="alternative_action",
    )

    result = policy.select_fallback(
        task,
        [fallback],
    )

    assert result.action == DecisionAction.FALLBACK
    assert result.selected_fallback is not None
    assert result.selected_fallback.id == "fallback_1"


# =============================================================================
# Multiple fallbacks
# =============================================================================


def test_highest_priority_fallback_is_selected() -> None:
    """
    The fallback with the highest priority must be selected.

    Lower priority number = higher preference.
    """

    task = make_task()

    fallback_1 = FallbackOption(
        id="fallback_1",
        action="action_1",
        priority=2,
    )

    fallback_2 = FallbackOption(
        id="fallback_2",
        action="action_2",
        priority=1,
    )

    result = policy.select_fallback(
        task,
        [fallback_1, fallback_2],
    )

    assert result.action == DecisionAction.FALLBACK
    assert result.selected_fallback is not None
    assert result.selected_fallback.id == "fallback_2"


# =============================================================================
# Fallback parameters
# =============================================================================


def test_selected_fallback_preserves_parameters() -> None:
    """
    Selected fallback parameters must be preserved unchanged.
    """

    task = make_task()

    fallback = FallbackOption(
        id="fallback_file",
        action="alternative_file_operation",
        parameters={
            "path": "test.txt",
            "mode": "safe",
        },
    )

    result = policy.select_fallback(
        task,
        [fallback],
    )

    assert result.action == DecisionAction.FALLBACK
    assert result.selected_fallback is not None

    assert result.selected_fallback.parameters == {
        "path": "test.txt",
        "mode": "safe",
    }


# =============================================================================
# Tool information
# =============================================================================


def test_selected_fallback_preserves_tool() -> None:
    """
    Selected fallback tool information must be preserved.
    """

    task = make_task()

    fallback = FallbackOption(
        id="fallback_browser",
        action="alternative_browser_action",
        tool="alternative_browser",
    )

    result = policy.select_fallback(
        task,
        [fallback],
    )

    assert result.action == DecisionAction.FALLBACK
    assert result.selected_fallback is not None
    assert result.selected_fallback.tool == "alternative_browser"


# =============================================================================
# Ordering
# =============================================================================


def test_fallback_selection_is_independent_of_input_order() -> None:
    """
    Fallback selection must depend on priority, not input order.
    """

    task = make_task()

    fallback_high = FallbackOption(
        id="high_priority",
        action="action_high",
        priority=1,
    )

    fallback_low = FallbackOption(
        id="low_priority",
        action="action_low",
        priority=5,
    )

    result = policy.select_fallback(
        task,
        [
            fallback_low,
            fallback_high,
        ],
    )

    assert result.action == DecisionAction.FALLBACK
    assert result.selected_fallback is not None
    assert result.selected_fallback.id == "high_priority"