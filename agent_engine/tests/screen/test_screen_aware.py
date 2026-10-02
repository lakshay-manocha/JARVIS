from agent_engine.automation.agents.screen.fake_screen_backend import (
    FakeScreenBackend,
)
from agent_engine.perception.screen.screen_aware import (
    ScreenAware,
)


class FakeOCR:

    def readtext(self, image):

        return [
            (
                [
                    [100, 200],
                    [250, 200],
                    [250, 240],
                    [100, 240],
                ],
                "Settings",
                0.94,
            )
        ]


class FakeGroundingModel:

    def locate(self, image, query):

        return {
            "bbox": [800, 400, 1000, 500],
            "confidence": None,
            "method": "vlm",
        }

    def detect_visible_elements(self, image):

        return [
            {
                "type": "button",
                "text": "Login",
                "bbox": [700, 500, 850, 550],
                "confidence": 0.87,
            },
            {
                "type": "text",
                "text": "Settings",
                "bbox": [100, 200, 250, 240],
                "confidence": 0.93,
            },
        ]


def create_screen():

    return ScreenAware(
        backend=FakeScreenBackend(
            width=1920,
            height=1080,
        ),
        ocr=FakeOCR(),
        grounding_model=FakeGroundingModel(),
    )


def test_locate_text():

    screen = create_screen()

    result = screen.locate_text("Settings")

    assert result["found"] is True
    assert result["method"] == "ocr"
    assert result["confidence"] == 0.94

    assert result["center"] == {
        "x": 175,
        "y": 220,
    }


def test_locate_text_not_found():

    class EmptyOCR:

        def readtext(self, image):
            return []

    screen = ScreenAware(
        backend=FakeScreenBackend(),
        ocr=EmptyOCR(),
    )

    result = screen.locate_text("Settings")

    assert result["found"] is False
    assert result["bbox"] is None
    assert result["confidence"] is None


def test_locate_element():

    screen = create_screen()

    result = screen.locate_element(
        "login button"
    )

    assert result["found"] is True
    assert result["method"] == "vlm"

    assert result["center"] == {
        "x": 900,
        "y": 450,
    }


def test_detect_visible_elements():

    screen = create_screen()

    results = screen.detect_visible_elements()

    assert len(results) == 2

    assert results[0]["type"] == "button"
    assert results[0]["center"] == {
        "x": 775,
        "y": 525,
    }


def test_invalid_bbox_is_rejected():

    class InvalidGrounding:

        def locate(self, image, query):

            return {
                "bbox": [-10, 100, 200, 200],
                "confidence": None,
            }

    screen = ScreenAware(
        backend=FakeScreenBackend(),
        grounding_model=InvalidGrounding(),
    )

    try:
        screen.locate_element("button")
        assert False
    except ValueError:
        assert True