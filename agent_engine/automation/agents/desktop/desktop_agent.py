"""
Application & Window Automation Agent for M5-K.

This agent provides the JARVIS automation-layer interface for:

Application lifecycle:
    - launch_application
    - close_application
    - restart_application
    - terminate_application

Window management:
    - focus_window
    - switch_window
    - resize_window
    - position_window

The agent delegates OS-specific operations to a concrete DesktopBackend.
"""

from __future__ import annotations

from typing import Any

from agent_engine.automation.models.capabilities import AgentCapabilities
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.automation.models.lifecycle import AgentLifecycleState
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType
from agent_engine.decision_manager.models.execution_outcome import FailureType

from agent_engine.automation.agents.base import AutomationAgent

from .application_controller import ApplicationController
from .desktop_backend import DesktopBackend
from .window_controller import WindowController


class ApplicationWindowAutomationAgent(AutomationAgent):
    """
    M5-K Application & Window Automation Agent.

    Responsibilities:
        - Application lifecycle automation.
        - Application-window management.
        - Action validation and routing.
        - Delegation to application/window controllers.
        - Standardized AutomationExecutionResult generation.

    This agent does NOT perform:
        - planning
        - scheduling
        - retry/fallback
        - process monitoring
        - filesystem automation
        - keyboard automation
        - mouse automation
        - browser automation
        - screen/OCR automation
        - LLM communication
    """

    SUPPORTED_ACTIONS = frozenset(
        {
            "launch_application",
            "close_application",
            "restart_application",
            "terminate_application",
            "focus_window",
            "switch_window",
            "resize_window",
            "position_window",
        }
    )

    APPLICATION_ACTIONS = frozenset(
        {
            "launch_application",
            "close_application",
            "restart_application",
            "terminate_application",
        }
    )

    WINDOW_ACTIONS = frozenset(
        {
            "focus_window",
            "switch_window",
            "resize_window",
            "position_window",
        }
    )

    def __init__(
        self,
        *,
        backend: DesktopBackend,
    ) -> None:
        """
        Initialize the Application & Window Automation Agent.

        Args:
            backend:
                A concrete implementation of DesktopBackend.

        The concrete backend is injected so that the agent remains
        independent from OS-specific implementation details.
        """
        super().__init__()

        if not isinstance(backend, DesktopBackend):
            raise TypeError(
                "backend must be a DesktopBackend."
            )

        self._backend = backend

        self._application_controller = ApplicationController(
            self._backend
        )

        self._window_controller = WindowController(
            self._backend
        )

        self._capabilities = AgentCapabilities(
            self.SUPPORTED_ACTIONS
        )

    # ------------------------------------------------------------------
    # Agent identity
    # ------------------------------------------------------------------

    @property
    def agent_id(self) -> str:
        return "desktop_agent"

    @property
    def name(self) -> str:
        return "Application & Window Automation Agent"

    @property
    def description(self) -> str:
        return (
            "Controls application lifecycle and application-window "
            "operations through a DesktopBackend."
        )

    @property
    def tool_type(self) -> ToolType:
        return ToolType.DESKTOP

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "agent_type": "application_window",
            "tool_type": self.tool_type.value,
            "backend": type(self._backend).__name__,
            "version": "M5-K",
        }

    @property
    def capabilities(self) -> AgentCapabilities:
        return self._capabilities

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """
        Initialize the agent.

        The backend itself is currently dependency-injected and does not
        require an additional initialization contract at this layer.
        """
        current_state = self.lifecycle_state

        if current_state == AgentLifecycleState.CREATED:
            self._transition_to(
                AgentLifecycleState.INITIALIZING
            )

            try:
                self._transition_to(
                    AgentLifecycleState.READY
                )
            except Exception:
                self._transition_to(
                    AgentLifecycleState.FAILED
                )
                raise

            return

        if current_state == AgentLifecycleState.READY:
            return

        raise RuntimeError(
            f"Cannot initialize agent from lifecycle state: "
            f"{current_state.value}"
        )

    # ------------------------------------------------------------------
    # Capability validation
    # ------------------------------------------------------------------

    def can_execute(
        self,
        action_request: ActionRequest,
    ) -> bool:
        """
        Determine whether this agent can execute the supplied request.

        Requirements:
            - ActionRequest must be valid.
            - Tool must be DESKTOP.
            - Category must be APPLICATION.
            - Action must be one of the eight M5-K actions.
        """
        if not isinstance(action_request, ActionRequest):
            return False

        if action_request.tool != ToolType.DESKTOP:
            return False

        if action_request.category != ActionCategory.APPLICATION:
            return False

        return self.supports(action_request.action)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        action_request: ActionRequest,
    ) -> AutomationExecutionResult:
        """
        Execute a validated M5-K action request.

        The agent itself does not implement retry, timeout, or fallback.
        Those decisions remain outside the automation agent.
        """
        if not isinstance(action_request, ActionRequest):
            raise TypeError(
                "action_request must be an ActionRequest."
            )

        action = action_request.action.strip().lower()

        if not self.can_execute(action_request):
            return self._failure_result(
                action_request=action_request,
                error=(
                    f"Agent cannot execute action: "
                    f"{action}"
                ),
            )

        if self.lifecycle_state == AgentLifecycleState.CREATED:
            self.initialize()

        if self.lifecycle_state != AgentLifecycleState.READY:
            return self._failure_result(
                action_request=action_request,
                error=(
                    "Agent is not ready for execution. "
                    f"Current state: "
                    f"{self.lifecycle_state.value}"
                ),
            )

        self._transition_to(
            AgentLifecycleState.EXECUTING
        )

        try:
            output = self._execute_action(
                action_request
            )

            self._transition_to(
                AgentLifecycleState.READY
            )

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action,
                success=True,
                output=output,
                metadata={
                    "agent_id": self.agent_id,
                    "agent_type": "application_window",
                    "backend": type(self._backend).__name__,
                },
            )

        except Exception as exc:
            self._transition_to(
                AgentLifecycleState.FAILED
            )

            failure_type = (
                FailureType.VALIDATION
                if isinstance(
                    exc,
                    (
                        ValueError,
                        TypeError,
                    ),
                )
                else FailureType.UNKNOWN
            )

            return self._failure_result(
                action_request=action_request,
                error=str(exc),
                failure_type=failure_type,
            )
    # ------------------------------------------------------------------
    # Action routing
    # ------------------------------------------------------------------

    def _execute_action(
        self,
        action_request: ActionRequest,
    ) -> Any:
        """
        Route an action to the appropriate controller.

        Controllers are responsible for parameter validation and backend
        delegation.
        """
        action = action_request.action.strip().lower()
        parameters = action_request.parameters

        if action in self.APPLICATION_ACTIONS:
            application = self._require_parameter(
                parameters,
                "application",
            )

            if action == "launch_application":
                return self._application_controller.launch(
                    application
                )

            if action == "close_application":
                return self._application_controller.close(
                    application
                )

            if action == "restart_application":
                return self._application_controller.restart(
                    application
                )

            if action == "terminate_application":
                return self._application_controller.terminate(
                    application
                )

        if action == "focus_window":
            application = self._require_parameter(
                parameters,
                "application",
            )

            return self._window_controller.focus(
                application
            )

        if action == "switch_window":
            target = self._require_parameter(
                parameters,
                "target",
            )

            return self._window_controller.switch(
                target
            )

        if action == "resize_window":
            application = self._require_parameter(
                parameters,
                "application",
            )

            width = self._require_parameter(
                parameters,
                "width",
            )

            height = self._require_parameter(
                parameters,
                "height",
            )

            return self._window_controller.resize(
                application,
                width,
                height,
            )

        if action == "position_window":
            application = self._require_parameter(
                parameters,
                "application",
            )

            x = self._require_parameter(
                parameters,
                "x",
            )

            y = self._require_parameter(
                parameters,
                "y",
            )

            return self._window_controller.position(
                application,
                x,
                y,
            )

        raise ValueError(
            f"Unsupported M5-K action: {action}"
        )

    # ------------------------------------------------------------------
    # Parameter helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require_parameter(
        parameters: dict[str, Any],
        parameter_name: str,
    ) -> Any:
        """
        Retrieve a required action parameter.
        """
        if parameter_name not in parameters:
            raise ValueError(
                f"Missing required parameter: "
                f"{parameter_name}"
            )

        value = parameters[parameter_name]

        if isinstance(value, str) and not value.strip():
            raise ValueError(
                f"Parameter '{parameter_name}' "
                "must not be empty."
            )

        return value

    # ------------------------------------------------------------------
    # Failure handling
    # ------------------------------------------------------------------

    def _failure_result(
        self,
        *,
        action_request: ActionRequest,
        error: str,
        failure_type: FailureType = FailureType.UNKNOWN,
    ) -> AutomationExecutionResult:
        """
        Build a standardized failed automation result.
        """
        return AutomationExecutionResult(
            task_id=action_request.task_id,
            action=action_request.action,
            success=False,
            error=error,
            metadata={
                "agent_id": self.agent_id,
                "agent_type": "application_window",
                "backend": type(self._backend).__name__,
                "failure_type": failure_type.value,
            },
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """
        Clean up the agent lifecycle state.

        No OS-level application cleanup is performed here. This method
        only manages the AutomationAgent lifecycle.
        """
        current_state = self.lifecycle_state

        if current_state == AgentLifecycleState.CLEANED:
            return

        if current_state == AgentLifecycleState.CREATED:
            self._transition_to(
                AgentLifecycleState.CLEANED
            )
            return

        if current_state == AgentLifecycleState.READY:
            self._transition_to(
                AgentLifecycleState.CLEANING_UP
            )
            self._transition_to(
                AgentLifecycleState.CLEANED
            )
            return

        if current_state == AgentLifecycleState.FAILED:
            self._transition_to(
                AgentLifecycleState.CLEANING_UP
            )
            self._transition_to(
                AgentLifecycleState.CLEANED
            )
            return

        if current_state == AgentLifecycleState.EXECUTING:
            self._transition_to(
                AgentLifecycleState.FAILED
            )
            self._transition_to(
                AgentLifecycleState.CLEANING_UP
            )
            self._transition_to(
                AgentLifecycleState.CLEANED
            )
            return

        if current_state == AgentLifecycleState.INITIALIZING:
            self._transition_to(
                AgentLifecycleState.FAILED
            )
            self._transition_to(
                AgentLifecycleState.CLEANING_UP
            )
            self._transition_to(
                AgentLifecycleState.CLEANED
            )
            return

        if current_state == AgentLifecycleState.CLEANING_UP:
            self._transition_to(
                AgentLifecycleState.CLEANED
            )
            return

        raise RuntimeError(
            f"Cannot cleanup agent from lifecycle state: "
            f"{current_state.value}"
        )