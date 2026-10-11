"""
Tests for the Automation Agent Registry.
"""

import pytest

from agent_engine.automation.agents.base import AutomationAgent
from agent_engine.automation.agents.filesystem.filesystem_agent import FileSystemAutomationAgent
from agent_engine.automation.models.capabilities import AgentCapabilities
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.automation.registry.agent_registry import AgentRegistry
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType
from agent_engine.automation.agents.mouse.mouse_agent import MouseAutomationAgent
from agent_engine.automation.agents.desktop.desktop_agent import ApplicationWindowAutomationAgent
from agent_engine.automation.agents.desktop.fake_desktop_backend import FakeDesktopBackend
from agent_engine.automation.registry.tool_agent_mapper import ToolAgentMapper
from agent_engine.tests.unit.test_file_controller import FakeFileSystemBackend


# =============================================================================
# Test Agent
# =============================================================================

class TestRegistryAgent(AutomationAgent):
    """
    Minimal concrete agent used for registry tests.
    """

    def __init__(
        self,
        agent_id: str = "test_agent",
    ) -> None:
        super().__init__()
        self._agent_id = agent_id

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def name(self) -> str:
        return "Test Agent"

    @property
    def description(self) -> str:
        return "Test automation agent."

    @property
    def tool_type(self) -> ToolType:
        return ToolType.KEYBOARD

    @property
    def metadata(self) -> dict[str, object]:
        return {"test": True}

    @property
    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            actions={"type_text", "press_key"}
        )

    def initialize(self) -> None:
        pass

    def can_execute(
        self,
        action_request: ActionRequest,
    ) -> bool:
        return self.supports(action_request.action)

    def execute(
        self,
        action_request: ActionRequest,
    ) -> AutomationExecutionResult:
        return AutomationExecutionResult(
            task_id=action_request.task_id,
            action=action_request.action,
            success=True,
        )

    def cleanup(self) -> None:
        pass


# =============================================================================
# Registration Tests
# =============================================================================

def test_register_agent() -> None:
    registry = AgentRegistry()
    agent = TestRegistryAgent()

    registry.register(agent)

    assert registry.count() == 1
    assert registry.contains("test_agent")


def test_registered_agent_can_be_retrieved() -> None:
    registry = AgentRegistry()
    agent = TestRegistryAgent()

    registry.register(agent)

    retrieved = registry.get("test_agent")

    assert retrieved is agent


def test_multiple_agents_can_be_registered() -> None:
    registry = AgentRegistry()

    first = TestRegistryAgent("agent_one")
    second = TestRegistryAgent("agent_two")

    registry.register(first)
    registry.register(second)

    assert registry.count() == 2
    assert registry.get("agent_one") is first
    assert registry.get("agent_two") is second


def test_duplicate_agent_id_is_rejected() -> None:
    registry = AgentRegistry()

    first = TestRegistryAgent("duplicate")
    second = TestRegistryAgent("duplicate")

    registry.register(first)

    with pytest.raises(KeyError):
        registry.register(second)


# =============================================================================
# Validation Tests
# =============================================================================

def test_non_agent_registration_is_rejected() -> None:
    registry = AgentRegistry()

    with pytest.raises(TypeError):
        registry.register("not an agent")  # type: ignore[arg-type]


def test_empty_agent_id_is_rejected() -> None:
    registry = AgentRegistry()

    agent = TestRegistryAgent("   ")

    with pytest.raises(ValueError):
        registry.register(agent)


def test_unknown_agent_raises_key_error() -> None:
    registry = AgentRegistry()

    with pytest.raises(KeyError):
        registry.get("unknown_agent")


def test_empty_lookup_id_is_rejected() -> None:
    registry = AgentRegistry()

    with pytest.raises(ValueError):
        registry.get("   ")


# =============================================================================
# Membership Tests
# =============================================================================

def test_contains_returns_false_for_unknown_agent() -> None:
    registry = AgentRegistry()

    assert registry.contains("unknown_agent") is False


def test_contains_handles_whitespace() -> None:
    registry = AgentRegistry()
    agent = TestRegistryAgent("keyboard_agent")

    registry.register(agent)

    assert registry.contains(" keyboard_agent ") is True


# =============================================================================
# Unregistration Tests
# =============================================================================

def test_agent_can_be_unregistered() -> None:
    registry = AgentRegistry()
    agent = TestRegistryAgent()

    registry.register(agent)

    removed = registry.unregister("test_agent")

    assert removed is agent
    assert registry.count() == 0
    assert registry.contains("test_agent") is False


def test_unregister_unknown_agent_raises_key_error() -> None:
    registry = AgentRegistry()

    with pytest.raises(KeyError):
        registry.unregister("unknown_agent")


# =============================================================================
# Listing Tests
# =============================================================================

def test_list_agents_returns_registered_agents() -> None:
    registry = AgentRegistry()

    first = TestRegistryAgent("agent_one")
    second = TestRegistryAgent("agent_two")

    registry.register(first)
    registry.register(second)

    agents = registry.list_agents()

    assert agents == [first, second]


