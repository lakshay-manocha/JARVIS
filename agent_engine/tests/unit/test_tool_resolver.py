"""
===============================================================================
File Name   : test_tool_resolver.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for ToolResolver.

Verifies that the correct automation controller is selected based on the
resolved action and extracted parameters.

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.agent_brain.tool_resolver import ToolResolver

from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.agent_brain.models.intent_result import IntentResult
from agent_engine.agent_brain.models.llm_plan import LLMPlan

from agent_engine.contracts.enums import (
    IntentType,
    ProcessingStage,
    ToolType,
)


# =============================================================================
# Helper
# =============================================================================

def build_context(
    action: str,
    parameters: dict | None = None,
) -> ProcessingContext:
    """
    Creates a ProcessingContext containing one interpreted task.
    """

    if parameters is None:
        parameters = {}

    plan = LLMPlan(
        goal="Test Goal",
        summary="Test Summary",
        missing_information=[],
        tasks=["Dummy Task"],
    )

    context = ProcessingContext(
        llm_plan=plan
    )

    context.interpreted_tasks.append(

        InterpretedTask(
            task_id=1,
            original_text="Dummy Task",
            normalized_text="dummy task",

            intent=IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Unit Test",
            ),

            action=action,
            parameters=parameters,
        )
    )

    return context


# =============================================================================
# Tool Resolution
# =============================================================================

@pytest.mark.parametrize(
    "action, parameters, expected_tool",
    [

        ("open",
         {"browser": "chrome"},
         ToolType.DESKTOP.value),

        ("open",
         {"application": "vscode"},
         ToolType.DESKTOP.value),

        ("open",
         {"website": "github"},
         ToolType.BROWSER.value),

        ("search",
         {},
         ToolType.BROWSER.value),

        ("download",
         {"filetype": "pdf"},
         ToolType.BROWSER.value),

        ("delete",
         {},
         ToolType.FILESYSTEM.value),

        ("move",
         {},
         ToolType.FILESYSTEM.value),

        ("copy",
         {},
         ToolType.FILESYSTEM.value),

        ("rename",
         {},
         ToolType.FILESYSTEM.value),

        ("summarize",
         {},
         ToolType.FILESYSTEM.value),

        ("capture_screen", {}, ToolType.SCREEN.value),
        ("capture_region", {}, ToolType.SCREEN.value),
        ("get_screen_size", {}, ToolType.SCREEN.value),
        ("locate_text", {}, ToolType.SCREEN.value),
        ("locate_element", {}, ToolType.SCREEN.value),
        ("detect_visible_elements", {}, ToolType.SCREEN.value),

    ]
)
def test_tool_resolution(
    action,
    parameters,
    expected_tool,
):

    resolver = ToolResolver()

    context = build_context(
        action,
        parameters,
    )

    result = resolver.resolve(context)

    assert (
        result.interpreted_tasks[0].tool
        == expected_tool
    )


# =============================================================================
# Unknown Tool
# =============================================================================

def test_unknown_tool():

    resolver = ToolResolver()

    context = build_context(
        "unsupported_action"
    )

    result = resolver.resolve(context)

    assert (
        result.interpreted_tasks[0].tool
        is None
    )


# =============================================================================
# Processing Stage
# =============================================================================

def test_processing_stage_updated():

    resolver = ToolResolver()

    context = build_context(
        "search"
    )

    result = resolver.resolve(context)

    assert (
        result.current_stage
        == ProcessingStage.TOOL_RESOLUTION
    )


# =============================================================================
# Logs Created
# =============================================================================

def test_logs_created():

    resolver = ToolResolver()

    context = build_context(
        "download"
    )

    result = resolver.resolve(context)

    assert len(result.processing_logs) >= 2


# =============================================================================
# Multiple Tasks
# =============================================================================

def test_multiple_tasks():

    resolver = ToolResolver()

    plan = LLMPlan(
        goal="Goal",
        summary="Summary",
        missing_information=[],
        tasks=[
            "Task 1",
            "Task 2",
        ],
    )

    context = ProcessingContext(
        llm_plan=plan
    )

    context.interpreted_tasks = [

        InterpretedTask(
            task_id=1,
            original_text="Task 1",
            normalized_text="task 1",

            intent=IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Unit Test",
            ),

            action="search",
        ),

        InterpretedTask(
            task_id=2,
            original_text="Task 2",
            normalized_text="task 2",

            intent=IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Unit Test",
            ),

            action="delete",
        ),
    ]

    result = resolver.resolve(context)

    assert len(result.interpreted_tasks) == 2


# =============================================================================
# Tool Assigned
# =============================================================================

def test_tool_assigned():

    resolver = ToolResolver()

    context = build_context(
        "search"
    )

    result = resolver.resolve(context)

    assert (
        result.interpreted_tasks[0].tool
        is not None
    )


# =============================================================================
# Context Returned
# =============================================================================

def test_context_returned():

    resolver = ToolResolver()

    context = build_context(
        "search"
    )

    result = resolver.resolve(context)

    assert isinstance(
        result,
        ProcessingContext,
    )