"""
===============================================================================
File Name   : mock_automation_engine.py
Module      : Automation Engine - Engine
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides a deterministic mock implementation of the Automation Engine.

The MockAutomationEngine simulates execution of automation actions without
controlling a real browser, desktop, filesystem, keyboard, mouse, or screen.

It is intentionally isolated from the Agent Brain so that the complete
Agentic -> Automation execution pipeline can be tested safely before real
automation controllers are introduced.

Responsibilities:
    - Execute registered automation actions
    - Validate action parameters
    - Produce deterministic execution results
    - Support controlled success/failure simulation
    - Remain independent from Agent Engine state

It does NOT:
    - decide retry policy
    - decide fallback
    - modify task state
    - perform orchestration
    - control real external applications

Author      : Team Automation
===============================================================================
"""

from __future__ import annotations

from typing import Any, Callable


# =============================================================================
# Type Definitions
# =============================================================================

MockHandler = Callable[..., Any]


# =============================================================================
# Mock Automation Engine
# =============================================================================

class MockAutomationEngine:
    """
    Deterministic automation engine used for Module 5 development and testing.
    """

    def __init__(self) -> None:
        """
        Initialize the mock automation engine.
        """

        self._handlers: dict[str, MockHandler] = {}
        self._execution_history: list[dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Handler Registration
    # -------------------------------------------------------------------------

    def register(
        self,
        action: str,
        handler: MockHandler,
    ) -> None:
        """
        Register a mock handler for an automation action.

        Args:
            action:
                Name of the action.

            handler:
                Callable that simulates the action.

        Raises:
            ValueError:
                If action name is empty.

            TypeError:
                If handler is not callable.
        """

        if not action or not action.strip():
            raise ValueError("Action name cannot be empty.")

        if not callable(handler):
            raise TypeError("Mock action handler must be callable.")

        self._handlers[action.strip().lower()] = handler

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def execute(
        self,
        action: str,
        parameters: dict[str, Any] | None = None,
    ) -> Any:
        """
        Execute a registered mock action.

        Args:
            action:
                Action to execute.

            parameters:
                Parameters required by the action.

        Returns:
            Result returned by the registered mock handler.

        Raises:
            ValueError:
                If action name is empty.

            KeyError:
                If action is not registered.
        """

        if not action or not action.strip():
            raise ValueError("Action name cannot be empty.")

        normalized_action = action.strip().lower()
        parameters = parameters or {}

        if normalized_action not in self._handlers:
            raise KeyError(
                f"No mock handler registered for action: '{action}'"
            )

        handler = self._handlers[normalized_action]

        result = handler(**parameters)

        self._execution_history.append(
            {
                "action": normalized_action,
                "parameters": parameters.copy(),
                "result": result,
            }
        )

        return result

    # -------------------------------------------------------------------------
    # Inspection
    # -------------------------------------------------------------------------

    def list_actions(self) -> list[str]:
        """
        Return all registered mock actions.
        """

        return sorted(self._handlers.keys())

    def get_execution_history(self) -> list[dict[str, Any]]:
        """
        Return a copy of the execution history.
        """

        return list(self._execution_history)

    def clear_history(self) -> None:
        """
        Clear recorded execution history.
        """

        self._execution_history.clear()

    def contains(self, action: str) -> bool:
        """
        Check whether a mock action is registered.
        """

        if not action or not action.strip():
            return False

        return action.strip().lower() in self._handlers
# =============================================================================
# Default Mock Actions
# =============================================================================

def create_default_mock_engine() -> MockAutomationEngine:
    """
    Create a mock automation engine with standard JARVIS actions registered.
    """

    engine = MockAutomationEngine()

    # -------------------------------------------------------------------------
    # Browser Actions
    # -------------------------------------------------------------------------

    engine.register(
        "open",
        lambda **kwargs: {
            "action": "open",
            "message": "Application opened successfully.",
            "parameters": kwargs,
        },
    )

    engine.register(
        "open_url",
        lambda **kwargs: {
            "action": "open_url",
            "message": f"URL opened successfully: {kwargs.get('url')}",
            "parameters": kwargs,
        },
    )

    engine.register(
        "search",
        lambda **kwargs: {
            "action": "search",
            "message": f"Search completed for: {kwargs.get('query')}",
            "parameters": kwargs,
        },
    )

    # -------------------------------------------------------------------------
    # Keyboard Actions
    # -------------------------------------------------------------------------

    engine.register(
        "type_text",
        lambda **kwargs: {
            "action": "type_text",
            "message": f"Text typed: {kwargs.get('text')}",
            "parameters": kwargs,
        },
    )

    # -------------------------------------------------------------------------
    # Mouse Actions
    # -------------------------------------------------------------------------

    engine.register(
        "click",
        lambda **kwargs: {
            "action": "click",
            "message": "Click action completed.",
            "parameters": kwargs,
        },
    )

    # -------------------------------------------------------------------------
    # System Actions
    # -------------------------------------------------------------------------

    engine.register(
        "wait",
        lambda **kwargs: {
            "action": "wait",
            "message": f"Wait simulated for {kwargs.get('seconds')} seconds.",
            "parameters": kwargs,
        },
    )

    # -------------------------------------------------------------------------
    # Screen Actions
    # -------------------------------------------------------------------------

    engine.register(
        "take_screenshot",
        lambda **kwargs: {
            "action": "take_screenshot",
            "message": "Screenshot captured successfully.",
            "parameters": kwargs,
        },
    )

    return engine