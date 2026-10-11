"""
===============================================================================
File Name   : test_mock_agent_pipeline.py
Module      : Automation Engine - Integration Tests
Project     : JARVIS

Description:
-------------
Verifies the complete M5-G mock automation path.

Architecture:

    ActionRequest
         ↓
    ToolAgentMapper
         ↓
    MockAutomationAgent
         ↓
    MockAutomationEngine
         ↓
    AutomationExecutionResult
         ↓
    ExecutionResultIntegrator
         ↓
    ExecutionOutcome

Author      : Team JARVIS
===============================================================================
"""

from agent_engine.agent_brain.models.interpreted_task import (
    InterpretedTask,
)
from agent_engine.automation.agents.mock_agent import (
    MockAutomationAgent,
)
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)
from agent_engine.automation.engine.mock_automation_engine import (
    create_default_mock_engine,
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
from agent_engine.contracts.enums import (
    ExecutionStatus,
    ToolType,
)


def create_task() -> InterpretedTask:
    """
    Create a representative browser task.
    """

    return InterpretedTask(
        task_id=100,
        original_text="Open example website",
        normalized_text="open example website",
        action="open_url",
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
    )


def test_complete_mock_agent_dispatch_pipeline():
    """
    Verify the complete mock AutomationAgent execution path.
    """

    # -------------------------------------------------------------------------
    # Create Mock Agent
    # -------------------------------------------------------------------------

    mock_engine = create_default_mock_engine()

    mock_agent = MockAutomationAgent(
        agent_id="mock_browser_agent",
        tool_type=ToolType.BROWSER,
        engine=mock_engine,
        supported_actions={
            "open",
            "open_url",
            "search",
        },
    )

    # -------------------------------------------------------------------------
    # Register Agent
    # -------------------------------------------------------------------------

    agent_registry = AgentRegistry()

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.BROWSER,
        mock_agent,
    )

    # -------------------------------------------------------------------------
    # Create Dispatcher
    # -------------------------------------------------------------------------

    dispatcher = AutomationActionDispatcher(
        ActionRegistry(),
        tool_agent_mapper=mapper,
    )

    # -------------------------------------------------------------------------
    # Dispatch
    # -------------------------------------------------------------------------

    result = dispatcher.dispatch(
        create_task(),
        attempt=1,
    )

    # -------------------------------------------------------------------------
    # Verify ExecutionOutcome
    # -------------------------------------------------------------------------

    assert result.task_id == 100
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type.value == "NONE"

    # -------------------------------------------------------------------------
    # Verify Mock Engine Actually Executed
    # -------------------------------------------------------------------------

    history = mock_engine.get_execution_history()

    assert len(history) == 1

    assert history[0]["action"] == "open_url"

    assert history[0]["parameters"] == {
        "url": "https://example.com",
    }

    assert history[0]["result"]["action"] == (
        "open_url"
    )