"""
===============================================================================
File Name   : base.py
Module      : Automation Engine - Agents
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the abstract base contract for all Automation Agents.

The AutomationAgent establishes the common interface that concrete
automation agents must implement.

Examples:
    - Browser Agent
    - Keyboard Agent
    - Mouse Agent
    - Desktop/Application Agent
    - Filesystem Agent
    - Screen/Vision Agent

The base contract defines:
    - Agent identity
    - Agent metadata
    - Agent tool type
    - Agent capabilities
    - Agent lifecycle
    - Action execution interface
    - Standardized execution result

It does NOT:
    - perform planning
    - interpret natural language
    - make retry decisions
    - perform fallback decisions
    - manage execution state
    - communicate directly with the LLM

Those responsibilities belong to the appropriate Agent Brain,
Decision Manager, State Manager, and orchestration components.

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent_engine.automation.models.capabilities import AgentCapabilities
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.automation.models.lifecycle import (
    AgentLifecycleState,
    can_transition,
)
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ToolType


# =============================================================================
# Automation Agent
# =============================================================================

class AutomationAgent(ABC):
    """
    Abstract base class for all JARVIS Automation Agents.

    Concrete agents must implement the identity, capability, lifecycle,
    and execution methods defined by this contract.
    """

    def __init__(self) -> None:
        """
        Initialize the base automation agent.

        Every agent starts in the CREATED lifecycle state.
        """

        self._lifecycle_state = AgentLifecycleState.CREATED

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """
        Return the unique identifier of the automation agent.
        """
        raise NotImplementedError

    @property
    def lifecycle_state(self) -> AgentLifecycleState:
        """
        Return the current lifecycle state of the agent.
        """
        return self._lifecycle_state

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the human-readable name of the agent.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Return a description of the agent's purpose.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Tool Type
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def tool_type(self) -> ToolType:
        """
        Return the ToolType handled by this agent.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def metadata(self) -> dict[str, object]:
        """
        Return metadata describing the automation agent.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Capabilities
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def capabilities(self) -> AgentCapabilities:
        """
        Return the actions supported by this automation agent.
        """
        raise NotImplementedError

    def supports(self, action: str) -> bool:
        """
        Check whether this automation agent supports an action.

        Args:
            action:
                Action name to check.

        Returns:
            True if the agent supports the action, otherwise False.
        """

        return self.capabilities.supports(action)

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize resources required by the automation agent.

        Expected lifecycle behavior:
            CREATED -> INITIALIZING -> READY

        If initialization fails:
            INITIALIZING -> FAILED

        Concrete agents are responsible for calling _transition_to()
        at the appropriate points in their implementation.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Execution Capability
    # -------------------------------------------------------------------------

    @abstractmethod
    def can_execute(
        self,
        action_request: ActionRequest,
    ) -> bool:
        """
        Determine whether the agent can execute the supplied ActionRequest.

        This method only performs contract-level capability validation.

        It does not execute the action and does not modify lifecycle state.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    @abstractmethod
    def execute(
        self,
        action_request: ActionRequest,
    ) -> AutomationExecutionResult:
        """
        Execute the supplied ActionRequest.

        Expected lifecycle behavior:
            READY -> EXECUTING -> READY

        If execution fails:
            EXECUTING -> FAILED

        Returns:
            AutomationExecutionResult containing the immediate result
            of the automation attempt.

        Note:
            Retry, timeout policy, fallback, and state management are
            handled by higher-level components.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    @abstractmethod
    def cleanup(self) -> None:
        """
        Release resources owned by the automation agent.

        Expected lifecycle behavior:
            READY -> CLEANING_UP -> CLEANED

        Cleanup may also be performed after a failure:

            FAILED -> CLEANING_UP -> CLEANED

        Concrete agents are responsible for calling _transition_to()
        at the appropriate points in their implementation.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Lifecycle Transition
    # -------------------------------------------------------------------------

    def _transition_to(self, target: AgentLifecycleState) -> None:
        """
        Transition the agent to a new lifecycle state.

        Only transitions defined by VALID_LIFECYCLE_TRANSITIONS are allowed.

        Args:
            target:
                Desired lifecycle state.

        Raises:
            RuntimeError:
                If the requested lifecycle transition is invalid.
        """

        current = self._lifecycle_state

        if not can_transition(current, target):
            raise RuntimeError(
                f"Invalid agent lifecycle transition: "
                f"{current.value} -> {target.value}"
            )

        self._lifecycle_state = target
