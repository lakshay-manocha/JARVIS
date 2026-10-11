from pydantic import ValidationError
import pytest

from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType


def test_valid_action_request():
    request = ActionRequest(
        task_id=1,
        action="open_url",
        category=ActionCategory.BROWSER,
        tool=ToolType.BROWSER,
        parameters={
            "url": "https://example.com"
        },
        timeout_seconds=30,
    )

    assert request.task_id == 1
    assert request.action == "open_url"
    assert request.category == ActionCategory.BROWSER
    assert request.tool == ToolType.BROWSER
    assert request.parameters["url"] == "https://example.com"


def test_action_request_rejects_empty_action():
    with pytest.raises(ValidationError):
        ActionRequest(
            task_id=1,
            action="",
            category=ActionCategory.BROWSER,
            tool=ToolType.BROWSER,
        )


def test_action_request_rejects_invalid_timeout():
    with pytest.raises(ValidationError):
        ActionRequest(
            task_id=1,
            action="open_url",
            category=ActionCategory.BROWSER,
            tool=ToolType.BROWSER,
            timeout_seconds=0,
        )


def test_action_request_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        ActionRequest(
            task_id=1,
            action="open_url",
            category=ActionCategory.BROWSER,
            tool=ToolType.BROWSER,
            unexpected_field="invalid",
        )

def test_browser_action_request():
    request = ActionRequest(
        task_id=5,
        action="open_url",
        category=ActionCategory.BROWSER,
        tool=ToolType.BROWSER,
        parameters={
            "url": "https://example.com"
        },
        timeout_seconds=30,
        metadata={
            "source": "agent_orchestrator"
        },
    )

    assert request.task_id == 5
    assert request.action == "open_url"
    assert request.tool == ToolType.BROWSER
    assert request.parameters["url"] == "https://example.com"