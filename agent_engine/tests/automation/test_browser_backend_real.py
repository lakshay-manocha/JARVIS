"""
===============================================================================
File Name   : test_browser_backend_real.py
Module      : Automation Tests - Browser Backend
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Real integration tests for the Playwright-backed BrowserBackend.

Unlike the BrowserAutomationAgent integration tests, these tests use the
actual Playwright browser and therefore validate the real browser execution
layer.

These tests require:
    - Playwright Python package
    - Chromium browser installation

The tests use example.com as a deterministic external test target.
===============================================================================
"""

from __future__ import annotations

import pytest

from agent_engine.automation.agents.browser.browser_backend import (
    BrowserBackend,
)
from agent_engine.automation.agents.browser.browser_config import (
    BrowserConfig,
)
from agent_engine.automation.exceptions import (
    AgentExecutionError,
    AutomationValidationError,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def backend() -> BrowserBackend:
    """
    Create a real Playwright BrowserBackend configured for headless execution.
    """

    config = BrowserConfig(
        browser="chromium",
        headless=True,
    )

    backend = BrowserBackend(config)

    try:
        backend.initialize()
    except Exception as exc:
        pytest.fail(
            f"Real Playwright browser could not be initialized: {exc}"
        )

    yield backend

    backend.cleanup()


# =============================================================================
# Initialization
# =============================================================================


def test_real_browser_backend_initializes(
    backend: BrowserBackend,
) -> None:
    """
    BrowserBackend must initialize a real Playwright browser and page.
    """

    assert backend.initialized is True
    assert backend.page is not None


# =============================================================================
# Open URL
# =============================================================================


def test_real_browser_backend_opens_url(
    backend: BrowserBackend,
) -> None:
    """
    BrowserBackend must navigate to a real URL.
    """

    result = backend.execute(
        "open_url",
        {
            "url": "https://example.com",
        },
    )

    assert result["url"] == "https://example.com/"
    assert result["status"] == 200
    assert result["title"] == "Example Domain"


# =============================================================================
# Current URL
# =============================================================================


def test_real_browser_backend_returns_current_url(
    backend: BrowserBackend,
) -> None:
    """
    get_current_url must return the actual browser URL.
    """

    backend.execute(
        "open_url",
        {
            "url": "https://example.com",
        },
    )

    result = backend.execute(
        "get_current_url",
    )

    assert result == "https://example.com/"


# =============================================================================
# Page Title
# =============================================================================


def test_real_browser_backend_returns_page_title(
    backend: BrowserBackend,
) -> None:
    """
    get_page_title must return the actual page title.
    """

    backend.execute(
        "open_url",
        {
            "url": "https://example.com",
        },
    )

    result = backend.execute(
        "get_page_title",
    )

    assert result == "Example Domain"


# =============================================================================
# Text Extraction
# =============================================================================


def test_real_browser_backend_extracts_page_text(
    backend: BrowserBackend,
) -> None:
    """
    get_text must extract text from the loaded page body.
    """

    backend.execute(
        "open_url",
        {
            "url": "https://example.com",
        },
    )

    result = backend.execute(
        "get_text",
    )

    assert isinstance(result, str)
    assert "Example Domain" in result
    assert "documentation examples" in result

# =============================================================================
# Selector-Based Text Extraction
# =============================================================================


def test_real_browser_backend_extracts_text_by_selector(
    backend: BrowserBackend,
) -> None:
    """
    get_text must support selector-based extraction.
    """

    backend.execute(
        "open_url",
        {
            "url": "https://example.com",
        },
    )

    result = backend.execute(
        "get_text",
        {
            "selector": "h1",
        },
    )

    assert result.strip() == "Example Domain"


# =============================================================================
# Search
# =============================================================================


def test_real_browser_backend_search(
    backend: BrowserBackend,
) -> None:
    """
    Search action must construct and navigate to the configured search URL.
    """

    try:
        result = backend.execute(
            "search",
            {
                "query": "JARVIS AI",
            },
        )
    except AgentExecutionError as exc:
        pytest.skip(
            f"External search engine unavailable in current environment: {exc}"
        )

    assert result["query"] == "JARVIS AI"
    assert result["url"]
    assert result["title"]


# =============================================================================
# Invalid Parameters
# =============================================================================


def test_real_browser_backend_rejects_missing_url(
    backend: BrowserBackend,
) -> None:
    """
    open_url must reject a missing URL.
    """

    with pytest.raises(AutomationValidationError):
        backend.execute(
            "open_url",
            {},
        )


def test_real_browser_backend_rejects_invalid_timeout(
    backend: BrowserBackend,
) -> None:
    """
    BrowserBackend must reject non-positive execution timeouts.
    """

    with pytest.raises(AutomationValidationError):
        backend.execute(
            "get_page_title",
            timeout_seconds=0,
        )


# =============================================================================
# Unsupported Action
# =============================================================================


def test_real_browser_backend_rejects_unsupported_action(
    backend: BrowserBackend,
) -> None:
    """
    Unsupported browser actions must be rejected.
    """

    with pytest.raises(AutomationValidationError):
        backend.execute(
            "delete_file",
        )


# =============================================================================
# Cleanup
# =============================================================================


def test_real_browser_backend_cleanup(
    backend: BrowserBackend,
) -> None:
    """
    BrowserBackend cleanup must release browser resources.
    """

    assert backend.initialized is True

    backend.cleanup()

    assert backend.initialized is False
    assert backend.page is None