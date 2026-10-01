from agent_engine.automation.agents.keyboard import (
    KeyboardAutomationAgent,
)
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import (
    ActionCategory,
    ToolType,
)


class FakeKeyboardActions:

    def __init__(self):
        self.calls = []

    def type_text(self, text):
        self.calls.append(("type_text", text))

    def press_key(self, key):
        self.calls.append(("press_key", key))

    def hotkey(self, keys):
        self.calls.append(("hotkey", keys))

    def key_down(self, key):
        self.calls.append(("key_down", key))

    def key_up(self, key):
        self.calls.append(("key_up", key))

    def release_all(self):
        self.calls.append(("release_all",))


def make_request(action, parameters):
    return ActionRequest(
        task_id=1,
        action=action,
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters=parameters,
    )


def test_keyboard_agent_identity():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    assert agent.agent_id == "keyboard_agent"
    assert agent.tool_type == ToolType.KEYBOARD
    assert agent.name == "Keyboard Automation Agent"


def test_keyboard_agent_capabilities():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    assert agent.supports("type_text")
    assert agent.supports("press_key")
    assert agent.supports("hotkey")
    assert agent.supports("key_down")
    assert agent.supports("key_up")

    assert not agent.supports("click")


def test_can_execute_keyboard_action():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    request = make_request(
        "type_text",
        {"text": "test"},
    )

    assert agent.can_execute(request)


def test_can_execute_rejects_mouse_action():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    request = ActionRequest(
        task_id=1,
        action="click",
        category=ActionCategory.MOUSE,
        tool=ToolType.MOUSE,
        parameters={},
    )

    assert not agent.can_execute(request)


def test_type_text_execution():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    request = make_request(
        "type_text",
        {"text": "Hello"},
    )

    result = agent.execute(request)

    assert isinstance(
        result,
        AutomationExecutionResult,
    )

    assert result.success is True
    assert result.task_id == 1
    assert result.action == "type_text"

    assert actions.calls == [
        ("type_text", "Hello")
    ]


def test_press_key_execution():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    request = make_request(
        "press_key",
        {"key": "enter"},
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        ("press_key", "enter")
    ]


def test_hotkey_execution():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    request = make_request(
        "hotkey",
        {
            "keys": [
                "ctrl",
                "c",
            ]
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "hotkey",
            [
                "ctrl",
                "c",
            ],
        )
    ]


def test_key_down_execution():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    request = make_request(
        "key_down",
        {"key": "shift"},
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        ("key_down", "shift")
    ]


def test_key_up_execution():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    request = make_request(
        "key_up",
        {"key": "shift"},
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        ("key_up", "shift")
    ]


def test_missing_parameter_returns_failure():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    request = make_request(
        "type_text",
        {},
    )

    result = agent.execute(request)

    assert result.success is False
    assert "text" in result.error.lower()


def test_cleanup_releases_modifiers():
    actions = FakeKeyboardActions()
    agent = KeyboardAutomationAgent(
        actions=actions
    )

    agent.initialize()
    agent.cleanup()

    assert (
        "release_all",
    ) in actions.calls