class AutomationAgentError(Exception):
    """Base exception for all automation agents."""
    pass


class KeyboardAgentError(AutomationAgentError):
    """Base exception for keyboard automation errors."""
    pass


class InvalidActionError(KeyboardAgentError):
    """Raised when an unsupported keyboard action is requested."""
    pass


class InvalidParameterError(KeyboardAgentError):
    """Raised when action parameters are invalid."""
    pass


class UnsupportedKeyError(KeyboardAgentError):
    """Raised when a requested key is not supported."""
    pass


class KeyboardInputError(KeyboardAgentError):
    """Raised when the OS keyboard operation fails."""
    pass


class AgentNotInitializedError(KeyboardAgentError):
    """Raised when execution is attempted before initialization."""
    pass