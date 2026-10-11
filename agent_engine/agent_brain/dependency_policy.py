"""
===============================================================================
File Name   : dependency_policy.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the policy used by GraphBuilder to decide whether a detected
dependency should become an execution graph edge.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from agent_engine.agent_brain.models.dependency_result import DependencyResult
from agent_engine.contracts.dependency_types import DependencyType


class DependencyPolicy:
    """
    Determines whether a detected dependency should be promoted
    to a graph edge.
    """

    # ------------------------------------------------------------------
    # Minimum confidence thresholds
    # ------------------------------------------------------------------

    MIN_CONFIDENCE = 0.70

    STRONG_DEPENDENCY_TYPES = {
        DependencyType.DATA,
        DependencyType.RESOURCE,
        DependencyType.STATE,
        DependencyType.EXECUTION,
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def should_create_edge(
        self,
        result: DependencyResult,
    ) -> bool:
        """
        Decide whether a dependency result should become
        an execution graph edge.
        """

        # --------------------------------------------------------------
        # Explicit negative result
        # --------------------------------------------------------------

        if not result.depends_on:
            return False

        # --------------------------------------------------------------
        # Invalid confidence
        # --------------------------------------------------------------

        if result.confidence < self.MIN_CONFIDENCE:
            return False

        # --------------------------------------------------------------
        # Strong dependency types
        # --------------------------------------------------------------

        if result.dependency_type in self.STRONG_DEPENDENCY_TYPES:
            return True

        # --------------------------------------------------------------
        # Context dependencies require higher confidence
        # --------------------------------------------------------------

        if result.dependency_type == DependencyType.CONTEXT:
            return result.confidence >= 0.80

        # --------------------------------------------------------------
        # Unknown / NONE dependency types
        # --------------------------------------------------------------

        return False