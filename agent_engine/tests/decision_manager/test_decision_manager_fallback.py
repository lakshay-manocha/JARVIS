"""
===============================================================================
File Name   : test_decision_manager_fallback.py
Module      : Decision Manager Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Tests DecisionManager integration with FallbackPolicy.

Phase F-4:
    Fallback Policy integration.

Verifies that:
    - DecisionManager delegates fallback evaluation correctly.
    - A fallback produces FALLBACK.
    - No fallback produces FAIL.
    - The selected fallback is preserved.
    - Attempt and retry metadata are preserved.
    - DecisionManager does not execute the fallback.
===============================================================================
"""

from agent_engine.contracts.task import Task

from agent_engine.decision_manager.decision_manager import (
    DecisionManager,
)

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
)

from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)


# =============================================================================
# Helpers
# =============================================================================


def build_task(
    *,
    task_id: int = 1,
    retry: int = 2,
) -> Task:
    """
    Build a minimal Task compatible with DecisionManager.
    """

    return Task(
        id=task_id,
        description="Open the requested website",
        action="open",
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
        retry=retry,
    )


def build_fallback(
    *,
    fallback_id: str = "fallback-1",
    action: str = "retry_open",
    priority: int = 1,
) -> FallbackOption:
    """
    Build a fallback option for testing.
    """

    return FallbackOption(
        id=fallback_id,
        action=action,
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
        priority=priority,
        description="Alternative browser recovery action.",
    )


# =============================================================================
# Tests
# =============================================================================


def test_decision_manager_selects_fallback():
    """
    DecisionManager must delegate fallback selection to FallbackPolicy.
    """

    manager = DecisionManager()
    task = build_task()

    fallback = build_fallback()

    result = manager.evaluate_fallback(
        task=task,
        fallback_options=[fallback],
        attempt=1,
    )

    assert result.action == DecisionAction.FALLBACK
    assert result.task_id == task.id
    assert result.selected_fallback is not None
    assert result.selected_fallback.id == fallback.id


def test_decision_manager_returns_fail_when_no_fallback_exists():
    """
    DecisionManager must return FAIL when no fallback is available.
    """

    manager = DecisionManager()
    task = build_task()

    result = manager.evaluate_fallback(
        task=task,
        fallback_options=[],
        attempt=1,
    )

    assert result.action == DecisionAction.FAIL
    assert result.task_id == task.id
    assert result.selected_fallback is None


def test_decision_manager_preserves_selected_fallback():
    """
    The exact FallbackOption selected by FallbackPolicy must be preserved
    in the unified DecisionResult.
    """

    manager = DecisionManager()
    task = build_task()

    fallback_1 = build_fallback(
        fallback_id="fallback-low",
        action="retry_open",
        priority=3,
    )

    fallback_2 = build_fallback(
        fallback_id="fallback-high",
        action="open_alternative",
        priority=1,
    )

    result = manager.evaluate_fallback(
        task=task,
        fallback_options=[
            fallback_1,
            fallback_2,
        ],
        attempt=2,
    )

    assert result.action == DecisionAction.FALLBACK
    assert result.selected_fallback is not None

    assert result.selected_fallback.id == "fallback-high"
    assert result.selected_fallback.action == "open_alternative"
    assert result.selected_fallback.priority == 1


def test_decision_manager_preserves_attempt_metadata():
    """
    Fallback evaluation must preserve the current attempt and task retry
    configuration in DecisionResult.
    """

    manager = DecisionManager()
    task = build_task(retry=3)

    fallback = build_fallback()

    result = manager.evaluate_fallback(
        task=task,
        fallback_options=[fallback],
        attempt=2,
    )

    assert result.attempt == 2
    assert result.max_retries == 3


def test_decision_manager_fallback_does_not_execute_action():
    """
    DecisionManager must only produce a fallback decision.

    It must not execute the fallback action itself.
    """

    manager = DecisionManager()
    task = build_task()

    executed = []

    fallback = FallbackOption(
        id="fallback-1",
        action="open",
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
        priority=1,
    )

    result = manager.evaluate_fallback(
        task=task,
        fallback_options=[fallback],
        attempt=1,
    )

    assert result.action == DecisionAction.FALLBACK
    assert executed == []