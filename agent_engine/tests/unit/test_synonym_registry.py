"""
===============================================================================
File Name   : test_synonym_registry.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for SynonymRegistry.

This test suite verifies:
    • Synonym normalization
    • Case insensitivity
    • Whitespace handling
    • Unknown words
    • Registry lookup
    • Registry immutability

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.registry.synonym_registry import SynonymRegistry


# =============================================================================
# Fixture
# =============================================================================

@pytest.fixture
def registry():
    """Returns SynonymRegistry."""
    return SynonymRegistry()


# =============================================================================
# Normalization Tests
# =============================================================================

@pytest.mark.parametrize(
    "word, expected",
    [
        ("doc", "document"),
        ("docs", "documents"),
        ("file", "document"),
        ("pic", "image"),
        ("pics", "images"),
        ("photo", "image"),
        ("photos", "images"),
        ("picture", "image"),
        ("pictures", "images"),
        ("folder", "directory"),
        ("folders", "directories"),
        ("webpage", "website"),
        ("webpages", "websites"),
        ("site", "website"),
        ("login", "sign in"),
        ("log in", "sign in"),
        ("logout", "sign out"),
        ("log out", "sign out"),
        ("save as", "download"),
        ("tab", "browser tab"),
        ("tabs", "browser tabs"),
        ("window", "application window"),
        ("windows", "application windows"),
    ],
)
def test_normalize_known_synonyms(registry, word, expected):
    assert registry.normalize(word) == expected


# =============================================================================
# Case Insensitivity
# =============================================================================

@pytest.mark.parametrize(
    "word, expected",
    [
        ("DOC", "document"),
        ("Photo", "image"),
        ("FOLDER", "directory"),
        ("WebPage", "website"),
        ("LOGIN", "sign in"),
        ("SAVE AS", "download"),
        ("WINDOW", "application window"),
    ],
)
def test_case_insensitive_normalization(registry, word, expected):
    assert registry.normalize(word) == expected


# =============================================================================
# Whitespace Handling
# =============================================================================

@pytest.mark.parametrize(
    "word, expected",
    [
        (" doc ", "document"),
        ("  photo", "image"),
        ("folder   ", "directory"),
        ("  login  ", "sign in"),
    ],
)
def test_whitespace_normalization(registry, word, expected):
    assert registry.normalize(word) == expected


# =============================================================================
# Unknown Words
# =============================================================================

@pytest.mark.parametrize(
    "word",
    [
        "banana",
        "python",
        "chrome",
        "github",
        "spreadsheet",
    ],
)
def test_unknown_words_return_original(registry, word):
    assert registry.normalize(word) == word.lower()


# =============================================================================
# Contains Tests
# =============================================================================

@pytest.mark.parametrize(
    "word",
    [
        "doc",
        "docs",
        "file",
        "pic",
        "photo",
        "folder",
        "site",
        "login",
        "logout",
        "save as",
        "tab",
        "window",
    ],
)
def test_contains_known_synonyms(registry, word):
    assert registry.contains(word)


@pytest.mark.parametrize(
    "word",
    [
        "banana",
        "python",
        "chrome",
        "github",
    ],
)
def test_contains_unknown_synonyms(registry, word):
    assert not registry.contains(word)


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

def test_all_synonyms_returns_copy(registry):
    synonyms = registry.all_synonyms()

    synonyms["doc"] = "modified"

    assert registry.normalize("doc") == "document"


# =============================================================================
# Registry Consistency
# =============================================================================

def test_registry_is_not_modified(registry):
    before = registry.all_synonyms()

    registry.normalize("doc")
    registry.normalize("photo")
    registry.normalize("folder")
    registry.contains("login")

    after = registry.all_synonyms()

    assert before == after