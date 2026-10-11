"""
===============================================================================
File Name   : test_parameter_resolver.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for ParameterResolver.

These tests verify that structured parameters are correctly extracted from
normalized task text and attached to interpreted tasks.

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.agent_brain.parameter_resolver import ParameterResolver

from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.agent_brain.models.llm_plan import LLMPlan

from agent_engine.contracts.enums import ProcessingStage


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
        tasks=[task_text]
    )

    context = ProcessingContext(llm_plan=plan)

    context.interpreted_tasks.append(
        InterpretedTask(
            task_id=1,
            original_text=task_text,
            normalized_text=task_text.lower()
        )
    )

    return context


# =============================================================================
# Browser Extraction
# =============================================================================

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Open Chrome", "chrome"),
        ("Launch Firefox", "firefox"),
        ("Start Edge", "edge"),
    ]
)
def test_browser_parameter(text, expected):

    resolver = ParameterResolver()

    result = resolver.resolve(
        build_context(text)
    )

    assert (
        result.interpreted_tasks[0]
        .parameters["browser"]
        == expected
    )


# =============================================================================
# Application Extraction
# =============================================================================

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Open VS Code", "vscode"),
        ("Launch Notepad", "notepad"),
    ]
)
def test_application_parameter(text, expected):

    resolver = ParameterResolver()

    result = resolver.resolve(
        build_context(text)
    )

    assert (
        result.interpreted_tasks[0]
        .parameters["application"]
        == expected
    )


# =============================================================================
# Website Extraction
# =============================================================================

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Open GitHub", "github"),
        ("Visit Google", "google"),
    ]
)
def test_website_parameter(text, expected):

    resolver = ParameterResolver()

    result = resolver.resolve(
        build_context(text)
    )

    assert (
        result.interpreted_tasks[0]
        .parameters["website"]
        == expected
    )


# =============================================================================
# Filetype Extraction
# =============================================================================

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Download PDF", "pdf"),
        ("Open DOCX", "word"),
        ("Read TXT", "text"),
    ]
)
def test_filetype_parameter(text, expected):

    resolver = ParameterResolver()

    result = resolver.resolve(
        build_context(text)
    )

    assert (
        result.interpreted_tasks[0]
        .parameters["filetype"]
        == expected
    )


# =============================================================================
# Multiple Parameters
# =============================================================================

def test_multiple_parameters():

    resolver = ParameterResolver()

    result = resolver.resolve(
        build_context(
            "Open Chrome and download PDF from GitHub"
        )
    )

    params = result.interpreted_tasks[0].parameters

    assert params["browser"] == "chrome"
    assert params["website"] == "github"
    assert params["filetype"] == "pdf"


# =============================================================================
# No Parameters
# =============================================================================

def test_no_parameters():

    resolver = ParameterResolver()

    result = resolver.resolve(
        build_context(
            "Think about artificial intelligence"
        )
    )

    assert (
        result.interpreted_tasks[0].parameters
        == {}
    )


# =============================================================================
# Processing Stage
# =============================================================================

def test_processing_stage_updated():

    resolver = ParameterResolver()

    result = resolver.resolve(
        build_context("Open Chrome")
    )

    assert (
        result.current_stage
        == ProcessingStage.PARAMETER_RESOLUTION
    )


# =============================================================================
# Logs
# =============================================================================

def test_logs_created():

    resolver = ParameterResolver()

    result = resolver.resolve(
        build_context("Open Chrome")
    )

    assert len(result.processing_logs) >= 2


# =============================================================================
# Multiple Tasks
# =============================================================================

def test_multiple_tasks():

    resolver = ParameterResolver()

    plan = LLMPlan(
        goal="Goal",
        summary="Summary",
        missing_information=[],
        tasks=[
            "Open Chrome",
            "Download PDF"
        ]
    )

    context = ProcessingContext(
        llm_plan=plan
    )

    context.interpreted_tasks = [

        InterpretedTask(
            task_id=1,
            original_text="Open Chrome",
            normalized_text="open chrome"
        ),

        InterpretedTask(
            task_id=2,
            original_text="Download PDF",
            normalized_text="download pdf"
        )
    ]

    result = resolver.resolve(context)

    assert (
        len(result.interpreted_tasks)
        == 2
    )


# =============================================================================
# Parameters Assigned
# =============================================================================

def test_parameters_assigned():

    resolver = ParameterResolver()

    result = resolver.resolve(
        build_context("Open Chrome")
    )

    assert (
        result.interpreted_tasks[0].parameters
        != {}
    )


# =============================================================================
# Context Returned
# =============================================================================

def test_context_returned():

    resolver = ParameterResolver()

    context = build_context("Open Chrome")

    result = resolver.resolve(context)

    assert isinstance(
        result,
        ProcessingContext
    )