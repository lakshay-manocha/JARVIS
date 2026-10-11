"""
===============================================================================
File Name   : capabilities.py
Module      : Automation Engine - Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the capability model used by Automation Agents.

An Automation Agent declares the actions it is capable of executing through
this model. The capability model is declarative only; it does not execute
actions or contain execution logic.

Responsibilities:
    - Store supported automation actions.
    - Normalize action names for capability checks.
    - Check whether an action is supported.
    - Expose the declared capabilities.

It does NOT:
    - execute actions
    - resolve execution handlers
    - manage retries
    - manage fallbacks
    - manage task state
    - perform planning
    - communicate with the LLM

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from collections.abc import Iterable


# =============================================================================
# Agent Capabilities
# =============================================================================

class AgentCapabilities:
    """
    Declarative collection of actions supported by an Automation Agent.

    The capability model answers a simple question:

        "Can this Automation Agent execute this action?"

    It does not perform the execution itself.
    """

    def __init__(self, actions: Iterable[str] | None = None) -> None:
        """
        Initialize the capability model.

        Args:
            actions:
                Iterable containing action names supported by the agent.

        Raises:
            ValueError:
                If an action name is empty or contains only whitespace.

            TypeError:
                If an action is not a string.
        """

        if actions is None:
            actions = ()

        normalized_actions: set[str] = set()

        for action in actions:

            if not isinstance(action, str):
                raise TypeError(
                    "Capability action names must be strings."
                )

            normalized_action = action.strip().lower()

            if not normalized_action:
                raise ValueError(
                    "Capability action name cannot be empty."
                )

            normalized_actions.add(normalized_action)

        self._actions: frozenset[str] = frozenset(normalized_actions)

    # -------------------------------------------------------------------------
    # Capability Query
    # -------------------------------------------------------------------------

    def supports(self, action: str) -> bool:
        """
        Check whether the agent supports the specified action.

        Action matching is case-insensitive and ignores surrounding
        whitespace.

        Args:
            action:
                Action name to check.

        Returns:
            True if the action is supported, otherwise False.

        Raises:
            TypeError:
                If action is not a string.
        """

        if not isinstance(action, str):
            raise TypeError(
                "Action name must be a string."
            )

        normalized_action = action.strip().lower()

        if not normalized_action:
            return False

        return normalized_action in self._actions

    # -------------------------------------------------------------------------
    # Inspection
    # -------------------------------------------------------------------------

    def all_actions(self) -> frozenset[str]:
        """
        Return all actions supported by the agent.

        Returns:
            Immutable set of canonical capability action names.
        """

        return self._actions

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __contains__(self, action: str) -> bool:
        """
        Allow membership checks using the ``in`` operator.

        Example:
            "type_text" in capabilities
        """

        return self.supports(action)

    def __len__(self) -> int:
        """
        Return the number of supported actions.
        """

        return len(self._actions)

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation.
        """

        actions = sorted(self._actions)

        return (
            f"AgentCapabilities(actions={actions!r})"
        )