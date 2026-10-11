from __future__ import annotations

from typing import Any

from agent_engine.automation.agents.browser import (
    BrowserAutomationAgent,
    BrowserBackend,
    BrowserConfig,
)
from agent_engine.automation.models.lifecycle import AgentLifecycleState
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType


class FakeBrowserBackend(BrowserBackend):
    def __init__(self) -> None:
        super().__init__(BrowserConfig())
        self.initialize_calls = 0
        self.execute_calls: list[tuple[str, dict[str, Any], float | None]] = []
        self.cleanup_calls = 0

    @property
    def initialized(self) -> bool:
        return self.initialize_calls > 0 and self.cleanup_calls == 0

    def initialize(self) -> None:
        self.initialize_calls += 1

    def execute(
        self,
        action: str,
        parameters: dict[str, Any] | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> Any:
        self.execute_calls.append(
            (action, dict(parameters or {}), timeout_seconds)
        )
        return {"action": action, "parameters": dict(parameters or {})}

    def cleanup(self) -> None:
        self.cleanup_calls += 1


def browser_request(
    action: str = "open_url",
    *,
    parameters: dict[str, Any] | None = None,
) -> ActionRequest:
    return ActionRequest(
        task_id=1,
        action=action,
        category=ActionCategory.BROWSER,
        tool=ToolType.BROWSER,
        parameters=parameters or {"url": "https://example.com"},
    )


def test_browser_agent_exposes_identity() -> None:
    agent = BrowserAutomationAgent(backend=FakeBrowserBackend())

    assert agent.agent_id == "browser_agent"
    assert agent.tool_type == ToolType.BROWSER
    assert agent.name == "Browser Automation Agent"


def test_browser_agent_exposes_capabilities() -> None:
    agent = BrowserAutomationAgent(backend=FakeBrowserBackend())

    assert agent.supports("open_url")
    assert agent.supports("search")
    assert agent.supports("click_element")
    assert agent.supports("type_text")
    assert agent.supports("get_page_title")
    assert agent.supports("new_tab")
    assert not agent.supports("delete_file")


def test_browser_agent_can_execute_browser_action() -> None:
    agent = BrowserAutomationAgent(backend=FakeBrowserBackend())

    assert agent.can_execute(browser_request())


def test_browser_agent_rejects_wrong_tool() -> None:
    agent = BrowserAutomationAgent(backend=FakeBrowserBackend())

    request = ActionRequest(
        task_id=1,
        action="open_url",
        category=ActionCategory.BROWSER,
        tool=ToolType.DESKTOP,
        parameters={"url": "https://example.com"},
    )

    assert not agent.can_execute(request)


def test_browser_agent_rejects_unsupported_action() -> None:
    agent = BrowserAutomationAgent(backend=FakeBrowserBackend())

    request = browser_request("delete_file")

    assert not agent.can_execute(request)


def test_browser_agent_lazy_initializes_and_executes() -> None:
    backend = FakeBrowserBackend()
    agent = BrowserAutomationAgent(backend=backend)

    result = agent.execute(browser_request())

    assert result.success is True
    assert backend.initialize_calls == 1
    assert len(backend.execute_calls) == 1
    assert agent.lifecycle_state == AgentLifecycleState.READY


def test_browser_agent_passes_parameters_and_timeout() -> None:
    backend = FakeBrowserBackend()
    agent = BrowserAutomationAgent(backend=backend)

    request = ActionRequest(
        task_id=7,
        action="search",
        category=ActionCategory.BROWSER,
        tool=ToolType.BROWSER,
        parameters={"query": "JARVIS AI"},
        timeout_seconds=15,
    )

    result = agent.execute(request)

    assert result.success is True
    assert backend.execute_calls == [
        ("search", {"query": "JARVIS AI"}, 15)
    ]


def test_browser_agent_returns_standard_automation_result() -> None:
    agent = BrowserAutomationAgent(backend=FakeBrowserBackend())

    result = agent.execute(browser_request())

    assert result.task_id == 1
    assert result.action == "open_url"
    assert result.output["action"] == "open_url"
    assert result.execution_time is not None


def test_browser_agent_execution_failure_is_normalized() -> None:
    class FailingBackend(FakeBrowserBackend):
        def execute(
            self,
            action: str,
            parameters: dict[str, Any] | None = None,
            *,
            timeout_seconds: float | None = None,
        ) -> Any:
            raise RuntimeError("browser failed")

    agent = BrowserAutomationAgent(backend=FailingBackend())

    result = agent.execute(browser_request())

    assert result.success is False
    assert result.error is not None
    assert "browser failed" in result.error
    assert agent.lifecycle_state == AgentLifecycleState.FAILED


def test_browser_agent_cleanup() -> None:
    backend = FakeBrowserBackend()
    agent = BrowserAutomationAgent(backend=backend)

    agent.initialize()
    agent.cleanup()

    assert backend.cleanup_calls == 1
    assert agent.lifecycle_state == AgentLifecycleState.CLEANED
