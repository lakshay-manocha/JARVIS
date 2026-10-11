"""
Tests for the concrete Automation Engine Action Dispatcher.
"""

from unittest import result

from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)
from agent_engine.automation.integration.action_request_builder import (
    ActionRequestBuilder,
)
from agent_engine.automation.registry.action_registry import ActionRegistry
from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.decision_manager.models.execution_outcome import FailureType
from agent_engine.contracts.enums import (
    ActionCategory,
)
from unittest.mock import MagicMock

from agent_engine.automation.agents.mouse.mouse_agent import MouseAutomationAgent
from agent_engine.automation.registry.agent_registry import AgentRegistry
from agent_engine.automation.registry.tool_agent_mapper import ToolAgentMapper
from agent_engine.contracts.enums import ToolType
from agent_engine.automation.agents.base import AutomationAgent
from agent_engine.automation.models.capabilities import AgentCapabilities
from agent_engine.automation.agents.desktop.desktop_agent import ApplicationWindowAutomationAgent
from agent_engine.automation.agents.desktop.fake_desktop_backend import FakeDesktopBackend
from agent_engine.automation.agents.base import AgentLifecycleState
from agent_engine.automation.agents.filesystem.filesystem_agent import (
    FileSystemAutomationAgent,
)
from agent_engine.automation.agents.filesystem.fake_filesystem_backend import (
    FakeFileSystemBackend,
)
class FakeMouseActions:

    def __init__(self):
        self.calls = []

    def move_mouse(self, x, y):
        self.calls.append(
            ("move_mouse", x, y)
        )
        return {
            "x": x,
            "y": y,
        }

    def click(self, button="left"):
        self.calls.append(
            ("click", button)
        )
        return {
            "button": button,
        }

    def double_click(self, button="left"):
        self.calls.append(
            ("double_click", button)
        )
        return {
            "button": button,
        }

    def right_click(self):
        self.calls.append(
            ("right_click",)
        )
        return {
            "button": "right",
        }

    def mouse_down(self, button="left"):
        self.calls.append(
            ("mouse_down", button)
        )
        return {
            "button": button,
        }

    def mouse_up(self, button="left"):
        self.calls.append(
            ("mouse_up", button)
        )
        return {
            "button": button,
        }

    def scroll(self, dx=0, dy=0):
        self.calls.append(
            ("scroll", dx, dy)
        )
        return {
            "dx": dx,
            "dy": dy,
        }

def create_task(
    *,
    task_id: int = 1,
    action: str = "open_url",
    tool: str = "browser_agent",
    parameters: dict | None = None,
) -> InterpretedTask:

    return InterpretedTask(
        task_id=task_id,
        original_text="Open example website",
        normalized_text="open example website",
        action=action,
        tool=tool,
        parameters=parameters or {},
    )


