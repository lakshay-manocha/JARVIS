"""
===============================================================================
File Name   : test_agent_orchestrator_automation.py
Module      : Integration Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
M5-E.7 integration test.

Verifies that the existing AgentOrchestrator can execute a planned Agent
Brain task through the Automation Engine.

Pipeline:

    LLM Plan
        ↓
    AgentOrchestrator
        ↓
    Validator
        ↓
    Interpreter
        ↓
    GraphBuilder
        ↓
    Planner
        ↓
    AutomationActionDispatcher
        ↓
    ActionRegistry
        ↓
    MockAutomationEngine
        ↓
    ExecutionOutcome
        ↓
    DecisionManager
        ↓
    StateManager

This test intentionally uses the MockAutomationEngine so that no real
browser, desktop, filesystem, keyboard, mouse, or screen automation occurs.

Author : Team JARVIS
===============================================================================
"""

from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)
from agent_engine.automation.engine.mock_automation_engine import (
    create_default_mock_engine,
)
from agent_engine.automation.registry.action_registry import ActionRegistry
from agent_engine.contracts.enums import (
    ExecutionMode,
    ExecutionStatus,
    ResultStatus,
)
from agent_engine.orchestration.agent_orchestrator import AgentOrchestrator


# =============================================================================
# Test Plan
# =============================================================================

def build_level_1_llm_plan() -> LLMPlan:
    """
    Build a simple single-task LLM plan for Level-1 automation testing.
    """

    return LLMPlan(
        goal="Open example website",
        summary="Open the example website in the browser.",
        missing_information=[],
        tasks=[
            "Open https://example.com",
        ],
    )

def create_handler(mock_engine, action):
    """
    Create a handler bound to one specific mock action.
    """

    def handler(**kwargs):
        return mock_engine.execute(
            action,
            kwargs,
        )

    return handler

# =============================================================================
# Automation Engine Setup
# =============================================================================

def create_automation_dispatcher() -> tuple[
    AutomationActionDispatcher,
    object,
]:
    """
    Create the mock Automation Engine and connect it to the
    AutomationActionDispatcher.
    """

    mock_engine = create_default_mock_engine()

    registry = ActionRegistry()

    for action in mock_engine.list_actions():
        registry.register(
            action,
            create_handler(mock_engine, action),
        )

    dispatcher = AutomationActionDispatcher(
        registry,
    )

    return dispatcher, mock_engine

# =============================================================================
# M5-E.7 — AgentOrchestrator → Automation Engine
# =============================================================================

def test_agent_orchestrator_executes_automation_task():

    # -------------------------------------------------------------------------
    # Stage 1 — Create Mock Automation Engine
    # -------------------------------------------------------------------------

    dispatcher, mock_engine = create_automation_dispatcher()

    # -------------------------------------------------------------------------
    # Stage 2 — Create Agent Orchestrator
    # -------------------------------------------------------------------------

    orchestrator = AgentOrchestrator(
        dispatcher,
        execution_mode=ExecutionMode.SEQUENTIAL,
        timeout_seconds=30.0,
        max_retries=0,
    )

    # -------------------------------------------------------------------------
    # Stage 3 — Create LLM Plan
    # -------------------------------------------------------------------------

    plan = build_level_1_llm_plan()

    # -------------------------------------------------------------------------
    # Stage 4 — Run Complete Orchestration
    # -------------------------------------------------------------------------

    result = orchestrator.run(plan)
    

    # -------------------------------------------------------------------------
    # Stage 5 — Request Result
    # -------------------------------------------------------------------------

    assert result is not None

    assert result.request_id is not None

    assert result.status == ResultStatus.SUCCESS

    # -------------------------------------------------------------------------
    # Stage 6 — Agent Brain Planning
    # -------------------------------------------------------------------------

    assert result.validation is not None

    assert result.validation.is_valid is True

    assert result.planning_result is not None

    assert result.planning_result.is_valid is True

    assert result.planning_result.total_steps == 1

    # -------------------------------------------------------------------------
    # Stage 7 — Automation Execution
    # -------------------------------------------------------------------------

    assert len(result.outcomes) == 1

    outcome = result.outcomes[0]

    assert outcome.task_id == 1

    assert outcome.success is True

    assert outcome.status == ExecutionStatus.COMPLETED

    assert outcome.attempt == 1

    # -------------------------------------------------------------------------
    # Stage 8 — Decision Manager
    # -------------------------------------------------------------------------

    assert len(result.decisions) == 1

    decision = result.decisions[0]

    assert decision.task_id == 1

    # -------------------------------------------------------------------------
    # Stage 9 — Final Runtime State
    # -------------------------------------------------------------------------

    assert (
        result.context.execution_graph
        is not None
    )

    # The orchestrator's StateManager should have moved the task
    # to COMPLETED after successful automation execution.
    assert (
        orchestrator.state_manager.get_status(1)
        == ExecutionStatus.COMPLETED
    )

    # -------------------------------------------------------------------------
    # Stage 10 — Mock Automation Verification
    # -------------------------------------------------------------------------

    history = mock_engine.get_execution_history()

    assert len(history) == 1

    assert history[0]["action"] == "open"

    assert history[0]["parameters"] is not None