"""
===============================================================================
File Name   : mock_agent.py
Module      : Automation Engine - Agents
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides a Mock Automation Agent that adapts the existing
MockAutomationEngine to the standard AutomationAgent contract.

The MockAutomationAgent allows the complete Automation Agent architecture
to be exercised without performing real browser, desktop, filesystem,
keyboard, mouse, or screen operations.

Architecture:

    ActionRequest
          ↓
    MockAutomationAgent
          ↓
    MockAutomationEngine
          ↓
    AutomationExecutionResult

Responsibilities:
    - Implement the AutomationAgent contract
    - Expose agent identity and ToolType
    - Declare supported actions
    - Delegate execution to MockAutomationEngine
    - Convert mock execution results into AutomationExecutionResult
    - Preserve mock engine execution history

It does NOT:
    - perform real automation
    - make retry decisions
    - perform fallback decisions
    - manage Agent Brain state
    - communicate with the LLM

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from typing import Any, Iterable

from agent_engine.automation.agents.base import (
    AutomationAgent,
)
from agent_engine.automation.engine.mock_automation_engine import (
    MockAutomationEngine,
)
from agent_engine.automation.models.capabilities import (
    AgentCapabilities,
)
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import (
    ToolType,
)


class MockAutomationAgent(AutomationAgent):
    """
    Adapter that exposes MockAutomationEngine through the standard
    AutomationAgent interface.

    This class is intentionally thin.

    The existing MockAutomationEngine remains responsible for:
        - action registration
        - action execution
        - parameter passing
        - execution history

    This adapter is responsible for:
        - AutomationAgent identity
        - ToolType
        - capability declaration
        - ActionRequest handling
        - standardized AutomationExecutionResult
    """

    def __init__(
        self,
        *,
        agent_id: str,
        tool_type: ToolType,
        engine: MockAutomationEngine | None = None,
        supported_actions: Iterable[str] | None = None,
        name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the MockAutomationAgent.

        Args:
            agent_id:
                Unique identifier for the mock agent.

            tool_type:
                ToolType represented by this mock agent.

            engine:
                Existing MockAutomationEngine instance.

            supported_actions:
                Actions this agent advertises as executable.

                If omitted, actions registered in the supplied engine are
                used.

            name:
                Optional human-readable agent name.

            description:
                Optional agent description.

            metadata:
                Optional metadata dictionary.
        """

        super().__init__()

        if not isinstance(
            agent_id,
            str,
        ):
            raise TypeError(
                "agent_id must be a string."
            )

        normalized_agent_id = agent_id.strip()

        if not normalized_agent_id:
            raise ValueError(
                "agent_id cannot be empty."
            )

        if not isinstance(
            tool_type,
            ToolType,
        ):
            raise TypeError(
                "tool_type must be a ToolType."
            )

        if engine is not None and not isinstance(
            engine,
            MockAutomationEngine,
        ):
            raise TypeError(
                "engine must be a MockAutomationEngine."
            )

        if name is not None and not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "name must be a string."
            )

        if description is not None and not isinstance(
            description,
            str,
        ):
            raise TypeError(
                "description must be a string."
            )

        if metadata is not None and not isinstance(
            metadata,
            dict,
        ):
            raise TypeError(
                "metadata must be a dictionary."
            )

        self._agent_id = normalized_agent_id
        self._tool_type = tool_type
        self._engine = (
            engine
            or MockAutomationEngine()
        )

        if supported_actions is None:
            supported_actions = self._engine.list_actions()

        self._capabilities = AgentCapabilities(
            supported_actions
        )

        self._name = (
            name
            or f"Mock {tool_type.value}"
        )

        self._description = (
            description
            or (
                "Mock automation agent used for "
                "architecture validation and testing."
            )
        )

        self._metadata = dict(
            metadata
            or {}
        )

        self._metadata.setdefault(
            "mock",
            True,
        )

    # =========================================================================
    # Agent Identity
    # =========================================================================

    @property
    def agent_id(self) -> str:
        """
        Return the unique agent identifier.
        """

        return self._agent_id

    @property
    def name(self) -> str:
        """
        Return the human-readable agent name.
        """

        return self._name

    @property
    def description(self) -> str:
        """
        Return the agent description.
        """

        return self._description

    @property
    def tool_type(self) -> ToolType:
        """
        Return the ToolType represented by this agent.
        """

        return self._tool_type

    @property
    def metadata(self) -> dict[str, object]:
        """
        Return agent metadata.

        A copy is returned so callers cannot directly mutate the internal
        metadata dictionary.
        """

        return dict(
            self._metadata
        )

    @property
    def capabilities(self) -> AgentCapabilities:
        """
        Return the declared agent capabilities.
        """

        return self._capabilities

    # =========================================================================
    # Mock Engine Access
    # =========================================================================

    @property
    def engine(self) -> MockAutomationEngine:
        """
        Return the underlying MockAutomationEngine.

        This is primarily useful for tests and controlled demonstrations.
        """

        return self._engine

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def initialize(self) -> None:
        """
        Initialize the mock agent.

        The mock engine does not require external resources, so initialization
        only updates the standard AutomationAgent lifecycle state.
        """

        self._transition_to(
            self._lifecycle_state.INITIALIZING
        )

        self._transition_to(
            self._lifecycle_state.READY
        )

    def cleanup(self) -> None:
        """
        Clean up the mock agent.

        No external resources need to be released.
        """

        if self.lifecycle_state.value == "cleaned":
            return

        if self.lifecycle_state.value == "created":
            self._transition_to(
                self._lifecycle_state.CLEANED
            )
            return

        if self.lifecycle_state.value in {
            "ready",
            "failed",
        }:
            self._transition_to(
                self._lifecycle_state.CLEANING_UP
            )

        if self.lifecycle_state.value == "cleaning_up":
            self._transition_to(
                self._lifecycle_state.CLEANED
            )

    # =========================================================================
    # Capability Validation
    # =========================================================================

    def can_execute(
        self,
        action_request: ActionRequest,
    ) -> bool:
        """
        Determine whether this mock agent can execute the request.

        The request must:
            1. Be an ActionRequest.
            2. Target this agent's ToolType.
            3. Reference an action supported by this agent.
            4. Have that action registered in the underlying mock engine.
        """

        if not isinstance(
            action_request,
            ActionRequest,
        ):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        if action_request.tool != self._tool_type:
            return False

        if not self._capabilities.supports(
            action_request.action
        ):
            return False

        return self._engine.contains(
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
        Execute an ActionRequest using the underlying MockAutomationEngine.

        The method always returns AutomationExecutionResult so that the mock
        follows exactly the same result contract as future real agents.
        """

        if not isinstance(
            action_request,
            ActionRequest,
        ):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        if not self.can_execute(
            action_request
        ):
            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=False,
                error=(
                    f"Mock agent '{self._agent_id}' cannot execute "
                    f"action '{action_request.action}'."
                ),
                metadata={
                    "mock": True,
                    "agent_id": self._agent_id,
                    "tool_type": self._tool_type.value,
                    "failure_type": "VALIDATION",
                },
            )

        try:
            result = self._engine.execute(
                action_request.action,
                action_request.parameters,
            )

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=True,
                output=result,
                metadata={
                    "mock": True,
                    "agent_id": self._agent_id,
                    "tool_type": self._tool_type.value,
                },
            )

        except ValueError as exc:

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=False,
                error=str(exc),
                metadata={
                    "mock": True,
                    "agent_id": self._agent_id,
                    "tool_type": self._tool_type.value,
                    "failure_type": "VALIDATION",
                },
            )

        except KeyError as exc:

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=False,
                error=str(exc),
                metadata={
                    "mock": True,
                    "agent_id": self._agent_id,
                    "tool_type": self._tool_type.value,
                    "failure_type": "UNKNOWN",
                },
            )

        except Exception as exc:

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=False,
                error=str(exc),
                metadata={
                    "mock": True,
                    "agent_id": self._agent_id,
                    "tool_type": self._tool_type.value,
                    "failure_type": "UNKNOWN",
                },
            )