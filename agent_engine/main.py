import threading

from agent_engine.safety.emergency_stop import emergency_stop
from agent_engine.safety.emergency_hotkey import (
    start_emergency_hotkey,
)


def install_emergency_control(runtime_shutdown):
    shutdown_requested = threading.Event()

    def stop_runtime():
        # This callback must be fast and must not wait for workers.
        shutdown_requested.set()

    emergency_stop.register_shutdown_callback(stop_runtime)

    listener = threading.Thread(
        target=start_emergency_hotkey,
        args=(shutdown_requested,),
        name="jarvis-emergency-hotkey",
        daemon=True,
    )
    listener.start()

    def monitor():
        shutdown_requested.wait()
        emergency_stop.trigger("Runtime shutdown requested")
        runtime_shutdown()

    threading.Thread(
        target=monitor,
        name="jarvis-shutdown-supervisor",
        daemon=True,
    ).start()

    return shutdown_requested