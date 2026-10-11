"""
===============================================================================
File Name   : registry_manager.py
Module      : Utilities
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Acts as the single access point for all knowledge registries used by the
Agent Brain.

This manager follows the Facade Pattern, exposing all registries through a
single interface to reduce coupling between modules.

Author : Team JARVIS
===============================================================================
"""

from agent_engine.registry.action_registry import ActionRegistry
from agent_engine.registry.application_registry import ApplicationRegistry
from agent_engine.registry.browser_registry import BrowserRegistry
from agent_engine.registry.filetype_registry import FileTypeRegistry
from agent_engine.registry.stopwords_registry import StopwordsRegistry
from agent_engine.registry.synonym_registry import SynonymRegistry
from agent_engine.registry.website_registry import WebsiteRegistry


class RegistryManager:
    """
    Central registry manager.

    Provides unified access to all knowledge registries used by the
    Agent Brain.
    """

    actions = ActionRegistry
    browsers = BrowserRegistry
    applications = ApplicationRegistry
    websites = WebsiteRegistry
    filetypes = FileTypeRegistry
    stopwords = StopwordsRegistry
    synonyms = SynonymRegistry

    @classmethod
    def get_registry(cls, category: str):
        """
        Returns a registry based on its category.

        Parameters
        ----------
        category : str
            Registry category.

        Returns
        -------
        Registry class

        Raises
        ------
        ValueError
            If the registry category is not supported.
        """

        registry_map = {
            "ACTION": cls.actions,
            "APPLICATION": cls.applications,
            "BROWSER": cls.browsers,
            "WEBSITE": cls.websites,
            "FILETYPE": cls.filetypes,
            "STOPWORDS": cls.stopwords,
            "SYNONYM": cls.synonyms,
        }

        category = category.strip().upper()

        if category not in registry_map:
            raise ValueError(f"Unsupported registry category: {category}")

        return registry_map[category]

    @classmethod
    def available_registries(cls) -> list[str]:
        """
        Returns the list of supported registries.
        """

        return [
            "ACTION",
            "APPLICATION",
            "BROWSER",
            "WEBSITE",
            "FILETYPE",
            "STOPWORDS",
            "SYNONYM",
        ]