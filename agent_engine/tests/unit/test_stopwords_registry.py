"""
===============================================================================
File Name   : test_stopwords_registry.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for StopwordsRegistry.

This test suite verifies:
    • Stopword lookup
    • Stopword removal
    • Case insensitivity
    • Whitespace handling
    • Unknown words
    • Empty input
    • Registry immutability

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.registry.stopwords_registry import StopwordsRegistry


# =============================================================================
# Fixture
# =============================================================================

@pytest.fixture
def registry():
    """Returns StopwordsRegistry."""
    return StopwordsRegistry()


# =============================================================================
# Contains Tests
# =============================================================================

@pytest.mark.parametrize(
    "word",
    [
        "please",
        "kindly",
        "just",
        "simply",
        "only",
        "a",
        "an",
        "the",
        "latest",
        "available",
        "current",
        "new",
        "can",
        "could",
        "would",
        "me",
        "my",
    ],
)
def test_contains_known_stopwords(registry, word):
    assert registry.contains(word)


@pytest.mark.parametrize(
    "word",
    [
        "chrome",
        "download",
        "github",
        "pdf",
        "excel",
        "summarize",
    ],
)
def test_contains_unknown_words(registry, word):
    assert not registry.contains(word)


# =============================================================================
# Case Insensitivity
# =============================================================================

@pytest.mark.parametrize(
    "word",
    [
        "PLEASE",
        "Kindly",
        "JUST",
        "Latest",
        "CURRENT",
        "Would",
        "MY",
    ],
)
def test_case_insensitive_lookup(registry, word):
    assert registry.contains(word)


# =============================================================================
# Whitespace Handling
# =============================================================================

@pytest.mark.parametrize(
    "word",
    [
        " please ",
        "  kindly",
        "latest   ",
        "  current  ",
    ],
)
def test_whitespace_lookup(registry, word):
    assert registry.contains(word)


# =============================================================================
# Remove Stopwords
# =============================================================================

def test_remove_stopwords(registry):
    words = [
        "please",
        "download",
        "the",
        "latest",
        "pdf",
    ]

    expected = [
        "download",
        "pdf",
    ]

    assert registry.remove(words) == expected


def test_remove_no_stopwords(registry):
    words = [
        "download",
        "chrome",
        "github",
    ]

    assert registry.remove(words) == words


def test_remove_all_stopwords(registry):
    words = [
        "please",
        "the",
        "latest",
        "can",
        "me",
    ]

    assert registry.remove(words) == []


def test_remove_preserves_order(registry):
    words = [
        "download",
        "please",
        "github",
        "latest",
        "pdf",
    ]

    expected = [
        "download",
        "github",
        "pdf",
    ]

    assert registry.remove(words) == expected


# =============================================================================
# Empty Input
# =============================================================================

def test_remove_empty_list(registry):
    assert registry.remove([]) == []


def test_empty_string(registry):
    assert not registry.contains("")


# =============================================================================
# None Handling
# =============================================================================

def test_none_input_contains(registry):
    with pytest.raises(Exception):
        registry.contains(None)


def test_none_input_remove(registry):
    with pytest.raises(Exception):
        registry.remove(None)


# =============================================================================
# Registry Copy
# =============================================================================

def test_all_stopwords_returns_copy(registry):
    stopwords = registry.all_stopwords()

    stopwords.add("temporary")

    assert not registry.contains("temporary")


# =============================================================================
# Registry Consistency
# =============================================================================

def test_registry_is_not_modified(registry):
    before = registry.all_stopwords()

    registry.contains("please")
    registry.contains("latest")
    registry.remove(["please", "download", "pdf"])

    after = registry.all_stopwords()

    assert before == after