def test_empty_registry_returns_empty_list() -> None:
    registry = AgentRegistry()

    assert registry.list_agents() == []


# =============================================================================
# Clear Tests
# =============================================================================

def test_clear_registry() -> None:
    registry = AgentRegistry()

    registry.register(TestRegistryAgent("agent_one"))
    registry.register(TestRegistryAgent("agent_two"))

    registry.clear()

    assert registry.count() == 0
    assert registry.list_agents() == []


# =============================================================================
# Isolation Test
# =============================================================================

def test_each_registry_has_independent_storage() -> None:
    first_registry = AgentRegistry()
    second_registry = AgentRegistry()

    first_registry.register(TestRegistryAgent("agent_one"))

    assert first_registry.count() == 1
    assert second_registry.count() == 0

# =============================================================================
# Mouse Agent Registration Tests
# =============================================================================

def test_mouse_agent_can_be_registered() -> None:
    registry = AgentRegistry()
    agent = MouseAutomationAgent()

    registry.register(agent)

    assert registry.count() == 1
    assert registry.contains("mouse_agent")


def test_registered_mouse_agent_can_be_retrieved() -> None:
    registry = AgentRegistry()
    agent = MouseAutomationAgent()

    registry.register(agent)

    retrieved = registry.get("mouse_agent")

    assert retrieved is agent
    assert isinstance(retrieved, MouseAutomationAgent)

# =============================================================================
# M5-K Desktop Agent Registration + Mapping Tests
# =============================================================================

def test_desktop_agent_can_be_registered() -> None:
    registry = AgentRegistry()

    backend = FakeDesktopBackend()
    agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    registry.register(agent)

    assert registry.count() == 1
    assert registry.contains("desktop_agent")


def test_desktop_agent_can_be_resolved_through_tool_agent_mapper() -> None:
    registry = AgentRegistry()

    backend = FakeDesktopBackend()
    agent = ApplicationWindowAutomationAgent(
        backend=backend,
    )

    mapper = ToolAgentMapper(registry)

    mapper.register(
        ToolType.DESKTOP,
        agent,
    )

    resolved = mapper.resolve(
        ToolType.DESKTOP
    )

    assert resolved is agent
    assert resolved.agent_id == "desktop_agent"
    assert resolved.tool_type == ToolType.DESKTOP

def test_filesystem_agent_can_be_registered_and_retrieved():
    """
    AgentRegistry should register and retrieve the
    FileSystemAutomationAgent by its agent ID.
    """

    registry = AgentRegistry()

    backend = FakeFileSystemBackend()

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    registry.register(filesystem_agent)

    assert registry.contains("filesystem_agent") is True
    assert registry.count() == 1

    retrieved_agent = registry.get("filesystem_agent")

    assert retrieved_agent is filesystem_agent
    assert retrieved_agent.agent_id == "filesystem_agent"
    assert retrieved_agent.tool_type == ToolType.FILESYSTEM

def test_filesystem_mapper_registers_agent_in_agent_registry():
    """
    Registering a filesystem agent through ToolAgentMapper should
    also register that agent in AgentRegistry.
    """

    registry = AgentRegistry()

    mapper = ToolAgentMapper(registry)

    backend = FakeFileSystemBackend()

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    assert registry.contains("filesystem_agent") is False

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    assert registry.contains("filesystem_agent") is True
    assert registry.count() == 1

    registered_agent = registry.get("filesystem_agent")

    assert registered_agent is filesystem_agent

def test_filesystem_mapper_fails_when_no_mapping_exists():
    """
    ToolAgentMapper should reject filesystem resolution when
    no filesystem mapping has been registered.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    with pytest.raises(KeyError, match="No AutomationAgent mapped"):
        mapper.resolve(ToolType.FILESYSTEM)

def test_filesystem_mapping_removal_preserves_registered_agent():
    """
    Removing the filesystem ToolType mapping should not remove
    the filesystem agent from AgentRegistry.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    backend = FakeFileSystemBackend()

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    assert mapper.contains(ToolType.FILESYSTEM) is True
    assert registry.contains("filesystem_agent") is True

    mapper.unregister(ToolType.FILESYSTEM)

    assert mapper.contains(ToolType.FILESYSTEM) is False
    assert registry.contains("filesystem_agent") is True

    assert registry.get("filesystem_agent") is filesystem_agent

def test_filesystem_registry_mapper_resolution_flow():
    """
    Verify the complete filesystem registry and mapper resolution flow.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    backend = FakeFileSystemBackend()

    filesystem_agent = FileSystemAutomationAgent(
        backend=backend,
    )

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    agent_id = mapper.get_agent_id(
        ToolType.FILESYSTEM,
    )

    assert agent_id == "filesystem_agent"

    resolved_agent = mapper.resolve(
        ToolType.FILESYSTEM,
    )

    registered_agent = registry.get(
        "filesystem_agent",
    )

    assert resolved_agent is filesystem_agent
    assert resolved_agent is registered_agent
    assert resolved_agent.agent_id == agent_id