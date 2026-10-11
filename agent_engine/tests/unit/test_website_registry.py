"""
===============================================================================
File Name   : test_website_registry.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for WebsiteRegistry.

This test suite verifies:
    • Website normalization
    • Canonical website names
    • Case insensitivity
    • Unknown website handling
    • Registry lookup
    • Website metadata
    • URL retrieval
    • Registry immutability

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.registry.website_registry import WebsiteRegistry


# =============================================================================
# Fixture
# =============================================================================

@pytest.fixture
def registry():
    """Returns WebsiteRegistry."""
    return WebsiteRegistry()


# =============================================================================
# Normalization Tests
# =============================================================================

@pytest.mark.parametrize(
    "website, expected",
    [
        ("google", "google"),
        ("youtube", "youtube"),
        ("github", "github"),
        ("chatgpt", "chatgpt"),
        ("openai chat", "chatgpt"),
        ("gmail", "gmail"),
        ("linkedin", "linkedin"),
        ("stackoverflow", "stackoverflow"),
        ("stack overflow", "stackoverflow"),
    ],
)
def test_normalize_known_websites(registry, website, expected):
    assert registry.normalize(website) == expected


# =============================================================================
# Case Insensitivity
# =============================================================================

@pytest.mark.parametrize(
    "website, expected",
    [
        ("Google", "google"),
        ("YOUTUBE", "youtube"),
        ("GitHub", "github"),
        ("CHATGPT", "chatgpt"),
        ("OpenAI Chat", "chatgpt"),
        ("Gmail", "gmail"),
        ("LINKEDIN", "linkedin"),
        ("Stack Overflow", "stackoverflow"),
    ],
)
def test_case_insensitive_normalization(registry, website, expected):
    assert registry.normalize(website) == expected


# =============================================================================
# Whitespace Handling
# =============================================================================

@pytest.mark.parametrize(
    "website, expected",
    [
        (" google ", "google"),
        ("  youtube", "youtube"),
        ("github   ", "github"),
        ("  stack overflow  ", "stackoverflow"),
    ],
)
def test_whitespace_normalization(registry, website, expected):
    assert registry.normalize(website) == expected


# =============================================================================
# Unknown Websites
# =============================================================================

@pytest.mark.parametrize(
    "website",
    [
        "facebook",
        "instagram",
        "reddit",
        "amazon",
    ],
)
def test_unknown_website_returns_original(registry, website):
    assert registry.normalize(website) == website.lower()


# =============================================================================
# Contains Tests
# =============================================================================

@pytest.mark.parametrize(
    "website",
    [
        "google",
        "youtube",
        "github",
        "chatgpt",
        "openai chat",
        "gmail",
        "linkedin",
        "stackoverflow",
        "stack overflow",
    ],
)
def test_contains_known_website(registry, website):
    assert registry.contains(website)


@pytest.mark.parametrize(
    "website",
    [
        "facebook",
        "reddit",
        "amazon",
    ],
)
def test_contains_unknown_website(registry, website):
    assert not registry.contains(website)


# =============================================================================
# Metadata Tests
# =============================================================================

def test_metadata_google(registry):
    metadata = registry.get_metadata("google")

    assert metadata["canonical"] == "google"
    assert metadata["display_name"] == "Google"
    assert metadata["requires_login"] is False


def test_metadata_chatgpt(registry):
    metadata = registry.get_metadata("chatgpt")

    assert metadata["canonical"] == "chatgpt"
    assert metadata["display_name"] == "ChatGPT"
    assert metadata["requires_login"] is True


def test_metadata_stackoverflow(registry):
    metadata = registry.get_metadata("stack overflow")

    assert metadata["canonical"] == "stackoverflow"
    assert metadata["display_name"] == "Stack Overflow"
    assert metadata["requires_login"] is False


def test_unknown_metadata(registry):
    assert registry.get_metadata("facebook") is None


# =============================================================================
# URL Tests
# =============================================================================

def test_google_url(registry):
    assert registry.get_url("google") == "https://www.google.com"


def test_youtube_url(registry):
    assert registry.get_url("youtube") == "https://www.youtube.com"


def test_github_url(registry):
    assert registry.get_url("github") == "https://github.com"


def test_chatgpt_url(registry):
    assert registry.get_url("chatgpt") == "https://chat.openai.com"


def test_stackoverflow_url(registry):
    assert registry.get_url("stack overflow") == "https://stackoverflow.com"


def test_unknown_url(registry):
    assert registry.get_url("facebook") is None


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

def test_all_websites_returns_copy(registry):
    websites = registry.all_websites()

    websites["google"] = {
        "canonical": "modified",
        "display_name": "Modified",
        "url": "https://example.com",
        "requires_login": True,
    }

    metadata = registry.get_metadata("google")

    assert metadata["canonical"] == "google"
    assert metadata["display_name"] == "Google"
    assert metadata["url"] == "https://www.google.com"


# =============================================================================
# Registry Consistency
# =============================================================================

def test_registry_is_not_modified(registry):
    before = registry.all_websites()

    registry.normalize("google")
    registry.normalize("github")
    registry.normalize("chatgpt")
    registry.get_metadata("youtube")
    registry.get_url("linkedin")

    after = registry.all_websites()

    assert before == after