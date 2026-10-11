"""
===============================================================================
File Name   : test_intent_detector.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for the IntentDetector.

These tests verify that interpreted tasks are assigned the correct intent
using the current rule-based implementation.

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.agent_brain.intent_detector import IntentDetector
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

def build_context(task_text: str) -> ProcessingContext:
    """
    Creates a ProcessingContext containing a single interpreted task.
    """

    plan = LLMPlan(
        goal="Test Goal",
        summary="Test Summary",
        missing_information=[],
        tasks=[task_text],
    )

    context = ProcessingContext(llm_plan=plan)

    context.interpreted_tasks = [
        InterpretedTask(
            task_id=1,
            original_text=task_text,
            normalized_text=task_text.lower(),
        )
    ]

    return context


# =============================================================================
# Intent Detection Tests
# =============================================================================

@pytest.mark.parametrize(
    "task,intent",
    [
        ("Open Chrome", IntentType.OPEN_APPLICATION),
        ("Launch VS Code", IntentType.OPEN_APPLICATION),
        ("Run Calculator", IntentType.OPEN_APPLICATION),

        ("Search Python tutorials", IntentType.SEARCH_WEB),
        ("Find AI papers", IntentType.SEARCH_WEB),
        ("Lookup weather", IntentType.SEARCH_WEB),

        ("Download latest PDF", IntentType.DOWNLOAD_FILE),
        ("Fetch report", IntentType.DOWNLOAD_FILE),
        ("Grab document", IntentType.DOWNLOAD_FILE),

        ("Summarize report", IntentType.SUMMARIZE_DOCUMENT),

        ("Delete temp file", IntentType.DELETE_FILE),
        ("Remove folder", IntentType.DELETE_FILE),

        ("Move report", IntentType.MOVE_FILE),

        ("Copy document", IntentType.COPY_FILE),

        ("Rename report", IntentType.RENAME_FILE),

        ("Take a screenshot", IntentType.CAPTURE_SCREEN),

        ("Capture screen", IntentType.CAPTURE_SCREEN),

        ("Capture region", IntentType.CAPTURE_REGION),

        ("Get screen size", IntentType.GET_SCREEN_SIZE),

        ("Find text on screen", IntentType.LOCATE_TEXT),

        ("Find element on screen", IntentType.LOCATE_ELEMENT),

        ("Detect visible elements", IntentType.DETECT_VISIBLE_ELEMENTS),

    ],
)
def test_detect_intent(task, intent):

    detector = IntentDetector()

    context = build_context(task)

    result = detector.detect(context)

    assert (
        result.interpreted_tasks[0]
        .intent
        .intent
        == intent
    )


# =============================================================================
# Unknown Intent
# =============================================================================

def test_unknown_intent():

    detector = IntentDetector()

    context = build_context(
        "Elephant dancing in forest"
    )

    result = detector.detect(context)

    assert (
        result.interpreted_tasks[0]
        .intent
        .intent
        == IntentType.UNKNOWN
    )


# =============================================================================
# Confidence
# =============================================================================

def test_confidence_score():

    detector = IntentDetector()

    context = build_context(
        "Download PDF"
    )

    result = detector.detect(context)

    assert (
        result.interpreted_tasks[0]
        .intent
        .confidence
        == 1.0
    )


# =============================================================================
# Detection Method
# =============================================================================

def test_detection_method():

    detector = IntentDetector()

    context = build_context(
        "Search Python"
    )

    result = detector.detect(context)

    assert (
        result.interpreted_tasks[0]
        .intent
        .detection_method
        == "rule_based"
    )


# =============================================================================
# Processing Stage
# =============================================================================

def test_processing_stage_updated():

    detector = IntentDetector()

    context = build_context(
        "Open Chrome"
    )

    result = detector.detect(context)

    assert (
        result.current_stage
        == ProcessingStage.DETECTING_INTENT
    )


# =============================================================================
# Intent Result Exists
# =============================================================================

def test_intent_result_created():

    detector = IntentDetector()

    context = build_context(
        "Open Chrome"
    )

    result = detector.detect(context)

    assert result.interpreted_tasks[0].intent is not None


# =============================================================================
# Multiple Tasks
# =============================================================================

def test_multiple_tasks():

    detector = IntentDetector()

    plan = LLMPlan(
        goal="Goal",
        summary="Summary",
        missing_information=[],
        tasks=[
            "Open Chrome",
            "Search AI",
            "Download PDF",
        ],
    )

    context = ProcessingContext(llm_plan=plan)

    context.interpreted_tasks = [

        InterpretedTask(
            task_id=1,
            original_text="Open Chrome",
            normalized_text="open chrome",
        ),

        InterpretedTask(
            task_id=2,
            original_text="Search AI",
            normalized_text="search ai",
        ),

        InterpretedTask(
            task_id=3,
            original_text="Download PDF",
            normalized_text="download pdf",
        ),
    ]

    result = detector.detect(context)

    assert len(result.interpreted_tasks) == 3

    assert (
        result.interpreted_tasks[0]
        .intent
        .intent
        == IntentType.OPEN_APPLICATION
    )

    assert (
        result.interpreted_tasks[1]
        .intent
        .intent
        == IntentType.SEARCH_WEB
    )

    assert (
        result.interpreted_tasks[2]
        .intent
        .intent
        == IntentType.DOWNLOAD_FILE
    )