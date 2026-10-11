"""
===============================================================================
File Name   : test_action_registry.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for the Action Registry.

This test suite verifies:
    • Action normalization
    • Canonical action handling
    • Case insensitivity
    • Unknown action behavior
    • Registry lookup
    • Registry immutability

Author : Team Agent
===============================================================================
"""

import pytest

from agent_engine.registry.action_registry import ActionRegistry


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def registry():
    """
    Returns a fresh ActionRegistry instance.
    """
    return ActionRegistry()


# =============================================================================
# Normalization Tests
# =============================================================================

@pytest.mark.parametrize(
    "input_action, expected",
    [
        ("launch", "open"),
        ("Launch", "open"),
        ("LAUNCH", "open"),
        ("start", "open"),
        ("run", "open"),
        ("fetch", "download"),
        ("grab", "download"),
        ("remove", "delete"),
        ("erase", "delete"),
        ("copy", "copy"),
    ]
)
def test_normalize_known_actions(registry, input_action, expected):
    """
    Verify that known action synonyms are normalized correctly.
    """
    assert registry.normalize(input_action) == expected


# =============================================================================
# Canonical Actions
# =============================================================================

@pytest.mark.parametrize(
    "action",
    [
        "open",
        "download",
        "delete",
        "copy",
        "move",
        "rename",
        "search",
        "summarize",
    ]
)
def test_canonical_actions_remain_unchanged(registry, action):
    """
    Canonical actions should remain unchanged.
    """
    assert registry.normalize(action) == action


# =============================================================================
# Unknown Actions
# =============================================================================

@pytest.mark.parametrize(
    "action",
    [
        "banana",
        "elephant",
        "unknown_action",
        "xyz123",
    ]
)
def test_unknown_actions_are_not_modified(registry, action):
    """
    Unknown actions should be returned unchanged.
    """
    assert registry.normalize(action) == action


# =============================================================================
# Contains Tests
# =============================================================================

@pytest.mark.parametrize(
    "action",
    [
        "launch",
        "download",
        "remove",
        "copy",
        "search",
    ]
)
def test_contains_known_action(registry, action):
    """
    Registry should recognize known actions.
    """
    assert registry.contains(action)


@pytest.mark.parametrize(
    "action",
    [
        "banana",
        "unknown",
        "football",
    ]
)
def test_contains_unknown_action(registry, action):
    """
    Registry should reject unknown actions.
    """
    assert not registry.contains(action)


# =============================================================================
# Whitespace Handling
# =============================================================================

@pytest.mark.parametrize(
    "action, expected",
    [
        (" launch ", "open"),
        ("   fetch", "download"),
        ("remove   ", "delete"),
    ]
)
def test_normalize_trims_whitespace(registry, action, expected):
    """
    Leading/trailing whitespace should not affect normalization.
    """
    assert registry.normalize(action.strip()) == expected


# =============================================================================
# Empty Input
# =============================================================================

def test_empty_string(registry):
    """
    Empty string should be returned unchanged.
    """
    assert registry.normalize("") == ""


# =============================================================================
# None Handling
# =============================================================================

def test_none_input(registry):
    """
    Registry should either safely return None or raise a TypeError.
    Adjust this test according to your implementation.
    """
    with pytest.raises(Exception):
        registry.normalize(None)


# =============================================================================
# Registry Copy
# =============================================================================

def test_registry_is_not_modified(registry):
    """
    Verify that registry data is never modified after multiple operations.
    """

    before = registry.all_actions()

    registry.normalize("launch")
    registry.normalize("download")
    registry.normalize("remove")
    registry.normalize("copy")

    after = registry.all_actions()

    assert before == after

    # Ensure the returned dictionary is a copy
    after["launch"] = "modified"

    assert registry.normalize("launch") == "open"