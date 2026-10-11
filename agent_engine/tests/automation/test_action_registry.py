"""
===============================================================================
File Name   : test_action_registry.py
Module      : Automation Engine Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for the ActionRegistry.

Author      : Team Automation
===============================================================================
"""

import pytest

from agent_engine.automation.registry.action_registry import (
    ActionRegistry,
)


# =============================================================================
# Test Handlers
# =============================================================================

def open_url_handler(**kwargs):
    return "URL_OPENED"


def click_handler(**kwargs):
    return "CLICKED"


# =============================================================================
# Registration Tests
# =============================================================================

def test_register_action():
    registry = ActionRegistry()

    registry.register("open_url", open_url_handler)

    assert registry.contains("open_url")


def test_registered_action_can_be_resolved():
    registry = ActionRegistry()

    registry.register("open_url", open_url_handler)

    handler = registry.resolve("open_url")

    assert handler is open_url_handler


def test_action_is_normalized():
    registry = ActionRegistry()

    registry.register("OPEN_URL", open_url_handler)

    assert registry.contains("open_url")
    assert registry.contains("OPEN_URL")

    assert registry.resolve("OPEN_URL") is open_url_handler


# =============================================================================
# Multiple Actions
# =============================================================================

def test_multiple_actions_can_be_registered():
    registry = ActionRegistry()

    registry.register("open_url", open_url_handler)
    registry.register("click", click_handler)

    assert len(registry) == 2

    assert registry.contains("open_url")
    assert registry.contains("click")


# =============================================================================
# Handler Execution
# =============================================================================

def test_resolved_handler_can_execute():
    registry = ActionRegistry()

    registry.register("open_url", open_url_handler)

    handler = registry.resolve("open_url")

    result = handler(url="https://example.com")

    assert result == "URL_OPENED"


# =============================================================================
# Missing Action
# =============================================================================

def test_unknown_action_raises_key_error():
    registry = ActionRegistry()

    with pytest.raises(KeyError):
        registry.resolve("unknown_action")


# =============================================================================
# Invalid Registration
# =============================================================================

def test_empty_action_rejected():
    registry = ActionRegistry()

    with pytest.raises(ValueError):
        registry.register("", open_url_handler)


def test_non_callable_handler_rejected():
    registry = ActionRegistry()

    with pytest.raises(TypeError):
        registry.register("open_url", "not_callable")


# =============================================================================
# Unregister
# =============================================================================

def test_unregister_action():
    registry = ActionRegistry()

    registry.register("open_url", open_url_handler)

    assert registry.contains("open_url")

    registry.unregister("open_url")

    assert not registry.contains("open_url")


# =============================================================================
# List Actions
# =============================================================================

def test_list_actions():
    registry = ActionRegistry()

    registry.register("click", click_handler)
    registry.register("open_url", open_url_handler)

    assert registry.list_actions() == [
        "click",
        "open_url",
    ]


# =============================================================================
# Clear
# =============================================================================

def test_clear_registry():
    registry = ActionRegistry()

    registry.register("open_url", open_url_handler)
    registry.register("click", click_handler)

    registry.clear()

    assert len(registry) == 0
    assert registry.list_actions() == []