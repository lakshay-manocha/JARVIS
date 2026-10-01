from __future__ import annotations

from PIL import ImageGrab


class ScreenCapture:
    """
    Captures the current desktop screen.

    This class intentionally contains no OCR or AI logic.
    """

    def __init__(self, all_screens: bool = True):
        self.all_screens = all_screens

    def capture(self):
        """
        Capture the desktop and return a PIL RGB image.
        """

        image = ImageGrab.grab(
            all_screens=self.all_screens
        )

        if image.mode != "RGB":
            image = image.convert("RGB")

        return image

    def size(self):
        image = self.capture()
        return image.size