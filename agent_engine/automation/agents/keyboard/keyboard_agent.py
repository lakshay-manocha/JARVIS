"""
===============================================================================
File Name   : keyboard_agent.py
Module      : Automation Agents - Keyboard
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Real Keyboard Automation Agent for M5-I.

This class adapts the low-level KeyboardActions implementation to the existing
JARVIS AutomationAgent contract.

Architecture:

    ActionRequest
          ↓
    KeyboardAutomationAgent
          ↓
    KeyboardActions
          ↓
        pynput
          ↓
    Real Keyboard

The agent does NOT:
    - perform planning
    - interpret natural language
    - perform retries
    - make fallback decisions
    - manage task execution state
===============================================================================
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from agent_engine.automation.agents.base import AutomationAgent
from agent_engine.automation.exceptions import (
    AgentCleanupError,
    AgentExecutionError,
    AgentInitializationError,
)
from agent_engine.automation.models.capabilities import AgentCapabilities
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.automation.models.lifecycle import AgentLifecycleState
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType

from .keyboard_actions import KeyboardActions


# =============================================================================
# Keyboard Automation Agent
# =============================================================================


class KeyboardAutomationAgent(AutomationAgent):
    """
    Real keyboard automation agent.

    The agent follows the existing JARVIS AutomationAgent contract while
    delegating low-level keyboard operations to KeyboardActions.
    """

    SUPPORTED_ACTIONS = frozenset(
        {
            "type_text",
            "press_key",
            "hotkey",
            "key_down",
            "key_up",
        }
    )

    # =========================================================================
    # Initialization
    # =========================================================================

    def __init__(
        self,
        *,
        actions: Any = None,
    ) -> None:
        """
        Initialize the keyboard automation agent.

        Args:
            actions:
                Optional keyboard action backend.

                A real KeyboardActions instance is used in production.
                A fake/mock object can be injected during unit testing.
        """

        super().__init__()

        # ---------------------------------------------------------------------
        # Keyboard backend
        # ---------------------------------------------------------------------

        self._actions = (
            actions
            if actions is not None
            else KeyboardActions()
        )

        # ---------------------------------------------------------------------
        # Agent capabilities
        # ---------------------------------------------------------------------

        self._capabilities = AgentCapabilities(
            self.SUPPORTED_ACTIONS
        )

    # =========================================================================
    # Identity
    # =========================================================================

    @property
    def agent_id(self) -> str:
        """
        Return the unique JARVIS agent identifier.
        """

        return "keyboard_agent"

    @property
    def name(self) -> str:
        """
        Return the human-readable agent name.
        """

        return "Keyboard Automation Agent"

    @property
    def description(self) -> str:
        """
        Return the purpose of the keyboard agent.
        """

        return (
            "Controls keyboard input through the JARVIS "
            "Automation Engine using pynput."
        )

    # =========================================================================
    # Tool Type
    # =========================================================================

    @property
    def tool_type(self) -> ToolType:
        """
        Return the ToolType handled by this agent.
        """

        return ToolType.KEYBOARD

    # =========================================================================
    # Metadata
    # =========================================================================

    @property
    def metadata(self) -> dict[str, object]:
        """
        Return metadata describing this automation agent.
        """

        return {
            "agent_id": self.agent_id,
            "agent_type": "keyboard",
            "backend": "pynput",
            "version": "M5-I",
        }

    # =========================================================================
    # Capabilities
    # =========================================================================

    @property
    def capabilities(self) -> AgentCapabilities:
        """
        Return the actions supported by this agent.
        """

        return self._capabilities

    # =========================================================================
    # Backend Access
    # =========================================================================

    @property
    def actions(self) -> Any:
        """
        Return the underlying keyboard action implementation.

        This is primarily useful for controlled testing and diagnostics.
        """

        return self._actions

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def initialize(self) -> None:
        """
        Initialize the keyboard agent.

        pynput's Controller does not require an explicit connection step,
        therefore initialization establishes the JARVIS lifecycle state.
        """

        if self.lifecycle_state == AgentLifecycleState.READY:
            return

        if self.lifecycle_state != AgentLifecycleState.CREATED:
            raise AgentInitializationError(
                "Keyboard agent cannot initialize from lifecycle state "
                f"'{self.lifecycle_state.value}'.",
                agent_id=self.agent_id,
            )

        self._transition_to(
            AgentLifecycleState.INITIALIZING
        )

        try:
            # KeyboardActions creates the pynput Controller.
            # No additional OS initialization is required.

            self._transition_to(
                AgentLifecycleState.READY
            )

        except Exception as exc:

            self._transition_to(
                AgentLifecycleState.FAILED
            )

            if isinstance(
                exc,
                AgentInitializationError,
            ):
                raise

            raise AgentInitializationError(
                f"Failed to initialize keyboard agent: {exc}",
                agent_id=self.agent_id,
            ) from exc

    # =========================================================================
    # Capability Check
    # =========================================================================

    def can_execute(
        self,
        action_request: ActionRequest,
    ) -> bool:
        """
        Determine whether this agent can execute the supplied ActionRequest.

        Requirements:

        1. Request must be an ActionRequest.
        2. Tool must be ToolType.KEYBOARD.
        3. Category must be ActionCategory.KEYBOARD.
        4. Action must be supported by this agent.
        """

        if not isinstance(
            action_request,
            ActionRequest,
        ):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        if action_request.tool != ToolType.KEYBOARD:
            return False

        if action_request.category != ActionCategory.KEYBOARD:
            return False

        return self.supports(
            action_request.action
        )

    # =========================================================================
    # Execution
    # =========================================================================

    def execute(
        self,
        action_request: ActionRequest,
    ) -> AutomationExecutionResult:
        """
        Execute one keyboard ActionRequest.

        Execution failures are converted into
        AutomationExecutionResult objects.

        Retry, timeout, fallback, and state-management policies remain
        outside this agent.
        """

        if not isinstance(
            action_request,
            ActionRequest,
        ):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        start_time = perf_counter()

        # ---------------------------------------------------------------------
        # Capability validation
        # ---------------------------------------------------------------------

        if not self.can_execute(
            action_request
        ):
            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=False,
                error=(
                    "Keyboard agent cannot execute action "
                    f"'{action_request.action}'."
                ),
                execution_time=(
                    perf_counter() - start_time
                ),
                metadata={
                    "agent_id": self.agent_id,
                    "tool": self.tool_type.value,
                    "backend": "pynput",
                    "failure_type": "CAPABILITY",
                },
            )

        try:

            # -----------------------------------------------------------------
            # Lazy initialization
            # -----------------------------------------------------------------

            if self.lifecycle_state == AgentLifecycleState.CREATED:
                self.initialize()

            if self.lifecycle_state != AgentLifecycleState.READY:
                raise AgentExecutionError(
                    "Keyboard agent is not ready; current lifecycle state is "
                    f"'{self.lifecycle_state.value}'.",
                    task_id=action_request.task_id,
                    agent_id=self.agent_id,
                )

            # -----------------------------------------------------------------
            # Execution lifecycle
            # -----------------------------------------------------------------

            self._transition_to(
                AgentLifecycleState.EXECUTING
            )

            action = action_request.action
            parameters = action_request.parameters

            # -----------------------------------------------------------------
            # Action dispatch
            # -----------------------------------------------------------------

            if action == "type_text":

                if "text" not in parameters:
                    raise ValueError(
                        "Missing required parameter: text"
                    )

                text = parameters["text"]

                self._actions.type_text(
                    text
                )

                output = {
                    "text_length": len(text)
                }

            elif action == "press_key":

                if "key" not in parameters:
                    raise ValueError(
                        "Missing required parameter: key"
                    )

                key = parameters["key"]

                self._actions.press_key(
                    key
                )

                output = {
                    "key": key
                }

            elif action == "hotkey":

                if "keys" not in parameters:
                    raise ValueError(
                        "Missing required parameter: keys"
                    )

                keys = parameters["keys"]

                self._actions.hotkey(
                    keys
                )

                output = {
                    "keys": keys
                }

            elif action == "key_down":

                if "key" not in parameters:
                    raise ValueError(
                        "Missing required parameter: key"
                    )

                key = parameters["key"]

                self._actions.key_down(
                    key
                )

                output = {
                    "key": key
                }

            elif action == "key_up":

                if "key" not in parameters:
                    raise ValueError(
                        "Missing required parameter: key"
                    )

                key = parameters["key"]

                self._actions.key_up(
                    key
                )

                output = {
                    "key": key
                }

            else:

                raise AgentExecutionError(
                    f"Unsupported keyboard action: {action}",
                    task_id=action_request.task_id,
                    agent_id=self.agent_id,
                )

            # -----------------------------------------------------------------
            # Successful execution
            # -----------------------------------------------------------------

            execution_time = (
                perf_counter() - start_time
            )

            self._transition_to(
                AgentLifecycleState.READY
            )

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={
                    "agent_id": self.agent_id,
                    "tool": self.tool_type.value,
                    "backend": "pynput",
                    "attempt": action_request.metadata.get(
                        "attempt"
                    ),
                },
            )

        except Exception as exc:

            execution_time = (
                perf_counter() - start_time
            )

            if self.lifecycle_state == AgentLifecycleState.EXECUTING:
                self._transition_to(
                    AgentLifecycleState.FAILED
                )

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=False,
                error=str(exc),
                execution_time=execution_time,
                metadata={
                    "agent_id": self.agent_id,
                    "tool": self.tool_type.value,
                    "backend": "pynput",
                    "exception_type": type(exc).__name__,
                },
            )

    # =========================================================================
    # Cleanup
    # =========================================================================

    def cleanup(self) -> None:
        """
        Release keyboard resources and modifier keys.
        """

        if self.lifecycle_state == AgentLifecycleState.CLEANED:
            return

        # ---------------------------------------------------------------------
        # CREATED -> CLEANED
        # ---------------------------------------------------------------------

        if self.lifecycle_state == AgentLifecycleState.CREATED:
            self._transition_to(
                AgentLifecycleState.CLEANED
            )
            return

        # ---------------------------------------------------------------------
        # EXECUTING -> FAILED
        # ---------------------------------------------------------------------

        if self.lifecycle_state == AgentLifecycleState.EXECUTING:
            self._transition_to(
                AgentLifecycleState.FAILED
            )

        # ---------------------------------------------------------------------
        # Validate cleanup state
        # ---------------------------------------------------------------------

        if self.lifecycle_state not in {
            AgentLifecycleState.READY,
            AgentLifecycleState.FAILED,
        }:
            raise AgentCleanupError(
                "Keyboard agent cannot cleanup from lifecycle state "
                f"'{self.lifecycle_state.value}'.",
                agent_id=self.agent_id,
            )

        # ---------------------------------------------------------------------
        # CLEANING_UP
        # ---------------------------------------------------------------------

        self._transition_to(
            AgentLifecycleState.CLEANING_UP
        )

        try:

            self._actions.release_all()

            self._transition_to(
                AgentLifecycleState.CLEANED
            )

        except Exception as exc:

            self._transition_to(
                AgentLifecycleState.FAILED
            )

            if isinstance(
                exc,
                AgentCleanupError,
            ):
                raise

            raise AgentCleanupError(
                f"Failed to cleanup keyboard agent: {exc}",
                agent_id=self.agent_id,
            ) from exc