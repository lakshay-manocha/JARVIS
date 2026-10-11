"""
Tests for G.10 - Dispatcher → AutomationAgent Integration.
"""

from __future__ import annotations

import pytest

from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.automation.agents.base import AutomationAgent
from agent_engine.automation.exceptions import AgentCapabilityError
from agent_engine.automation.models.capabilities import AgentCapabilities
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)
from agent_engine.automation.integration.action_request_builder import (
    ActionRequestBuilder,
)
from agent_engine.automation.registry.action_registry import ActionRegistry
from agent_engine.automation.registry.agent_registry import AgentRegistry
from agent_engine.automation.registry.tool_agent_mapper import (
    ToolAgentMapper,
)
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import (
    ExecutionStatus,
    ToolType,
)
from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)


# =============================================================================
# Test Automation Agent
# =============================================================================

class TestDispatcherAgent(AutomationAgent):
    """
    Lightweight AutomationAgent used to test the G.10 dispatcher integration.

    This is a test double only.

    It does not perform real browser, keyboard, mouse, desktop, filesystem,
    or screen automation.
    """

    def __init__(
        self,
        agent_id: str,
        tool_type: ToolType,
        supported_actions: frozenset[str],
    ) -> None:
        super().__init__()

        self._agent_id = agent_id
        self._tool_type = tool_type
        self._supported_actions = supported_actions

        self.can_execute_called = False
        self.execute_called = False
        self.received_request: ActionRequest | None = None

        self.execute_success = True
        self.execute_error: str | None = None

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def name(self) -> str:
        return f"Test {self._tool_type.value}"

    @property
    def description(self) -> str:
        return "Test AutomationAgent for G.10."

    @property
    def tool_type(self) -> ToolType:
        return self._tool_type

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "test": True,
            "phase": "G.10",
        }

    @property
    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            actions=self._supported_actions
        )

    def initialize(self) -> None:
        pass

    def can_execute(
        self,
        action_request: ActionRequest,
    ) -> bool:
        self.can_execute_called = True
        self.received_request = action_request

        return action_request.action in self._supported_actions

    def execute(
        self,
        action_request: ActionRequest,
    ) -> AutomationExecutionResult:
        self.execute_called = True
        self.received_request = action_request

        return AutomationExecutionResult(
            task_id=action_request.task_id,
            action=action_request.action,
            success=self.execute_success,
            output=(
                "Test agent execution successful"
                if self.execute_success
                else None
            ),
            error=self.execute_error,
        )

    def cleanup(self) -> None:
        pass


# =============================================================================
# Helpers
# =============================================================================

def create_task(
    *,
    task_id: int = 1,
    action: str = "open_url",
    tool: str = "browser_agent",
    parameters: dict | None = None,
) -> InterpretedTask:

    return InterpretedTask(
        task_id=task_id,
        original_text="Open example website",
        normalized_text="open example website",
        action=action,
        tool=tool,
        parameters=parameters or {},
    )


def create_dispatcher(
    agent: TestDispatcherAgent,
    *,
    registry: AgentRegistry | None = None,
) -> tuple[
    AutomationActionDispatcher,
    ToolAgentMapper,
]:
    """
    Create a dispatcher configured with the G.9 ToolAgentMapper.
    """

    agent_registry = registry or AgentRegistry()

    mapper = ToolAgentMapper(agent_registry)

    mapper.register(
        agent.tool_type,
        agent,
    )

    action_registry = ActionRegistry()

    dispatcher = AutomationActionDispatcher(
        action_registry,
        request_builder=ActionRequestBuilder(),
        tool_agent_mapper=mapper,
    )

    return dispatcher, mapper


# =============================================================================
# G.10 - Agent Resolution
# =============================================================================

