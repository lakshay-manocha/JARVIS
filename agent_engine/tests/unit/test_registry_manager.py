"""
===============================================================================
File Name   : test_registry_manager.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for RegistryManager.

This test suite verifies:
    • Registry retrieval
    • Available registries
    • Invalid registry handling
    • Registry facade functionality

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.utils.registry_manager import RegistryManager

from agent_engine.registry.action_registry import ActionRegistry
from agent_engine.registry.application_registry import ApplicationRegistry
from agent_engine.registry.browser_registry import BrowserRegistry
from agent_engine.registry.website_registry import WebsiteRegistry
from agent_engine.registry.filetype_registry import FileTypeRegistry
from agent_engine.registry.stopwords_registry import StopwordsRegistry
from agent_engine.registry.synonym_registry import SynonymRegistry


# =============================================================================
# Registry Retrieval
# =============================================================================

@pytest.mark.parametrize(
    "category, expected",
    [
        ("ACTION", ActionRegistry),
        ("APPLICATION", ApplicationRegistry),
        ("BROWSER", BrowserRegistry),
        ("WEBSITE", WebsiteRegistry),
        ("FILETYPE", FileTypeRegistry),
        ("STOPWORDS", StopwordsRegistry),
        ("SYNONYM", SynonymRegistry),
    ],
)
def test_get_registry(category, expected):
    assert RegistryManager.get_registry(category) is expected


# =============================================================================
# Case Insensitivity
# =============================================================================

@pytest.mark.parametrize(
    "category, expected",
    [
        ("action", ActionRegistry),
        ("Application", ApplicationRegistry),
        ("browser", BrowserRegistry),
        ("Website", WebsiteRegistry),
        ("filetype", FileTypeRegistry),
        ("StopWords", StopwordsRegistry),
        ("synonym", SynonymRegistry),
    ],
)
def test_get_registry_case_insensitive(category, expected):
    assert RegistryManager.get_registry(category) is expected


# =============================================================================
# Whitespace Handling
# =============================================================================

@pytest.mark.parametrize(
    "category, expected",
    [
        (" ACTION ", ActionRegistry),
        ("  browser", BrowserRegistry),
        ("website  ", WebsiteRegistry),
        (" filetype ", FileTypeRegistry),
    ],
)
def test_get_registry_with_whitespace(category, expected):
    assert RegistryManager.get_registry(category) is expected


# =============================================================================
# Invalid Registry
# =============================================================================

@pytest.mark.parametrize(
    "category",
    [
        "DATABASE",
        "MODEL",
        "UNKNOWN",
        "",
    ],
)
def test_invalid_registry(category):
    with pytest.raises(ValueError):
        RegistryManager.get_registry(category)


# =============================================================================
# Available Registries
# =============================================================================

def test_available_registries():

    registries = RegistryManager.available_registries()

    expected = [
        "ACTION",
        "APPLICATION",
        "BROWSER",
        "WEBSITE",
        "FILETYPE",
        "STOPWORDS",
        "SYNONYM",
    ]

    assert registries == expected


# =============================================================================
# Registry Facade
# =============================================================================

def test_action_registry_access():
    registry = RegistryManager.get_registry("ACTION")

    assert registry.normalize("launch") == "open"


def test_browser_registry_access():
    registry = RegistryManager.get_registry("BROWSER")

    assert registry.normalize("google chrome") == "chrome"


def test_application_registry_access():
    registry = RegistryManager.get_registry("APPLICATION")

    assert registry.normalize("vs code") == "vscode"


def test_website_registry_access():
    registry = RegistryManager.get_registry("WEBSITE")

    assert registry.normalize("github") == "github"


def test_filetype_registry_access():
    registry = RegistryManager.get_registry("FILETYPE")

    assert registry.normalize("docx") == "word"


def test_stopwords_registry_access():
    registry = RegistryManager.get_registry("STOPWORDS")

    assert registry.contains("please")


def test_synonym_registry_access():
    registry = RegistryManager.get_registry("SYNONYM")

    assert registry.normalize("photo") == "image"