"""
===============================================================================
File Name   : application_registry.py
Module      : Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Maintains the canonical application registry used throughout the Agent Brain.

This registry normalizes application aliases into a single canonical
application name and stores metadata required by the automation engine.

Author : Team JARVIS
===============================================================================
"""

from typing import Dict, Optional


class ApplicationRegistry:
    """
    Registry responsible for desktop application normalization.
    """

    CATEGORY = "APPLICATION"

    _APPLICATION_MAP: Dict[str, Dict[str, str]] = {

        # ------------------------------------------------------------------
        # Visual Studio Code
        # ------------------------------------------------------------------

        "visual studio code": {
            "canonical": "vscode",
            "display_name": "Visual Studio Code"
        },

        "vs code": {
            "canonical": "vscode",
            "display_name": "Visual Studio Code"
        },

        "vscode": {
            "canonical": "vscode",
            "display_name": "Visual Studio Code"
        },

        # ------------------------------------------------------------------
        # Microsoft Word
        # ------------------------------------------------------------------

        "microsoft word": {
            "canonical": "word",
            "display_name": "Microsoft Word"
        },

        "ms word": {
            "canonical": "word",
            "display_name": "Microsoft Word"
        },

        "word": {
            "canonical": "word",
            "display_name": "Microsoft Word"
        },

        # ------------------------------------------------------------------
        # Microsoft Excel
        # ------------------------------------------------------------------

        "microsoft excel": {
            "canonical": "excel",
            "display_name": "Microsoft Excel"
        },

        "excel": {
            "canonical": "excel",
            "display_name": "Microsoft Excel"
        },

        # ------------------------------------------------------------------
        # Microsoft PowerPoint
        # ------------------------------------------------------------------

        "microsoft powerpoint": {
            "canonical": "powerpoint",
            "display_name": "Microsoft PowerPoint"
        },

        "powerpoint": {
            "canonical": "powerpoint",
            "display_name": "Microsoft PowerPoint"
        },

        # ------------------------------------------------------------------
        # Notepad
        # ------------------------------------------------------------------

        "notepad": {
            "canonical": "notepad",
            "display_name": "Notepad"
        },

        # ------------------------------------------------------------------
        # Calculator
        # ------------------------------------------------------------------

        "calculator": {
            "canonical": "calculator",
            "display_name": "Calculator"
        },

        "calc": {
            "canonical": "calculator",
            "display_name": "Calculator"
        },

        # ------------------------------------------------------------------
        # Paint
        # ------------------------------------------------------------------

        "paint": {
            "canonical": "paint",
            "display_name": "Paint"
        },

        "mspaint": {
            "canonical": "paint",
            "display_name": "Paint"
        },

        # ------------------------------------------------------------------
        # File Explorer
        # ------------------------------------------------------------------

        "file explorer": {
            "canonical": "explorer",
            "display_name": "File Explorer"
        },

        "windows explorer": {
            "canonical": "explorer",
            "display_name": "File Explorer"
        },

        "explorer": {
            "canonical": "explorer",
            "display_name": "File Explorer"
        },

        # ------------------------------------------------------------------
        # Command Prompt
        # ------------------------------------------------------------------

        "command prompt": {
            "canonical": "cmd",
            "display_name": "Command Prompt"
        },

        "cmd": {
            "canonical": "cmd",
            "display_name": "Command Prompt"
        },

        # ------------------------------------------------------------------
        # PowerShell
        # ------------------------------------------------------------------

        "powershell": {
            "canonical": "powershell",
            "display_name": "Windows PowerShell"
        }
    }

    @classmethod
    def normalize(cls, application_name: str) -> str:
        """
        Returns the canonical application name.
        """

        application_name = application_name.lower().strip()

        if application_name in cls._APPLICATION_MAP:
            return cls._APPLICATION_MAP[application_name]["canonical"]

        return application_name

    @classmethod
    def contains(cls, application_name: str) -> bool:
        """
        Checks whether an application exists in the registry.
        """

        return application_name.lower().strip() in cls._APPLICATION_MAP

    @classmethod
    def get_metadata(cls, application_name: str) -> Optional[Dict[str, str]]:
        """
        Returns metadata associated with an application.
        """

        return cls._APPLICATION_MAP.get(application_name.lower().strip())

    @classmethod
    def all_applications(cls) -> Dict[str, Dict[str, str]]:
        """
        Returns the complete application registry.
        """

        return cls._APPLICATION_MAP.copy()