def test_successful_action_dispatch():
    registry = ActionRegistry()

    registry.register(
        "open_url",
        lambda **kwargs: "SUCCESS",
    )

    dispatcher = AutomationActionDispatcher(registry)

    task = create_task(
        parameters={"url": "https://example.com"}
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 1
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.attempt == 1
    assert result.failure_type == FailureType.NONE
    assert result.execution_time is not None
    assert result.execution_time >= 0


def test_handler_receives_parameters():
    registry = ActionRegistry()

    received = {}

    def handler(**kwargs):
        received.update(kwargs)
        return "SUCCESS"

    registry.register("open_url", handler)

    dispatcher = AutomationActionDispatcher(registry)

    task = create_task(
        parameters={
            "url": "https://example.com"
        }
    )

    dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert received == {
        "url": "https://example.com"
    }


def test_unknown_action_returns_failed_outcome():
    registry = ActionRegistry()

    dispatcher = AutomationActionDispatcher(registry)

    task = create_task(
        action="unknown_action"
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 1
    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.failure_type == FailureType.UNKNOWN
    assert result.error_message is not None


def test_handler_exception_returns_failed_outcome():
    registry = ActionRegistry()

    def failing_handler(**kwargs):
        raise RuntimeError("Automation failed")

    registry.register(
        "open_url",
        failing_handler,
    )

    dispatcher = AutomationActionDispatcher(registry)

    task = create_task()

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.failure_type == FailureType.UNKNOWN
    assert result.error_message == "Automation failed"


def test_attempt_number_is_preserved():
    registry = ActionRegistry()

    registry.register(
        "open_url",
        lambda **kwargs: "SUCCESS",
    )

    dispatcher = AutomationActionDispatcher(registry)

    task = create_task()

    result = dispatcher.dispatch(
        task,
        attempt=3,
    )

    assert result.attempt == 3
    assert result.retry_count == 2


def test_timeout_is_preserved():
    registry = ActionRegistry()

    registry.register(
        "open_url",
        lambda **kwargs: "SUCCESS",
    )

    dispatcher = AutomationActionDispatcher(registry)

    task = create_task()

    result = dispatcher.dispatch(
        task,
        attempt=1,
        timeout_seconds=30,
    )

    assert result.timeout_seconds == 30
    assert result.timed_out is False


def test_missing_action_fails():
    registry = ActionRegistry()

    dispatcher = AutomationActionDispatcher(registry)

    task = create_task(
        action=None
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION


def test_missing_tool_fails():
    registry = ActionRegistry()

    dispatcher = AutomationActionDispatcher(registry)

    task = create_task(
        tool=None
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION

# =============================================================================
# M5-E.2 Integration Tests
# =============================================================================

def test_dispatcher_uses_action_request_builder():
    """
    Dispatcher should use ActionRequestBuilder to construct the request.
    """

    class SpyBuilder(ActionRequestBuilder):
        def __init__(self):
            self.called = False

        def build(self, task, *, timeout_seconds=None):
            self.called = True
            return super().build(
                task,
                timeout_seconds=timeout_seconds,
            )

    registry = ActionRegistry()

    def open_url(**kwargs):
        return "SUCCESS"

    registry.register("open_url", open_url)

    builder = SpyBuilder()

    dispatcher = AutomationActionDispatcher(
        registry,
        request_builder=builder,
    )

    task = InterpretedTask(
        task_id=1,
        original_text="Open example website",
        normalized_text="open example website",
        action="open_url",
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
        timeout_seconds=30,
    )

    assert builder.called is True
    assert result.success is True
    assert result.status == ExecutionStatus.COMPLETED

def test_dispatcher_passes_timeout_to_action_request_builder():
    """
    Dispatcher should forward timeout configuration to the builder.
    """

    class SpyBuilder(ActionRequestBuilder):
        def __init__(self):
            self.received_timeout = None

        def build(self, task, *, timeout_seconds=None):
            self.received_timeout = timeout_seconds
            return super().build(
                task,
                timeout_seconds=timeout_seconds,
            )

    registry = ActionRegistry()

    def open_url(**kwargs):
        return "SUCCESS"

    registry.register("open_url", open_url)

    builder = SpyBuilder()

    dispatcher = AutomationActionDispatcher(
        registry,
        request_builder=builder,
    )

    task = InterpretedTask(
        task_id=1,
        original_text="Open example website",
        normalized_text="open example website",
        action="open_url",
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
    )

    dispatcher.dispatch(
        task,
        attempt=1,
        timeout_seconds=45,
    )

    assert builder.received_timeout == 45

def test_dispatcher_routes_mouse_action_to_mouse_agent():

    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    mouse_actions = MagicMock()

    mouse_agent = MouseAutomationAgent(
        actions=mouse_actions,
    )

    agent_registry.register(mouse_agent)

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.MOUSE,
        mouse_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        action="move_mouse",
        tool="mouse_agent",
        parameters={
            "x": 500,
            "y": 300,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 1
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True

    mouse_actions.move_mouse.assert_called_once_with(
        x=500,
        y=300,
    )

def test_dispatcher_routes_mouse_click_to_mouse_agent():

    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    mouse_actions = MagicMock()

    mouse_agent = MouseAutomationAgent(
        actions=mouse_actions,
    )

    agent_registry.register(mouse_agent)

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.MOUSE,
        mouse_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        action="click",
        tool="mouse_agent",
        parameters={
            "button": "left",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 1
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True

    mouse_actions.click.assert_called_once_with(
        button="left",
    )

def test_dispatcher_rejects_mouse_request_when_agent_cannot_execute():

    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    class NonCapableMouseAgent(AutomationAgent):

        @property
        def agent_id(self) -> str:
            return "mouse_agent"

        @property
        def name(self) -> str:
            return "Non-Capable Mouse Agent"

        @property
        def description(self) -> str:
            return "Test agent that cannot execute mouse actions."

        @property
        def tool_type(self) -> ToolType:
            return ToolType.MOUSE

        @property
        def metadata(self) -> dict[str, object]:
            return {
                "agent_id": self.agent_id,
                "agent_type": "mouse",
                "backend": "test",
            }

        @property
        def capabilities(self):
            return AgentCapabilities(
                frozenset()
            )

        def can_execute(
            self,
            action_request,
        ) -> bool:
            return False

        def execute(
            self,
            action_request,
        ):
            raise AssertionError(
                "execute() should not be called when can_execute() is False."
            )

        def initialize(self) -> None:
            pass

        def cleanup(self) -> None:
            pass

    mouse_agent = NonCapableMouseAgent()

    agent_registry.register(
        mouse_agent
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.MOUSE,
        mouse_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        action="move_mouse",
        tool="mouse_agent",
        parameters={
            "x": 500,
            "y": 300,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 1
    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION
    assert result.error_message is not None
    assert "cannot execute" in result.error_message

def test_dispatcher_integrates_mouse_execution_result():

    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    mouse_actions = MagicMock()

    mouse_actions.click.return_value = {
        "action": "click",
        "button": "left",
    }

    mouse_agent = MouseAutomationAgent(
        actions=mouse_actions,
    )

    agent_registry.register(mouse_agent)

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.MOUSE,
        mouse_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=10,
        action="click",
        tool="mouse_agent",
        parameters={
            "button": "left",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 10
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE
    assert result.execution_time is not None
    assert result.execution_time >= 0

    mouse_actions.click.assert_called_once_with(
        button="left",
    )
# =============================================================================
# M5-K.8 Dispatcher → Desktop Agent Integration Tests
# =============================================================================

def test_dispatcher_routes_launch_application_to_desktop_agent():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=100,
        action="launch_application",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 100
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "launch_application",
            "parameters": {
                "application": "notepad",
            },
        }
    ]

def test_dispatcher_routes_resize_window_to_desktop_agent():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=101,
        action="resize_window",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
            "width": 1200,
            "height": 800,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 101
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "resize_window",
            "parameters": {
                "application": "notepad",
                "width": 1200,
                "height": 800,
            },
        }
    ]


def test_dispatcher_routes_position_window_to_desktop_agent():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=102,
        action="position_window",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
            "x": 100,
            "y": 50,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 102
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "position_window",
            "parameters": {
                "application": "notepad",
                "x": 100,
                "y": 50,
            },
        }
    ]

# =============================================================================
# M5-K.8C Complete Dispatcher Coverage — Remaining Desktop Actions
# =============================================================================


def test_dispatcher_routes_close_application_to_desktop_agent():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=103,
        action="close_application",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 103
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "close_application",
            "parameters": {
                "application": "notepad",
            },
        }
    ]


def test_dispatcher_routes_restart_application_to_desktop_agent():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=104,
        action="restart_application",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 104
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "restart_application",
            "parameters": {
                "application": "notepad",
            },
        }
    ]


