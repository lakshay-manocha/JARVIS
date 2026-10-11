"""
===============================================================================
File Name   : test_action_resolver.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for ActionResolver.

These tests verify that detected intents are correctly resolved into canonical
actions using the Action Registry.

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.agent_brain.action_resolver import ActionResolver
from agent_engine.agent_brain.models.intent_result import IntentResult
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.contracts.enums import (
    IntentType,
    ProcessingStage,
)


# =============================================================================
# Helper
# =============================================================================

def build_context(intent: IntentType) -> ProcessingContext:
    """
    Creates a ProcessingContext with one interpreted task.
    """

    plan = LLMPlan(
        goal="Test",
        summary="Testing Action Resolver",
        missing_information=[],
        tasks=["Dummy Task"]
    )

    task = InterpretedTask(
        task_id=1,
        original_text="Dummy Task",
        normalized_text="dummy task",
        intent=IntentResult(
            intent=intent,
            confidence=1.0,
            detection_method="rule_based",
            reasoning="Unit Test"
        )
    )

    context = ProcessingContext(llm_plan=plan)
    context.interpreted_tasks.append(task)

    return context


# =============================================================================
# Intent -> Action Mapping
# =============================================================================

@pytest.mark.parametrize(
    "intent, expected_action",
    [
        (IntentType.OPEN_APPLICATION, "open"),
        (IntentType.OPEN_WEBSITE, "open"),
        (IntentType.SEARCH_WEB, "search"),
        (IntentType.DOWNLOAD_FILE, "download"),
        (IntentType.SUMMARIZE_DOCUMENT, "summarize"),
        (IntentType.DELETE_FILE, "delete"),
        (IntentType.MOVE_FILE, "move"),
        (IntentType.COPY_FILE, "copy"),
        (IntentType.RENAME_FILE, "rename"),
    ]
)
def test_action_resolution(intent, expected_action):

    resolver = ActionResolver()

    context = build_context(intent)

    result = resolver.resolve(context)

    assert (
        result.interpreted_tasks[0].action
        == expected_action
    )


# =============================================================================
# Unknown Intent
# =============================================================================

def test_unknown_action():

    resolver = ActionResolver()

    context = build_context(
        IntentType.UNKNOWN
    )

    result = resolver.resolve(context)

    assert result.interpreted_tasks[0].action is None


# =============================================================================
# Processing Stage
# =============================================================================

def test_processing_stage_updated():

    resolver = ActionResolver()

    context = build_context(
        IntentType.OPEN_APPLICATION
    )

    result = resolver.resolve(context)

    assert (
        result.current_stage
        == ProcessingStage.RESOLVING_ACTIONS
    )


# =============================================================================
# Logging
# =============================================================================

def test_logs_created():

    resolver = ActionResolver()

    context = build_context(
        IntentType.OPEN_APPLICATION
    )

    result = resolver.resolve(context)

    assert len(result.processing_logs) >= 2


# =============================================================================
# Multiple Tasks
# =============================================================================

def test_multiple_tasks():

    resolver = ActionResolver()

    plan = LLMPlan(
        goal="Test",
        summary="Multiple Tasks",
        missing_information=[],
        tasks=["Task1", "Task2"]
    )

    context = ProcessingContext(
        llm_plan=plan
    )

    context.interpreted_tasks.extend([

        InterpretedTask(
            task_id=1,
            original_text="Task1",
            normalized_text="open chrome",
            intent=IntentResult(
                intent=IntentType.OPEN_APPLICATION,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Test"
            )
        ),

        InterpretedTask(
            task_id=2,
            original_text="Task2",
            normalized_text="download pdf",
            intent=IntentResult(
                intent=IntentType.DOWNLOAD_FILE,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Test"
            )
        )
    ])

    result = resolver.resolve(context)

    assert (
        result.interpreted_tasks[0].action
        == "open"
    )

    assert (
        result.interpreted_tasks[1].action
        == "download"
    )


# =============================================================================
# Action Assigned
# =============================================================================

def test_action_assigned():

    resolver = ActionResolver()

    context = build_context(
        IntentType.SEARCH_WEB
    )

    result = resolver.resolve(context)

    assert result.interpreted_tasks[0].action is not None


# =============================================================================
# Context Returned
# =============================================================================

def test_context_returned():

    resolver = ActionResolver()

    context = build_context(
        IntentType.OPEN_APPLICATION
    )

    result = resolver.resolve(context)

    assert isinstance(
        result,
        ProcessingContext
    )