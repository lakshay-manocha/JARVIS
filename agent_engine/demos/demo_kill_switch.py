
"""
JARVIS Kill Switch — Safe Live Demo

Run:
    python demo_kill_switch.py

Optional global shortcut:
    Ctrl + Alt + F12

This demo uses a simulated worker. It does not control the
real mouse, keyboard, browser, or operating system.
"""

import logging
import threading
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger("JARVIS-KillSwitch")


def main():
    try:
        from agent_engine.safety.emergency_stop import (
            EmergencyStop,
            EmergencyStopTriggered,
        )
    except ImportError as exc:
        print(f"Could not import the emergency-stop module: {exc}")
        print("Check agent_engine/safety/emergency_stop.py.")
        return

    # Separate lock file: this demo will not latch the real app's lock.
    lock_path = Path.home() / ".jarvis" / "demo_emergency_stop.lock"
    stop = EmergencyStop(str(lock_path))

    if stop.is_stopped:
        print("Demo lock is already active:", stop.reason)
        print("Inspect it before clearing it manually.")
        return

    finished = threading.Event()

    def simulated_task():
        log.info("Task started.")

        try:
            for step in range(1, 31):
                # Every real automation worker needs an equivalent check.
                stop.check()

                log.info("Working... step %d/30", step)

                # Wait can be interrupted immediately by the stop event.
                if stop.cancellation_event.wait(0.7):
                    stop.check()

        except EmergencyStopTriggered as exc:
            log.critical("EMERGENCY STOP: %s", exc)

        finally:
            finished.set()
            log.info("Worker stopped.")

    def trigger_stop(reason):
        stop.trigger(reason)

    # Optional global hotkey.
    try:
        import keyboard

        keyboard.add_hotkey(
            "ctrl+alt+f12",
            lambda: trigger_stop("Ctrl+Alt+F12"),
            suppress=False,
        )
        log.info("Hotkey enabled: Ctrl+Alt+F12")

    except ImportError:
        log.warning(
            "The 'keyboard' package is not installed. "
            "Press Enter in the console to trigger the stop."
        )

    worker = threading.Thread(
        target=simulated_task,
        name="JARVIS-Demo-Worker",
        daemon=True,
    )
    worker.start()

    print("\n" + "=" * 55)
    print("       JARVIS EMERGENCY KILL-SWITCH DEMO")
    print("=" * 55)
    print("A simulated task is now running.")
    print("Press Ctrl+Alt+F12 or Enter to stop it.")
    print("No real computer actions will be performed.")
    print("=" * 55 + "\n")

    try:
        input("Press Enter to activate emergency stop...\n")
        trigger_stop("Console emergency stop")
    except (EOFError, KeyboardInterrupt):
        trigger_stop("Console interrupted")

    worker.join(timeout=5)

    print("\n" + "=" * 55)
    print("EMERGENCY STOP STATUS:", "ACTIVE" if stop.is_stopped else "FAILED")
    print("REASON:", stop.reason)
    print("WORKER EXITED:", finished.is_set())
    print("=" * 55)

    if stop.is_stopped and finished.is_set():
        print("DEMO PASSED: The simulated worker stopped.")
    else:
        print("DEMO FAILED: Investigate the stop controller.")


if __name__ == "__main__":
    main()
