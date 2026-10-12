from datetime import datetime, timezone

from agent_engine.automation.agents.screen.screen_backend import (
    ScreenBackend,
    ScreenCaptureResult,
)
from agent_engine.automation.integration.execution_result_integrator import (
    ExecutionResultIntegrator,
)
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.perception.screen.screen_aware import ScreenAware


class FakeScreenBackend(ScreenBackend):
    def capture_screen(
        self,
        monitor=None,
        all_screens=False,
    ):
        return ScreenCaptureResult(
            image=object(),
            width=800,
            height=600,
            monitor=monitor,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def capture_region(self, x, y, width, height):
        return {
            "success": True,
            "bbox": {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            },
        }

    def get_screen_size(self, monitor=None):
        return {"width": 800, "height": 600}


class FakeOCR:
    def readtext(self, image):
        return [
            (
                [
                    [100, 100],
                    [200, 100],
                    [200, 140],
                    [100, 140],
                ],
                "Settings",
                0.98,
            )
        ]


def test_screen_aware_initializes_without_backend_initializer():
    screen = ScreenAware(
        backend=FakeScreenBackend(),
        ocr=FakeOCR(),
    )

    # A backend without an initialize() method is supported.
    screen.initialize()

    result = screen.capture_screen()

    assert result["success"] is True
    assert result["width"] == 800
    assert result["height"] == 600


def test_visible_element_detection_returns_normalized_result():
    screen = ScreenAware(
        backend=FakeScreenBackend(),
        ocr=FakeOCR(),
    )

    result = screen.detect_visible_elements()

    assert result["success"] is True
    assert result["count"] == 1
    assert result["elements"][0]["type"] == "text"
    assert result["elements"][0]["text"] == "Settings"
    assert result["elements"][0]["center"] == {
        "x": 150,
        "y": 120,
    }


def test_execution_result_integrator_preserves_coordinates():
    expected_output = {
        "found": True,
        "coordinates": {"x": 150, "y": 120},
        "bbox": {
            "x1": 100,
            "y1": 100,
            "x2": 200,
            "y2": 140,
        },
        "confidence": 0.98,
        "method": "ocr",
    }

    result = AutomationExecutionResult(
        task_id=7,
        action="locate_element",
        success=True,
        output=expected_output,
        execution_time=0.05,
        metadata={},
    )

    outcome = ExecutionResultIntegrator().integrate(
        result,
        attempt=1,
    )

    assert outcome.success is True
    assert outcome.output == expected_output
    assert outcome.output["coordinates"] == {
        "x": 150,
        "y": 120,
    }