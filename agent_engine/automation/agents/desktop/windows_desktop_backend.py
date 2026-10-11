"""
Windows desktop backend for M5-K.

Implemented:
    M5-K Step 6-A:
        - Windows backend foundation

    M5-K Step 6-B:
        - launch_application
        - close_application
        - restart_application
        - terminate_application

    M5-K Step 6-C:
        - focus_window
        - switch_window
        - resize_window
        - position_window

The backend contains Windows-specific OS interaction only.
"""

from __future__ import annotations

import ctypes
import os
import platform
import subprocess
import time
from turtle import width
from typing import Any
from contextlib import contextmanager
from .desktop_backend import DesktopBackend


class WindowsDesktopBackend(DesktopBackend):
    """
    Windows-specific implementation of DesktopBackend.

    Responsibilities:
        - Application lifecycle.
        - Application-window discovery.
        - Window activation.
        - Window switching.
        - Window resizing.
        - Window positioning.

    This backend does not own:
        - planning
        - scheduling
        - retry/fallback
        - process analytics
        - keyboard automation
        - mouse automation
        - browser automation
        - screen/OCR automation
    """

    # ------------------------------------------------------------------
    # Application executable mapping
    # ------------------------------------------------------------------

    APPLICATION_EXECUTABLES: dict[str, str] = {
        "vscode": "code.exe",
        "word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
        "powerpoint": "POWERPNT.EXE",
        "notepad": "notepad.exe",
        "calculator": "CalculatorApp.exe",
        "paint": "mspaint.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
    }

    APPLICATION_COMMANDS: dict[str, list[str]] = {
        "vscode": ["code"],
        "word": ["winword"],
        "excel": ["excel"],
        "powerpoint": ["powerpnt"],
        "notepad": ["notepad"],
        "calculator": ["calc"],
        "paint": ["mspaint"],
        "explorer": ["explorer"],
        "cmd": ["cmd"],
        "powershell": ["powershell"],
    }

    CLOSE_WAIT_SECONDS = 10.0
    PROCESS_POLL_INTERVAL = 0.25

    # Win32 constants.
    SW_RESTORE = 9

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        self._validate_windows_environment()

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_windows_environment() -> None:
        """
        Ensure that this backend is running on Windows.
        """

        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsDesktopBackend can only be used on Windows."
            )

    @property
    def platform_name(self) -> str:
        """Return the current operating-system name."""

        return platform.system()

    @property
    def is_windows(self) -> bool:
        """Return True when running on Windows."""

        return platform.system() == "Windows"

    @contextmanager
    def _per_monitor_dpi_context(self):
        """
        Temporarily execute Windows window-geometry operations under
        Per-Monitor DPI Awareness V2.

        The previous thread DPI context is restored automatically when
        the context exits.
        """

        user32 = ctypes.windll.user32

        set_thread_dpi_awareness_context = (
            user32.SetThreadDpiAwarenessContext
        )

        set_thread_dpi_awareness_context.argtypes = [
            ctypes.c_void_p,
        ]
        set_thread_dpi_awareness_context.restype = ctypes.c_void_p

        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        per_monitor_v2 = ctypes.c_void_p(-4)

        previous_context = set_thread_dpi_awareness_context(
            per_monitor_v2
        )

        if not previous_context:
            raise RuntimeError(
                "Failed to set Per-Monitor DPI Awareness V2."
            )

        try:
            yield
        finally:
            set_thread_dpi_awareness_context(
                previous_context
            )
            
    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_application(application: str) -> str:
        """
        Validate an already-normalized application identifier.
        """

        if not isinstance(application, str) or not application.strip():
            raise ValueError(
                "application must be a non-empty string"
            )

        return application.strip().lower()

    @classmethod
    def _get_executable(
        cls,
        application: str,
    ) -> str:
        """
        Resolve an application identifier to its Windows executable.
        """

        normalized_application = cls._validate_application(
            application
        )

        try:
            return cls.APPLICATION_EXECUTABLES[
                normalized_application
            ]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported Windows application: "
                f"{normalized_application}"
            ) from exc

    @classmethod
    def _get_launch_command(
        cls,
        application: str,
    ) -> list[str]:
        """
        Resolve an application identifier to its launch command.
        """

        normalized_application = cls._validate_application(
            application
        )

        try:
            return list(
                cls.APPLICATION_COMMANDS[
                    normalized_application
                ]
            )
        except KeyError as exc:
            raise ValueError(
                f"Unsupported Windows application: "
                f"{normalized_application}"
            ) from exc

    @staticmethod
    def _validate_target(target: str) -> str:
        """
        Validate a window title target.
        """

        if not isinstance(target, str) or not target.strip():
            raise ValueError(
                "target must be a non-empty string"
            )

        return target.strip()

    @staticmethod
    def _validate_dimension(
        value: int,
        parameter_name: str,
    ) -> int:
        """
        Validate a positive window dimension.
        """

        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"{parameter_name} must be a positive integer"
            )

        if value <= 0:
            raise ValueError(
                f"{parameter_name} must be a positive integer"
            )

        return value

    @staticmethod
    def _validate_coordinate(
        value: int,
        parameter_name: str,
    ) -> int:
        """
        Validate a window coordinate.

        Negative coordinates are allowed because a monitor may be
        positioned to the left or above the primary monitor.
        """

        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"{parameter_name} must be an integer"
            )

        return value

    # ------------------------------------------------------------------
    # Process discovery
    # ------------------------------------------------------------------

    @classmethod
    def _get_process_ids(
        cls,
        executable: str,
    ) -> list[int]:
        """
        Return process IDs belonging to the requested executable.
        """

        result = subprocess.run(
            [
                "tasklist",
                "/FI",
                f"IMAGENAME eq {executable}",
                "/FO",
                "CSV",
                "/NH",
            ],
            capture_output=True,
            text=True,
            check=False,
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            ),
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Unable to query Windows process information: "
                f"{result.stderr.strip()}"
            )

        process_ids: list[int] = []

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line or line.startswith("INFO:"):
                continue

            parts = [
                part.strip('"')
                for part in line.split('","')
            ]

            if len(parts) < 2:
                continue

            try:
                process_ids.append(int(parts[1]))
            except ValueError:
                continue

        return process_ids

    @classmethod
    def _is_process_running(
        cls,
        executable: str,
    ) -> bool:
        """Return True when at least one matching process is running."""

        return bool(
            cls._get_process_ids(executable)
        )

    @classmethod
    def _wait_for_process_exit(
        cls,
        executable: str,
        timeout: float | None = None,
    ) -> bool:
        """
        Wait until the requested executable exits.
        """

        if timeout is None:
            timeout = cls.CLOSE_WAIT_SECONDS

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if not cls._is_process_running(executable):
                return True

            time.sleep(
                cls.PROCESS_POLL_INTERVAL
            )

        return not cls._is_process_running(
            executable
        )

    # ------------------------------------------------------------------
    # Window discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _get_window_title(
        hwnd: int,
    ) -> str:
        """
        Return the title text of a window.
        """

        user32 = ctypes.windll.user32

        length = user32.GetWindowTextLengthW(
            hwnd
        )

        if length <= 0:
            return ""

        buffer = ctypes.create_unicode_buffer(
            length + 1
        )

        user32.GetWindowTextW(
            hwnd,
            buffer,
            length + 1,
        )

        return buffer.value

    @staticmethod
    def _get_window_process_id(
        hwnd: int,
    ) -> int:
        """
        Return the process ID owning a window.
        """

        user32 = ctypes.windll.user32

        process_id = ctypes.c_ulong()

        user32.GetWindowThreadProcessId(
            hwnd,
            ctypes.byref(process_id),
        )

        return process_id.value

    @classmethod
    def _enumerate_windows(
        cls,
    ) -> list[dict[str, Any]]:
        """
        Enumerate visible top-level desktop windows.

        Returns dictionaries containing:
            hwnd
            title
            process_id
        """

        user32 = ctypes.windll.user32

        enum_windows_proc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )

        windows: list[dict[str, Any]] = []

        def enum_window(
            hwnd: int,
            _lparam: int,
        ) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True

            title = cls._get_window_title(hwnd)

            if not title.strip():
                return True

            process_id = cls._get_window_process_id(
                hwnd
            )

            windows.append(
                {
                    "hwnd": hwnd,
                    "title": title,
                    "process_id": process_id,
                }
            )

            return True

        callback = enum_windows_proc(enum_window)

        success = user32.EnumWindows(
            callback,
            0,
        )

        if not success:
            raise RuntimeError(
                "Windows EnumWindows failed."
            )

        return windows

    @classmethod
    def _find_window_by_process_ids(
        cls,
        process_ids: set[int],
    ) -> int:
        """
        Find the first visible top-level window belonging to one of
        the supplied process IDs.
        """

        if not process_ids:
            raise RuntimeError(
                "No process IDs were supplied for window lookup."
            )

        windows = cls._enumerate_windows()

        for window in windows:
            if window["process_id"] in process_ids:
                return int(window["hwnd"])

        raise RuntimeError(
            "No visible top-level window was found for "
            "the requested application."
        )

    @classmethod
    def _find_window_by_title(
        cls,
        target: str,
    ) -> int:
        """
        Find a visible top-level window by title.

        Matching strategy:
            1. Exact case-insensitive title match.
            2. Case-insensitive substring match.

        Exact matches are always preferred.
        """

        normalized_target = target.casefold()

        windows = cls._enumerate_windows()

        exact_matches: list[int] = []
        partial_matches: list[int] = []

        for window in windows:
            title = str(
                window["title"]
            )

            normalized_title = title.casefold()

            if normalized_title == normalized_target:
                exact_matches.append(
                    int(window["hwnd"])
                )
            elif normalized_target in normalized_title:
                partial_matches.append(
                    int(window["hwnd"])
                )

        if exact_matches:
            return exact_matches[0]

        if partial_matches:
            return partial_matches[0]

        raise RuntimeError(
            f"No visible window found matching target "
            f"'{target}'."
        )

    @classmethod
    def _find_application_window(
        cls,
        application: str,
    ) -> tuple[int, int, str]:
        """
        Resolve an application to a visible top-level window.

        Returns:
            (window_handle, process_id, window_title)
        """

        executable = cls._get_executable(
            application
        )

        process_ids = cls._get_process_ids(
            executable
        )

        if not process_ids:
            raise RuntimeError(
                f"Application '{application}' is not running."
            )

        hwnd = cls._find_window_by_process_ids(
            set(process_ids)
        )

        title = cls._get_window_title(
            hwnd
        )

        process_id = cls._get_window_process_id(
            hwnd
        )

        return (
            hwnd,
            process_id,
            title,
        )

    # ------------------------------------------------------------------
    # Window geometry
    # ------------------------------------------------------------------

    @staticmethod
    def _get_window_rect(
        hwnd: int,
    ) -> dict[str, int]:
        """
        Retrieve the current window rectangle.

        Coordinates are screen coordinates.
        """

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        rect = RECT()

        get_window_rect = ctypes.windll.user32.GetWindowRect

        # Explicit Windows API signature.
        get_window_rect.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(RECT),
        ]
        get_window_rect.restype = ctypes.c_int

        success = get_window_rect(
            ctypes.c_void_p(hwnd),
            ctypes.byref(rect),
        )

        if not success:
            raise RuntimeError(
                "GetWindowRect failed."
            )

        return {
            "x": rect.left,
            "y": rect.top,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top,
        }
    # ------------------------------------------------------------------
    # Window activation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _restore_window(
        hwnd: int,
    ) -> None:
        """
        Restore a minimized window before activation.
        """

        ctypes.windll.user32.ShowWindow(
            hwnd,
            WindowsDesktopBackend.SW_RESTORE,
        )

    def _set_foreground_window(
        self,
        hwnd: int,
    ) -> None:
        """
        Restore and activate a target window.

        Windows may not update the foreground window immediately after
        SetForegroundWindow(). Therefore, activation is attempted more
        than once and the foreground state is verified with a short
        polling window.
        """

        if not hwnd:
            raise ValueError("hwnd must be a valid window handle.")

        user32 = ctypes.windll.user32

        # Restore the window if it is minimized.
        user32.ShowWindow(
            hwnd,
            self.SW_RESTORE,
        )

        activated = False

        # Windows foreground activation may require more than one attempt.
        for _ in range(3):
            user32.SetForegroundWindow(hwnd)

            # Allow Windows a short period to update the foreground window.
            deadline = time.monotonic() + 0.25

            while time.monotonic() < deadline:
                foreground_hwnd = user32.GetForegroundWindow()

                if foreground_hwnd == hwnd:
                    activated = True
                    break

                time.sleep(0.02)

            if activated:
                break

        if not activated:
            foreground_hwnd = user32.GetForegroundWindow()

            raise RuntimeError(
                "The target window could not be verified as the "
                f"foreground window. target_hwnd={hwnd}, "
                f"foreground_hwnd={foreground_hwnd}"
            )
    # ------------------------------------------------------------------
    # Application lifecycle
    # ------------------------------------------------------------------

    def launch_application(
        self,
        application: str,
    ) -> dict[str, Any]:
        """
        Launch an application asynchronously.
        """

        normalized_application = self._validate_application(
            application
        )

        command = self._get_launch_command(
            normalized_application
        )

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NEW_PROCESS_GROUP",
                    0,
                ),
            )
        except OSError as exc:
            raise RuntimeError(
                f"Failed to launch application "
                f"'{normalized_application}': {exc}"
            ) from exc

        return {
            "operation": "launch_application",
            "application": normalized_application,
            "pid": process.pid,
            "status": "launched",
        }

    def close_application(
        self,
        application: str,
    ) -> dict[str, Any]:
        """
        Gracefully close an application using WM_CLOSE.
        """

        normalized_application = self._validate_application(
            application
        )

        executable = self._get_executable(
            normalized_application
        )

        process_ids = self._get_process_ids(
            executable
        )

        if not process_ids:
            return {
                "operation": "close_application",
                "application": normalized_application,
                "status": "not_running",
                "process_ids": [],
            }

        window_handles = self._get_process_window_handles(
            set(process_ids)
        )

        for hwnd in window_handles:
            self._send_close_message(
                hwnd
            )

        closed = self._wait_for_process_exit(
            executable,
            timeout=self.CLOSE_WAIT_SECONDS,
        )

        if not closed:
            raise RuntimeError(
                f"Application '{normalized_application}' "
                f"did not close gracefully within "
                f"{self.CLOSE_WAIT_SECONDS:.0f} seconds."
            )

        return {
            "operation": "close_application",
            "application": normalized_application,
            "status": "closed",
            "process_ids": process_ids,
            "windows_notified": len(window_handles),
        }

    def restart_application(
        self,
        application: str,
    ) -> dict[str, Any]:
        """
        Restart an application using:

            close -> verify exit -> launch
        """

        normalized_application = self._validate_application(
            application
        )

        close_result = self.close_application(
            normalized_application
        )

        launch_result = self.launch_application(
            normalized_application
        )

        return {
            "operation": "restart_application",
            "application": normalized_application,
            "status": "restarted",
            "close": close_result,
            "launch": launch_result,
        }

    def terminate_application(
        self,
        application: str,
    ) -> dict[str, Any]:
        """
        Forcefully terminate an application.
        """

        normalized_application = self._validate_application(
            application
        )

        executable = self._get_executable(
            normalized_application
        )

        process_ids = self._get_process_ids(
            executable
        )

        if not process_ids:
            return {
                "operation": "terminate_application",
                "application": normalized_application,
                "status": "not_running",
                "process_ids": [],
            }

        terminated_process_ids: list[int] = []

        for process_id in process_ids:
            result = subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(process_id),
                    "/T",
                    "/F",
                ],
                capture_output=True,
                text=True,
                check=False,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0,
                ),
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to terminate process "
                    f"{process_id} for "
                    f"'{normalized_application}': "
                    f"{result.stderr.strip()}"
                )

            terminated_process_ids.append(
                process_id
            )

        return {
            "operation": "terminate_application",
            "application": normalized_application,
            "status": "terminated",
            "process_ids": terminated_process_ids,
        }

    # ------------------------------------------------------------------
    # Graceful close helpers
    # ------------------------------------------------------------------

    @classmethod
    def _get_process_window_handles(
        cls,
        process_ids: set[int],
    ) -> list[int]:
        """
        Find visible top-level windows belonging to the supplied
        process IDs.
        """

        if not process_ids:
            return []

        user32 = ctypes.windll.user32

        enum_windows_proc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )

        window_handles: list[int] = []

        def enum_window(
            hwnd: int,
            _lparam: int,
        ) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True

            process_id = ctypes.c_ulong()

            user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(process_id),
            )

            if process_id.value in process_ids:
                window_handles.append(
                    hwnd
                )

            return True

        callback = enum_windows_proc(
            enum_window
        )

        user32.EnumWindows(
            callback,
            0,
        )

        return window_handles

    @staticmethod
    def _send_close_message(
        hwnd: int,
    ) -> None:
        """
        Send WM_CLOSE to a window.
        """

        WM_CLOSE = 0x0010

        ctypes.windll.user32.PostMessageW(
            hwnd,
            WM_CLOSE,
            0,
            0,
        )

    # ------------------------------------------------------------------
    # Step 6-C: Window management
    # ------------------------------------------------------------------

    def focus_window(
        self,
        application: str,
    ) -> dict[str, Any]:
        """
        Bring the specified application's window to the foreground.
        """

        normalized_application = self._validate_application(
            application
        )

        hwnd, process_id, title = (
            self._find_application_window(
                normalized_application
            )
        )

        self._set_foreground_window(
            hwnd
        )

        return {
            "operation": "focus_window",
            "application": normalized_application,
            "window_title": title,
            "process_id": process_id,
            "hwnd": hwnd,
            "status": "focused",
        }

    def switch_window(
        self,
        target: str,
    ) -> dict[str, Any]:
        """
        Switch to a visible window identified by its title.

        Exact title matching is preferred. If no exact match exists,
        a case-insensitive substring match is used.
        """

        normalized_target = self._validate_target(
            target
        )

        hwnd = self._find_window_by_title(
            normalized_target
        )

        title = self._get_window_title(
            hwnd
        )

        process_id = self._get_window_process_id(
            hwnd
        )

        self._set_foreground_window(
            hwnd
        )

        return {
            "operation": "switch_window",
            "target": normalized_target,
            "window_title": title,
            "process_id": process_id,
            "hwnd": hwnd,
            "status": "switched",
        }

    def resize_window(
        self,
        application: str,
        width: int,
        height: int,
    ) -> dict[str, object]:
        """
        Resize an application window to the requested dimensions.

        Width and height are interpreted as physical screen pixels.
        Window geometry is executed under Per-Monitor DPI Awareness V2
        so that DPI virtualization does not alter the requested size.
        """

        normalized_application = self._validate_application(
            application
        )

        if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
            raise ValueError(
                "width must be a positive integer."
            )

        if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
            raise ValueError(
                "height must be a positive integer."
            )

        with self._per_monitor_dpi_context():
            window_info = self._find_application_window(
                normalized_application
            )

            hwnd, process_id, window_title = window_info

            current_rect = self._get_window_rect(
                hwnd
            )

            success = ctypes.windll.user32.MoveWindow(
                ctypes.c_void_p(hwnd),
                current_rect["x"],
                current_rect["y"],
                width,
                height,
                True,
            )

            if not success:
                raise RuntimeError(
                    f"MoveWindow failed while resizing "
                    f"'{normalized_application}'."
                )

            updated_rect = self._get_window_rect(
                hwnd
            )

        return {
            "operation": "resize_window",
            "application": normalized_application,
            "window_title": window_title,
            "process_id": process_id,
            "hwnd": hwnd,
            "width": updated_rect["width"],
            "height": updated_rect["height"],
            "status": "resized",
        }
    
    def position_window(
        self,
        application: str,
        x: int,
        y: int,
    ) -> dict[str, Any]:
        """
        Move the specified application's window.

        The current width and height are preserved.
        """

        normalized_application = self._validate_application(
            application
        )

        validated_x = self._validate_coordinate(
            x,
            "x",
        )

        validated_y = self._validate_coordinate(
            y,
            "y",
        )

        hwnd, process_id, title = (
            self._find_application_window(
                normalized_application
            )
        )

        current_rect = self._get_window_rect(
            hwnd
        )

        success = ctypes.windll.user32.MoveWindow(
            hwnd,
            validated_x,
            validated_y,
            current_rect["width"],
            current_rect["height"],
            True,
        )

        if not success:
            raise RuntimeError(
                f"Failed to position window for "
                f"application '{normalized_application}'."
            )

        updated_rect = self._get_window_rect(
            hwnd
        )

        return {
            "operation": "position_window",
            "application": normalized_application,
            "window_title": title,
            "process_id": process_id,
            "hwnd": hwnd,
            "x": updated_rect["x"],
            "y": updated_rect["y"],
            "status": "positioned",
        }