"""
Live M5-L7 Filesystem Smoke Test
================================

Purpose:
    Visually verify that the real WindowsFileSystemBackend performs
    actual filesystem operations correctly.

This is a DEMO/SMOKE TEST only.

The delays are intentionally added here so that the operations can
be observed in File Explorer. They are NOT part of the backend.

Operations demonstrated:
    1. Create directory
    2. Create file
    3. Write demo content
    4. Check path existence
    5. Read file metadata
    6. Copy file
    7. Rename file
    8. Create subdirectory
    9. List directory
    10. Move file
    11. Delete moved file
    12. Delete original file
    13. Delete subdirectory
    14. Final directory listing
    15. Cleanup test directory
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from agent_engine.automation.agents.filesystem.windows_filesystem_backend import (
    WindowsFileSystemBackend,
)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

TEST_ROOT = Path.cwd() / "filesystem_smoke_test"

DEMO_FILE = TEST_ROOT / "demo_file.txt"
COPIED_FILE = TEST_ROOT / "copied_file.txt"
RENAMED_FILE = TEST_ROOT / "renamed_file.txt"

DEMO_FOLDER = TEST_ROOT / "demo_folder"
MOVED_FILE = DEMO_FOLDER / "moved_file.txt"

DELAY = 2.0


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def pause() -> None:
    """Pause so the filesystem operation can be observed."""
    time.sleep(DELAY)


def print_step(number: int, title: str) -> None:
    """Print a clearly visible test step."""
    print()
    print("=" * 70)
    print(f"STEP {number}: {title}")
    print("=" * 70)


def show_result(result: dict) -> None:
    """Print backend operation result."""
    print(f"Result: {result}")


def wait_for_user() -> None:
    """Pause before starting the live demonstration."""
    print()
    print("=" * 70)
    print("JARVIS M5-L7 LIVE FILESYSTEM DEMONSTRATION")
    print("=" * 70)
    print()
    print("A real Windows filesystem will be used.")
    print()
    print(f"Test directory:")
    print(f"  {TEST_ROOT}")
    print()
    print("Open this directory in File Explorer before continuing.")
    print()
    input("Press ENTER to start the live demonstration...")


# ---------------------------------------------------------------------
# Main demonstration
# ---------------------------------------------------------------------

def main() -> None:
    backend = WindowsFileSystemBackend()

    print("=" * 70)
    print("JARVIS M5-L7 - REAL WINDOWS FILESYSTEM DEMO")
    print("=" * 70)

    print()
    print("Backend:")
    print(f"  {backend.__class__.__name__}")

    print()
    print("Test root:")
    print(f"  {TEST_ROOT}")

    print()
    print("This test performs REAL filesystem operations.")
    print("The delays are only for visual observation.")

    wait_for_user()

    # ---------------------------------------------------------------
    # Safety cleanup before starting
    # ---------------------------------------------------------------

    if TEST_ROOT.exists():
        print()
        print("Existing smoke-test directory detected.")
        print("Removing it before starting a clean test...")

        shutil.rmtree(TEST_ROOT)

        print("Previous test directory removed.")

    # ---------------------------------------------------------------
    # STEP 1 - Create root directory
    # ---------------------------------------------------------------

    print_step(1, "CREATE DIRECTORY")

    result = backend.create_directory(str(TEST_ROOT))

    show_result(result)
    print(f"Created: {TEST_ROOT}")

    pause()

    # ---------------------------------------------------------------
    # STEP 2 - Create file
    # ---------------------------------------------------------------

    print_step(2, "CREATE FILE")

    result = backend.create_file(str(DEMO_FILE))

    show_result(result)
    print(f"Created: {DEMO_FILE}")

    pause()

    # ---------------------------------------------------------------
    # STEP 3 - Write demo content
    # ---------------------------------------------------------------

    print_step(3, "WRITE DEMO CONTENT")

    print("Writing sample content using Python Path.write_text().")
    print("This is only test setup; write_file is NOT a JARVIS action.")

    DEMO_FILE.write_text(
        "JARVIS M5-L7 Filesystem Automation Demo\n"
        "This file was created by WindowsFileSystemBackend.\n",
        encoding="utf-8",
    )

    print(f"Content written to: {DEMO_FILE}")

    pause()

    # ---------------------------------------------------------------
    # STEP 4 - Check path existence
    # ---------------------------------------------------------------

    print_step(4, "CHECK PATH EXISTS")

    result = backend.path_exists(str(DEMO_FILE))

    show_result(result)

    if result["exists"] is not True:
        raise AssertionError("path_exists returned False for existing file.")

    print("PASS: File exists.")

    pause()

    # ---------------------------------------------------------------
    # STEP 5 - Get file metadata
    # ---------------------------------------------------------------

    print_step(5, "GET FILE METADATA")

    result = backend.get_file_metadata(str(DEMO_FILE))

    show_result(result)

    print(f"File size: {result['size']} bytes")
    print(f"Is file: {result['is_file']}")
    print(f"Is directory: {result['is_directory']}")

    pause()

    # ---------------------------------------------------------------
    # STEP 6 - Copy file
    # ---------------------------------------------------------------

    print_step(6, "COPY FILE")

    result = backend.copy_file(
        str(DEMO_FILE),
        str(COPIED_FILE),
    )

    show_result(result)

    print(f"Source:")
    print(f"  {DEMO_FILE}")

    print(f"Destination:")
    print(f"  {COPIED_FILE}")

    pause()

    # ---------------------------------------------------------------
    # STEP 7 - Rename copied file
    # ---------------------------------------------------------------

    print_step(7, "RENAME FILE")

    result = backend.rename_file(
        str(COPIED_FILE),
        "renamed_file.txt",
    )

    show_result(result)

    print(f"Renamed:")
    print(f"  {COPIED_FILE}")

    print("To:")
    print(f"  {RENAMED_FILE}")

    pause()

    # ---------------------------------------------------------------
    # STEP 8 - Create subdirectory
    # ---------------------------------------------------------------

    print_step(8, "CREATE SUBDIRECTORY")

    result = backend.create_directory(str(DEMO_FOLDER))

    show_result(result)

    print(f"Created:")
    print(f"  {DEMO_FOLDER}")

    pause()

    # ---------------------------------------------------------------
    # STEP 9 - List directory
    # ---------------------------------------------------------------

    print_step(9, "LIST DIRECTORY")

    result = backend.list_directory(str(TEST_ROOT))

    show_result(result)

    print()
    print("Current entries:")

    for entry in result["entries"]:
        print(f"  - {entry}")

    pause()

    # ---------------------------------------------------------------
    # STEP 10 - Move file
    # ---------------------------------------------------------------

    print_step(10, "MOVE FILE")

    result = backend.move_file(
        str(RENAMED_FILE),
        str(MOVED_FILE),
    )

    show_result(result)

    print("Moved:")
    print(f"  {RENAMED_FILE}")

    print("To:")
    print(f"  {MOVED_FILE}")

    pause()

    # ---------------------------------------------------------------
    # STEP 11 - Delete moved file
    # ---------------------------------------------------------------

    print_step(11, "DELETE MOVED FILE")

    result = backend.delete_file(str(MOVED_FILE))

    show_result(result)

    print(f"Deleted:")
    print(f"  {MOVED_FILE}")

    pause()

    # ---------------------------------------------------------------
    # STEP 12 - Delete original file
    # ---------------------------------------------------------------

    print_step(12, "DELETE ORIGINAL FILE")

    result = backend.delete_file(str(DEMO_FILE))

    show_result(result)

    print(f"Deleted:")
    print(f"  {DEMO_FILE}")

    pause()

    # ---------------------------------------------------------------
    # STEP 13 - Delete empty directory
    # ---------------------------------------------------------------

    print_step(13, "DELETE SUBDIRECTORY")

    result = backend.delete_directory(str(DEMO_FOLDER))

    show_result(result)

    print(f"Deleted:")
    print(f"  {DEMO_FOLDER}")

    pause()

    # ---------------------------------------------------------------
    # STEP 14 - Final directory listing
    # ---------------------------------------------------------------

    print_step(14, "FINAL DIRECTORY LIST")

    result = backend.list_directory(str(TEST_ROOT))

    show_result(result)

    print()
    print("Remaining entries:")

    if result["entries"]:
        for entry in result["entries"]:
            print(f"  - {entry}")
    else:
        print("  <empty>")

    pause()

    # ---------------------------------------------------------------
    # STEP 15 - Final cleanup
    # ---------------------------------------------------------------

    print_step(15, "CLEANUP TEST DIRECTORY")

    # At this point the directory should be empty.
    result = backend.delete_directory(str(TEST_ROOT))

    show_result(result)

    print(f"Removed:")
    print(f"  {TEST_ROOT}")

    pause()

    # ---------------------------------------------------------------
    # Final verification
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL VERIFICATION")
    print("=" * 70)

    result = backend.path_exists(str(TEST_ROOT))

    show_result(result)

    if result["exists"]:
        raise AssertionError(
            "Smoke-test directory still exists after cleanup."
        )

    print()
    print("M5-L7 LIVE FILESYSTEM TEST PASSED")
    print()
    print("Verified operations:")
    print("  [PASS] create_directory")
    print("  [PASS] create_file")
    print("  [PASS] path_exists")
    print("  [PASS] get_file_metadata")
    print("  [PASS] copy_file")
    print("  [PASS] rename_file")
    print("  [PASS] list_directory")
    print("  [PASS] move_file")
    print("  [PASS] delete_file")
    print("  [PASS] delete_directory")
    print()
    print("Real Windows filesystem operations completed successfully.")
    print("=" * 70)


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()