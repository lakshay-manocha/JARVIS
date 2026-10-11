from __future__ import annotations

from enum import Enum


class AgentLifecycleState(str, Enum):
    """
    Lifecycle states for an automation agent.
    """

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    CLEANING_UP = "cleaning_up"
    CLEANED = "cleaned"
    FAILED = "failed"


VALID_LIFECYCLE_TRANSITIONS: dict[
    AgentLifecycleState,
    frozenset[AgentLifecycleState],
] = {
    AgentLifecycleState.CREATED: frozenset(
        {
            AgentLifecycleState.INITIALIZING,
            AgentLifecycleState.CLEANED,
        }
    ),
    AgentLifecycleState.INITIALIZING: frozenset(
        {
            AgentLifecycleState.READY,
            AgentLifecycleState.FAILED,
        }
    ),
    AgentLifecycleState.READY: frozenset(
        {
            AgentLifecycleState.EXECUTING,
            AgentLifecycleState.CLEANING_UP,
            AgentLifecycleState.FAILED,
        }
    ),
    AgentLifecycleState.EXECUTING: frozenset(
        {
            AgentLifecycleState.READY,
            AgentLifecycleState.FAILED,
        }
    ),
    AgentLifecycleState.CLEANING_UP: frozenset(
        {
            AgentLifecycleState.CLEANED,
            AgentLifecycleState.FAILED,
        }
    ),
    AgentLifecycleState.CLEANED: frozenset(),
    AgentLifecycleState.FAILED: frozenset(
        {
            AgentLifecycleState.CLEANING_UP,
            AgentLifecycleState.CLEANED,
        }
    ),
}

def can_transition(
    current: AgentLifecycleState,
    target: AgentLifecycleState,
) -> bool:
    """
    Return whether a lifecycle transition is valid.
    """

    return target in VALID_LIFECYCLE_TRANSITIONS.get(current, frozenset())