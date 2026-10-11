class AutomationAgentError(Exception):
    """Base exception for automation agents."""


class MouseAgentError(AutomationAgentError):
    """Base exception for mouse-related errors."""


class InvalidActionError(MouseAgentError):
    """Raised when an unsupported mouse action is requested."""


class InvalidParameterError(MouseAgentError):
    """Raised when action parameters are invalid."""


class InvalidCoordinateError(MouseAgentError):
    """Raised when mouse coordinates are invalid."""


class MouseInputError(MouseAgentError):
    """Raised when a mouse operation fails."""


class AgentNotInitializedError(MouseAgentError):
    """Raised when the mouse agent is not initialized."""