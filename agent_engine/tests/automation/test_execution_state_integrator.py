"""
===============================================================================
File Name   : test_execution_state_integrator.py
Module      : Automation Engine - Integration Tests
Project     : JARVIS

Description:
-------------
Tests the M5-E.6 integration between ExecutionOutcome, DecisionManager,
DecisionStateBridge, and StateManager.

Author : Team Automation
===============================================================================
"""

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.decision_manager.decision_manager import DecisionManager
from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)
from agent_engine.integration.decision_state_bridge import DecisionStateBridge
from agent_engine.state_manager.state_manager import StateManager
from agent_engine.automation.integration.execution_state_integrator import (
    ExecutionStateIntegrator,
)


# =============================================================================
# Helpers
# =============================================================================

def create_integrator():
    """
    Create a real M5-E.6 integration chain.
    """

    state_manager = StateManager()
    decision_manager = DecisionManager()
    bridge = DecisionStateBridge(state_manager)

    integrator = ExecutionStateIntegrator(
        decision_manager,
        bridge,
    )

    return integrator, state_manager


def register_task(
    state_manager: StateManager,
    task_id: int,
) -> None:
    """
    Register a task so the StateManager can accept runtime transitions.
    """

    state_manager.register_tasks([task_id])


# =============================================================================
# Successful Execution
# =============================================================================

def test_successful_outcome_moves_task_to_completed():
    """
    A successful ExecutionOutcome should result in:

        ExecutionOutcome(COMPLETED)
            ↓
        DecisionManager → COMPLETE
            ↓
        StateManager → COMPLETED
    """

    integrator, state_manager = create_integrator()

    register_task(state_manager, 1)

    state_manager.set_state(
        1,
        ExecutionStatus.RUNNING,
    )

    outcome = ExecutionOutcome(
        task_id=1,
        status=ExecutionStatus.COMPLETED,
        success=True,
        attempt=1,
        retry_count=0,
        max_retries=0,
        timeout_seconds=30,
        execution_time=0.1,
        timed_out=False,
        failure_type=FailureType.NONE,
    )

    decision = integrator.integrate(outcome)

    assert decision.task_id == 1
    assert state_manager.get_status(1) == ExecutionStatus.COMPLETED


# =============================================================================
# Failed Execution
# =============================================================================

def test_failed_outcome_moves_task_to_failed():
    """
    A failed execution with no retry budget should result in:

        ExecutionOutcome(FAILED)
            ↓
        DecisionManager → FAIL
            ↓
        StateManager → FAILED
    """

    integrator, state_manager = create_integrator()

    register_task(state_manager, 2)

    state_manager.set_state(
        2,
        ExecutionStatus.READY,
    )

    state_manager.set_state(
        2,
        ExecutionStatus.RUNNING,
    )

    outcome = ExecutionOutcome(
        task_id=2,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=0,
        timeout_seconds=30,
        execution_time=0.2,
        timed_out=False,
        failure_type=FailureType.PERMANENT,
        error_message="Simulated failure",
    )

    decision = integrator.integrate(outcome)

    assert decision.task_id == 2
    assert state_manager.get_status(2) == ExecutionStatus.FAILED


# =============================================================================
# Invalid Input
# =============================================================================

def test_invalid_outcome_is_rejected():
    """
    The integration boundary should accept only ExecutionOutcome objects.
    """

    integrator, _ = create_integrator()

    with pytest.raises(TypeError):
        integrator.integrate("invalid outcome")