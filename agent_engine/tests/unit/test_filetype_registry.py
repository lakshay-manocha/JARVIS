"""
===============================================================================
File Name   : test_filetype_registry.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for FileTypeRegistry.

This test suite verifies:
    • File type normalization
    • Canonical file types
    • Case insensitivity
    • Unknown file types
    • Registry lookup
    • Metadata retrieval
    • Extension retrieval
    • Registry immutability

Author : Team JARVIS
===============================================================================
"""

import pytest

from agent_engine.registry.filetype_registry import FileTypeRegistry


# =============================================================================
# Fixture
# =============================================================================

@pytest.fixture
def registry():
    """Returns FileTypeRegistry."""
    return FileTypeRegistry()


# =============================================================================
# Normalization Tests
# =============================================================================

@pytest.mark.parametrize(
    "filetype, expected",
    [
        ("pdf", "pdf"),
        ("word", "word"),
        ("docx", "word"),
        ("excel", "excel"),
        ("xlsx", "excel"),
        ("powerpoint", "powerpoint"),
        ("pptx", "powerpoint"),
        ("text", "text"),
        ("txt", "text"),
        ("csv", "csv"),
        ("image", "image"),
        ("png", "image"),
        ("jpg", "image"),
        ("jpeg", "image"),
        ("zip", "zip"),
    ],
)
def test_normalize_known_filetypes(registry, filetype, expected):
    assert registry.normalize(filetype) == expected


# =============================================================================
# Case Insensitivity
# =============================================================================

@pytest.mark.parametrize(
    "filetype, expected",
    [
        ("PDF", "pdf"),
        ("Docx", "word"),
        ("XLSX", "excel"),
        ("PPTX", "powerpoint"),
        ("TXT", "text"),
        ("PNG", "image"),
        ("JPEG", "image"),
        ("ZIP", "zip"),
    ],
)
def test_case_insensitive_normalization(registry, filetype, expected):
    assert registry.normalize(filetype) == expected


# =============================================================================
# Whitespace Handling
# =============================================================================

@pytest.mark.parametrize(
    "filetype, expected",
    [
        (" pdf ", "pdf"),
        ("   docx", "word"),
        ("xlsx   ", "excel"),
        ("   png   ", "image"),
    ],
)
def test_whitespace_normalization(registry, filetype, expected):
    assert registry.normalize(filetype) == expected


# =============================================================================
# Unknown File Types
# =============================================================================

@pytest.mark.parametrize(
    "filetype",
    [
        "exe",
        "apk",
        "iso",
        "rar",
    ],
)
def test_unknown_filetype_returns_original(registry, filetype):
    assert registry.normalize(filetype) == filetype.lower()


# =============================================================================
# Contains Tests
# =============================================================================

@pytest.mark.parametrize(
    "filetype",
    [
        "pdf",
        "docx",
        "word",
        "xlsx",
        "excel",
        "pptx",
        "powerpoint",
        "txt",
        "text",
        "csv",
        "png",
        "jpg",
        "jpeg",
        "zip",
    ],
)
def test_contains_known_filetypes(registry, filetype):
    assert registry.contains(filetype)


@pytest.mark.parametrize(
    "filetype",
    [
        "exe",
        "apk",
        "rar",
    ],
)
def test_contains_unknown_filetypes(registry, filetype):
    assert not registry.contains(filetype)


# =============================================================================
# Metadata Tests
# =============================================================================

def test_pdf_metadata(registry):
    metadata = registry.get_metadata("pdf")

    assert metadata["canonical"] == "pdf"
    assert metadata["extension"] == ".pdf"
    assert metadata["category"] == "document"


def test_docx_metadata(registry):
    metadata = registry.get_metadata("docx")

    assert metadata["canonical"] == "word"
    assert metadata["extension"] == ".docx"


def test_png_metadata(registry):
    metadata = registry.get_metadata("png")

    assert metadata["canonical"] == "image"
    assert metadata["mime_type"] == "image/png"


def test_zip_metadata(registry):
    metadata = registry.get_metadata("zip")

    assert metadata["canonical"] == "zip"
    assert metadata["category"] == "archive"


def test_unknown_metadata(registry):
    assert registry.get_metadata("exe") is None


# =============================================================================
# Extension Tests
# =============================================================================

def test_pdf_extension(registry):
    assert registry.get_extension("pdf") == ".pdf"


def test_docx_extension(registry):
    assert registry.get_extension("docx") == ".docx"


def test_excel_extension(registry):
    assert registry.get_extension("excel") == ".xlsx"


def test_png_extension(registry):
    assert registry.get_extension("png") == ".png"


def test_unknown_extension(registry):
    assert registry.get_extension("exe") is None


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

def test_all_filetypes_returns_copy(registry):
    filetypes = registry.all_filetypes()

    filetypes["pdf"] = {
        "canonical": "modified",
        "extension": ".xyz",
        "display_name": "Modified PDF",
        "mime_type": "application/test",
        "category": "test",
    }

    metadata = registry.get_metadata("pdf")

    assert metadata["canonical"] == "pdf"
    assert metadata["extension"] == ".pdf"


# =============================================================================
# Registry Consistency
# =============================================================================

def test_registry_is_not_modified(registry):
    before = registry.all_filetypes()

    registry.normalize("pdf")
    registry.normalize("docx")
    registry.get_metadata("png")
    registry.get_extension("zip")

    after = registry.all_filetypes()

    assert before == after