def test_dispatcher_routes_terminate_application_to_desktop_agent():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=105,
        action="terminate_application",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 105
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "terminate_application",
            "parameters": {
                "application": "notepad",
            },
        }
    ]


def test_dispatcher_routes_focus_window_to_desktop_agent():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=106,
        action="focus_window",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 106
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "focus_window",
            "parameters": {
                "application": "notepad",
            },
        }
    ]


def test_dispatcher_routes_switch_window_to_desktop_agent():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=107,
        action="switch_window",
        tool="desktop_agent",
        parameters={
            "target": "Notepad",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 107
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "switch_window",
            "parameters": {
                "target": "Notepad",
            },
        }
    ]

# =============================================================================
# M5-K.9A End-to-End Integration Test
# =============================================================================


def test_application_window_agent_end_to_end_execution_flow():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    tasks = [
        create_task(
            task_id=200,
            action="launch_application",
            tool="desktop_agent",
            parameters={
                "application": "notepad",
            },
        ),
        create_task(
            task_id=201,
            action="focus_window",
            tool="desktop_agent",
            parameters={
                "application": "notepad",
            },
        ),
        create_task(
            task_id=202,
            action="resize_window",
            tool="desktop_agent",
            parameters={
                "application": "notepad",
                "width": 1200,
                "height": 800,
            },
        ),
        create_task(
            task_id=203,
            action="position_window",
            tool="desktop_agent",
            parameters={
                "application": "notepad",
                "x": 100,
                "y": 50,
            },
        ),
        create_task(
            task_id=204,
            action="switch_window",
            tool="desktop_agent",
            parameters={
                "target": "Notepad",
            },
        ),
        create_task(
            task_id=205,
            action="close_application",
            tool="desktop_agent",
            parameters={
                "application": "notepad",
            },
        ),
    ]

    results = []

    for task in tasks:
        result = dispatcher.dispatch(
            task,
            attempt=1,
        )
        results.append(result)

    assert len(results) == 6

    for result, task in zip(results, tasks):
        assert result.task_id == task.task_id
        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "launch_application",
            "parameters": {
                "application": "notepad",
            },
        },
        {
            "operation": "focus_window",
            "parameters": {
                "application": "notepad",
            },
        },
        {
            "operation": "resize_window",
            "parameters": {
                "application": "notepad",
                "width": 1200,
                "height": 800,
            },
        },
        {
            "operation": "position_window",
            "parameters": {
                "application": "notepad",
                "x": 100,
                "y": 50,
            },
        },
        {
            "operation": "switch_window",
            "parameters": {
                "target": "Notepad",
            },
        },
        {
            "operation": "close_application",
            "parameters": {
                "application": "notepad",
            },
        },
    ]
