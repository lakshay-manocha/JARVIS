"""
===============================================================================
File Name   : decision_state_bridge.py
Module      : Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the Phase D → Phase E integration boundary.

Phase E-7:
    Decision Manager → State Manager Integration.

The DecisionStateBridge translates a DecisionResult produced by the
Decision Manager into a runtime ExecutionStatus managed by the State Manager.

Responsibilities:
    - Accept DecisionResult objects
    - Map decisions to runtime states
    - Delegate state changes to StateManager
    - Preserve StateTransitionPolicy enforcement
    - Preserve StateHistory recording

The bridge does NOT:
    - execute tasks
    - execute retries
    - execute fallbacks
    - dispatch actions
    - make decisions
    - modify TaskRuntimeState directly

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)
from agent_engine.state_manager.state_manager import StateManager


class DecisionStateBridge:
    """
    Integrates Phase D DecisionManager results with Phase E StateManager.

    Phase D remains responsible for deciding what should happen.

    Phase E remains responsible for representing and validating runtime
    execution state.

    This class only translates between the two layers.
    """

    # -------------------------------------------------------------------------
    # Decision → Runtime State mapping
    # -------------------------------------------------------------------------

    _DECISION_STATUS_MAP: dict[
        DecisionAction,
        ExecutionStatus,
    ] = {
        DecisionAction.COMPLETE: ExecutionStatus.COMPLETED,
        DecisionAction.FAIL: ExecutionStatus.FAILED,
        DecisionAction.RETRY: ExecutionStatus.RETRYING,
        DecisionAction.SKIP: ExecutionStatus.SKIPPED,
        DecisionAction.FALLBACK: ExecutionStatus.RUNNING,
    }
    def __init__(
        self,
        state_manager: StateManager,
    ) -> None:
        """
        Initialize the bridge with an existing StateManager.

        The StateManager remains the owner of runtime state.
        """

        self.state_manager = state_manager

    # =========================================================================
    # Public API
    # =========================================================================

    def apply_decision(
        self,
        decision: DecisionResult,
    ):
        """
        Apply a DecisionResult to the corresponding task runtime state.

        The bridge translates the DecisionAction into an ExecutionStatus and
        delegates the actual transition to StateManager.set_state().

        StateManager therefore remains responsible for:

            - transition validation
            - runtime state mutation
            - state history recording

        Raises:
            KeyError:
                If the task has not been registered.

            InvalidStateTransitionError:
                If the requested decision would produce an illegal runtime
                transition.

            ValueError:
                If the DecisionAction has no runtime state mapping.
        """

        action = decision.action

        if action not in self._DECISION_STATUS_MAP:
            raise ValueError(
                f"Decision action '{action}' cannot be mapped to a runtime "
                "execution state."
            )

        target_status = self._DECISION_STATUS_MAP[action]

        return self.state_manager.set_state(
            decision.task_id,
            target_status,
        )