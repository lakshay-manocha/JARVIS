"""
===============================================================================
File Name   : test_mock_automation_agent.py
Module      : Automation Engine - Tests
Project     : JARVIS

Description:
-------------
Tests M5-G.12 Mock Automation Compatibility.

Verifies that the existing MockAutomationEngine can operate through the
standard AutomationAgent architecture.

Author      : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.automation.agents.mock_agent import (
    MockAutomationAgent,
)
from agent_engine.automation.engine.mock_automation_engine import (
    MockAutomationEngine,
    create_default_mock_engine,
)
from agent_engine.automation.models.lifecycle import (
    AgentLifecycleState,
)
from agent_engine.contracts.action import (
    ActionRequest,
)
from agent_engine.contracts.enums import (
    ActionCategory,
    ToolType,
)


# =============================================================================
# Helpers
# =============================================================================

def create_browser_agent() -> MockAutomationAgent:
    """
    Create a mock Browser AutomationAgent.
    """

    engine = create_default_mock_engine()

    return MockAutomationAgent(
        agent_id="mock_browser_agent",
        tool_type=ToolType.BROWSER,
        engine=engine,
        supported_actions={
            "open",
            "open_url",
            "search",
        },
    )


def create_open_url_request(
    task_id: int = 1,
) -> ActionRequest:
    """
    Create a standard browser ActionRequest.
    """

    return ActionRequest(
        task_id=task_id,
        action="open_url",
        category=ActionCategory.BROWSER,
        tool=ToolType.BROWSER,
        parameters={
            "url": "https://example.com",
        },
    )


# =============================================================================
# Identity
# =============================================================================

def test_mock_agent_exposes_identity():
    """
    MockAutomationAgent should expose standard AutomationAgent identity.
    """

    agent = create_browser_agent()

    assert agent.agent_id == "mock_browser_agent"
    assert agent.tool_type == ToolType.BROWSER
    assert agent.name == "Mock browser_agent"
    assert agent.metadata["mock"] is True


# =============================================================================
# Capabilities
# =============================================================================

def test_mock_agent_exposes_capabilities():
    """
    Mock agent should expose its declared capabilities.
    """

    agent = create_browser_agent()

    assert agent.capabilities.supports("open")
    assert agent.capabilities.supports("open_url")
    assert agent.capabilities.supports("search")

    assert not agent.capabilities.supports(
        "type_text"
    )


# =============================================================================
# Capability Validation
# =============================================================================

def test_mock_agent_can_execute_supported_action():
    """
    A supported action with a matching ToolType should be executable.
    """

    agent = create_browser_agent()

    request = create_open_url_request()

    assert agent.can_execute(request) is True


def test_mock_agent_rejects_wrong_tool_type():
    """
    Mock agent should reject requests intended for another ToolType.
    """

    agent = create_browser_agent()

    request = ActionRequest(
        task_id=1,
        action="type_text",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters={
            "text": "Hello",
        },
    )

    assert agent.can_execute(request) is False


def test_mock_agent_rejects_unsupported_action():
    """
    Mock agent should reject actions outside its declared capabilities.
    """

    agent = create_browser_agent()

    request = ActionRequest(
        task_id=1,
        action="type_text",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.BROWSER,
        parameters={
            "text": "Hello",
        },
    )

    assert agent.can_execute(request) is False


# =============================================================================
# Execution
# =============================================================================

def test_mock_agent_returns_automation_execution_result():
    """
    Successful mock execution must return AutomationExecutionResult.
    """

    agent = create_browser_agent()

    result = agent.execute(
        create_open_url_request()
    )

    assert result.success is True
    assert result.task_id == 1
    assert result.action == "open_url"
    assert result.output is not None
    assert result.metadata["mock"] is True
    assert result.metadata["agent_id"] == (
        "mock_browser_agent"
    )


def test_mock_agent_passes_parameters_to_mock_engine():
    """
    ActionRequest parameters must reach the underlying mock engine.
    """

    agent = create_browser_agent()

    request = create_open_url_request()

    agent.execute(request)

    history = agent.engine.get_execution_history()

    assert len(history) == 1
    assert history[0]["action"] == "open_url"
    assert history[0]["parameters"] == {
        "url": "https://example.com",
    }


# =============================================================================
# Failure Handling
# =============================================================================

def test_mock_agent_returns_failed_result_for_unsupported_action():
    """
    Unsupported execution should produce a standardized failed result.
    """

    agent = create_browser_agent()

    request = ActionRequest(
        task_id=5,
        action="unsupported_action",
        category=ActionCategory.BROWSER,
        tool=ToolType.BROWSER,
        parameters={},
    )

    result = agent.execute(request)

    assert result.success is False
    assert result.task_id == 5
    assert result.action == "unsupported_action"
    assert result.error is not None
    assert result.metadata["failure_type"] == "VALIDATION"


# =============================================================================
# Lifecycle
# =============================================================================

def test_mock_agent_lifecycle():
    """
    Mock agent should follow the standard AutomationAgent lifecycle.
    """

    agent = create_browser_agent()

    assert agent.lifecycle_state == (
        AgentLifecycleState.CREATED
    )

    agent.initialize()

    assert agent.lifecycle_state == (
        AgentLifecycleState.READY
    )

    agent.cleanup()

    assert agent.lifecycle_state == (
        AgentLifecycleState.CLEANED
    )


# =============================================================================
# Existing Mock Engine Compatibility
# =============================================================================

def test_existing_mock_engine_remains_unchanged():
    """
    The MockAutomationEngine should remain usable independently.
    """

    engine = MockAutomationEngine()

    engine.register(
        "test_action",
        lambda **kwargs: {
            "status": "success",
            "parameters": kwargs,
        },
    )

    result = engine.execute(
        "test_action",
        {
            "value": 42,
        },
    )

    assert result["status"] == "success"
    assert result["parameters"]["value"] == 42