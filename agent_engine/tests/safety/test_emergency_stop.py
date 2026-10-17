
from pathlib import Path

import pytest

from agent_engine.safety.emergency_stop import (
    EmergencyStop,
    EmergencyStopTriggered,
)


def test_stop_blocks_execution(tmp_path: Path):
    stop = EmergencyStop(str(tmp_path / "stop.lock"))

    stop.check()
    stop.trigger("test emergency")

    assert stop.is_stopped
    assert stop.reason == "test emergency"

    with pytest.raises(EmergencyStopTriggered):
        stop.check()


def test_stop_is_latched(tmp_path: Path):
    stop = EmergencyStop(str(tmp_path / "stop.lock"))

    stop.trigger("first")
    stop.trigger("second")

    assert stop.is_stopped
    assert stop.reason == "first"


def test_stop_survives_new_controller(tmp_path: Path):
    lock_file = tmp_path / "stop.lock"

    first = EmergencyStop(str(lock_file))
    first.trigger("persisted emergency")

    second = EmergencyStop(str(lock_file))

    assert second.is_stopped

    with pytest.raises(EmergencyStopTriggered):
        second.check()


def test_reset_requires_explicit_confirmation(tmp_path: Path):
    stop = EmergencyStop(str(tmp_path / "stop.lock"))
    stop.trigger("test emergency")

    with pytest.raises(PermissionError):
        stop.reset()

    assert stop.is_stopped


def test_confirmed_reset_clears_lock(tmp_path: Path):
    lock_file = tmp_path / "stop.lock"
    stop = EmergencyStop(str(lock_file))
    stop.trigger("test emergency")

    stop.reset(confirmed=True)

    assert not stop.is_stopped
    assert not lock_file.exists()
    stop.check()


def test_shutdown_callbacks_run_once(tmp_path: Path):
    stop = EmergencyStop(str(tmp_path / "stop.lock"))
    calls = []

    stop.register_shutdown_callback(
        lambda: calls.append("shutdown")
    )

    stop.trigger("test")
    stop.trigger("again")

    assert calls == ["shutdown"]
