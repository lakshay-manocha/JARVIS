"""
===============================================================================
File Name   : decision_priority.py
Module      : Decision Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Implements deterministic decision priority resolution.

Phase D-7:
    Decision Priority.

The policy resolves multiple candidate DecisionResult objects by applying
a fixed priority hierarchy.

Priority order:

    ABORT
        ↓
    SKIP
        ↓
    COMPLETE
        ↓
    RETRY
        ↓
    FALLBACK
        ↓
    FAIL

Lower priority number means higher decision priority.

The policy:
    - does NOT execute decisions,
    - does NOT modify task state,
    - does NOT mutate DecisionResult objects,
    - does NOT perform retries,
    - does NOT execute fallbacks.

It only selects the highest-priority decision.

For equal-priority decisions, input order is preserved.

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from collections.abc import Sequence

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)


class DecisionPriorityPolicy:
    """
    Deterministic policy for resolving competing decisions.

    Lower numeric priority means higher decision priority.
    """

    # -------------------------------------------------------------------------
    # D-7 decision priority hierarchy
    # -------------------------------------------------------------------------

    PRIORITY: dict[DecisionAction, int] = {
        DecisionAction.ABORT: 0,
        DecisionAction.SKIP: 1,
        DecisionAction.COMPLETE: 2,
        DecisionAction.RETRY: 3,
        DecisionAction.FALLBACK: 4,
        DecisionAction.FAIL: 5,
    }

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def select(
        self,
        decisions: Sequence[DecisionResult],
    ) -> DecisionResult:
        """
        Select the highest-priority decision.

        Parameters
        ----------
        decisions:
            Candidate decisions to compare.

        Returns
        -------
        DecisionResult
            The highest-priority decision.

        Raises
        ------
        ValueError
            If no decisions are provided.
        """

        if not decisions:
            raise ValueError(
                "At least one decision is required."
            )

        return min(
            decisions,
            key=self._priority_key,
        )

    # -------------------------------------------------------------------------
    # Internal priority resolution
    # -------------------------------------------------------------------------

    def _priority_key(
        self,
        decision: DecisionResult,
    ) -> int:
        """
        Return the numeric priority of a decision.

        Raises
        ------
        ValueError
            If an unsupported DecisionAction is encountered.
        """

        try:
            return self.PRIORITY[decision.action]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported decision action: {decision.action}"
            ) from exc