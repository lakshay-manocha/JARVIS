"""
===============================================================================
File Name   : test_validator.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for BasicValidator.

This test suite verifies:
    • Summary validation
    • Missing information validation
    • Duplicate task detection
    • Goal-task consistency
    • Successful validation

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.agent_brain.validator import BasicValidator
from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.contracts.enums import ValidationCode


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def validator():
    return BasicValidator()


@pytest.fixture
def valid_plan():
    return LLMPlan(
        goal="Download and summarize the Spring AI PDF",
        summary=(
            "Search the official website, download the PDF "
            "and summarize its contents."
        ),
        missing_information=[],
        tasks=[
            "Search for Spring AI PDF",
            "Download the PDF",
            "Summarize the PDF"
        ]
    )


# =============================================================================
# Valid Plan
# =============================================================================

def test_valid_plan(validator, valid_plan):

    result = validator.validate(valid_plan)

    assert result.is_valid
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


# =============================================================================
# Summary Validation
# =============================================================================

def test_missing_summary_warning(validator, valid_plan):

    valid_plan.summary = None

    result = validator.validate(valid_plan)

    assert len(result.warnings) == 1

    assert result.warnings[0].code == ValidationCode.MISSING_SUMMARY


def test_short_summary_warning(validator, valid_plan):

    valid_plan.summary = "Too short"

    result = validator.validate(valid_plan)

    assert len(result.warnings) == 1

    assert result.warnings[0].code == ValidationCode.SHORT_SUMMARY


# =============================================================================
# Missing Information Validation
# =============================================================================

def test_empty_missing_information_error(validator, valid_plan):

    valid_plan.missing_information = [
        "URL",
        "",
        "Destination Folder"
    ]

    result = validator.validate(valid_plan)

    assert len(result.errors) == 1

    assert result.errors[0].code == (
        ValidationCode.INVALID_MISSING_INFORMATION
    )


# =============================================================================
# Duplicate Tasks
# =============================================================================

def test_duplicate_tasks_warning(validator, valid_plan):

    valid_plan.tasks = [
        "Open Chrome",
        "Search Spring AI",
        "Open Chrome"
    ]

    result = validator.validate(valid_plan)

    assert len(result.warnings) == 2

    warning_codes = {warning.code for warning in result.warnings}

    assert "DUPLICATE_TASKS" in warning_codes
    assert "GOAL_TASK_MISMATCH" in warning_codes

def test_duplicate_tasks_case_insensitive(validator, valid_plan):

    valid_plan.tasks = [
        "Open Chrome",
        "open chrome",
        "OPEN CHROME"
    ]

    result = validator.validate(valid_plan)

    assert len(result.warnings) == 2

    warning_codes = {warning.code for warning in result.warnings}

    assert "DUPLICATE_TASKS" in warning_codes
    assert "GOAL_TASK_MISMATCH" in warning_codes

# =============================================================================
# Goal Consistency
# =============================================================================

def test_goal_task_mismatch_warning(validator, valid_plan):

    valid_plan.goal = "Download and summarize the PDF"

    valid_plan.tasks = [
        "Open Chrome",
        "Search Spring AI"
    ]

    result = validator.validate(valid_plan)

    assert any(
        warning.code == ValidationCode.GOAL_TASK_MISMATCH
        for warning in result.warnings
    )


def test_goal_task_consistency_passes(validator, valid_plan):

    result = validator.validate(valid_plan)

    assert not any(
        warning.code == ValidationCode.GOAL_TASK_MISMATCH
        for warning in result.warnings
    )


# =============================================================================
# Multiple Warnings
# =============================================================================

def test_multiple_validation_results(validator, valid_plan):

    valid_plan.summary = "short"

    valid_plan.tasks = [
        "Open Chrome",
        "Open Chrome"
    ]

    valid_plan.goal = "Download PDF"

    result = validator.validate(valid_plan)

    warning_codes = {
        warning.code
        for warning in result.warnings
    }

    assert ValidationCode.SHORT_SUMMARY in warning_codes

    assert ValidationCode.DUPLICATE_TASKS in warning_codes

    assert ValidationCode.GOAL_TASK_MISMATCH in warning_codes


# =============================================================================
# Empty Missing Information List
# =============================================================================

def test_empty_missing_information_list(validator, valid_plan):

    valid_plan.missing_information = []

    result = validator.validate(valid_plan)

    assert len(result.errors) == 0


# =============================================================================
# Duplicate Detection Ignores Whitespace
# =============================================================================

def test_duplicate_tasks_with_whitespace(validator, valid_plan):

    valid_plan.tasks = [
        "Open Chrome",
        "  Open Chrome  "
    ]

    result = validator.validate(valid_plan)

    assert any(
        warning.code == ValidationCode.DUPLICATE_TASKS
        for warning in result.warnings
    )