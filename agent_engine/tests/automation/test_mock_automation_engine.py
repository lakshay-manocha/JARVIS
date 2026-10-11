"""
Tests for the Module 5-D Mock Automation Engine.
"""

import pytest

from agent_engine.automation.engine.mock_automation_engine import (
    MockAutomationEngine,
    create_default_mock_engine,
)


# =============================================================================
# Registration Tests
# =============================================================================

def test_register_mock_action():

    engine = MockAutomationEngine()

    def test_action(**kwargs):
        return "SUCCESS"

    engine.register("test_action", test_action)

    assert engine.contains("test_action")
    assert engine.list_actions() == ["test_action"]


def test_empty_action_rejected():

    engine = MockAutomationEngine()

    with pytest.raises(ValueError):
        engine.register("", lambda **kwargs: "SUCCESS")


def test_non_callable_handler_rejected():

    engine = MockAutomationEngine()

    with pytest.raises(TypeError):
        engine.register("test_action", "not_callable")


# =============================================================================
# Execution Tests
# =============================================================================

def test_registered_action_executes():

    engine = MockAutomationEngine()

    def open_url(**kwargs):
        return f"Opened {kwargs['url']}"

    engine.register("open_url", open_url)

    result = engine.execute(
        "open_url",
        {"url": "https://example.com"},
    )

    assert result == "Opened https://example.com"


def test_parameters_are_passed_to_handler():

    engine = MockAutomationEngine()

    def handler(**kwargs):
        return kwargs["value"]

    engine.register("test_action", handler)

    result = engine.execute(
        "test_action",
        {"value": 42},
    )

    assert result == 42


def test_unknown_action_raises_key_error():

    engine = MockAutomationEngine()

    with pytest.raises(KeyError):
        engine.execute("unknown_action")


# =============================================================================
# History Tests
# =============================================================================

def test_execution_history_is_recorded():

    engine = MockAutomationEngine()

    engine.register(
        "test_action",
        lambda **kwargs: "SUCCESS",
    )

    engine.execute(
        "test_action",
        {"value": 10},
    )

    history = engine.get_execution_history()

    assert len(history) == 1
    assert history[0]["action"] == "test_action"
    assert history[0]["parameters"]["value"] == 10
    assert history[0]["result"] == "SUCCESS"


def test_clear_history():

    engine = MockAutomationEngine()

    engine.register(
        "test_action",
        lambda **kwargs: "SUCCESS",
    )

    engine.execute("test_action")

    assert len(engine.get_execution_history()) == 1

    engine.clear_history()

    assert engine.get_execution_history() == []


# =============================================================================
# Default Engine Tests
# =============================================================================

def test_default_mock_engine_contains_standard_actions():

    engine = create_default_mock_engine()

    assert engine.contains("open")
    assert engine.contains("open_url")
    assert engine.contains("search")
    assert engine.contains("type_text")
    assert engine.contains("click")
    assert engine.contains("wait")
    assert engine.contains("take_screenshot")


def test_default_open_url_action():

    engine = create_default_mock_engine()

    result = engine.execute(
        "open_url",
        {
            "url": "https://example.com"
        },
    )

    assert result["action"] == "open_url"
    assert "https://example.com" in result["message"]