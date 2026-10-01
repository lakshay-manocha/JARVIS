from __future__ import annotations

from typing import Any

import pytest

from agent_engine.automation.agents.browser.browser_backend import BrowserBackend
from agent_engine.automation.agents.browser.browser_config import BrowserConfig
from agent_engine.automation.exceptions import AutomationValidationError


def test_browser_config_defaults() -> None:
    config = BrowserConfig()

    assert config.browser == "chromium"
    assert config.headless is False
    assert config.default_timeout_ms == 30_000


def test_browser_config_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError):
        BrowserConfig(default_timeout_ms=0)


def test_browser_backend_rejects_unknown_action_without_browser() -> None:
    backend = BrowserBackend()

    with pytest.raises(Exception):
        backend.execute("open_url", {"url": "https://example.com"})


def test_backend_parameter_validation() -> None:
    class PageStub:
        def set_default_timeout(self, value: int) -> None:
            pass

    backend = BrowserBackend()
    backend._page = PageStub()

    with pytest.raises(AutomationValidationError):
        backend.execute("open_url", {})


def test_backend_unsupported_action() -> None:
    class PageStub:
        def set_default_timeout(self, value: int) -> None:
            pass

    backend = BrowserBackend()
    backend._page = PageStub()

    with pytest.raises(AutomationValidationError):
        backend.execute("not_supported", {})