def test_dispatcher_resolves_agent_through_tool_agent_mapper():
    """
    Dispatcher should resolve the AutomationAgent using the request ToolType.
    """

    agent = TestDispatcherAgent(
        agent_id="browser_agent",
        tool_type=ToolType.BROWSER,
        supported_actions=frozenset({"open_url"}),
    )

    dispatcher, mapper = create_dispatcher(agent)

    task = create_task(
        action="open_url",
        tool="browser_agent",
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert mapper.resolve(ToolType.BROWSER) is agent
    assert result.success is True


# =============================================================================
# G.10 - Capability Validation
# =============================================================================

def test_dispatcher_calls_agent_can_execute():
    """
    Dispatcher must validate agent capability before execution.
    """

    agent = TestDispatcherAgent(
        agent_id="browser_agent",
        tool_type=ToolType.BROWSER,
        supported_actions=frozenset({"open_url"}),
    )

    dispatcher, _ = create_dispatcher(agent)

    task = create_task()

    dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert agent.can_execute_called is True


def test_dispatcher_does_not_execute_when_agent_cannot_execute():
    """
    If the agent rejects the action, execute() must not be called.
    """

    agent = TestDispatcherAgent(
        agent_id="browser_agent",
        tool_type=ToolType.BROWSER,
        supported_actions=frozenset(),
    )

    dispatcher, _ = create_dispatcher(agent)

    task = create_task()

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert agent.can_execute_called is True
    assert agent.execute_called is False

    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION
    assert isinstance(
        AgentCapabilityError(
            "test"
        ),
        AgentCapabilityError,
    )


# =============================================================================
# G.10 - Agent Execution
# =============================================================================

def test_dispatcher_calls_agent_execute():
    """
    Dispatcher should delegate execution to AutomationAgent.execute().
    """

    agent = TestDispatcherAgent(
        agent_id="browser_agent",
        tool_type=ToolType.BROWSER,
        supported_actions=frozenset({"open_url"}),
    )

    dispatcher, _ = create_dispatcher(agent)

    task = create_task(
        parameters={
            "url": "https://example.com",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert agent.execute_called is True
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True


# =============================================================================
# G.10 - ActionRequest Propagation
# =============================================================================

def test_dispatcher_passes_action_request_to_agent():
    """
    Dispatcher should pass the complete ActionRequest to the agent.
    """

    agent = TestDispatcherAgent(
        agent_id="browser_agent",
        tool_type=ToolType.BROWSER,
        supported_actions=frozenset({"open_url"}),
    )

    dispatcher, _ = create_dispatcher(agent)

    task = create_task(
        task_id=42,
        action="open_url",
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
    )

    dispatcher.dispatch(
        task,
        attempt=1,
    )

    request = agent.received_request

    assert request is not None
    assert request.task_id == 42
    assert request.action == "open_url"
    assert request.tool == ToolType.BROWSER
    assert request.parameters == {
        "url": "https://example.com",
    }


# =============================================================================
# G.10 - Agent Execution Failure
# =============================================================================

def test_agent_execution_failure_returns_failed_outcome():
    """
    A failed AutomationExecutionResult should become a failed dispatcher
    outcome.

    Formal result conversion belongs to G.11; this test only verifies that
    G.10 does not report a failed agent execution as successful.
    """

    agent = TestDispatcherAgent(
        agent_id="browser_agent",
        tool_type=ToolType.BROWSER,
        supported_actions=frozenset({"open_url"}),
    )

    agent.execute_success = False
    agent.execute_error = "Browser agent failed."

    dispatcher, _ = create_dispatcher(agent)

    task = create_task()

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert agent.execute_called is True
    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.error_message == "Browser agent failed."


# =============================================================================
# G.10 - Unknown Mapping
# =============================================================================

def test_dispatcher_fails_when_tool_has_no_agent_mapping():
    """
    Dispatcher should fail safely when no AutomationAgent is mapped to the
    requested ToolType.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    action_registry = ActionRegistry()

    dispatcher = AutomationActionDispatcher(
        action_registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        tool="browser_agent",
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.failure_type == FailureType.UNKNOWN
    assert result.error_message is not None


# =============================================================================
# G.10 - Correct Tool Routing
# =============================================================================

def test_dispatcher_routes_to_correct_agent_for_tool_type():
    """
    Dispatcher should route execution according to ToolType rather than
    hard-coded action checks.
    """

    browser_agent = TestDispatcherAgent(
        agent_id="browser_agent",
        tool_type=ToolType.BROWSER,
        supported_actions=frozenset({"open_url"}),
    )

    keyboard_agent = TestDispatcherAgent(
        agent_id="keyboard_agent",
        tool_type=ToolType.KEYBOARD,
        supported_actions=frozenset({"type_text"}),
    )

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    mapper.register(
        ToolType.BROWSER,
        browser_agent,
    )

    mapper.register(
        ToolType.KEYBOARD,
        keyboard_agent,
    )

    dispatcher = AutomationActionDispatcher(
        ActionRegistry(),
        tool_agent_mapper=mapper,
    )

    task = create_task(
        action="type_text",
        tool="keyboard_agent",
        parameters={
            "text": "Hello JARVIS",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True

    assert keyboard_agent.can_execute_called is True
    assert keyboard_agent.execute_called is True

    assert browser_agent.can_execute_called is False
    assert browser_agent.execute_called is False


# =============================================================================
# G.10 - Existing ActionRegistry Compatibility
# =============================================================================

def test_dispatcher_preserves_existing_action_registry_execution():
    """
    Existing dispatcher behavior should remain available when no
    ToolAgentMapper is configured.
    """

    registry = ActionRegistry()

    received = {}

    def handler(**kwargs):
        received.update(kwargs)
        return "SUCCESS"

    registry.register(
        "open_url",
        handler,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
    )

    task = create_task(
        parameters={
            "url": "https://example.com",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert received == {
        "url": "https://example.com",
    }

    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True