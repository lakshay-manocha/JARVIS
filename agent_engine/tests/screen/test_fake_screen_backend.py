from PIL import Image

from agent_engine.automation.agents.screen.fake_screen_backend import (
    FakeScreenBackend,
)


def test_capture_screen():

    backend = FakeScreenBackend(
        width=1920,
        height=1080,
    )

    result = backend.capture_screen()

    assert result.width == 1920
    assert result.height == 1080
    assert result.image.size == (1920, 1080)


def test_get_screen_size():

    backend = FakeScreenBackend(
        width=1280,
        height=720,
    )

    result = backend.get_screen_size()

    assert result == {
        "width": 1280,
        "height": 720,
    }


def test_capture_region():

    backend = FakeScreenBackend(
        width=1920,
        height=1080,
    )

    result = backend.capture_region(
        x=100,
        y=100,
        width=500,
        height=300,
    )

    assert result["success"] is True
    assert result["image"].size == (500, 300)


def test_invalid_region():

    backend = FakeScreenBackend()

    try:
        backend.capture_region(
            x=0,
            y=0,
            width=0,
            height=100,
        )
        assert False
    except ValueError:
        assert True


def test_region_outside_screen():

    backend = FakeScreenBackend(
        width=1920,
        height=1080,
    )

    try:
        backend.capture_region(
            x=1800,
            y=900,
            width=500,
            height=300,
        )
        assert False
    except ValueError:
        assert True