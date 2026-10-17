
# agent_engine/safety/emergency_hotkey.py

from __future__ import annotations

import logging
import threading

from agent_engine.safety.emergency_stop import emergency_stop

logger = logging.getLogger(__name__)


def start_emergency_hotkey(
    shutdown_requested: threading.Event,
) -> None:
    """
    Start the global emergency hotkey listener.

    Run this once during application startup. The supplied event should
    be monitored by the main application supervisor.
    """
    try:
        import keyboard
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional 'keyboard' package to enable "
            "the global emergency hotkey."
        ) from exc

    def activate() -> None:
        emergency_stop.trigger(
            "Emergency hotkey Ctrl+Alt+F12 activated"
        )
        shutdown_requested.set()

    keyboard.add_hotkey(
        "ctrl+alt+f12",
        activate,
        suppress=False,
        trigger_on_release=False,
    )

    logger.info(
        "Emergency hotkey registered: Ctrl+Alt+F12"
    )

    # Keep this listener alive in its calling thread.
    # Your application supervisor must monitor shutdown_requested.
    shutdown_requested.wait()
