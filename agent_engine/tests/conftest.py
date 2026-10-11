"""
===============================================================================
File Name   : conftest.py
Module      : Test Configuration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Global pytest configuration and reusable fixtures.

This file provides common fixtures, sample data, and helper utilities used
across unit, integration, and end-to-end tests.

Pytest automatically discovers this file. Fixtures defined here are available
to every test module without explicit imports.

Author : Team Agent
===============================================================================
"""
import sys
from pathlib import Path
from copy import deepcopy

import pytest

# =============================================================================
# Add Project Root to Python Path
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Sample LLM Output
# =============================================================================

@pytest.fixture
def sample_llm_output():
    """
    Sample LLM response used throughout the test suite.
    """

    return {
        "goal": "Summarize the latest PDF of Spring AI tutorial",
        "summary": (
            "Open browser, search for the Spring AI tutorial, "
            "download the latest PDF, and summarize it."
        ),
        "missing_information": [
            "URL or specific source"
        ],
        "tasks": [
            "Open Chrome",
            "Search for Spring AI tutorial",
            "Download latest PDF",
            "Summarize downloaded PDF"
        ]
    }


# =============================================================================
# Sample Task List
# =============================================================================

@pytest.fixture
def sample_tasks():
    """
    Common task list used for Interpreter and TextNormalizer tests.
    """

    return [
        "Open Chrome",
        "Search Google",
        "Download PDF",
        "Summarize PDF"
    ]


# =============================================================================
# Empty Task List
# =============================================================================

@pytest.fixture
def empty_tasks():
    """
    Empty task list fixture.
    """

    return []


# =============================================================================
# Deep Copy Utility
# =============================================================================

@pytest.fixture
def deep_copy():
    """
    Returns deepcopy function for safe object copying inside tests.
    """

    return deepcopy


# =============================================================================
# Common Normalization Samples
# =============================================================================

@pytest.fixture
def normalization_samples():
    """
    Sample inputs used by TextNormalizer tests.
    """

    return {
        "browser": "Launch Google Chrome Browser",
        "application": "Open Visual Studio Code",
        "website": "Go to GitHub",
        "filetype": "Download latest PDF",
        "stopwords": "Please open the browser",
        "synonym": "Open the webpage",
        "mixed": "Please Launch Google Chrome Browser and Download the latest PDF"
    }