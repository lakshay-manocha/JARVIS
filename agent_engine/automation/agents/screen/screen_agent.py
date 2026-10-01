"""
===============================================================================
File Name   : screen_agent.py
Module      : Automation Agents - Screen
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Screen perception agent for JARVIS.

Responsibilities:

    ActionRequest
          ↓
    ScreenAutomationAgent
          ↓
    ScreenAware
          ↓
    Screenshot
          ↓
    EasyOCR / Qwen2-VL
          ↓
    Coordinates

This agent DOES NOT:
    - move the mouse
    - click
    - plan tasks
    - interpret natural language
    - perform retries
    - make fallback decisions

MouseAutomationAgent remains responsible for physical mouse actions.
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

from agent_engine.perception.screen import (
    ScreenAware,
    get_screen_aware,
)


class ScreenAutomationAgent(AutomationAgent):
    """
    JARVIS screen perception agent.

    Uses one persistent ScreenAware instance.
    """

    SUPPORTED_ACTIONS = frozenset(
        {
            "locate",
            "find_text",
            "find_element",
        }
    )

    def __init__(
        self,
        *,
        screen: ScreenAware | None = None,
    ) -> None:

        super().__init__()

        self._screen = (
            screen
            if screen is not None
            else get_screen_aware()
        )

        self._capabilities = AgentCapabilities(
            self.SUPPORTED_ACTIONS
        )

    # =========================================================================
    # Identity
    # =========================================================================

    @property
    def agent_id(self) -> str:
        return "screen_agent"

    @property
    def name(self) -> str:
        return "Screen Automation Agent"

    @property
    def description(self) -> str:
        return (
            "Observes the desktop screen and locates requested "
            "text or visual UI elements using OCR and Qwen2-VL."
        )

    @property
    def tool_type(self) -> ToolType:
        return ToolType.SCREEN

    # =========================================================================
    # Metadata
    # =========================================================================

    @property
    def metadata(self) -> dict[str, object]:

        return {
            "agent_id": self.agent_id,
            "agent_type": "screen",
            "backend": "EasyOCR + Qwen2-VL",
            "version": "M1",
            "persistent_model": True,
        }

    # =========================================================================
    # Capabilities
    # =========================================================================

    @property
    def capabilities(self) -> AgentCapabilities:
        return self._capabilities

    # =========================================================================
    # Backend Access
    # =========================================================================

    @property
    def screen(self) -> ScreenAware:
        return self._screen

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def initialize(self) -> None:

        if self.lifecycle_state == AgentLifecycleState.READY:
            return

        if self.lifecycle_state != AgentLifecycleState.CREATED:

            raise AgentInitializationError(
                "Screen agent cannot initialize from lifecycle "
                f"state '{self.lifecycle_state.value}'.",
                agent_id=self.agent_id,
            )

        self._transition_to(
            AgentLifecycleState.INITIALIZING
        )

        try:

            # This loads EasyOCR + Qwen2-VL exactly once.
            self._screen.initialize()

            self._transition_to(
                AgentLifecycleState.READY
            )

        except Exception as exc:

            self._transition_to(
                AgentLifecycleState.FAILED
            )

            raise AgentInitializationError(
                f"Failed to initialize screen agent: {exc}",
                agent_id=self.agent_id,
            ) from exc

    # =========================================================================
    # Capability Check
    # =========================================================================

    def can_execute(
        self,
        action_request: ActionRequest,
    ) -> bool:

        if not isinstance(
            action_request,
            ActionRequest,
        ):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        if action_request.tool != self.tool_type:
            return False

        if action_request.category != ActionCategory.SCREEN:
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

        if not isinstance(
            action_request,
            ActionRequest,
        ):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        start_time = perf_counter()

        if not self.can_execute(
            action_request
        ):

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=False,
                error=(
                    f"Screen agent cannot execute action "
                    f"'{action_request.action}'."
                ),
                execution_time=(
                    perf_counter() - start_time
                ),
                metadata={
                    "agent_id": self.agent_id,
                    "tool": self.tool_type.value,
                    "failure_type": "CAPABILITY",
                },
            )

        try:

            # -----------------------------------------------------------------
            # Lazy initialization
            # -----------------------------------------------------------------

            if (
                self.lifecycle_state
                == AgentLifecycleState.CREATED
            ):
                self.initialize()

            if (
                self.lifecycle_state
                != AgentLifecycleState.READY
            ):

                raise AgentExecutionError(
                    "Screen agent is not ready; current lifecycle "
                    f"state is '{self.lifecycle_state.value}'.",
                    task_id=action_request.task_id,
                    agent_id=self.agent_id,
                )

            self._transition_to(
                AgentLifecycleState.EXECUTING
            )

            action = action_request.action
            parameters = action_request.parameters

            # -----------------------------------------------------------------
            # Query
            # -----------------------------------------------------------------

            query = parameters.get("query")

            if not query:

                # Support "text" as an alternate parameter.
                query = parameters.get("text")

            if not query:

                raise ValueError(
                    "Missing required parameter: query"
                )

            # -----------------------------------------------------------------
            # Locate
            # -----------------------------------------------------------------

            result = self._screen.find(
                str(query)
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
                success=bool(result["found"]),
                output=result,
                error=(
                    None
                    if result["found"]
                    else f"Could not locate '{query}' on screen."
                ),
                execution_time=execution_time,
                metadata={
                    "agent_id": self.agent_id,
                    "tool": self.tool_type.value,
                    "method": result.get("method"),
                    "confidence": result.get(
                        "confidence"
                    ),
                    "coordinates": result.get(
                        "coordinates"
                    ),
                    "screen_latency": result.get(
                        "latency"
                    ),
                },
            )

        except Exception as exc:

            execution_time = (
                perf_counter() - start_time
            )

            if (
                self.lifecycle_state
                == AgentLifecycleState.EXECUTING
            ):
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
                    "exception_type": type(exc).__name__,
                },
            )

    # =========================================================================
    # Cleanup
    # =========================================================================

    def cleanup(self) -> None:

        if (
            self.lifecycle_state
            == AgentLifecycleState.CLEANED
        ):
            return

        if (
            self.lifecycle_state
            == AgentLifecycleState.CREATED
        ):

            self._transition_to(
                AgentLifecycleState.CLEANED
            )

            return

        if (
            self.lifecycle_state
            == AgentLifecycleState.EXECUTING
        ):

            self._transition_to(
                AgentLifecycleState.FAILED
            )

        if self.lifecycle_state not in {
            AgentLifecycleState.READY,
            AgentLifecycleState.FAILED,
        }:

            raise AgentCleanupError(
                "Screen agent cannot cleanup from lifecycle "
                f"state '{self.lifecycle_state.value}'.",
                agent_id=self.agent_id,
            )

        self._transition_to(
            AgentLifecycleState.CLEANING_UP
        )

        try:

            # Do NOT destroy the singleton here during normal agent cleanup.
            #
            # Other JARVIS tasks may still use ScreenAware.
            #
            # Actual model release should happen during complete JARVIS
            # shutdown.

            self._transition_to(
                AgentLifecycleState.CLEANED
            )

        except Exception as exc:

            self._transition_to(
                AgentLifecycleState.FAILED
            )

            raise AgentCleanupError(
                f"Failed to cleanup screen agent: {exc}",
                agent_id=self.agent_id,
            ) from exc