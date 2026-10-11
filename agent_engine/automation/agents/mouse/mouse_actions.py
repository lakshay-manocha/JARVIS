from pynput.mouse import Controller, Button

from .exceptions import (
    InvalidCoordinateError,
    InvalidParameterError,
    MouseInputError,
)


class MouseActions:
    """
    Low-level mouse operations using pynput.
    """

    BUTTON_MAP = {
        "left": Button.left,
        "right": Button.right,
        "middle": Button.middle,
    }

    def __init__(self):
        self.controller = Controller()

    def _validate_coordinates(self, x, y):
        """
        Validate mouse coordinates.
        """

        if not isinstance(x, (int, float)):
            raise InvalidCoordinateError(
                "x must be numeric."
            )

        if not isinstance(y, (int, float)):
            raise InvalidCoordinateError(
                "y must be numeric."
            )

        if x < 0 or y < 0:
            raise InvalidCoordinateError(
                "Mouse coordinates cannot be negative."
            )

    def _resolve_button(self, button):
        """
        Convert button name to pynput Button.
        """

        if not isinstance(button, str):
            raise InvalidParameterError(
                "button must be a string."
            )

        button = button.lower().strip()

        if button not in self.BUTTON_MAP:
            raise InvalidParameterError(
                f"Unsupported mouse button: '{button}'"
            )

        return self.BUTTON_MAP[button]

    def move_mouse(self, x, y):
        """
        Move the mouse cursor.
        """

        self._validate_coordinates(x, y)

        try:
            self.controller.position = (x, y)
        except Exception as exc:
            raise MouseInputError(
                f"Failed to move mouse: {exc}"
            ) from exc

    def click(self, button="left"):
        """
        Perform a single click.
        """

        resolved_button = self._resolve_button(button)

        try:
            self.controller.click(resolved_button)
        except Exception as exc:
            raise MouseInputError(
                f"Failed to click mouse: {exc}"
            ) from exc

    def double_click(self, button="left"):
        """
        Perform a double click.
        """

        resolved_button = self._resolve_button(button)

        try:
            self.controller.click(
                resolved_button,
                count=2,
            )
        except Exception as exc:
            raise MouseInputError(
                f"Failed to double click mouse: {exc}"
            ) from exc

    def right_click(self):
        """
        Perform a right click.
        """

        self.click("right")

    def mouse_down(self, button="left"):
        """
        Press and hold a mouse button.
        """

        resolved_button = self._resolve_button(button)

        try:
            self.controller.press(resolved_button)
        except Exception as exc:
            raise MouseInputError(
                f"Failed to press mouse button: {exc}"
            ) from exc

    def mouse_up(self, button="left"):
        """
        Release a mouse button.
        """

        resolved_button = self._resolve_button(button)

        try:
            self.controller.release(resolved_button)
        except Exception as exc:
            raise MouseInputError(
                f"Failed to release mouse button: {exc}"
            ) from exc

    def scroll(self, dx=0, dy=0):
        """
        Scroll the mouse.

        Positive dy = scroll up.
        Negative dy = scroll down.
        """

        if not isinstance(dx, (int, float)):
            raise InvalidParameterError(
                "dx must be numeric."
            )

        if not isinstance(dy, (int, float)):
            raise InvalidParameterError(
                "dy must be numeric."
            )

        try:
            self.controller.scroll(dx, dy)
        except Exception as exc:
            raise MouseInputError(
                f"Failed to scroll mouse: {exc}"
            ) from exc
