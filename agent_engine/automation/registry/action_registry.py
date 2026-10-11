"""
===============================================================================
File Name   : action_registry.py
Module      : Automation Engine - Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Maintains the mapping between supported automation actions and their
corresponding execution handlers.

The Action Registry is responsible only for action-to-handler resolution.

It does NOT:
    - execute actions
    - manage retries
    - manage task state
    - perform fallback decisions
    - modify Agent Engine state

Those responsibilities belong to the Dispatcher, Decision Manager,
State Manager, and Automation handlers respectively.

Author      : Team Automation
===============================================================================
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


# =============================================================================
# Type Definition
# =============================================================================

ActionHandler = Callable[..., Any]


# =============================================================================
# Action Registry
# =============================================================================

class ActionRegistry:
    """
    Registry responsible for mapping action names to execution handlers.
    """

    def __init__(self) -> None:
        """
        Initialize an empty action registry.
        """

        self._handlers: dict[str, ActionHandler] = {}

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def register(
        self,
        action: str,
        handler: ActionHandler,
    ) -> None:
        """
        Register a handler for an action.

        Args:
            action:
                Name of the automation action.

            handler:
                Callable responsible for executing that action.

        Raises:
            ValueError:
                If the action name is empty.

            TypeError:
                If the handler is not callable.
        """

        if not action or not action.strip():
            raise ValueError("Action name cannot be empty.")

        if not callable(handler):
            raise TypeError("Action handler must be callable.")

        normalized_action = action.strip().lower()

        self._handlers[normalized_action] = handler

    # -------------------------------------------------------------------------
    # Resolution
    # -------------------------------------------------------------------------

    def resolve(self, action: str) -> ActionHandler:
        """
        Resolve the handler associated with an action.

        Args:
            action:
                Name of the action to resolve.

        Returns:
            Registered action handler.

        Raises:
            ValueError:
                If the action name is empty.

            KeyError:
                If no handler is registered for the action.
        """

        if not action or not action.strip():
            raise ValueError("Action name cannot be empty.")

        normalized_action = action.strip().lower()

        try:
            return self._handlers[normalized_action]
        except KeyError:
            raise KeyError(
                f"No handler registered for action: '{action}'"
            ) from None

    # -------------------------------------------------------------------------
    # Query
    # -------------------------------------------------------------------------

    def contains(self, action: str) -> bool:
        """
        Check whether an action is registered.
        """

        if not action or not action.strip():
            return False

        normalized_action = action.strip().lower()

        return normalized_action in self._handlers

    # -------------------------------------------------------------------------
    # Removal
    # -------------------------------------------------------------------------

    def unregister(self, action: str) -> None:
        """
        Remove an action handler from the registry.

        Raises:
            KeyError:
                If the action is not registered.
        """

        if not action or not action.strip():
            raise ValueError("Action name cannot be empty.")

        normalized_action = action.strip().lower()

        try:
            del self._handlers[normalized_action]
        except KeyError:
            raise KeyError(
                f"No handler registered for action: '{action}'"
            ) from None

    # -------------------------------------------------------------------------
    # Inspection
    # -------------------------------------------------------------------------

    def list_actions(self) -> list[str]:
        """
        Return all registered action names.
        """

        return sorted(self._handlers.keys())

    def clear(self) -> None:
        """
        Remove all registered action handlers.
        """

        self._handlers.clear()

    def __len__(self) -> int:
        """
        Return number of registered actions.
        """

        return len(self._handlers)