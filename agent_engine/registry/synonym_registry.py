"""
===============================================================================
File Name   : synonym_registry.py
Module      : Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Maintains general-purpose language synonyms used during task normalization.

This registry standardizes common words and phrases without changing the
meaning or intent of the task.

Author : Team JARVIS
===============================================================================
"""

from typing import Dict


class SynonymRegistry:
    """
    Registry responsible for general synonym normalization.
    """

    CATEGORY = "SYNONYM"

    _SYNONYM_MAP: Dict[str, str] = {

        # ------------------------------------------------------------------
        # Files & Documents
        # ------------------------------------------------------------------

        "doc": "document",
        "docs": "documents",
        "file": "document",

        # ------------------------------------------------------------------
        # Images
        # ------------------------------------------------------------------

        "pic": "image",
        "pics": "images",
        "photo": "image",
        "photos": "images",
        "picture": "image",
        "pictures": "images",

        # ------------------------------------------------------------------
        # Folder
        # ------------------------------------------------------------------

        "folder": "directory",
        "folders": "directories",

        # ------------------------------------------------------------------
        # Website
        # ------------------------------------------------------------------

        "webpage": "website",
        "webpages": "websites",
        "site": "website",

        # ------------------------------------------------------------------
        # Authentication
        # ------------------------------------------------------------------

        "login": "sign in",
        "log in": "sign in",
        "logout": "sign out",
        "log out": "sign out",

        # ------------------------------------------------------------------
        # Download
        # ------------------------------------------------------------------

        "save as": "download",

        # ------------------------------------------------------------------
        # Browser Tabs
        # ------------------------------------------------------------------

        "tab": "browser tab",
        "tabs": "browser tabs",

        # ------------------------------------------------------------------
        # Windows
        # ------------------------------------------------------------------

        "window": "application window",
        "windows": "application windows"
    }

    @classmethod
    def normalize(cls, word: str) -> str:
        """
        Returns the canonical synonym.
        """

        return cls._SYNONYM_MAP.get(
            word.lower().strip(),
            word.lower().strip()
        )

    @classmethod
    def contains(cls, word: str) -> bool:
        """
        Checks whether a synonym exists.
        """

        return word.lower().strip() in cls._SYNONYM_MAP

    @classmethod
    def all_synonyms(cls) -> Dict[str, str]:
        """
        Returns the complete synonym registry.
        """

        return cls._SYNONYM_MAP.copy()