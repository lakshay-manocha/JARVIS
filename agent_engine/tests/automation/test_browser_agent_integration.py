"""
===============================================================================
File Name   : test_browser_agent_integration.py
Module      : Automation Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Integration tests validating the Browser Automation Agent against the
existing M5-G Automation Agent architecture.

Validated execution path:

    InterpretedTask
        ↓
    ActionRequestBuilder
        ↓
    ActionRequest
        ↓
    ToolAgentMapper
        ↓
    AgentRegistry
        ↓
    BrowserAutomationAgent
        ↓
    BrowserBackend
        ↓
    AutomationExecutionResult
        ↓
    ExecutionResultIntegrator
        ↓
    ExecutionOutcome

The tests use a controlled BrowserBackend test double so that the complete
agent architecture can be validated without requiring an actual browser
session.

Real browser execution remains the responsibility of BrowserBackend and
dedicated browser/backend tests.
===============================================================================
"""

from __future__ import annotations

from typing import Any

import pytest

from agent_engine.agent_brain.models.interpreted_task import InterpretedTask

from agent_engine.automation.agents.browser.browser_agent import (
    BrowserAutomationAgent,
)

from agent_engine.automation.agents.browser.browser_backend import (
    BrowserBackend,
)

from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)

from agent_engine.automation.integration.action_request_builder import (
    ActionRequestBuilder,
)

from agent_engine.automation.integration.execution_result_integrator import (
    ExecutionResultIntegrator,
)

from agent_engine.automation.registry.action_registry import (
    ActionRegistry,
)

from agent_engine.automation.registry.agent_registry import (
    AgentRegistry,
)

from agent_engine.automation.registry.tool_agent_mapper import (
    ToolAgentMapper,
)

from agent_engine.contracts.action import ActionRequest

from agent_engine.contracts.enums import (
    ActionCategory,
    ExecutionStatus,
    ToolType,
)


# =============================================================================
# Browser Backend Test Double
# =============================================================================


