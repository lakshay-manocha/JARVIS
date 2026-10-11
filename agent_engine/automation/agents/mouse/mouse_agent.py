"""
===============================================================================
File Name   : mouse_agent.py
Module      : Automation Agents - Mouse
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Real Mouse Automation Agent for M5-J.

This class adapts the low-level MouseActions implementation to the existing
JARVIS AutomationAgent contract.

Architecture:

    ActionRequest
          ↓
    MouseAutomationAgent
          ↓
      MouseActions
          ↓
        pynput
          ↓
       Real Mouse

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

from .mouse_actions import MouseActions


class MouseAutomationAgent(AutomationAgent):
    """
    Real mouse automation agent.

    The agent follows the existing JARVIS AutomationAgent contract while
    delegating low-level mouse operations to Manocha's MouseActions
    implementation.
    """

    SUPPORTED_ACTIONS = frozenset(
        {
            "move_mouse",
            "click",
            "double_click",
            "right_click",
            "mouse_down",
            "mouse_up",
            "scroll",
        }
    )

    def __init__(
        self,
        *,
        actions: MouseActions | None = None,
    ) -> None:

        super().__init__()

        self._actions = (
            actions
            if actions is not None
            else MouseActions()
        )
        self._capabilities = AgentCapabilities(
            self.SUPPORTED_ACTIONS
        )

    # =========================================================================
    # Identity
    # =========================================================================

    @property
    def agent_id(self) -> str:
        """Return the unique JARVIS agent identifier."""

        return "mouse_agent"

    @property
    def name(self) -> str:
        """Return the human-readable agent name."""

        return "Mouse Automation Agent"

    @property
    def description(self) -> str:
        """Return the purpose of the agent."""

        return (
            "Controls real mouse input through the JARVIS "
            "Automation Engine using pynput."
        )

    @property
    def tool_type(self) -> ToolType:
        """Return the ToolType handled by this agent."""

        return ToolType.MOUSE

    # =========================================================================
    # Metadata
    # =========================================================================

    @property
    def metadata(self) -> dict[str, object]:
        """Return metadata describing this automation agent."""

        return {
            "agent_id": self.agent_id,
            "agent_type": "mouse",
            "backend": "pynput",
            "version": "M5-J",
        }

    # =========================================================================
    # Capabilities
    # =========================================================================

    @property
    def capabilities(self) -> AgentCapabilities:
        """Return the actions supported by this agent."""

        return self._capabilities

    # =========================================================================
    # Backend Access
    # =========================================================================

    @property
    def actions(self) -> MouseActions:
        """
        Return the underlying mouse action implementation.

        Primarily useful for controlled testing and diagnostics.
        """

        return self._actions

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def initialize(self) -> None:
        """
        Initialize the mouse agent.

        pynput's mouse Controller does not require an explicit connection
        step, therefore initialization establishes the JARVIS lifecycle state.
        """

        if self.lifecycle_state == AgentLifecycleState.READY:
            return

        if self.lifecycle_state != AgentLifecycleState.CREATED:
            raise AgentInitializationError(
                "Mouse agent cannot initialize from lifecycle state "
                f"'{self.lifecycle_state.value}'.",
                agent_id=self.agent_id,
            )

        self._transition_to(
            AgentLifecycleState.INITIALIZING
        )

        try:
            # MouseActions creates the pynput Controller.
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
                f"Failed to initialize mouse agent: {exc}",
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

        The request must:
            1. Be an ActionRequest.
            2. Target ToolType.MOUSE.
            3. Use ActionCategory.MOUSE.
            4. Contain a supported mouse action.
        """

        if not isinstance(
            action_request,
            ActionRequest,
        ):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        if action_request.tool != self.tool_type:
            return False

        if action_request.category != ActionCategory.MOUSE:
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
        Execute one mouse ActionRequest.

        Execution failures are converted into AutomationExecutionResult so
        higher-level JARVIS components can handle failure decisions.
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
                    f"Mouse agent cannot execute action "
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
                    "Mouse agent is not ready; current lifecycle state is "
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

            if action == "move_mouse":

                if "x" not in parameters:
                    raise ValueError(
                        "Missing required parameter: x"
                    )

                if "y" not in parameters:
                    raise ValueError(
                        "Missing required parameter: y"
                    )

                output = self._actions.move_mouse(
                    x=parameters["x"],
                    y=parameters["y"],
                )

            elif action == "click":

                output = self._actions.click(
                    button=parameters.get(
                        "button",
                        "left",
                    )
                )

            elif action == "double_click":

                output = self._actions.double_click(
                    button=parameters.get(
                        "button",
                        "left",
                    )
                )

            elif action == "right_click":

                output = self._actions.right_click()

            elif action == "mouse_down":

                output = self._actions.mouse_down(
                    button=parameters.get(
                        "button",
                        "left",
                    )
                )

            elif action == "mouse_up":

                output = self._actions.mouse_up(
                    button=parameters.get(
                        "button",
                        "left",
                    )
                )

            elif action == "scroll":

                output = self._actions.scroll(
                    dx=parameters.get(
                        "dx",
                        0,
                    ),
                    dy=parameters.get(
                        "dy",
                        0,
                    ),
                )

            else:

                raise ValueError(
                    f"Unsupported mouse action: {action}"
                )

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
        Cleanup mouse resources.

        Manocha's MouseActions uses pynput's Controller and does not require
        an explicit release-all operation for normal cleanup.
        """

        if self.lifecycle_state == AgentLifecycleState.CLEANED:
            return

        if self.lifecycle_state == AgentLifecycleState.CREATED:
            self._transition_to(
                AgentLifecycleState.CLEANED
            )
            return

        if self.lifecycle_state == AgentLifecycleState.EXECUTING:
            self._transition_to(
                AgentLifecycleState.FAILED
            )

        if self.lifecycle_state not in {
            AgentLifecycleState.READY,
            AgentLifecycleState.FAILED,
        }:
            raise AgentCleanupError(
                "Mouse agent cannot cleanup from lifecycle state "
                f"'{self.lifecycle_state.value}'.",
                agent_id=self.agent_id,
            )

        self._transition_to(
            AgentLifecycleState.CLEANING_UP
        )

        try:

            # MouseActions does not maintain pressed-key state like the
            # keyboard backend, so no explicit release_all() is required.

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
                f"Failed to cleanup mouse agent: {exc}",
                agent_id=self.agent_id,
            ) from exc