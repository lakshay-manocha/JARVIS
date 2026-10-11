"""
File-System Automation Agent for M5-L.

This agent provides the JARVIS automation-layer interface for:

File operations:
    - create_file
    - delete_file
    - copy_file
    - move_file
    - rename_file
    - get_file_metadata

Directory operations:
    - create_directory
    - delete_directory
    - list_directory
    - path_exists

The agent delegates filesystem operations to FileController and
DirectoryController, which in turn delegate to a FileSystemBackend.
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

from .directory_controller import DirectoryController
from .file_controller import FileController
from .filesystem_backend import FileSystemBackend


class FileSystemAutomationAgent(AutomationAgent):
    """
    M5-L File-System Automation Agent.

    Responsibilities:
        - File-system automation.
        - File and directory action validation/routing.
        - Delegation to FileController and DirectoryController.
        - Standardized AutomationExecutionResult generation.

    This agent does NOT perform:
        - planning
        - scheduling
        - retry/fallback
        - process monitoring
        - application automation
        - browser automation
        - keyboard automation
        - mouse automation
        - screen/OCR automation
        - LLM communication
    """

    SUPPORTED_ACTIONS = frozenset(
        {
            "create_file",
            "delete_file",
            "copy_file",
            "move_file",
            "rename_file",
            "get_file_metadata",
            "create_directory",
            "delete_directory",
            "list_directory",
            "path_exists",
        }
    )

    FILE_ACTIONS = frozenset(
        {
            "create_file",
            "delete_file",
            "copy_file",
            "move_file",
            "rename_file",
            "get_file_metadata",
        }
    )

    DIRECTORY_ACTIONS = frozenset(
        {
            "create_directory",
            "delete_directory",
            "list_directory",
            "path_exists",
        }
    )

    def __init__(
        self,
        *,
        backend: FileSystemBackend,
    ) -> None:
        """
        Initialize the File-System Automation Agent.

        Args:
            backend:
                A concrete implementation of FileSystemBackend.

        The backend is dependency-injected so that the agent remains
        independent from the concrete filesystem implementation.
        """
        super().__init__()

        if not isinstance(backend, FileSystemBackend):
            raise TypeError(
                "backend must be a FileSystemBackend."
            )

        self._backend = backend

        self._file_controller = FileController(
            self._backend
        )

        self._directory_controller = DirectoryController(
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
        return "filesystem_agent"

    @property
    def name(self) -> str:
        return "File-System Automation Agent"

    @property
    def description(self) -> str:
        return (
            "Controls file and directory operations through a "
            "FileSystemBackend."
        )

    @property
    def tool_type(self) -> ToolType:
        return ToolType.FILESYSTEM

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "agent_type": "filesystem",
            "tool_type": self.tool_type.value,
            "backend": type(self._backend).__name__,
            "version": "M5-L",
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

        The backend is dependency-injected and does not require an
        additional initialization contract at this layer.
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
            - Tool must be FILESYSTEM.
            - Category must be FILESYSTEM.
            - Action must be one of the ten M5-L actions.
        """
        if not isinstance(action_request, ActionRequest):
            return False

        if action_request.tool != ToolType.FILESYSTEM:
            return False

        if action_request.category != ActionCategory.FILESYSTEM:
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
        Execute a validated M5-L action request.

        Retry, timeout, and fallback decisions remain outside the
        automation agent.
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
                    "agent_type": "filesystem",
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
        Route a filesystem action to the appropriate controller.

        Controllers remain responsible for parameter validation and
        backend delegation.
        """
        action = action_request.action.strip().lower()
        parameters = action_request.parameters

        # --------------------------------------------------------------
        # File operations
        # --------------------------------------------------------------

        if action in self.FILE_ACTIONS:

            if action == "create_file":
                path = self._require_parameter(
                    parameters,
                    "path",
                )

                return self._file_controller.create_file(
                    path
                )

            if action == "delete_file":
                path = self._require_parameter(
                    parameters,
                    "path",
                )

                return self._file_controller.delete_file(
                    path
                )

            if action == "copy_file":
                source = self._require_parameter(
                    parameters,
                    "source",
                )

                destination = self._require_parameter(
                    parameters,
                    "destination",
                )

                return self._file_controller.copy_file(
                    source,
                    destination,
                )

            if action == "move_file":
                source = self._require_parameter(
                    parameters,
                    "source",
                )

                destination = self._require_parameter(
                    parameters,
                    "destination",
                )

                return self._file_controller.move_file(
                    source,
                    destination,
                )

            if action == "rename_file":
                path = self._require_parameter(
                    parameters,
                    "path",
                )

                new_name = self._require_parameter(
                    parameters,
                    "new_name",
                )

                return self._file_controller.rename_file(
                    path,
                    new_name,
                )

            if action == "get_file_metadata":
                path = self._require_parameter(
                    parameters,
                    "path",
                )

                return self._file_controller.get_file_metadata(
                    path
                )

        # --------------------------------------------------------------
        # Directory operations
        # --------------------------------------------------------------

        if action in self.DIRECTORY_ACTIONS:

            if action == "create_directory":
                path = self._require_parameter(
                    parameters,
                    "path",
                )

                return self._directory_controller.create_directory(
                    path
                )

            if action == "delete_directory":
                path = self._require_parameter(
                    parameters,
                    "path",
                )

                return self._directory_controller.delete_directory(
                    path
                )

            if action == "list_directory":
                path = self._require_parameter(
                    parameters,
                    "path",
                )

                return self._directory_controller.list_directory(
                    path
                )

            if action == "path_exists":
                path = self._require_parameter(
                    parameters,
                    "path",
                )

                return self._directory_controller.path_exists(
                    path
                )

        raise ValueError(
            f"Unsupported M5-L action: {action}"
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
                "agent_type": "filesystem",
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

        No filesystem deletion or modification is performed here.
        This method only manages the AutomationAgent lifecycle.
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