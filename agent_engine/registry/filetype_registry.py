"""
===============================================================================
File Name   : filetype_registry.py
Module      : Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Maintains the canonical file type registry used throughout the Agent Brain.

This registry normalizes different file type aliases into a canonical file type
and provides metadata required for desktop and browser automation.

Author : Team JARVIS
===============================================================================
"""

from typing import Dict, Optional


class FileTypeRegistry:
    """
    Registry responsible for file type normalization.
    """

    CATEGORY = "FILETYPE"

    _FILETYPE_MAP: Dict[str, Dict[str, object]] = {

        # ------------------------------------------------------------------
        # PDF
        # ------------------------------------------------------------------

        "pdf": {
            "canonical": "pdf",
            "display_name": "PDF Document",
            "extension": ".pdf",
            "mime_type": "application/pdf",
            "category": "document"
        },

        # ------------------------------------------------------------------
        # Microsoft Word
        # ------------------------------------------------------------------

        "word": {
            "canonical": "word",
            "display_name": "Microsoft Word Document",
            "extension": ".docx",
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "category": "document"
        },

        "docx": {
            "canonical": "word",
            "display_name": "Microsoft Word Document",
            "extension": ".docx",
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "category": "document"
        },

        # ------------------------------------------------------------------
        # Excel
        # ------------------------------------------------------------------

        "excel": {
            "canonical": "excel",
            "display_name": "Microsoft Excel Workbook",
            "extension": ".xlsx",
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "category": "spreadsheet"
        },

        "xlsx": {
            "canonical": "excel",
            "display_name": "Microsoft Excel Workbook",
            "extension": ".xlsx",
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "category": "spreadsheet"
        },

        # ------------------------------------------------------------------
        # PowerPoint
        # ------------------------------------------------------------------

        "powerpoint": {
            "canonical": "powerpoint",
            "display_name": "Microsoft PowerPoint Presentation",
            "extension": ".pptx",
            "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "category": "presentation"
        },

        "pptx": {
            "canonical": "powerpoint",
            "display_name": "Microsoft PowerPoint Presentation",
            "extension": ".pptx",
            "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "category": "presentation"
        },

        # ------------------------------------------------------------------
        # Text File
        # ------------------------------------------------------------------

        "text": {
            "canonical": "text",
            "display_name": "Text File",
            "extension": ".txt",
            "mime_type": "text/plain",
            "category": "document"
        },

        "txt": {
            "canonical": "text",
            "display_name": "Text File",
            "extension": ".txt",
            "mime_type": "text/plain",
            "category": "document"
        },

        # ------------------------------------------------------------------
        # CSV
        # ------------------------------------------------------------------

        "csv": {
            "canonical": "csv",
            "display_name": "CSV File",
            "extension": ".csv",
            "mime_type": "text/csv",
            "category": "spreadsheet"
        },

        # ------------------------------------------------------------------
        # Image
        # ------------------------------------------------------------------

        "image": {
            "canonical": "image",
            "display_name": "Image",
            "extension": ".png",
            "mime_type": "image/png",
            "category": "image"
        },

        "png": {
            "canonical": "image",
            "display_name": "PNG Image",
            "extension": ".png",
            "mime_type": "image/png",
            "category": "image"
        },

        "jpg": {
            "canonical": "image",
            "display_name": "JPEG Image",
            "extension": ".jpg",
            "mime_type": "image/jpeg",
            "category": "image"
        },

        "jpeg": {
            "canonical": "image",
            "display_name": "JPEG Image",
            "extension": ".jpeg",
            "mime_type": "image/jpeg",
            "category": "image"
        },

        # ------------------------------------------------------------------
        # ZIP
        # ------------------------------------------------------------------

        "zip": {
            "canonical": "zip",
            "display_name": "ZIP Archive",
            "extension": ".zip",
            "mime_type": "application/zip",
            "category": "archive"
        }
    }

    @classmethod
    def normalize(cls, filetype: str) -> str:
        filetype = filetype.lower().strip()

        if filetype in cls._FILETYPE_MAP:
            return cls._FILETYPE_MAP[filetype]["canonical"]

        return filetype

    @classmethod
    def contains(cls, filetype: str) -> bool:
        return filetype.lower().strip() in cls._FILETYPE_MAP

    @classmethod
    def get_metadata(cls, filetype: str) -> Optional[Dict[str, object]]:
        return cls._FILETYPE_MAP.get(filetype.lower().strip())

    @classmethod
    def get_extension(cls, filetype: str) -> Optional[str]:
        metadata = cls.get_metadata(filetype)

        if metadata:
            return metadata["extension"]

        return None

    @classmethod
    def all_filetypes(cls) -> Dict[str, Dict[str, object]]:
        return cls._FILETYPE_MAP.copy()