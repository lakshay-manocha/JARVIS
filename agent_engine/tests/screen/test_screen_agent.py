from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agent_engine.automation.agents.screen.screen_agent import (
    ScreenAutomationAgent,
)
from agent_engine.automation.models.lifecycle import AgentLifecycleState
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType


class FakeScreenAware:
    """
    Deterministic ScreenAware replacement.

    No OCR, VLM, GPU, or real screen is used.
    """

    def initialize(self):
        return None

    def capture_screen(
        self,
        *,
        monitor=None,
        all_screens=False,
    ):
        return {
            "success": True,
            "width": 1920,
            "height": 1080,
            "monitor": monitor,
            "all_screens": all_screens,
        }

    def capture_region(
        self,
        *,
        x,
        y,
        width,
        height,
    ):
        return {
            "success": True,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }

    def get_screen_size(
        self,
        *,
        monitor=None,
    ):
        return {
            "width": 1920,
            "height": 1080,
            "monitor": monitor,
        }

    def locate_text(
        self,
        *,
        text,
        case_sensitive=False,
    ):
        return {
            "found": text == "Settings",
            "coordinates": (
                {"x": 960, "y": 540}
                if text == "Settings"
                else None
            ),
            "bbox": (
                {
                    "x1": 900,
                    "y1": 510,
                    "x2": 1020,
                    "y2": 570,
                }
                if text == "Settings"
                else None
            ),
            "confidence": 0.95 if text == "Settings" else None,
            "method": "ocr",
            "latency_ms": 2.1,
        }

    def locate_element(
        self,
        *,
        query,
    ):
        return {
            "found": query == "Login button",
            "coordinates": (
                {"x": 800, "y": 450}
                if query == "Login button"
                else None
            ),
            "bbox": (
                {
                    "x1": 740,
                    "y1": 420,
                    "x2": 860,
                    "y2": 480,
                }
                if query == "Login button"
                else None
            ),
            "confidence": (
                0.91
                if query == "Login button"
                else None
            ),
            "method": "vlm",
            "latency_ms": 8.4,
        }

    def detect_visible_elements(
        self,
        *,
        element_types=None,
    ):
        return {
            "elements": [
                {
                    "type": "button",
                    "text": "Login",
                    "bbox": {
                        "x1": 740,
                        "y1": 420,
                        "x2": 860,
                        "y2": 480,
                    },
                    "confidence": 0.91,
                },
                {
                    "type": "text",
                    "text": "Settings",
                    "bbox": {
                        "x1": 900,
                        "y1": 510,
                        "x2": 1020,
                        "y2": 570,
                    },
                    "confidence": 0.95,
                },
            ],
            "method": "vlm",
            "latency_ms": 10.2,
        }


def make_request(
    action: str,
    parameters: dict | None = None,
):
    return ActionRequest(
        task_id= 1,
        action=action,
        parameters=parameters or {},
        tool=ToolType.SCREEN,
        category=ActionCategory.SCREEN,
    )


@pytest.fixture
def screen():
    return FakeScreenAware()


@pytest.fixture
def agent(screen):
    return ScreenAutomationAgent(
        screen=screen
    )


# =============================================================================
# Identity
# =============================================================================


def test_agent_id(agent):
    assert agent.agent_id == "screen_agent"


def test_agent_name(agent):
    assert agent.name == "Screen/Vision Automation Agent"


def test_tool_type(agent):
    assert agent.tool_type == ToolType.SCREEN


def test_supported_actions(agent):
    assert agent.SUPPORTED_ACTIONS == {
        "capture_screen",
        "capture_region",
        "get_screen_size",
        "locate_text",
        "locate_element",
        "detect_visible_elements",
    }


# =============================================================================
# Capability validation
# =============================================================================


@pytest.mark.parametrize(
    "action",
    [
        "capture_screen",
        "capture_region",
        "get_screen_size",
        "locate_text",
        "locate_element",
        "detect_visible_elements",
    ],
)
def test_can_execute_supported_actions(
    agent,
    action,
):
    request = make_request(
        action,
        (
            {
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
            }
            if action == "capture_region"
            else (
                {"text": "Settings"}
                if action == "locate_text"
                else (
                    {"query": "Login button"}
                    if action == "locate_element"
                    else {}
                )
            )
        ),
    )

    assert agent.can_execute(request) is True


@pytest.mark.parametrize(
    "action",
    [
        "locate",
        "find_text",
        "find_element",
    ],
)
def test_old_actions_are_rejected(
    agent,
    action,
):
    request = make_request(action)

    assert agent.can_execute(request) is False


def test_wrong_tool_is_rejected(agent):
    request = MagicMock()

    request.tool = ToolType.MOUSE
    request.category = ActionCategory.SCREEN
    request.action = "capture_screen"

    assert agent.can_execute(request) is False


# =============================================================================
# Capture
# =============================================================================


