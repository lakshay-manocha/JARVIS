"""
===============================================================================
File Name   : test_fallback_state_integration.py
Module      : Decision Manager / State Manager Integration Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Tests the Phase F fallback decision integration with the State Manager.

Verifies that:
    - FALLBACK decisions are translated to RUNNING state
    - FAILED -> RUNNING is accepted by StateTransitionPolicy
    - StateManager records the transition
    - fallback selection does not execute any action
    - invalid/unregistered tasks are rejected
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.contracts.task import Task
from agent_engine.decision_manager.fallback_policy import FallbackPolicy
from agent_engine.decision_manager.models.decision import DecisionAction
from agent_engine.decision_manager.models.fallback import FallbackOption
from agent_engine.integration.decision_state_bridge import DecisionStateBridge
from agent_engine.state_manager.state_manager import StateManager


def build_task(task_id: int = 1) -> Task:
    """
    Build a minimal task suitable for fallback integration testing.
    """

    return Task(
        id=task_id,
        description="Open the requested website",
        action="open",
        tool="browser_agent",
        retry=1,
    )

def build_fallback_option() -> FallbackOption:
    """
    Build a deterministic fallback option.
    """

    return FallbackOption(
        id="fallback_browser",
        action="open",
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
        priority=1,
        description="Use an alternate browser execution path.",
    )


def test_fallback_decision_moves_failed_task_to_running():
    """
    A FALLBACK decision should translate to:

        FAILED -> RUNNING
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)
    policy = FallbackPolicy()

    task = build_task()

    state_manager.register_task(task.id)

    # Move task into the failure state first.
    state_manager.set_state(
        task.id,
        ExecutionStatus.READY,
    )
    state_manager.set_state(
        task.id,
        ExecutionStatus.RUNNING,
    )
    state_manager.set_state(
        task.id,
        ExecutionStatus.FAILED,
    )

    decision = policy.select_fallback(
        task=task,
        fallback_options=[build_fallback_option()],
        attempt=1,
    )

    assert decision.action == DecisionAction.FALLBACK

    bridge.apply_decision(decision)

    assert (
        state_manager.get_status(task.id)
        == ExecutionStatus.RUNNING
    )


def test_fallback_transition_is_recorded_in_history():
    """
    StateManager must record FAILED -> RUNNING in state history.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)
    policy = FallbackPolicy()

    task = build_task()

    state_manager.register_task(task.id)

    state_manager.set_state(
        task.id,
        ExecutionStatus.READY,
    )
    state_manager.set_state(
        task.id,
        ExecutionStatus.RUNNING,
    )
    state_manager.set_state(
        task.id,
        ExecutionStatus.FAILED,
    )

    decision = policy.select_fallback(
        task=task,
        fallback_options=[build_fallback_option()],
        attempt=1,
    )

    bridge.apply_decision(decision)

    history = state_manager.get_history(task.id)

    assert history[-1].from_status == ExecutionStatus.FAILED
    assert history[-1].to_status == ExecutionStatus.RUNNING


def test_fallback_without_options_does_not_move_failed_task_to_running():
    """
    If no fallback exists, FallbackPolicy returns FAIL.

    Therefore:

        FAILED -> FAILED

    should remain unchanged.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)
    policy = FallbackPolicy()

    task = build_task()

    state_manager.register_task(task.id)

    state_manager.set_state(
        task.id,
        ExecutionStatus.READY,
    )
    state_manager.set_state(
        task.id,
        ExecutionStatus.RUNNING,
    )
    state_manager.set_state(
        task.id,
        ExecutionStatus.FAILED,
    )

    decision = policy.select_fallback(
        task=task,
        fallback_options=[],
        attempt=1,
    )

    assert decision.action == DecisionAction.FAIL

    bridge.apply_decision(decision)

    assert (
        state_manager.get_status(task.id)
        == ExecutionStatus.FAILED
    )


def test_fallback_decision_preserves_selected_fallback():
    """
    The selected fallback must survive the DecisionManager -> StateManager
    boundary. StateManager changes runtime state only; it does not execute
    the selected fallback.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)
    policy = FallbackPolicy()

    task = build_task()
    fallback = build_fallback_option()

    state_manager.register_task(task.id)

    state_manager.set_state(
        task.id,
        ExecutionStatus.READY,
    )
    state_manager.set_state(
        task.id,
        ExecutionStatus.RUNNING,
    )
    state_manager.set_state(
        task.id,
        ExecutionStatus.FAILED,
    )

    decision = policy.select_fallback(
        task=task,
        fallback_options=[fallback],
        attempt=1,
    )

    assert decision.selected_fallback is not None
    assert decision.selected_fallback.id == "fallback_browser"

    bridge.apply_decision(decision)

    assert (
        state_manager.get_status(task.id)
        == ExecutionStatus.RUNNING
    )


def test_bridge_rejects_unregistered_task():
    """
    DecisionStateBridge must delegate task validation to StateManager.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)
    policy = FallbackPolicy()

    task = build_task(task_id=99)

    decision = policy.select_fallback(
        task=task,
        fallback_options=[build_fallback_option()],
        attempt=1,
    )

    try:
        bridge.apply_decision(decision)
    except KeyError:
        pass
    else:
        raise AssertionError(
            "Expected KeyError for an unregistered task."
        )