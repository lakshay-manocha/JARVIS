from __future__ import annotations

from agent_engine.automation.agents.mouse.mouse_agent import (
    MouseAutomationAgent,
)
from agent_engine.automation.agents.screen.screen_agent import (
    ScreenAutomationAgent,
)
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
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
from agent_engine.contracts.enums import ToolType
from agent_engine.perception.screen import ScreenAware


def build_automation_dispatcher() -> AutomationActionDispatcher:
    """
    Construct the agent-based automation execution path.

    The screen agent handles perception.
    The mouse agent handles physical mouse actions.
    Both are registered in one registry and resolved by one mapper.
    """
    agent_registry = AgentRegistry()
    tool_agent_mapper = ToolAgentMapper(agent_registry)

    screen_agent = ScreenAutomationAgent(
        screen=ScreenAware(),
    )
    mouse_agent = MouseAutomationAgent()

    tool_agent_mapper.register(
        ToolType.SCREEN,
        screen_agent,
    )
    tool_agent_mapper.register(
        ToolType.MOUSE,
        mouse_agent,
    )

    dispatcher = AutomationActionDispatcher(
        registry=ActionRegistry(),
        tool_agent_mapper=tool_agent_mapper,
    )

    # Fail at startup instead of discovering missing registrations
    # during a user request.
    assert tool_agent_mapper.contains(ToolType.SCREEN)
    assert tool_agent_mapper.contains(ToolType.MOUSE)

    return dispatcher