"""
===============================================================================
File Name   : enums.py
Module      : Contracts
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
This module contains all global enumerations used across the Agent &
Automation Engine.

The purpose of these enums is to standardize values shared between different
modules such as the Validator, Scheduler, Dispatcher, Controllers, Monitoring,
and Result Generator.

Using enums instead of raw strings ensures:
    • Consistent values throughout the project
    • Better readability
    • IDE auto-completion support
    • Type safety
    • Easier maintenance
    • Reduced runtime errors

Author      : Team Agent
===============================================================================
"""

from enum import Enum


# =============================================================================
# Execution Mode
# =============================================================================

class ExecutionMode(str, Enum):
    """
    Defines how tasks should be executed.
    """

    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"


# =============================================================================
# Task Priority
# =============================================================================

class Priority(str, Enum):
    """
    Represents execution priority of a task.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# =============================================================================
# Task Execution Status
# =============================================================================

class ExecutionStatus(str, Enum):
    """
    Represents the runtime status of a task during execution.
    """

    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    SKIPPED = "SKIPPED"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"

# =============================================================================
# Available Automation Controllers
# =============================================================================

class ToolType(str, Enum):
    """
    Represents available automation controllers.
    """

    DESKTOP = "desktop_agent"
    BROWSER = "browser_agent"
    FILESYSTEM = "filesystem_agent"
    KEYBOARD = "keyboard_agent"
    MOUSE = "mouse_agent"
    SCREEN = "screen_agent"


# =============================================================================
# Action Categories
# =============================================================================

class ActionCategory(str, Enum):
    """
    Groups actions into logical categories.

    These categories are useful for routing actions to the
    appropriate controller and for organizing the Action Registry.
    """

    APPLICATION = "APPLICATION"
    BROWSER = "BROWSER"
    FILESYSTEM = "FILESYSTEM"
    KEYBOARD = "KEYBOARD"
    MOUSE = "MOUSE"
    SCREEN = "SCREEN"


# =============================================================================
# Overall Request Result
# =============================================================================

class ResultStatus(str, Enum):
    """
    Represents the final execution outcome of a complete request.
    """

    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"


# =============================================================================
# Retry Strategy
# =============================================================================

class RetryStrategy(str, Enum):
    """
    Defines retry behavior when an action fails.
    """

    NONE = "NONE"
    IMMEDIATE = "IMMEDIATE"
    EXPONENTIAL_BACKOFF = "EXPONENTIAL_BACKOFF"


# =============================================================================
# Log Levels
# =============================================================================

class LogLevel(str, Enum):
    """
    Standard log levels used throughout the project.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ValidationCode(str, Enum):
    EMPTY_GOAL = "EMPTY_GOAL"
    EMPTY_TASK_LIST = "EMPTY_TASK_LIST"
    EMPTY_TASK_DESCRIPTION = "EMPTY_TASK_DESCRIPTION"
    INVALID_MISSING_INFORMATION = "INVALID_MISSING_INFORMATION"
    INVALID_SUMMARY = "INVALID_SUMMARY"
    MISSING_SUMMARY = "MISSING_SUMMARY"

    SHORT_SUMMARY = "SHORT_SUMMARY"

    DUPLICATE_TASKS = "DUPLICATE_TASKS"

    GOAL_TASK_MISMATCH = "GOAL_TASK_MISMATCH"

class RequestStatus(str, Enum):
    READY = "READY"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RequestSource(str, Enum):
    LLM = "LLM"
    API = "API"
    SYSTEM = "SYSTEM"
    USER = "USER"

class IntentType(str, Enum):
    """
    High-level intent categories detected from user tasks.

    These intents represent what the user wants to accomplish.
    They are intentionally independent from tools or controllers.
    """

    OPEN_APPLICATION = "OPEN_APPLICATION"

    OPEN_WEBSITE = "OPEN_WEBSITE"

    SEARCH_WEB = "SEARCH_WEB"

    DOWNLOAD_FILE = "DOWNLOAD_FILE"

    SUMMARIZE_DOCUMENT = "SUMMARIZE_DOCUMENT"

    DELETE_FILE = "DELETE_FILE"

    MOVE_FILE = "MOVE_FILE"

    COPY_FILE = "COPY_FILE"

    RENAME_FILE = "RENAME_FILE"

    TYPE_TEXT = "TYPE_TEXT"
    PRESS_KEY = "PRESS_KEY"
    HOTKEY = "HOTKEY"

    MOVE_MOUSE = "MOVE_MOUSE"
    MOUSE_CLICK = "MOUSE_CLICK"
    MOUSE_DOUBLE_CLICK = "MOUSE_DOUBLE_CLICK"
    MOUSE_RIGHT_CLICK = "MOUSE_RIGHT_CLICK"
    MOUSE_DOWN = "MOUSE_DOWN"
    MOUSE_UP = "MOUSE_UP"
    MOUSE_SCROLL = "MOUSE_SCROLL"

    UNKNOWN = "UNKNOWN"

# =============================================================================
# Agent Brain Processing Stages
# =============================================================================

class ProcessingStage(str, Enum):
    """
    Represents the current stage of the Agent Brain processing pipeline.
    """

    INITIALIZED = "INITIALIZED"

    VALIDATING = "VALIDATING"

    INTERPRETING = "INTERPRETING"

    NORMALIZING = "NORMALIZING"

    DETECTING_INTENT = "DETECTING_INTENT"

    RESOLVING_ACTIONS = "RESOLVING_ACTIONS"

    RESOLVING_PARAMETERS = "RESOLVING_PARAMETERS"
    PARAMETER_RESOLUTION = "PARAMETER_RESOLUTION"

    RESOLVING_TOOL = "RESOLVING_TOOL"
    TOOL_RESOLUTION = "TOOL_RESOLUTION"

    GRAPH_BUILDING = "GRAPH_BUILDING"

    PLANNING = "PLANNING"

    DISPATCHING = "DISPATCHING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"