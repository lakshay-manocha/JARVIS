"""
Tests for G.9 - ToolType -> AutomationAgent Mapping.
"""

import pytest

from agent_engine.automation.agents.base import AutomationAgent
from agent_engine.automation.models.capabilities import AgentCapabilities
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.automation.registry.agent_registry import AgentRegistry
from agent_engine.automation.registry.tool_agent_mapper import ToolAgentMapper
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ToolType
from agent_engine.automation.agents.mouse.mouse_agent import (
    MouseAutomationAgent,
)
from agent_engine.automation.agents.filesystem.filesystem_agent import (
    FileSystemAutomationAgent,
)
from agent_engine.automation.agents.filesystem.fake_filesystem_backend import (
    FakeFileSystemBackend,
)

class TestMapperAgent(AutomationAgent):
    """
    Lightweight AutomationAgent implementation used only for testing.
    """

    def __init__(
        self,
        agent_id: str,
        tool_type: ToolType,
    ) -> None:
        super().__init__()

        self._agent_id = agent_id
        self._tool_type = tool_type

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def name(self) -> str:
        return f"Test {self._tool_type.value}"

    @property
    def description(self) -> str:
        return "Test automation agent."

    @property
    def tool_type(self) -> ToolType:
        return self._tool_type

    @property
    def metadata(self) -> dict[str, object]:
        return {"test": True}

    @property
    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            actions=frozenset({"test_action"})
        )

    def initialize(self) -> None:
        pass

    def can_execute(
        self,
        action_request: ActionRequest,
    ) -> bool:
        return action_request.action == "test_action"

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


@pytest.fixture
def registry() -> AgentRegistry:
    return AgentRegistry()


@pytest.fixture
def mapper(registry: AgentRegistry) -> ToolAgentMapper:
    return ToolAgentMapper(registry)


def test_register_tool_agent(
    mapper: ToolAgentMapper,
) -> None:
    agent = TestMapperAgent(
        "browser_agent",
        ToolType.BROWSER,
    )

    mapper.register(ToolType.BROWSER, agent)

    assert mapper.contains(ToolType.BROWSER)


def test_resolve_returns_registered_agent(
    mapper: ToolAgentMapper,
) -> None:
    agent = TestMapperAgent(
        "browser_agent",
        ToolType.BROWSER,
    )

    mapper.register(ToolType.BROWSER, agent)

    resolved = mapper.resolve(ToolType.BROWSER)

    assert resolved is agent


def test_resolve_returns_correct_agent_for_multiple_tools(
    mapper: ToolAgentMapper,
) -> None:
    browser_agent = TestMapperAgent(
        "browser_agent",
        ToolType.BROWSER,
    )

    keyboard_agent = TestMapperAgent(
        "keyboard_agent",
        ToolType.KEYBOARD,
    )

    mapper.register(ToolType.BROWSER, browser_agent)
    mapper.register(ToolType.KEYBOARD, keyboard_agent)

    assert mapper.resolve(ToolType.BROWSER) is browser_agent
    assert mapper.resolve(ToolType.KEYBOARD) is keyboard_agent


def test_get_agent_id(
    mapper: ToolAgentMapper,
) -> None:
    agent = TestMapperAgent(
        "mouse_agent",
        ToolType.MOUSE,
    )

    mapper.register(ToolType.MOUSE, agent)

    assert mapper.get_agent_id(ToolType.MOUSE) == "mouse_agent"


def test_duplicate_tool_mapping_is_rejected(
    mapper: ToolAgentMapper,
) -> None:
    first_agent = TestMapperAgent(
        "browser_agent_1",
        ToolType.BROWSER,
    )

    second_agent = TestMapperAgent(
        "browser_agent_2",
        ToolType.BROWSER,
    )

    mapper.register(ToolType.BROWSER, first_agent)

    with pytest.raises(KeyError):
        mapper.register(ToolType.BROWSER, second_agent)


def test_tool_type_mismatch_is_rejected(
    mapper: ToolAgentMapper,
) -> None:
    agent = TestMapperAgent(
        "keyboard_agent",
        ToolType.KEYBOARD,
    )

    with pytest.raises(ValueError):
        mapper.register(ToolType.BROWSER, agent)


def test_non_tool_type_is_rejected(
    mapper: ToolAgentMapper,
) -> None:
    agent = TestMapperAgent(
        "browser_agent",
        ToolType.BROWSER,
    )

    with pytest.raises(TypeError):
        mapper.register("browser", agent)  # type: ignore[arg-type]


def test_non_agent_is_rejected(
    mapper: ToolAgentMapper,
) -> None:
    with pytest.raises(TypeError):
        mapper.register(
            ToolType.BROWSER,
            object(),  # type: ignore[arg-type]
        )


def test_unknown_tool_type_raises_key_error(
    mapper: ToolAgentMapper,
) -> None:
    with pytest.raises(KeyError):
        mapper.resolve(ToolType.BROWSER)


def test_contains_returns_false_for_unmapped_tool(
    mapper: ToolAgentMapper,
) -> None:
    assert mapper.contains(ToolType.SCREEN) is False


def test_list_mappings_returns_current_mappings(
    mapper: ToolAgentMapper,
) -> None:
    browser_agent = TestMapperAgent(
        "browser_agent",
        ToolType.BROWSER,
    )

    keyboard_agent = TestMapperAgent(
        "keyboard_agent",
        ToolType.KEYBOARD,
    )

    mapper.register(ToolType.BROWSER, browser_agent)
    mapper.register(ToolType.KEYBOARD, keyboard_agent)

    mappings = mapper.list_mappings()

    assert mappings == {
        ToolType.BROWSER: "browser_agent",
        ToolType.KEYBOARD: "keyboard_agent",
    }


