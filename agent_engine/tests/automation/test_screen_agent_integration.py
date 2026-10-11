
from __future__ import annotations

from agent_engine.agent_brain.models.interpreted_task import (
    InterpretedTask,
)
from agent_engine.automation.agents.screen.screen_agent import (
    ScreenAutomationAgent,
)
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)
from agent_engine.automation.integration.action_request_builder import (
    ActionRequestBuilder,
)
from agent_engine.automation.integration.execution_result_integrator import (
    ExecutionResultIntegrator,
)
from agent_engine.automation.registry.action_registry import (
    ActionRegistry,
)
from agent_engine.automation.registry.agent_registry import (
    AgentRegistry,
)
from agent_engine.automation.registry.tool_agent_mapper import (
    ToolAgentMapper,
)
from agent_engine.contracts.enums import (
    ExecutionStatus,
    ToolType,
)


class FakeScreenAware:
    """Deterministic screen backend; never accesses the real desktop."""

    def __init__(self):
        self.initialize_calls = 0
        self.capture_calls = 0

    def initialize(self):
        self.initialize_calls += 1

    def capture_screen(self, *, monitor=None, all_screens=False):
        self.capture_calls += 1
        return {
            "success": True,
            "width": 1920,
            "height": 1080,
            "monitor": monitor,
            "all_screens": all_screens,
        }


def test_screen_agent_dispatch_integration():
    # Arrange: real agent and infrastructure, fake perception backend.
    fake_screen = FakeScreenAware()
    screen_agent = ScreenAutomationAgent(screen=fake_screen)

    agent_registry = AgentRegistry()
    agent_registry.register(screen_agent)

    mapper = ToolAgentMapper(agent_registry)
    mapper.register(ToolType.SCREEN, screen_agent)

    dispatcher = AutomationActionDispatcher(
        ActionRegistry(),
        request_builder=ActionRequestBuilder(),
        tool_agent_mapper=mapper,
        result_integrator=ExecutionResultIntegrator(),
    )

    task = InterpretedTask(
        task_id=101,
        original_text="Capture the screen",
        normalized_text="capture the screen",
        action="capture_screen",
        tool="screen_agent",
        parameters={},
    )

    # Act: dispatch through the actual integration pipeline.
    outcome = dispatcher.dispatch(task, attempt=1)

    # Assert: request reached the fake backend and succeeded.
    assert outcome.success is True
    assert outcome.status == ExecutionStatus.COMPLETED
    assert fake_screen.initialize_calls == 1
    assert fake_screen.capture_calls == 1
