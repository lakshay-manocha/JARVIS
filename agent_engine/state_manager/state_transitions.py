"""
===============================================================================
File Name   : state_transitions.py
Module      : State Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the legal runtime state transitions for executable tasks.

Phase E-3:
    State Transitions.

The transition policy determines whether a task may move from its current
ExecutionStatus to a requested ExecutionStatus.

The policy does not modify task state. It only validates transitions.
===============================================================================
"""

from __future__ import annotations

from agent_engine.contracts.enums import ExecutionStatus


class InvalidStateTransitionError(ValueError):
    """
    Raised when an invalid task state transition is requested.
    """


class StateTransitionPolicy:
    """
    Defines and validates legal task execution state transitions.
    """

    _TRANSITIONS: dict[
        ExecutionStatus,
        frozenset[ExecutionStatus],
    ] = {
        # -------------------------------------------------------------------------
        # Initial execution
        # -------------------------------------------------------------------------
        ExecutionStatus.PENDING: frozenset({
            ExecutionStatus.READY,
            ExecutionStatus.RUNNING,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.STOPPED,
        }),

        # -------------------------------------------------------------------------
        # Ready for execution
        # -------------------------------------------------------------------------
        ExecutionStatus.READY: frozenset({
            ExecutionStatus.RUNNING,
            ExecutionStatus.SKIPPED,
            ExecutionStatus.CANCELLED,
        }),
        # -------------------------------------------------------------------------
        # Active execution
        # -------------------------------------------------------------------------
        ExecutionStatus.RUNNING: frozenset({
            ExecutionStatus.WAITING,
            ExecutionStatus.PAUSED,
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.STOPPED,
            ExecutionStatus.CANCELLED,
        }),

        # -------------------------------------------------------------------------
        # Paused execution
        # -------------------------------------------------------------------------
        ExecutionStatus.PAUSED: frozenset({
            ExecutionStatus.RUNNING,
            ExecutionStatus.STOPPED,
            ExecutionStatus.CANCELLED,
        }),

        # -------------------------------------------------------------------------
        # Temporarily waiting
        # -------------------------------------------------------------------------
        ExecutionStatus.WAITING: frozenset({
            ExecutionStatus.RUNNING,
            ExecutionStatus.PAUSED,
            ExecutionStatus.STOPPED,
            ExecutionStatus.CANCELLED,
        }),

        # -------------------------------------------------------------------------
        # Failed execution
        # -------------------------------------------------------------------------
        ExecutionStatus.FAILED: frozenset({
            ExecutionStatus.RETRYING,
            ExecutionStatus.RUNNING,
            ExecutionStatus.CANCELLED,
        }),

        # -------------------------------------------------------------------------
        # Retry execution
        # -------------------------------------------------------------------------
        ExecutionStatus.RETRYING: frozenset({
            ExecutionStatus.RUNNING,
            ExecutionStatus.FAILED,
            ExecutionStatus.STOPPED,
            ExecutionStatus.CANCELLED,
        }),

        # -------------------------------------------------------------------------
        # Terminal states
        # -------------------------------------------------------------------------
        ExecutionStatus.COMPLETED: frozenset(),

        ExecutionStatus.STOPPED: frozenset(),

        ExecutionStatus.CANCELLED: frozenset(),

        # -------------------------------------------------------------------------
        # Non-terminal skipped state
        # -------------------------------------------------------------------------
        ExecutionStatus.SKIPPED: frozenset(),
    }
    @classmethod
    def can_transition(
        cls,
        current: ExecutionStatus,
        target: ExecutionStatus,
    ) -> bool:
        """
        Return whether the requested transition is legal.

        Staying in the same state is considered valid and therefore
        idempotent.
        """

        if current == target:
            return True

        return target in cls._TRANSITIONS.get(
            current,
            frozenset(),
        )

    @classmethod
    def validate_transition(
        cls,
        current: ExecutionStatus,
        target: ExecutionStatus,
    ) -> None:
        """
        Validate a requested state transition.

        Raises:
            InvalidStateTransitionError:
                If the transition is not permitted.
        """

        if cls.can_transition(current, target):
            return

        raise InvalidStateTransitionError(
            f"Invalid state transition: "
            f"{current.value} -> {target.value}."
        )

    @classmethod
    def allowed_transitions(
        cls,
        current: ExecutionStatus,
    ) -> frozenset[ExecutionStatus]:
        """
        Return all legal target states for the current state.
        """

        return cls._TRANSITIONS.get(
            current,
            frozenset(),
        )