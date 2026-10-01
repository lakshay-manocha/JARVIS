"""
===============================================================================
File Name   : browser_agent.py
Module      : Automation Agents - Browser
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Concrete real Browser Automation Agent for M5-H.

This class implements the existing Phase-G AutomationAgent contract and
delegates actual browser operations to BrowserBackend.

The agent does not implement planning, retry, fallback, or task-state logic.
===============================================================================
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from agent_engine.automation.agents.base import AutomationAgent
from agent_engine.automation.agents.browser.browser_backend import BrowserBackend
from agent_engine.automation.agents.browser.browser_config import BrowserConfig
from agent_engine.automation.exceptions import (
    AgentCapabilityError,
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


class BrowserAutomationAgent(AutomationAgent):
    """
    Real browser automation agent.

    The default backend is Playwright-backed BrowserBackend. A backend can be
    injected for unit testing, keeping browser tests deterministic and making
    the agent independent from a real browser during unit-level testing.
    """

    SUPPORTED_ACTIONS = frozenset(
        {
            "open",
            "open_url",
            "search",
            "go_back",
            "go_forward",
            "refresh",
            "click",
            "click_element",
            "type_text",
            "get_page_title",
            "get_current_url",
            "get_text",
            "extract_text",
            "new_tab",
            "switch_tab",
            "close_tab",
            "close",
        }
    )

    def __init__(
        self,
        *,
        config: BrowserConfig | None = None,
        backend: BrowserBackend | None = None,
    ) -> None:
        super().__init__()

        if backend is not None and not isinstance(backend, BrowserBackend):
            raise TypeError("backend must be a BrowserBackend.")

        self._config = config or BrowserConfig()
        self._backend = backend or BrowserBackend(self._config)
        self._capabilities = AgentCapabilities(self.SUPPORTED_ACTIONS)

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------

    @property
    def agent_id(self) -> str:
        return "browser_agent"

    @property
    def name(self) -> str:
        return "Browser Automation Agent"

    @property
    def description(self) -> str:
        return (
            "Controls a real web browser through the JARVIS Automation "
            "Agent architecture."
        )

    @property
    def tool_type(self) -> ToolType:
        return ToolType.BROWSER

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "agent_type": "browser",
            "backend": "playwright",
            "browser": self._config.browser,
            "headless": self._config.headless,
            "version": "M5-H",
        }

    @property
    def capabilities(self) -> AgentCapabilities:
        return self._capabilities

    @property
    def backend(self) -> BrowserBackend:
        return self._backend

    @property
    def config(self) -> BrowserConfig:
        return self._config

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def initialize(self) -> None:
        if self.lifecycle_state == AgentLifecycleState.READY:
            return

        if self.lifecycle_state != AgentLifecycleState.CREATED:
            raise AgentInitializationError(
                f"Browser agent cannot initialize from lifecycle state "
                f"'{self.lifecycle_state.value}'."
            )

        self._transition_to(AgentLifecycleState.INITIALIZING)

        try:
            self._backend.initialize()
            self._transition_to(AgentLifecycleState.READY)
        except Exception as exc:
            self._transition_to(AgentLifecycleState.FAILED)

            if isinstance(exc, AgentInitializationError):
                raise

            raise AgentInitializationError(
                f"Failed to initialize browser agent: {exc}",
                agent_id=self.agent_id,
            ) from exc

    # -------------------------------------------------------------------------
    # Capability Check
    # -------------------------------------------------------------------------

    def can_execute(self, action_request: ActionRequest) -> bool:
        if not isinstance(action_request, ActionRequest):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        if action_request.tool != self.tool_type:
            return False

        if action_request.category != ActionCategory.BROWSER:
            return False

        return self.supports(action_request.action)

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def execute(
        self,
        action_request: ActionRequest,
    ) -> AutomationExecutionResult:
        if not isinstance(action_request, ActionRequest):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        start_time = perf_counter()

        if not self.can_execute(action_request):
            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=False,
                error=(
                    f"Browser agent cannot execute action "
                    f"'{action_request.action}'."
                ),
                execution_time=perf_counter() - start_time,
                metadata={
                    "agent_id": self.agent_id,
                    "tool": self.tool_type.value,
                },
            )

        try:
            # G.10 dispatcher currently does not own agent initialization.
            # Lazy initialization therefore keeps the new real agent
            # compatible with the already-completed dispatcher architecture.
            if self.lifecycle_state == AgentLifecycleState.CREATED:
                self.initialize()

            if self.lifecycle_state != AgentLifecycleState.READY:
                raise AgentExecutionError(
                    f"Browser agent is not ready; current state is "
                    f"'{self.lifecycle_state.value}'.",
                    task_id=action_request.task_id,
                    agent_id=self.agent_id,
                )

            self._transition_to(AgentLifecycleState.EXECUTING)

            output = self._backend.execute(
                action_request.action,
                action_request.parameters,
                timeout_seconds=action_request.timeout_seconds,
            )

            execution_time = perf_counter() - start_time
            self._transition_to(AgentLifecycleState.READY)

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={
                    "agent_id": self.agent_id,
                    "tool": self.tool_type.value,
                    "backend": "playwright",
                    "attempt": action_request.metadata.get("attempt"),
                },
            )

        except Exception as exc:
            execution_time = perf_counter() - start_time

            if self.lifecycle_state == AgentLifecycleState.EXECUTING:
                self._transition_to(AgentLifecycleState.FAILED)

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=False,
                error=str(exc),
                execution_time=execution_time,
                metadata={
                    "agent_id": self.agent_id,
                    "tool": self.tool_type.value,
                    "backend": "playwright",
                    "exception_type": type(exc).__name__,
                },
            )

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def cleanup(self) -> None:
        if self.lifecycle_state == AgentLifecycleState.CLEANED:
            return

        if self.lifecycle_state == AgentLifecycleState.CREATED:
            self._transition_to(AgentLifecycleState.CLEANED)
            return

        if self.lifecycle_state == AgentLifecycleState.EXECUTING:
            self._transition_to(AgentLifecycleState.FAILED)

        if self.lifecycle_state not in {
            AgentLifecycleState.READY,
            AgentLifecycleState.FAILED,
        }:
            raise AgentCleanupError(
                f"Browser agent cannot cleanup from lifecycle state "
                f"'{self.lifecycle_state.value}'.",
                agent_id=self.agent_id,
            )

        self._transition_to(AgentLifecycleState.CLEANING_UP)

        try:
            self._backend.cleanup()
            self._transition_to(AgentLifecycleState.CLEANED)
        except Exception as exc:
            self._transition_to(AgentLifecycleState.FAILED)

            if isinstance(exc, AgentCleanupError):
                raise

            raise AgentCleanupError(
                f"Failed to cleanup browser agent: {exc}",
                agent_id=self.agent_id,
            ) from exc
