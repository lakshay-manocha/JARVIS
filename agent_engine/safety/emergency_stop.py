
# agent_engine/safety/emergency_stop.py

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class EmergencyStopTriggered(RuntimeError):
    """Raised when execution is attempted while JARVIS is stopped."""


class EmergencyStop:
    """
    Process-wide, latched emergency stop.

    - Blocks new side-effecting actions.
    - Signals active workers to stop cooperatively.
    - Persists the stop across application restarts.
    - Requires an explicit reset.
    """

    def __init__(self, lock_file: str | None = None) -> None:
        default_path = Path.home() / ".jarvis" / "emergency_stop.lock"
        self._lock_file = Path(
            lock_file or os.getenv(
                "JARVIS_KILL_SWITCH_FILE", str(default_path)
            )
        )
        self._lock = threading.RLock()
        self._stopped = threading.Event()
        self._reason: str | None = None
        self._callbacks: list[Callable[[], None]] = []

        # Fail closed if the persistent lock cannot be checked.
        try:
            if self._lock_file.exists():
                self._stopped.set()
                self._reason = (
                    self._lock_file.read_text(encoding="utf-8").strip()
                    or "Previous emergency shutdown"
                )
        except OSError as exc:
            self._stopped.set()
            self._reason = f"Cannot verify emergency lock: {exc}"
            logger.critical("%s", self._reason)

    @property
    def is_stopped(self) -> bool:
        return self._stopped.is_set()

    @property
    def reason(self) -> str | None:
        with self._lock:
            return self._reason

    @property
    def cancellation_event(self) -> threading.Event:
        """Workers can wait on this event or check it between operations."""
        return self._stopped

    def register_shutdown_callback(
        self, callback: Callable[[], None]
    ) -> None:
        """Register best-effort cleanup, e.g. release input or stop services."""
        with self._lock:
            if self.is_stopped:
                run_now = True
            else:
                self._callbacks.append(callback)
                run_now = False

        if run_now:
            try:
                callback()
            except Exception:
                logger.exception("Emergency cleanup callback failed")

    def check(self) -> None:
        """Call before scheduling and immediately before every side effect."""
        if self.is_stopped:
            raise EmergencyStopTriggered(
                f"JARVIS emergency stop is active: {self.reason}"
            )

    def trigger(self, reason: str = "Manual emergency stop") -> None:
        """Latch the stop. Safe to call repeatedly from different threads."""
        with self._lock:
            if self.is_stopped:
                return

            # Persist first. If persistence fails, still stop this process.
            self._stopped.set()
            self._reason = reason
            callbacks = list(self._callbacks)
            self._callbacks.clear()

            try:
                self._lock_file.parent.mkdir(
                    parents=True, exist_ok=True
                )
                self._lock_file.write_text(reason, encoding="utf-8")
            except OSError:
                logger.exception(
                    "Could not persist emergency lock; "
                    "JARVIS remains stopped in this process"
                )

        logger.critical("JARVIS EMERGENCY STOP: %s", reason)

        for callback in callbacks:
            try:
                callback()
            except Exception:
                logger.exception("Emergency cleanup callback failed")

    def reset(self, *, confirmed: bool = False) -> None:
        """
        Explicit operator-only reset.

        Do not expose this as an LLM tool or normal automation action.
        """
        if confirmed is not True:
            raise PermissionError(
                "Reset requires explicit operator confirmation."
            )

        with self._lock:
            try:
                self._lock_file.unlink(missing_ok=True)
            except OSError as exc:
                # Remain stopped if persistent state cannot be cleared.
                raise RuntimeError(
                    "Cannot clear emergency lock; JARVIS remains stopped."
                ) from exc

            self._reason = None
            self._stopped.clear()

        logger.warning("Emergency stop reset by explicit operator action")


# One shared controller per Python process.
emergency_stop = EmergencyStop()
