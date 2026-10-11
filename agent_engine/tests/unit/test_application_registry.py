"""
===============================================================================
File Name   : test_application_registry.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for ApplicationRegistry.

This test suite verifies:
    • Application normalization
    • Canonical application names
    • Case insensitivity
    • Unknown application handling
    • Registry lookup
    • Application metadata
    • Registry immutability

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.registry.application_registry import ApplicationRegistry


# =============================================================================
# Fixture
# =============================================================================

@pytest.fixture
def registry():
    """Returns ApplicationRegistry."""
    return ApplicationRegistry()


# =============================================================================
# Normalization Tests
# =============================================================================

@pytest.mark.parametrize(
    "application, expected",
    [
        ("visual studio code", "vscode"),
        ("vs code", "vscode"),
        ("vscode", "vscode"),
        ("microsoft word", "word"),
        ("ms word", "word"),
        ("word", "word"),
        ("microsoft excel", "excel"),
        ("excel", "excel"),
        ("microsoft powerpoint", "powerpoint"),
        ("powerpoint", "powerpoint"),
        ("notepad", "notepad"),
        ("calculator", "calculator"),
        ("calc", "calculator"),
        ("paint", "paint"),
        ("mspaint", "paint"),
        ("file explorer", "explorer"),
        ("windows explorer", "explorer"),
        ("explorer", "explorer"),
        ("command prompt", "cmd"),
        ("cmd", "cmd"),
        ("powershell", "powershell"),
    ],
)
def test_normalize_known_applications(registry, application, expected):
    assert registry.normalize(application) == expected


# =============================================================================
# Case Insensitivity
# =============================================================================

@pytest.mark.parametrize(
    "application, expected",
    [
        ("VS CODE", "vscode"),
        ("Visual Studio Code", "vscode"),
        ("WORD", "word"),
        ("Excel", "excel"),
        ("POWERPOINT", "powerpoint"),
        ("Notepad", "notepad"),
        ("CALC", "calculator"),
        ("Paint", "paint"),
        ("Explorer", "explorer"),
        ("CMD", "cmd"),
        ("PowerShell", "powershell"),
    ],
)
def test_case_insensitive_normalization(registry, application, expected):
    assert registry.normalize(application) == expected


# =============================================================================
# Whitespace Handling
# =============================================================================

@pytest.mark.parametrize(
    "application, expected",
    [
        (" vscode ", "vscode"),
        ("   word", "word"),
        ("excel   ", "excel"),
        ("  powershell  ", "powershell"),
    ],
)
def test_whitespace_normalization(registry, application, expected):
    assert registry.normalize(application) == expected


# =============================================================================
# Unknown Applications
# =============================================================================

@pytest.mark.parametrize(
    "application",
    [
        "figma",
        "slack",
        "discord",
        "photoshop",
    ],
)
def test_unknown_application_returns_original(registry, application):
    assert registry.normalize(application) == application.lower()


# =============================================================================
# Contains Tests
# =============================================================================

@pytest.mark.parametrize(
    "application",
    [
        "visual studio code",
        "vs code",
        "vscode",
        "word",
        "excel",
        "powerpoint",
        "notepad",
        "calculator",
        "calc",
        "paint",
        "mspaint",
        "file explorer",
        "explorer",
        "cmd",
        "powershell",
    ],
)
def test_contains_known_application(registry, application):
    assert registry.contains(application)


@pytest.mark.parametrize(
    "application",
    [
        "figma",
        "slack",
        "discord",
    ],
)
def test_contains_unknown_application(registry, application):
    assert not registry.contains(application)


# =============================================================================
# Metadata Tests
# =============================================================================

def test_metadata_vscode(registry):
    metadata = registry.get_metadata("vs code")

    assert metadata is not None
    assert metadata["canonical"] == "vscode"
    assert metadata["display_name"] == "Visual Studio Code"


def test_metadata_word(registry):
    metadata = registry.get_metadata("word")

    assert metadata["canonical"] == "word"
    assert metadata["display_name"] == "Microsoft Word"


def test_metadata_excel(registry):
    metadata = registry.get_metadata("excel")

    assert metadata["canonical"] == "excel"
    assert metadata["display_name"] == "Microsoft Excel"


def test_metadata_explorer(registry):
    metadata = registry.get_metadata("explorer")

    assert metadata["canonical"] == "explorer"
    assert metadata["display_name"] == "File Explorer"


def test_unknown_metadata(registry):
    assert registry.get_metadata("figma") is None


# =============================================================================
# Empty String
# =============================================================================

def test_empty_string(registry):
    assert registry.normalize("") == ""
    assert not registry.contains("")


# =============================================================================
# None Handling
# =============================================================================

def test_none_input(registry):
    with pytest.raises(Exception):
        registry.normalize(None)


# =============================================================================
# Registry Copy
# =============================================================================

def test_all_applications_returns_copy(registry):
    apps = registry.all_applications()

    apps["word"] = {
        "canonical": "modified",
        "display_name": "Modified"
    }

    metadata = registry.get_metadata("word")

    assert metadata["canonical"] == "word"
    assert metadata["display_name"] == "Microsoft Word"


# =============================================================================
# Registry Consistency
# =============================================================================

def test_registry_is_not_modified(registry):
    before = registry.all_applications()

    registry.normalize("vscode")
    registry.normalize("word")
    registry.normalize("excel")
    registry.normalize("paint")
    registry.normalize("cmd")

    after = registry.all_applications()

    assert before == after