# =============================================================================
# M5-K.9B Lifecycle Integration Tests
# =============================================================================


def test_application_window_agent_restart_lifecycle_through_dispatcher():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=210,
        action="restart_application",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 210
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "restart_application",
            "parameters": {
                "application": "notepad",
            },
        }
    ]

def test_application_window_agent_terminate_lifecycle_through_dispatcher():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=211,
        action="terminate_application",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 211
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.calls == [
        {
            "operation": "terminate_application",
            "parameters": {
                "application": "notepad",
            },
        }
    ]
# =============================================================================
# M5-K.9C Failure / Validation Propagation Tests
# =============================================================================


def test_dispatcher_propagates_missing_application_validation_failure():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=220,
        action="launch_application",
        tool="desktop_agent",
        parameters={},
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 220
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION

    assert backend.calls == []
def test_dispatcher_propagates_invalid_resize_validation_failure():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=221,
        action="resize_window",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
            "width": -1200,
            "height": 800,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 221
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION

    assert backend.calls == []
def test_dispatcher_propagates_invalid_position_validation_failure():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=222,
        action="position_window",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
            "x": "100",
            "y": 50,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 222
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION

    assert backend.calls == []
def test_dispatcher_propagates_missing_switch_target_validation_failure():
    registry = ActionRegistry()

    agent_registry = AgentRegistry()

    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.DESKTOP,
        desktop_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=223,
        action="switch_window",
        tool="desktop_agent",
        parameters={},
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 223
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION

    assert backend.calls == []

