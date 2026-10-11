from enum import Enum


class DependencyType(str, Enum):
    """
    Defines the semantic relationship between two tasks.
    """

    DATA = "data"

    RESOURCE = "resource"

    STATE = "state"

    CONTEXT = "context"

    EXECUTION = "execution"

    NONE = "none"