"""
===============================================================================
File Name   : execution_state_integrator.py
Module      : Automation Engine - Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides the M5-E.6 integration boundary between execution outcomes and
runtime task state.

The integrator receives an ExecutionOutcome produced by the Automation
Dispatcher, asks the DecisionManager what should happen next, and applies
that decision through the DecisionStateBridge.

Flow:

    ExecutionOutcome
          ↓
    DecisionManager
          ↓
    DecisionResult
          ↓
    DecisionStateBridge
          ↓
    StateManager

The integrator does NOT:
    - execute automation actions
    - implement retry policy
    - implement fallback policy
    - directly modify StateManager state
    - replace DecisionManager logic
    - replace DecisionStateBridge logic

Author : Team Automation
===============================================================================
"""

from __future__ import annotations

from agent_engine.decision_manager.decision_manager import DecisionManager
from agent_engine.decision_manager.models.decision import DecisionResult
from agent_engine.decision_manager.models.execution_outcome import ExecutionOutcome
from agent_engine.integration.decision_state_bridge import DecisionStateBridge


class ExecutionStateIntegrator:
    """
    Integrates an ExecutionOutcome with the existing Decision Manager and
    State Manager pipeline.

    Responsibilities:

        ExecutionOutcome
              ↓
        DecisionManager
              ↓
        DecisionResult
              ↓
        DecisionStateBridge
    """

    def __init__(
        self,
        decision_manager: DecisionManager,
        decision_state_bridge: DecisionStateBridge,
    ) -> None:
        """
        Initialize the execution-state integration boundary.

        Args:
            decision_manager:
                Existing DecisionManager responsible for deciding the next
                execution action.

            decision_state_bridge:
                Existing bridge responsible for translating the decision into
                a runtime state transition.
        """

        self._decision_manager = decision_manager
        self._decision_state_bridge = decision_state_bridge

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def integrate(
        self,
        outcome: ExecutionOutcome,
    ) -> DecisionResult:
        """
        Process an execution outcome and apply its resulting state decision.

        Args:
            outcome:
                Normalized result produced by the Automation Dispatcher.

        Returns:
            DecisionResult produced by the DecisionManager.

        Raises:
            TypeError:
                If the supplied outcome is not an ExecutionOutcome.
        """

        if not isinstance(outcome, ExecutionOutcome):
            raise TypeError(
                "outcome must be an ExecutionOutcome."
            )

        decision = self._decision_manager.decide(outcome)

        self._decision_state_bridge.apply_decision(decision)

        return decision