def test_list_mappings_returns_copy(
    mapper: ToolAgentMapper,
) -> None:
    agent = TestMapperAgent(
        "browser_agent",
        ToolType.BROWSER,
    )

    mapper.register(ToolType.BROWSER, agent)

    mappings = mapper.list_mappings()
    mappings.clear()

    assert mapper.contains(ToolType.BROWSER)


def test_unregister_mapping(
    mapper: ToolAgentMapper,
) -> None:
    agent = TestMapperAgent(
        "browser_agent",
        ToolType.BROWSER,
    )

    mapper.register(ToolType.BROWSER, agent)

    mapper.unregister(ToolType.BROWSER)

    assert mapper.contains(ToolType.BROWSER) is False


def test_unregister_unknown_mapping_raises_key_error(
    mapper: ToolAgentMapper,
) -> None:
    with pytest.raises(KeyError):
        mapper.unregister(ToolType.BROWSER)


def test_clear_removes_all_mappings(
    mapper: ToolAgentMapper,
) -> None:
    browser_agent = TestMapperAgent(
        "browser_agent",
        ToolType.BROWSER,
    )

    keyboard_agent = TestMapperAgent(
        "keyboard_agent",
        ToolType.KEYBOARD,
    )

    mapper.register(ToolType.BROWSER, browser_agent)
    mapper.register(ToolType.KEYBOARD, keyboard_agent)

    mapper.clear()

    assert mapper.contains(ToolType.BROWSER) is False
    assert mapper.contains(ToolType.KEYBOARD) is False


def test_mapper_and_registry_share_same_agent_instance(
    registry: AgentRegistry,
) -> None:
    mapper = ToolAgentMapper(registry)

    agent = TestMapperAgent(
        "browser_agent",
        ToolType.BROWSER,
    )

    mapper.register(ToolType.BROWSER, agent)

    assert registry.get("browser_agent") is agent
    assert mapper.resolve(ToolType.BROWSER) is registry.get("browser_agent")

# =============================================================================
# Mouse Agent Integration
# =============================================================================


def test_mouse_agent_can_be_mapped() -> None:
    """
    MouseAutomationAgent must be registerable through ToolAgentMapper.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    mouse_agent = MouseAutomationAgent()

    mapper.register(
        ToolType.MOUSE,
        mouse_agent,
    )

    assert mapper.contains(
        ToolType.MOUSE,
    )

    assert registry.contains(
        "mouse_agent",
    )

def test_mouse_tool_resolves_to_mouse_agent() -> None:
    """
    ToolType.MOUSE must resolve to the registered MouseAutomationAgent.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    mouse_agent = MouseAutomationAgent()

    mapper.register(
        ToolType.MOUSE,
        mouse_agent,
    )

    resolved = mapper.resolve(
        ToolType.MOUSE,
    )

    assert resolved is mouse_agent

    assert resolved.tool_type == ToolType.MOUSE

    assert resolved.agent_id == "mouse_agent"

def test_mouse_mapper_and_registry_share_same_agent() -> None:
    """
    ToolAgentMapper and AgentRegistry must reference the same
    MouseAutomationAgent instance.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    mouse_agent = MouseAutomationAgent()

    mapper.register(
        ToolType.MOUSE,
        mouse_agent,
    )

    registered = registry.get(
        "mouse_agent",
    )

    resolved = mapper.resolve(
        ToolType.MOUSE,
    )

    assert registered is mouse_agent
    assert resolved is mouse_agent
    assert resolved is registered

# =============================================================================
# File-System Agent Integration
# =============================================================================


def test_filesystem_agent_can_be_mapped() -> None:
    """
    FileSystemAutomationAgent must be registerable through
    ToolAgentMapper.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    filesystem_agent = FileSystemAutomationAgent(
        backend=FakeFileSystemBackend(),
    )

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    assert mapper.contains(
        ToolType.FILESYSTEM,
    )

    assert registry.contains(
        "filesystem_agent",
    )


def test_filesystem_tool_resolves_to_filesystem_agent() -> None:
    """
    ToolType.FILESYSTEM must resolve to the registered
    FileSystemAutomationAgent.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    filesystem_agent = FileSystemAutomationAgent(
        backend=FakeFileSystemBackend(),
    )

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    resolved = mapper.resolve(
        ToolType.FILESYSTEM,
    )

    assert resolved is filesystem_agent

    assert resolved.tool_type == ToolType.FILESYSTEM

    assert resolved.agent_id == "filesystem_agent"


def test_filesystem_mapper_and_registry_share_same_agent() -> None:
    """
    ToolAgentMapper and AgentRegistry must reference the same
    FileSystemAutomationAgent instance.
    """

    registry = AgentRegistry()
    mapper = ToolAgentMapper(registry)

    filesystem_agent = FileSystemAutomationAgent(
        backend=FakeFileSystemBackend(),
    )

    mapper.register(
        ToolType.FILESYSTEM,
        filesystem_agent,
    )

    registered = registry.get(
        "filesystem_agent",
    )

    resolved = mapper.resolve(
        ToolType.FILESYSTEM,
    )

    assert registered is filesystem_agent
    assert resolved is filesystem_agent
    assert resolved is registered