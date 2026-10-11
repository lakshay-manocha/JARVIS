"""
===============================================================================
File Name   : test_automation_agent_base.py
Module      : Automation Engine - Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Tests the AutomationAgent base contract and capability model.

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations
from abc import abstractmethod

import pytest

from agent_engine.automation.agents.base import AutomationAgent
from agent_engine.automation.models.capabilities import AgentCapabilities
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType
from agent_engine.automation.models.execution_result import AutomationExecutionResult


# =============================================================================
# Test Automation Agent
# =============================================================================

class TestAutomationAgent(AutomationAgent):
    """
    Concrete test implementation of AutomationAgent.
    """

    @property
    def agent_id(self) -> str:
        return "test_agent"

    @property
    def name(self) -> str:
        return "Test Agent"

    @property
    def description(self) -> str:
        return "A test automation agent for contract testing."

    @property
    def tool_type(self) -> ToolType:
        return ToolType.KEYBOARD

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "version": "1.0.0",
        }

    @property
    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            actions={
                "type_text",
                "press_key",
                "hotkey",
            }
        )

    def initialize(self) -> None:
        pass

    def can_execute(self, action_request: ActionRequest) -> bool:
        return self.supports(action_request.action)

    def execute(
        self,
        action_request: ActionRequest,
    ) -> AutomationExecutionResult:
        return AutomationExecutionResult(
            task_id=action_request.task_id,
            action=action_request.action,
            success=True,
            output={
                "message": "Test execution successful.",
            },
            execution_time=0.01,
        )


    def cleanup(self) -> None:
        pass

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def agent() -> TestAutomationAgent:
    return TestAutomationAgent()


# =============================================================================
# Identity Tests
# =============================================================================

def test_agent_id(agent: TestAutomationAgent) -> None:
    assert agent.agent_id == "test_agent"


def test_agent_name(agent: TestAutomationAgent) -> None:
    assert agent.name == "Test Agent"


def test_agent_description(agent: TestAutomationAgent) -> None:
    assert agent.description == (
        "A test automation agent for contract testing."
    )


def test_agent_tool_type(agent: TestAutomationAgent) -> None:
    assert agent.tool_type == ToolType.KEYBOARD


def test_agent_metadata(agent: TestAutomationAgent) -> None:
    assert agent.metadata["version"] == "1.0.0"


# =============================================================================
# Capability Tests
# =============================================================================

def test_agent_capabilities(agent: TestAutomationAgent) -> None:
    assert isinstance(agent.capabilities, AgentCapabilities)

    assert agent.capabilities.supports("type_text")
    assert agent.capabilities.supports("press_key")
    assert agent.capabilities.supports("hotkey")


def test_supported_action(agent: TestAutomationAgent) -> None:
    assert agent.supports("type_text") is True


def test_unsupported_action(agent: TestAutomationAgent) -> None:
    assert agent.supports("click_mouse") is False


def test_capability_case_insensitive(agent: TestAutomationAgent) -> None:
    assert agent.supports("TYPE_TEXT") is True
    assert agent.supports("Press_Key") is True


def test_capability_ignores_whitespace(
    agent: TestAutomationAgent,
) -> None:
    assert agent.supports(" type_text ") is True


def test_empty_capability_action(agent: TestAutomationAgent) -> None:
    assert agent.supports("") is False


# =============================================================================
# Capability Model Tests
# =============================================================================

def test_capability_model_normalizes_actions() -> None:
    capabilities = AgentCapabilities(
        actions={
            "type_text",
            " PRESS_KEY ",
            "HotKey",
        }
    )

    assert capabilities.supports("type_text")
    assert capabilities.supports("press_key")
    assert capabilities.supports("hotkey")


def test_capability_model_returns_all_actions() -> None:
    capabilities = AgentCapabilities(
        actions={
            "type_text",
            "press_key",
        }
    )

    assert capabilities.all_actions() == frozenset(
        {
            "type_text",
            "press_key",
        }
    )


def test_capability_model_removes_duplicates() -> None:
    capabilities = AgentCapabilities(
        actions=[
            "type_text",
            "TYPE_TEXT",
            " type_text ",
        ]
    )

    assert len(capabilities) == 1
    assert capabilities.supports("type_text")


def test_capability_model_empty_actions() -> None:
    capabilities = AgentCapabilities()

    assert len(capabilities) == 0
    assert capabilities.supports("type_text") is False


def test_capability_model_rejects_empty_action() -> None:
    with pytest.raises(ValueError):
        AgentCapabilities(
            actions={
                "type_text",
                "   ",
            }
        )


def test_capability_model_rejects_non_string_action() -> None:
    with pytest.raises(TypeError):
        AgentCapabilities(
            actions={
                "type_text",
                123,  # type: ignore[arg-type]
            }
        )


def test_capability_model_rejects_non_string_query() -> None:
    capabilities = AgentCapabilities(
        actions={"type_text"}
    )

    with pytest.raises(TypeError):
        capabilities.supports(123)  # type: ignore[arg-type]


# =============================================================================
# Membership Tests
# =============================================================================

def test_capability_membership_operator(
    agent: TestAutomationAgent,
) -> None:
    assert "type_text" in agent.capabilities
    assert "click_mouse" not in agent.capabilities


# =============================================================================
# Agent Execution Contract Tests
# =============================================================================

def test_can_execute_supported_action(
    agent: TestAutomationAgent,
) -> None:

    request = ActionRequest(
        task_id=1,
        action="type_text",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters={
            "text": "Hello JARVIS",
        },
    )

    assert agent.can_execute(request) is True


def test_can_execute_unsupported_action(
    agent: TestAutomationAgent,
) -> None:

    request = ActionRequest(
        task_id=1,
        action="click_mouse",
        category=ActionCategory.MOUSE,
        tool=ToolType.MOUSE,
        parameters={
            "x": 100,
            "y": 200,
        },
    )

    assert agent.can_execute(request) is False

# =============================================================================
# Automation Execution Result Tests
# =============================================================================

def test_execute_returns_automation_execution_result(
    agent: TestAutomationAgent,
) -> None:

    request = ActionRequest(
        task_id=1,
        action="type_text",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters={
            "text": "Hello JARVIS",
        },
    )

    result = agent.execute(request)

    assert isinstance(
        result,
        AutomationExecutionResult,
    )


def test_execution_result_contains_task_information(
    agent: TestAutomationAgent,
) -> None:

    request = ActionRequest(
        task_id=42,
        action="type_text",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters={
            "text": "Hello",
        },
    )

    result = agent.execute(request)

    assert result.task_id == 42
    assert result.action == "type_text"


def test_execution_result_success(
    agent: TestAutomationAgent,
) -> None:

    request = ActionRequest(
        task_id=1,
        action="type_text",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters={
            "text": "Hello",
        },
    )

    result = agent.execute(request)

    assert result.success is True
    assert result.failed is False


def test_execution_result_output(
    agent: TestAutomationAgent,
) -> None:

    request = ActionRequest(
        task_id=1,
        action="type_text",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters={
            "text": "Hello",
        },
    )

    result = agent.execute(request)

    assert result.has_output is True
    assert result.output["message"] == (
        "Test execution successful."
    )


def test_execution_result_execution_time(
    agent: TestAutomationAgent,
) -> None:

    request = ActionRequest(
        task_id=1,
        action="type_text",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters={
            "text": "Hello",
        },
    )

    result = agent.execute(request)

    assert result.execution_time == 0.01


def test_failed_execution_result() -> None:

    result = AutomationExecutionResult(
        task_id=10,
        action="click_mouse",
        success=False,
        error="Mouse click failed.",
        execution_time=0.25,
    )

    assert result.success is False
    assert result.failed is True
    assert result.has_error is True
    assert result.error == "Mouse click failed."


def test_successful_result_cannot_have_error() -> None:

    with pytest.raises(ValueError):
        AutomationExecutionResult(
            task_id=1,
            action="type_text",
            success=True,
            error="Unexpected error.",
        )


def test_negative_execution_time_rejected() -> None:

    with pytest.raises(ValueError):
        AutomationExecutionResult(
            task_id=1,
            action="type_text",
            success=True,
            execution_time=-1.0,
        )


def test_negative_task_id_rejected() -> None:

    with pytest.raises(ValueError):
        AutomationExecutionResult(
            task_id=-1,
            action="type_text",
            success=True,
        )


def test_empty_action_rejected() -> None:

    with pytest.raises(ValueError):
        AutomationExecutionResult(
            task_id=1,
            action="",
            success=True,
        )


def test_action_is_normalized() -> None:

    result = AutomationExecutionResult(
        task_id=1,
        action="  TYPE_TEXT  ",
        success=True,
    )

    assert result.action == "type_text"


def test_execution_result_is_immutable() -> None:

    result = AutomationExecutionResult(
        task_id=1,
        action="type_text",
        success=True,
    )

    with pytest.raises(AttributeError):
        result.success = False  # type: ignore[misc]