class IntegrationBrowserBackend(BrowserBackend):
    """
    Controlled BrowserBackend used for integration testing.

    It preserves the real BrowserBackend interface while avoiding a real
    Playwright browser session.

    The BrowserAutomationAgent remains the real Phase-H implementation.
    """

    def __init__(
        self,
        *,
        execution_output: Any | None = None,
        execution_error: Exception | None = None,
    ) -> None:
        super().__init__()

        self.initialize_calls = 0
        self.execute_calls: list[
            tuple[str, dict[str, Any], float | None]
        ] = []
        self.cleanup_calls = 0

        self.execution_output = (
            execution_output
            if execution_output is not None
            else {
                "url": "https://example.com",
                "status": 200,
                "title": "Example Domain",
            }
        )

        self.execution_error = execution_error

    @property
    def initialized(self) -> bool:
        """
        Treat the test backend as initialized after initialize() is called.
        """
        return self.initialize_calls > 0

    def initialize(self) -> None:
        """
        Simulate successful backend initialization.
        """
        self.initialize_calls += 1

    def execute(
        self,
        action: str,
        parameters: dict[str, Any] | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> Any:
        """
        Record the request and return a controlled result.
        """

        parameters = dict(parameters or {})

        self.execute_calls.append(
            (
                action,
                parameters,
                timeout_seconds,
            )
        )

        if self.execution_error is not None:
            raise self.execution_error

        return self.execution_output

    def cleanup(self) -> None:
        """
        Simulate backend cleanup.
        """
        self.cleanup_calls += 1


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def backend() -> IntegrationBrowserBackend:
    """
    Provide a deterministic browser backend.
    """
    return IntegrationBrowserBackend()


@pytest.fixture
def browser_agent(
    backend: IntegrationBrowserBackend,
) -> BrowserAutomationAgent:
    """
    Provide the real BrowserAutomationAgent using the controlled backend.
    """
    return BrowserAutomationAgent(
        backend=backend,
    )


@pytest.fixture
def registry() -> AgentRegistry:
    """
    Provide the real M5-G AgentRegistry.
    """
    return AgentRegistry()


@pytest.fixture
def mapper(
    registry: AgentRegistry,
) -> ToolAgentMapper:
    """
    Provide the real M5-G ToolAgentMapper.
    """
    return ToolAgentMapper(registry)


@pytest.fixture
def dispatcher(
    mapper: ToolAgentMapper,
) -> AutomationActionDispatcher:
    """
    Provide the real M5-G AutomationActionDispatcher.
    """

    return AutomationActionDispatcher(
        ActionRegistry(),
        request_builder=ActionRequestBuilder(),
        tool_agent_mapper=mapper,
    )


# =============================================================================
# Test Helpers
# =============================================================================


def create_browser_task(
    *,
    task_id: int = 1,
    action: str = "open_url",
    parameters: dict[str, Any] | None = None,
) -> InterpretedTask:
    """
    Create an InterpretedTask compatible with the existing dispatcher
    architecture.
    """

    return InterpretedTask(
        task_id=task_id,
        original_text="Open example website",
        normalized_text="open example website",
        action=action,
        tool="browser_agent",
        parameters=(
            dict(parameters)
            if parameters is not None
            else {
                "url": "https://example.com",
            }
        ),
    )


def create_browser_request(
    *,
    task_id: int = 1,
    action: str = "open_url",
    parameters: dict[str, Any] | None = None,
    timeout_seconds: float | None = None,
) -> ActionRequest:
    """
    Create a direct ActionRequest for agent-level integration tests.
    """

    return ActionRequest(
        task_id=task_id,
        action=action,
        category=ActionCategory.BROWSER,
        tool=ToolType.BROWSER,
        parameters=(
            dict(parameters)
            if parameters is not None
            else {
                "url": "https://example.com",
            }
        ),
        timeout_seconds=timeout_seconds,
    )


def register_browser_agent(
    registry: AgentRegistry,
    mapper: ToolAgentMapper,
    agent: BrowserAutomationAgent,
) -> None:
    """
    Register the browser agent in both M5-G components.
    """

    registry.register(agent)

    mapper.register(
        ToolType.BROWSER,
        agent,
    )


# =============================================================================
# Registry Integration
# =============================================================================


def test_browser_agent_can_be_registered(
    browser_agent: BrowserAutomationAgent,
    registry: AgentRegistry,
) -> None:
    """
    BrowserAutomationAgent must satisfy the M5-G AgentRegistry contract.
    """

    registry.register(browser_agent)

    resolved = registry.get(
        browser_agent.agent_id,
    )

    assert resolved is browser_agent


# =============================================================================
# Tool → Agent Mapping
# =============================================================================


def test_browser_tool_resolves_to_browser_agent(
    browser_agent: BrowserAutomationAgent,
    registry: AgentRegistry,
    mapper: ToolAgentMapper,
) -> None:
    """
    ToolType.BROWSER must resolve to the BrowserAutomationAgent instance.
    """

    register_browser_agent(
        registry,
        mapper,
        browser_agent,
    )

    resolved = mapper.resolve(
        ToolType.BROWSER,
    )

    assert resolved is browser_agent
    assert resolved.tool_type == ToolType.BROWSER


# =============================================================================
# Action Capability Validation
# =============================================================================


def test_browser_agent_accepts_valid_browser_request(
    browser_agent: BrowserAutomationAgent,
) -> None:
    """
    BrowserAutomationAgent must accept a valid browser ActionRequest.
    """

    request = create_browser_request(
        action="open_url",
    )

    assert browser_agent.can_execute(request) is True


def test_browser_agent_rejects_non_browser_request(
    browser_agent: BrowserAutomationAgent,
) -> None:
    """
    BrowserAutomationAgent must reject requests belonging to another
    ToolType.
    """

    request = ActionRequest(
        task_id=1,
        action="type_text",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters={
            "text": "Hello",
        },
    )

    assert browser_agent.can_execute(request) is False


# =============================================================================
# Agent → Backend Execution
# =============================================================================


def test_browser_agent_delegates_execution_to_backend(
    browser_agent: BrowserAutomationAgent,
    backend: IntegrationBrowserBackend,
) -> None:
    """
    BrowserAutomationAgent must delegate browser execution to BrowserBackend.
    """

    request = create_browser_request(
        task_id=10,
        action="open_url",
        parameters={
            "url": "https://example.com",
        },
        timeout_seconds=15,
    )

    result = browser_agent.execute(
        request,
    )

    assert result.success is True

    assert backend.initialize_calls == 1

    assert backend.execute_calls == [
        (
            "open_url",
            {
                "url": "https://example.com",
            },
            15,
        )
    ]


# =============================================================================
# Execution Result Contract
# =============================================================================


def test_browser_execution_returns_standard_automation_result(
    browser_agent: BrowserAutomationAgent,
) -> None:
    """
    Browser execution must return the standard AutomationExecutionResult
    defined by M5-G.
    """

    request = create_browser_request(
        task_id=25,
        action="open_url",
    )

    result = browser_agent.execute(
        request,
    )

    assert result.task_id == 25
    assert result.action == "open_url"
    assert result.success is True
    assert result.output is not None
    assert result.execution_time is not None
    assert result.execution_time >= 0


# =============================================================================
# Result → ExecutionOutcome Integration
# =============================================================================


def test_browser_result_integrates_into_execution_outcome(
    browser_agent: BrowserAutomationAgent,
) -> None:
    """
    BrowserAutomationAgent's result must integrate into the existing
    ExecutionOutcome model.
    """

    request = create_browser_request(
        task_id=30,
        action="open_url",
    )

    result = browser_agent.execute(
        request,
    )

    integrator = ExecutionResultIntegrator()

    outcome = integrator.integrate(
        result=result,
        attempt=1,
        max_retries=0,
    )

    assert outcome.task_id == 30
    assert outcome.status == ExecutionStatus.COMPLETED
    assert outcome.success is True


# =============================================================================
# Full Dispatcher → Browser Agent Integration
# =============================================================================


def test_dispatcher_routes_browser_task_to_browser_agent(
    browser_agent: BrowserAutomationAgent,
    registry: AgentRegistry,
    mapper: ToolAgentMapper,
    dispatcher: AutomationActionDispatcher,
) -> None:
    """
    The complete M5-G dispatcher path must route a browser task to the
    BrowserAutomationAgent.
    """

    register_browser_agent(
        registry,
        mapper,
        browser_agent,
    )

    task = create_browser_task(
        task_id=50,
        action="open_url",
        parameters={
            "url": "https://example.com",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True
    assert result.status == ExecutionStatus.COMPLETED
    assert result.task_id == 50


# =============================================================================
# Dispatcher → Agent → Backend Propagation
# =============================================================================


def test_dispatcher_propagates_browser_request_to_backend(
    browser_agent: BrowserAutomationAgent,
    backend: IntegrationBrowserBackend,
    registry: AgentRegistry,
    mapper: ToolAgentMapper,
    dispatcher: AutomationActionDispatcher,
) -> None:
    """
    Parameters originating from the InterpretedTask must reach the browser
    backend without being lost or rewritten incorrectly.
    """

    register_browser_agent(
        registry,
        mapper,
        browser_agent,
    )

    task = create_browser_task(
        task_id=60,
        action="search",
        parameters={
            "query": "JARVIS AI",
        },
    )

    dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert len(backend.execute_calls) == 1

    action, parameters, timeout = backend.execute_calls[0]

    assert action == "search"
    assert parameters == {
        "query": "JARVIS AI",
    }


# =============================================================================
# Failure Propagation
# =============================================================================


def test_browser_backend_failure_propagates_as_failed_execution(
    registry: AgentRegistry,
    mapper: ToolAgentMapper,
    dispatcher: AutomationActionDispatcher,
) -> None:
    """
    A BrowserBackend execution failure must not be reported as a successful
    dispatcher execution.
    """

    failing_backend = IntegrationBrowserBackend(
        execution_error=RuntimeError(
            "Browser backend execution failed."
        )
    )

    browser_agent = BrowserAutomationAgent(
        backend=failing_backend,
    )

    register_browser_agent(
        registry,
        mapper,
        browser_agent,
    )

    task = create_browser_task(
        task_id=70,
        action="open_url",
        parameters={
            "url": "https://example.com",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED
    assert result.error_message is not None
    assert "Browser backend execution failed." in result.error_message


# =============================================================================
# Unsupported Browser Action
# =============================================================================


def test_dispatcher_does_not_execute_unsupported_browser_action(
    browser_agent: BrowserAutomationAgent,
    backend: IntegrationBrowserBackend,
    registry: AgentRegistry,
    mapper: ToolAgentMapper,
    dispatcher: AutomationActionDispatcher,
) -> None:
    """
    Unsupported browser actions must be rejected by the BrowserAgent before
    reaching the BrowserBackend.
    """

    register_browser_agent(
        registry,
        mapper,
        browser_agent,
    )

    task = create_browser_task(
        task_id=80,
        action="delete_file",
        parameters={},
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED

    assert backend.execute_calls == []


# =============================================================================
# Agent Lifecycle Integration
# =============================================================================


def test_browser_agent_lifecycle_is_preserved_during_dispatch(
    browser_agent: BrowserAutomationAgent,
    backend: IntegrationBrowserBackend,
    registry: AgentRegistry,
    mapper: ToolAgentMapper,
    dispatcher: AutomationActionDispatcher,
) -> None:
    """
    Dispatcher execution must preserve the BrowserAutomationAgent lifecycle
    contract.

    CREATED
        ↓
    INITIALIZING
        ↓
    READY
        ↓
    EXECUTING
        ↓
    READY
    """

    register_browser_agent(
        registry,
        mapper,
        browser_agent,
    )

    assert browser_agent.lifecycle_state.value.lower() == "created"

    task = create_browser_task(
        task_id=90,
        action="open_url",
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True

    assert backend.initialize_calls == 1
    assert browser_agent.lifecycle_state.value.lower() == "ready"


# =============================================================================
# Multiple Browser Actions
# =============================================================================


@pytest.mark.parametrize(
    "action,parameters",
    [
        (
            "open_url",
            {
                "url": "https://example.com",
            },
        ),
        (
            "search",
            {
                "query": "JARVIS AI",
            },
        ),
        (
            "get_page_title",
            {},
        ),
        (
            "get_current_url",
            {},
        ),
        (
            "get_text",
            {},
        ),
    ],
)
def test_browser_agent_dispatches_supported_actions(
    action: str,
    parameters: dict[str, Any],
    browser_agent: BrowserAutomationAgent,
    registry: AgentRegistry,
    mapper: ToolAgentMapper,
    dispatcher: AutomationActionDispatcher,
) -> None:
    """
    Representative supported BrowserAutomationAgent actions must pass
    through the complete M5-G dispatch architecture.
    """

    register_browser_agent(
        registry,
        mapper,
        browser_agent,
    )

    task = create_browser_task(
        task_id=100,
        action=action,
        parameters=parameters,
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True, (
        f"Browser action '{action}' failed: "
        f"{result.error_message}"
    )

    assert result.status == ExecutionStatus.COMPLETED