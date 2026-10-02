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
    Screen Backend
          ↓
    Screenshot / OCR / Qwen2-VL
          ↓
    Structured Perception Result
          ↓
    Coordinates / Bounding Boxes

This agent is PERCEPTION-ONLY.

This agent DOES NOT:
    - move the mouse
    - click
    - type
    - press keys
    - plan tasks
    - interpret natural language
    - execute another agent
    - perform retries
    - make fallback decisions
    - modify the dispatcher
    - modify the registry

MouseAutomationAgent remains responsible for physical mouse actions.

Frozen identity:
    Agent ID   : screen_agent
    Agent Name : Screen/Vision Automation Agent
    Tool Type  : ToolType.SCREEN
    Category   : ActionCategory.SCREEN

Frozen actions:
    - capture_screen
    - capture_region
    - get_screen_size
    - locate_text
    - locate_element
    - detect_visible_elements
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

from agent_engine.perception.screen import (
    ScreenAware,
    get_screen_aware,
)


class ScreenAutomationAgent(AutomationAgent):
    """
    Perception-only screen agent.

    The agent delegates all screen perception to ScreenAware.

    ScreenAutomationAgent is responsible for:

        - validating ActionRequest
        - validating supported screen actions
        - lifecycle management
        - dispatching perception requests
        - converting perception failures into
          AutomationExecutionResult

    It is NOT responsible for:

        - mouse movement
        - clicking
        - keyboard input
        - task planning
        - natural-language interpretation
        - retry/fallback policies
    """

    # =========================================================================
    # Frozen action contract
    # =========================================================================

    SUPPORTED_ACTIONS = frozenset(
        {
            "capture_screen",
            "capture_region",
            "get_screen_size",
            "locate_text",
            "locate_element",
            "detect_visible_elements",
        }
    )

    # =========================================================================
    # Initialization
    # =========================================================================

    def __init__(
        self,
        *,
        screen: ScreenAware | None = None,
    ) -> None:
        """
        Create the screen perception agent.

        ScreenAware can be injected for testing.

        Example:

            agent = ScreenAutomationAgent(
                screen=fake_screen_aware
            )
        """

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
        """
        Stable agent identifier.
        """
        return "screen_agent"

    @property
    def name(self) -> str:
        """
        Stable human-readable agent name.
        """
        return "Screen/Vision Automation Agent"

    @property
    def description(self) -> str:
        """
        Description of the agent's responsibility.
        """
        return (
            "Perception-only desktop screen agent that captures "
            "screens and regions, retrieves screen dimensions, "
            "locates text or visual elements, and detects "
            "visible UI elements using OCR and vision models."
        )

    @property
    def tool_type(self) -> ToolType:
        """
        Screen tool type.
        """
        return ToolType.SCREEN

    # =========================================================================
    # Metadata
    # =========================================================================

    @property
    def metadata(self) -> dict[str, object]:
        """
        Static agent metadata.

        Keep this metadata descriptive only.
        No execution behavior belongs here.
        """

        return {
            "agent_id": self.agent_id,
            "agent_type": "screen",
            "agent_name": self.name,
            "tool_type": self.tool_type.value,
            "action_category": ActionCategory.SCREEN.value,
            "backend": "ScreenAware",
            "perception_only": True,
            "persistent_model": True,
            "version": "M5-M",
            "capabilities": sorted(self.SUPPORTED_ACTIONS),
        }

    # =========================================================================
    # Capabilities
    # =========================================================================

    @property
    def capabilities(self) -> AgentCapabilities:
        """
        Return the agent capabilities.
        """
        return self._capabilities

    # =========================================================================
    # Backend Access
    # =========================================================================

    @property
    def screen(self) -> ScreenAware:
        """
        Return the ScreenAware perception layer.

        Exposed primarily for testing and controlled integration.
        """
        return self._screen

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def initialize(self) -> None:
        """
        Initialize the screen perception layer.

        ScreenAware is responsible for lazy-loading expensive
        perception resources such as OCR/VLM models.
        """

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
        """
        Determine whether this agent can execute an ActionRequest.

        Validation is deliberately limited to:

            1. ActionRequest type
            2. Tool type
            3. Action category
            4. Supported action

        No natural-language interpretation happens here.
        """

        if not isinstance(action_request, ActionRequest):
            return False

        if action_request.tool != self.tool_type:
            return False

        if action_request.category != ActionCategory.SCREEN:
            return False

        return self.supports(
            action_request.action
        )

    # =========================================================================
    # Parameter Validation
    # =========================================================================

    @staticmethod
    def _require_parameter(
        parameters: dict[str, object],
        name: str,
    ) -> object:
        """
        Retrieve a required parameter.
        """

        value = parameters.get(name)

        if value is None:
            raise ValueError(
                f"Missing required parameter: {name}"
            )

        return value

    @staticmethod
    def _require_int(
        parameters: dict[str, object],
        name: str,
    ) -> int:
        """
        Retrieve an integer parameter.
        """

        value = ScreenAutomationAgent._require_parameter(
            parameters,
            name,
        )

        # bool is a subclass of int, therefore explicitly reject it.
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"Parameter '{name}' must be an integer."
            )

        return value

    @staticmethod
    def _optional_int(
        parameters: dict[str, object],
        name: str,
    ) -> int | None:
        """
        Retrieve an optional integer parameter.
        """

        value = parameters.get(name)

        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"Parameter '{name}' must be an integer."
            )

        return value

    @staticmethod
    def _optional_bool(
        parameters: dict[str, object],
        name: str,
        *,
        default: bool = False,
    ) -> bool:
        """
        Retrieve an optional boolean parameter.
        """

        value = parameters.get(
            name,
            default,
        )

        if not isinstance(value, bool):
            raise ValueError(
                f"Parameter '{name}' must be a boolean."
            )

        return value

    # =========================================================================
    # Action Execution
    # =========================================================================

    def execute(
        self,
        action_request: ActionRequest,
    ) -> AutomationExecutionResult:
        """
        Execute a perception action.

        Supported actions:

            capture_screen
            capture_region
            get_screen_size
            locate_text
            locate_element
            detect_visible_elements

        Every action delegates to ScreenAware.

        No mouse or keyboard action is performed here.
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
            return self._failure_result(
                action_request=action_request,
                start_time=start_time,
                error=(
                    "Screen agent cannot execute action "
                    f"'{action_request.action}'."
                ),
                failure_type="CAPABILITY",
            )

        # ---------------------------------------------------------------------
        # Lazy initialization
        # ---------------------------------------------------------------------

        try:
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
            # Dispatch ONLY to ScreenAware.
            # -----------------------------------------------------------------

            result = self._dispatch_action(
                action=action,
                parameters=parameters,
            )

            execution_time = (
                perf_counter() - start_time
            )

            # -----------------------------------------------------------------
            # Return to READY after successful perception.
            # -----------------------------------------------------------------

            self._transition_to(
                AgentLifecycleState.READY
            )

            found = result.get("found")

            # Capture/size actions do not have a "found" field.
            success = (
                bool(found)
                if isinstance(found, bool)
                else True
            )

            error = None

            if (
                isinstance(found, bool)
                and not found
            ):
                error = self._not_found_message(
                    action=action,
                    parameters=parameters,
                )

            return AutomationExecutionResult(
                task_id=action_request.task_id,
                action=action_request.action,
                success=success,
                output=result,
                error=error,
                execution_time=execution_time,
                metadata=self._build_metadata(
                    action=action,
                    result=result,
                ),
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
                    "action_category": (
                        ActionCategory.SCREEN.value
                    ),
                    "exception_type": type(exc).__name__,
                },
            )

    # =========================================================================
    # Action Dispatcher
    # =========================================================================

    def _dispatch_action(
        self,
        *,
        action: str,
        parameters: dict[str, object],
    ) -> dict[str, object]:
        """
        Dispatch a validated screen action to ScreenAware.

        This is NOT the global JARVIS ActionDispatcher.

        It is only the internal action-to-perception-method mapping
        inside this agent.

        No other agent is called.
        """

        # =====================================================================
        # 1. Capture complete screen
        # =====================================================================

        if action == "capture_screen":

            monitor = self._optional_int(
                parameters,
                "monitor",
            )

            all_screens = self._optional_bool(
                parameters,
                "all_screens",
                default=False,
            )

            return self._screen.capture_screen(
                monitor=monitor,
                all_screens=all_screens,
            )

        # =====================================================================
        # 2. Capture region
        # =====================================================================

        if action == "capture_region":

            x = self._require_int(
                parameters,
                "x",
            )

            y = self._require_int(
                parameters,
                "y",
            )

            width = self._require_int(
                parameters,
                "width",
            )

            height = self._require_int(
                parameters,
                "height",
            )

            if width <= 0:
                raise ValueError(
                    "Parameter 'width' must be greater than zero."
                )

            if height <= 0:
                raise ValueError(
                    "Parameter 'height' must be greater than zero."
                )

            return self._screen.capture_region(
                x=x,
                y=y,
                width=width,
                height=height,
            )

        # =====================================================================
        # 3. Screen size
        # =====================================================================

        if action == "get_screen_size":

            monitor = self._optional_int(
                parameters,
                "monitor",
            )

            return self._screen.get_screen_size(
                monitor=monitor,
            )

        # =====================================================================
        # 4. Locate text
        # =====================================================================

        if action == "locate_text":

            text = self._require_parameter(
                parameters,
                "text",
            )

            if not isinstance(text, str):
                raise ValueError(
                    "Parameter 'text' must be a string."
                )

            text = text.strip()

            if not text:
                raise ValueError(
                    "Parameter 'text' cannot be empty."
                )

            case_sensitive = self._optional_bool(
                parameters,
                "case_sensitive",
                default=False,
            )

            return self._screen.locate_text(
                text=text,
                case_sensitive=case_sensitive,
            )

        # =====================================================================
        # 5. Locate visual element
        # =====================================================================

        if action == "locate_element":

            query = self._require_parameter(
                parameters,
                "query",
            )

            if not isinstance(query, str):
                raise ValueError(
                    "Parameter 'query' must be a string."
                )

            query = query.strip()

            if not query:
                raise ValueError(
                    "Parameter 'query' cannot be empty."
                )

            return self._screen.locate_element(
                query=query,
            )

        # =====================================================================
        # 6. Detect visible elements
        # =====================================================================

        if action == "detect_visible_elements":

            return self._screen.detect_visible_elements(
                element_types=parameters.get(
                    "element_types"
                ),
            )

        # =====================================================================
        # This should be unreachable because can_execute()
        # already validates SUPPORTED_ACTIONS.
        # =====================================================================

        raise ValueError(
            f"Unsupported screen action: {action}"
        )

    # =========================================================================
    # Result Helpers
    # =========================================================================

    def _build_metadata(
        self,
        *,
        action: str,
        result: dict[str, object],
    ) -> dict[str, object]:
        """
        Build common execution metadata.

        Keep perception details here so downstream components can
        consume coordinates without understanding ScreenAware internals.
        """

        metadata: dict[str, object] = {
            "agent_id": self.agent_id,
            "tool": self.tool_type.value,
            "action_category": ActionCategory.SCREEN.value,
            "action": action,
        }

        # Common visual perception fields.
        for key in (
            "method",
            "confidence",
            "coordinates",
            "bbox",
            "latency_ms",
        ):
            if key in result:
                metadata[key] = result[key]

        return metadata

    def _not_found_message(
        self,
        *,
        action: str,
        parameters: dict[str, object],
    ) -> str:
        """
        Create a deterministic not-found message.
        """

        if action == "locate_text":
            text = parameters.get(
                "text",
                "",
            )

            return (
                f"Could not locate text '{text}' on screen."
            )

        if action == "locate_element":
            query = parameters.get(
                "query",
                "",
            )

            return (
                f"Could not locate element '{query}' on screen."
            )

        return (
            f"Screen perception action '{action}' "
            "did not find the requested target."
        )

    def _failure_result(
        self,
        *,
        action_request: ActionRequest,
        start_time: float,
        error: str,
        failure_type: str,
    ) -> AutomationExecutionResult:
        """
        Create a standard failed execution result.
        """

        return AutomationExecutionResult(
            task_id=action_request.task_id,
            action=action_request.action,
            success=False,
            error=error,
            execution_time=(
                perf_counter() - start_time
            ),
            metadata={
                "agent_id": self.agent_id,
                "tool": self.tool_type.value,
                "action_category": (
                    ActionCategory.SCREEN.value
                ),
                "failure_type": failure_type,
            },
        )

    # =========================================================================
    # Cleanup
    # =========================================================================

    def cleanup(self) -> None:
        """
        Cleanup the agent lifecycle.

        ScreenAware/model ownership is intentionally NOT destroyed here.

        Another JARVIS component may still use the shared ScreenAware
        instance. Full model release should happen during application
        shutdown.
        """

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
            # Intentionally do NOT call:
            #
            #     self._screen.cleanup()
            #
            # because ScreenAware/model ownership is shared.

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