def test_capture_screen(agent):
    result = agent.execute(
        make_request(
            "capture_screen"
        )
    )

    assert result.success is True
    assert result.output["width"] == 1920
    assert result.output["height"] == 1080


def test_capture_screen_all_monitors(agent):
    result = agent.execute(
        make_request(
            "capture_screen",
            {
                "all_screens": True,
            },
        )
    )

    assert result.success is True
    assert result.output["all_screens"] is True


def test_capture_region(agent):
    result = agent.execute(
        make_request(
            "capture_region",
            {
                "x": 100,
                "y": 200,
                "width": 500,
                "height": 300,
            },
        )
    )

    assert result.success is True
    assert result.output["x"] == 100
    assert result.output["y"] == 200
    assert result.output["width"] == 500
    assert result.output["height"] == 300


def test_capture_region_rejects_zero_width(agent):
    result = agent.execute(
        make_request(
            "capture_region",
            {
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 100,
            },
        )
    )

    assert result.success is False


# =============================================================================
# Screen size
# =============================================================================


def test_get_screen_size(agent):
    result = agent.execute(
        make_request(
            "get_screen_size"
        )
    )

    assert result.success is True
    assert result.output["width"] == 1920
    assert result.output["height"] == 1080


# =============================================================================
# Text location
# =============================================================================


def test_locate_text(agent):
    result = agent.execute(
        make_request(
            "locate_text",
            {
                "text": "Settings",
            },
        )
    )

    assert result.success is True

    assert result.output["found"] is True

    assert result.output["coordinates"] == {
        "x": 960,
        "y": 540,
    }

    assert result.output["bbox"] == {
        "x1": 900,
        "y1": 510,
        "x2": 1020,
        "y2": 570,
    }

    assert result.output["method"] == "ocr"


def test_locate_text_not_found(agent):
    result = agent.execute(
        make_request(
            "locate_text",
            {
                "text": "DoesNotExist",
            },
        )
    )

    assert result.success is False
    assert result.output["found"] is False
    assert result.output["confidence"] is None


def test_locate_text_requires_text(agent):
    result = agent.execute(
        make_request(
            "locate_text"
        )
    )

    assert result.success is False


# =============================================================================
# Element location
# =============================================================================


def test_locate_element(agent):
    result = agent.execute(
        make_request(
            "locate_element",
            {
                "query": "Login button",
            },
        )
    )

    assert result.success is True

    assert result.output["found"] is True

    assert result.output["coordinates"] == {
        "x": 800,
        "y": 450,
    }

    assert result.output["method"] == "vlm"


def test_locate_element_not_found(agent):
    result = agent.execute(
        make_request(
            "locate_element",
            {
                "query": "Unknown element",
            },
        )
    )

    assert result.success is False
    assert result.output["found"] is False


def test_locate_element_requires_query(agent):
    result = agent.execute(
        make_request(
            "locate_element"
        )
    )

    assert result.success is False


# =============================================================================
# Visible elements
# =============================================================================


def test_detect_visible_elements(agent):
    result = agent.execute(
        make_request(
            "detect_visible_elements"
        )
    )

    assert result.success is True

    elements = result.output["elements"]

    assert len(elements) == 2

    assert elements[0]["type"] == "button"
    assert elements[0]["text"] == "Login"

    assert elements[1]["type"] == "text"
    assert elements[1]["text"] == "Settings"


# =============================================================================
# Lifecycle
# =============================================================================


def test_initial_lifecycle(agent):
    assert (
        agent.lifecycle_state
        == AgentLifecycleState.CREATED
    )


def test_lazy_initialization(agent):
    result = agent.execute(
        make_request(
            "get_screen_size"
        )
    )

    assert result.success is True

    assert (
        agent.lifecycle_state
        == AgentLifecycleState.READY
    )


def test_cleanup(agent):
    agent.initialize()

    assert (
        agent.lifecycle_state
        == AgentLifecycleState.READY
    )

    agent.cleanup()

    assert (
        agent.lifecycle_state
        == AgentLifecycleState.CLEANED
    )


# =============================================================================
# Perception-only guarantee
# =============================================================================


def test_agent_has_no_mouse_execution_methods(agent):
    assert not hasattr(
        agent,
        "click",
    )

    assert not hasattr(
        agent,
        "move_mouse",
    )

    assert not hasattr(
        agent,
        "double_click",
    )


def test_agent_has_no_keyboard_execution_methods(agent):
    assert not hasattr(
        agent,
        "type_text",
    )

    assert not hasattr(
        agent,
        "press_key",
    )


# =============================================================================
# Metadata
# =============================================================================


def test_metadata(agent):
    metadata = agent.metadata

    assert metadata["agent_id"] == "screen_agent"

    assert (
        metadata["agent_name"]
        == "Screen/Vision Automation Agent"
    )

    assert metadata["perception_only"] is True

    assert (
        metadata["version"]
        == "M5-M"
    )