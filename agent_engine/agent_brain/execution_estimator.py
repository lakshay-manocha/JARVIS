"""
===============================================================================
File Name   : execution_estimator.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides deterministic execution-time estimates for executable tasks.

The estimator uses the resolved task action and selected tool to assign a
reasonable baseline execution duration.

These estimates are planning estimates, not measured execution times.
Actual runtime telemetry can be incorporated in future versions.

Author : Team JARVIS
===============================================================================
"""

from agent_engine.agent_brain.models.execution_node import ExecutionNode


class ExecutionEstimator:
    """
    Estimates execution duration for individual execution nodes.
    """

    # ------------------------------------------------------------------
    # Default duration
    # ------------------------------------------------------------------

    DEFAULT_DURATION = 2.0

    # ------------------------------------------------------------------
    # Action-based estimates
    # ------------------------------------------------------------------

    ACTION_DURATIONS = {
        "click": 0.5,
        "press": 0.5,
        "type": 1.0,
        "input": 1.0,
        "open": 2.0,
        "close": 1.0,
        "launch": 2.0,
        "search": 3.0,
        "navigate": 2.5,
        "read": 1.5,
        "write": 1.5,
        "save": 1.5,
        "download": 3.0,
        "upload": 3.0,
        "execute": 2.0,
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def estimate(self, node: ExecutionNode) -> float:
        """
        Estimates the execution duration of an ExecutionNode.

        Parameters
        ----------
        node : ExecutionNode
            Node whose execution duration should be estimated.

        Returns
        -------
        float
            Estimated execution duration in seconds.
        """

        if node is None:
            return self.DEFAULT_DURATION

        action = node.task.action

        if action is None:
            return self.DEFAULT_DURATION

        normalized_action = action.strip().lower()

        return self.ACTION_DURATIONS.get(
            normalized_action,
            self.DEFAULT_DURATION
        )