def test_application_window_agent_failure_cleanup_lifecycle():
    registry = ActionRegistry()
    agent_registry = AgentRegistry()
    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend
    )

    mapper = ToolAgentMapper(agent_registry)
    mapper.register(
        ToolType.DESKTOP,
        desktop_agent
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    failing_task = create_task(
        task_id=230,
        action="launch_application",
        tool="desktop_agent",
        parameters={},
    )

    failed_result = dispatcher.dispatch(
        failing_task,
        attempt=1,
    )

    assert failed_result.task_id == 230
    assert failed_result.success is False
    assert failed_result.failure_type == FailureType.VALIDATION

    assert (
        desktop_agent.lifecycle_state
        == AgentLifecycleState.FAILED
    )

    desktop_agent.cleanup()

    assert (
        desktop_agent.lifecycle_state
        == AgentLifecycleState.CLEANED
    )

    assert backend.calls == []

def test_application_window_agent_normal_cleanup_lifecycle():
    registry = ActionRegistry()
    agent_registry = AgentRegistry()
    backend = FakeDesktopBackend()

    desktop_agent = ApplicationWindowAutomationAgent(
        backend=backend
    )

    mapper = ToolAgentMapper(agent_registry)
    mapper.register(
        ToolType.DESKTOP,
        desktop_agent
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=240,
        action="launch_application",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 240
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert (
        desktop_agent.lifecycle_state
        == AgentLifecycleState.READY
    )

    desktop_agent.cleanup()

    assert (
        desktop_agent.lifecycle_state
        == AgentLifecycleState.CLEANED
    )

    assert backend.calls == [
        {
            "operation": "launch_application",
            "parameters": {
                "application": "notepad",
            },
        }
    ]

# =============================================================================
# M5-L.8 Dispatcher → File-System Agent Integration Tests
# =============================================================================


def test_dispatcher_routes_create_file_to_filesystem_agent():
    """
    Dispatcher should route a create_file ActionRequest to the
    FileSystemAutomationAgent and execute it through the fake backend.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry,
    )

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=300,
        action="create_file",
        tool="filesystem_agent",
        parameters={
            "path": r"C:\jarvis_m5_l\test.txt",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 300
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    exists_result = backend.path_exists(
        r"C:\jarvis_m5_l\test.txt",
    )

    assert exists_result["exists"] is True

# =============================================================================
# M5-L.8 Additional Dispatcher → File-System Agent Integration Tests
# =============================================================================


def test_dispatcher_routes_create_directory_to_filesystem_agent():
    """
    Dispatcher should route create_directory to the
    FileSystemAutomationAgent.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(agent_registry)

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=301,
        action="create_directory",
        tool="filesystem_agent",
        parameters={
            "path": r"C:\jarvis_m5_l",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 301
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    exists_result = backend.path_exists(
        r"C:\jarvis_m5_l",
    )

    assert exists_result["exists"] is True


def test_dispatcher_routes_copy_file_to_filesystem_agent():
    """
    Dispatcher should route copy_file to the
    FileSystemAutomationAgent.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    backend.create_file(
        r"C:\jarvis_m5_l\source.txt",
    )

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(agent_registry)

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=302,
        action="copy_file",
        tool="filesystem_agent",
        parameters={
            "source": r"C:\jarvis_m5_l\source.txt",
            "destination": r"C:\jarvis_m5_l\copy.txt",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 302
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.path_exists(
        r"C:\jarvis_m5_l\copy.txt",
    )["exists"] is True


def test_dispatcher_routes_move_file_to_filesystem_agent():
    """
    Dispatcher should route move_file to the
    FileSystemAutomationAgent.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    backend.create_file(
        r"C:\jarvis_m5_l\source.txt",
    )

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(agent_registry)

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=303,
        action="move_file",
        tool="filesystem_agent",
        parameters={
            "source": r"C:\jarvis_m5_l\source.txt",
            "destination": r"C:\jarvis_m5_l\moved.txt",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 303
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.path_exists(
        r"C:\jarvis_m5_l\source.txt",
    )["exists"] is False

    assert backend.path_exists(
        r"C:\jarvis_m5_l\moved.txt",
    )["exists"] is True


def test_dispatcher_routes_rename_file_to_filesystem_agent():
    """
    Dispatcher should route rename_file to the
    FileSystemAutomationAgent.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    backend.create_file(
        r"C:\jarvis_m5_l\old.txt",
    )

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(agent_registry)

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=304,
        action="rename_file",
        tool="filesystem_agent",
        parameters={
            "path": r"C:\jarvis_m5_l\old.txt",
            "new_name": "new.txt",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 304
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    assert backend.path_exists(
        r"C:\jarvis_m5_l\old.txt",
    )["exists"] is False

    assert backend.path_exists(
        r"C:\jarvis_m5_l\new.txt",
    )["exists"] is True


def test_dispatcher_routes_list_directory_to_filesystem_agent():
    """
    Dispatcher should route list_directory to the
    FileSystemAutomationAgent.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    backend.create_directory(
        r"C:\jarvis_m5_l",
    )

    backend.create_file(
        r"C:\jarvis_m5_l\file.txt",
    )

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(agent_registry)

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=305,
        action="list_directory",
        tool="filesystem_agent",
        parameters={
            "path": r"C:\jarvis_m5_l",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 305
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE

    # The dispatcher returns the integrated execution outcome.
    # The fake backend state verifies the directory itself exists.
    directory_result = backend.path_exists(
        r"C:\jarvis_m5_l",
    )

    assert directory_result["exists"] is True


def test_dispatcher_routes_path_exists_to_filesystem_agent():
    """
    Dispatcher should route path_exists to the
    FileSystemAutomationAgent.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    backend.create_file(
        r"C:\jarvis_m5_l\exists.txt",
    )

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(agent_registry)

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=306,
        action="path_exists",
        tool="filesystem_agent",
        parameters={
            "path": r"C:\jarvis_m5_l\exists.txt",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 306
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.failure_type == FailureType.NONE


def test_dispatcher_propagates_filesystem_validation_failure():
    """
    Dispatcher should propagate filesystem validation failures
    produced by the FileSystemAutomationAgent.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(agent_registry)

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=307,
        action="create_file",
        tool="filesystem_agent",
        parameters={
            "path": "",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 307
    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION
    assert result.error_message is not None

# =============================================================================
# M5-L.9 Registry + Dispatcher Integration Tests
# =============================================================================


def test_dispatcher_fails_when_filesystem_tool_mapping_is_missing():
    """
    Dispatcher should fail when a filesystem agent exists in the
    AgentRegistry but no ToolType.FILESYSTEM mapping exists.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    # Register the agent directly in AgentRegistry.
    agent_registry.register(filesystem_agent)

    # Mapper exists, but no FILESYSTEM mapping is registered.
    mapper = ToolAgentMapper(
        agent_registry,
    )

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=400,
        action="create_file",
        tool="filesystem_agent",
        parameters={
            "path": r"C:\jarvis_m5_l\missing_mapping.txt",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 400
    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.error_message is not None

    # The agent itself must still exist in the registry.
    assert agent_registry.contains("filesystem_agent") is True
    assert agent_registry.get("filesystem_agent") is filesystem_agent

    # The filesystem mapping must still be absent.
    assert mapper.contains(ToolType.FILESYSTEM) is False

def test_dispatcher_respects_filesystem_mapping_removal():
    """
    Removing the filesystem ToolType mapping should prevent dispatcher
    resolution while keeping the filesystem agent registered.
    """

    registry = ActionRegistry()
    agent_registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(
        agent_registry,
    )

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    # Verify initial integration state.
    assert mapper.contains(ToolType.FILESYSTEM) is True
    assert agent_registry.contains("filesystem_agent") is True

    # Remove only the ToolType mapping.
    mapper.unregister(ToolType.FILESYSTEM)

    assert mapper.contains(ToolType.FILESYSTEM) is False

    # Agent must remain registered.
    assert agent_registry.contains("filesystem_agent") is True
    assert agent_registry.get("filesystem_agent") is filesystem_agent

    dispatcher = AutomationActionDispatcher(
        registry,
        tool_agent_mapper=mapper,
    )

    task = create_task(
        task_id=401,
        action="create_file",
        tool="filesystem_agent",
        parameters={
            "path": r"C:\jarvis_m5_l\removed_mapping.txt",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.task_id == 401
    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.error_message is not None

    # The agent remains available in AgentRegistry even though
    # the ToolType mapping was removed.
    assert agent_registry.contains("filesystem_agent") is True
    assert agent_registry.get("filesystem_agent") is filesystem_agent