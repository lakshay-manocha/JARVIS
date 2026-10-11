"""
===============================================================================
File Name   : test_browser_registry.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for BrowserRegistry.

This test suite verifies:
    • Browser normalization
    • Canonical browser names
    • Case insensitivity
    • Unknown browser handling
    • Registry lookup
    • Browser metadata
    • Registry immutability

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.registry.browser_registry import BrowserRegistry


# =============================================================================
# Fixture
# =============================================================================

@pytest.fixture
def registry():
    """Returns BrowserRegistry."""
    return BrowserRegistry()


# =============================================================================
# Normalization Tests
# =============================================================================

@pytest.mark.parametrize(
    "browser, expected",
    [
        ("chrome", "chrome"),
        ("google chrome", "chrome"),
        ("chrome browser", "chrome"),
        ("firefox", "firefox"),
        ("mozilla firefox", "firefox"),
        ("edge", "edge"),
        ("microsoft edge", "edge"),
        ("edge browser", "edge"),
        ("safari", "safari"),
        ("opera", "opera"),
        ("brave", "brave"),
    ],
)
def test_normalize_known_browsers(registry, browser, expected):
    assert registry.normalize(browser) == expected


# =============================================================================
# Case Insensitivity
# =============================================================================

@pytest.mark.parametrize(
    "browser, expected",
    [
        ("Chrome", "chrome"),
        ("GOOGLE CHROME", "chrome"),
        ("FireFox", "firefox"),
        ("MICROSOFT EDGE", "edge"),
        ("Safari", "safari"),
        ("Opera", "opera"),
        ("BRAVE", "brave"),
    ],
)
def test_case_insensitive_normalization(registry, browser, expected):
    assert registry.normalize(browser) == expected


# =============================================================================
# Whitespace Handling
# =============================================================================

@pytest.mark.parametrize(
    "browser, expected",
    [
        (" chrome ", "chrome"),
        ("  google chrome", "chrome"),
        ("firefox   ", "firefox"),
        ("   microsoft edge   ", "edge"),
    ],
)
def test_whitespace_normalization(registry, browser, expected):
    assert registry.normalize(browser) == expected


# =============================================================================
# Unknown Browsers
# =============================================================================

@pytest.mark.parametrize(
    "browser",
    [
        "arc",
        "vivaldi",
        "netscape",
        "unknown browser",
    ],
)
def test_unknown_browser_returns_original(registry, browser):
    assert registry.normalize(browser) == browser.lower()


# =============================================================================
# Contains Tests
# =============================================================================

@pytest.mark.parametrize(
    "browser",
    [
        "chrome",
        "google chrome",
        "firefox",
        "mozilla firefox",
        "edge",
        "microsoft edge",
        "safari",
        "opera",
        "brave",
    ],
)
def test_contains_known_browser(registry, browser):
    assert registry.contains(browser)


@pytest.mark.parametrize(
    "browser",
    [
        "arc",
        "vivaldi",
        "netscape",
    ],
)
def test_contains_unknown_browser(registry, browser):
    assert not registry.contains(browser)


# =============================================================================
# Metadata Tests
# =============================================================================

def test_metadata_chrome(registry):
    metadata = registry.get_metadata("chrome")

    assert metadata is not None
    assert metadata["canonical"] == "chrome"
    assert metadata["display_name"] == "Google Chrome"


def test_metadata_google_chrome(registry):
    metadata = registry.get_metadata("google chrome")

    assert metadata["canonical"] == "chrome"
    assert metadata["display_name"] == "Google Chrome"


def test_metadata_firefox(registry):
    metadata = registry.get_metadata("firefox")

    assert metadata["canonical"] == "firefox"
    assert metadata["display_name"] == "Mozilla Firefox"


def test_metadata_edge(registry):
    metadata = registry.get_metadata("edge")

    assert metadata["canonical"] == "edge"
    assert metadata["display_name"] == "Microsoft Edge"


def test_unknown_metadata(registry):
    assert registry.get_metadata("arc") is None


# =============================================================================
# Empty String
# =============================================================================

def test_empty_string(registry):
    assert registry.normalize("") == ""
    assert not registry.contains("")


# =============================================================================
# None Handling
# =============================================================================

def test_none_input(registry):
    with pytest.raises(Exception):
        registry.normalize(None)


# =============================================================================
# Registry Copy
# =============================================================================

def test_all_browsers_returns_copy(registry):
    before = registry.all_browsers()

    before["chrome"] = {
        "canonical": "modified",
        "display_name": "Modified"
    }

    assert registry.normalize("chrome") == "chrome"

    metadata = registry.get_metadata("chrome")

    assert metadata["display_name"] == "Google Chrome"


# =============================================================================
# Registry Consistency
# =============================================================================

def test_registry_is_not_modified(registry):
    before = registry.all_browsers()

    registry.normalize("chrome")
    registry.normalize("firefox")
    registry.normalize("edge")
    registry.normalize("opera")

    after = registry.all_browsers()

    assert before == after