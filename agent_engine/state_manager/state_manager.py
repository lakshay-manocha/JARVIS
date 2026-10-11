"""
===============================================================================
File Name   : state_manager.py
Module      : State Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides centralized runtime state management for executable tasks.

Phase E:
    E-1 - State Manager Foundation.
    E-2 - Runtime State Updates.
    E-3 - State Transition Enforcement.
    E-4 - State History.
    E-5 - Checkpoint Handling.

The State Manager owns TaskRuntimeState objects, state transition history,
and immutable runtime checkpoints.

It does not execute tasks, make decisions, or perform orchestration.

Responsibilities:
    - Register tasks
    - Initialize runtime state
    - Read task state
    - Update task state
    - Enforce state transitions
    - Record state transition history
    - Read state history
    - Create runtime checkpoints
    - Read runtime checkpoints
    - Restore runtime checkpoints
    - Remove task state, history, and checkpoints
    - Clear all runtime state, history, and checkpoints

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.contracts.task_status import TaskRuntimeState
from agent_engine.state_manager.state_checkpoint import StateCheckpoint
from agent_engine.state_manager.state_history import StateHistoryEntry
from agent_engine.state_manager.state_transitions import (
    StateTransitionPolicy,
)


class StateManager:
    """
    Central owner of runtime task states, state history, and checkpoints.

    The State Manager maintains:

        - one TaskRuntimeState object per task ID
        - one ordered history sequence per task
        - one ordered checkpoint sequence per task

    It is deliberately independent from:

        - Task execution
        - Decision Manager
        - Planner
        - Graph Builder
        - Automation Controllers

    Those components may request or consume state information, but the
    State Manager owns runtime state, history, and checkpoints.
    """

    def __init__(self) -> None:
        """
        Initialize empty runtime state, history, and checkpoint registries.
        """

        self._states: dict[int, TaskRuntimeState] = {}

        self._history: dict[
            int,
            list[StateHistoryEntry],
        ] = {}

        self._checkpoints: dict[
            int,
            list[StateCheckpoint],
        ] = {}

    # =========================================================================
    # Registration
    # =========================================================================

    def register_task(self, task_id: int) -> TaskRuntimeState:
        """
        Register a task with an initial PENDING state.

        If the task is already registered, its existing state is returned
        unchanged and no duplicate history or checkpoint entry is created.

        Registration is idempotent.
        """

        if task_id in self._states:
            return self._states[task_id]

        state = TaskRuntimeState(
            task_id=task_id,
            status=ExecutionStatus.PENDING,
        )

        self._states[task_id] = state
        self._history[task_id] = []
        self._checkpoints[task_id] = []

        self._record_history(
            task_id=task_id,
            from_status=None,
            to_status=ExecutionStatus.PENDING,
        )

        return state

    def register_tasks(
        self,
        task_ids: list[int],
    ) -> list[TaskRuntimeState]:
        """
        Register multiple tasks with an initial PENDING state.

        Existing tasks are preserved and are not reset.

        Registration is idempotent.
        """

        states: list[TaskRuntimeState] = []

        for task_id in task_ids:
            state = self.register_task(task_id)
            states.append(state)

        return states

    # =========================================================================
    # State Access
    # =========================================================================

    def get_state(self, task_id: int) -> TaskRuntimeState:
        """
        Return the complete runtime state for a task.

        Raises:
            KeyError:
                If the task has not been registered.
        """

        if task_id not in self._states:
            raise KeyError(
                f"Task {task_id} is not registered with the State Manager."
            )

        return self._states[task_id]

    def get_status(self, task_id: int) -> ExecutionStatus:
        """
        Return only the current execution status of a task.
        """

        return self.get_state(task_id).status

    # =========================================================================
    # State Mutation
    # =========================================================================

    def set_state(
        self,
        task_id: int,
        status: ExecutionStatus,
    ) -> TaskRuntimeState:
        """
        Transition a registered task to a new execution status.

        Normal execution transitions are validated by StateTransitionPolicy.

        A history entry is created only when the state actually changes.

        Invalid transitions do not modify runtime state and do not create
        history entries.
        """

        state = self.get_state(task_id)

        current_status = state.status

        StateTransitionPolicy.validate_transition(
            current_status,
            status,
        )

        if current_status == status:
            return state

        state.status = status

        self._record_history(
            task_id=task_id,
            from_status=current_status,
            to_status=status,
        )

        return state

    def update_state(
        self,
        task_id: int,
        **updates,
    ) -> TaskRuntimeState:
        """
        Update one or more runtime state fields.

        Status updates are routed through set_state() so that all
        normal execution state transitions are validated consistently.

        Only actual status changes are recorded in state history.
        """

        state = self.get_state(task_id)

        allowed_fields = {
            "status",
            "retry_count",
            "progress",
            "started_at",
            "completed_at",
            "execution_time",
            "error_message",
            "error_code",
        }

        unknown_fields = set(updates) - allowed_fields

        if unknown_fields:
            raise ValueError(
                "Unknown runtime state field(s): "
                + ", ".join(sorted(unknown_fields))
            )

        if "status" in updates:
            self.set_state(
                task_id,
                updates.pop("status"),
            )

        for field_name, value in updates.items():
            setattr(state, field_name, value)

        return state

    # =========================================================================
    # State History
    # =========================================================================

    def get_history(
        self,
        task_id: int,
    ) -> tuple[StateHistoryEntry, ...]:
        """
        Return the complete state history for a task.

        History entries are returned as an immutable tuple.

        Raises:
            KeyError:
                If the task has not been registered.
        """

        if task_id not in self._states:
            raise KeyError(
                f"Task {task_id} is not registered with the State Manager."
            )

        return tuple(self._history[task_id])

    def history(self) -> Mapping[
        int,
        tuple[StateHistoryEntry, ...],
    ]:
        """
        Return a read-only view of all task histories.
        """

        history_snapshot = {
            task_id: tuple(entries)
            for task_id, entries in self._history.items()
        }

        return MappingProxyType(history_snapshot)

    def _record_history(
        self,
        task_id: int,
        from_status: ExecutionStatus | None,
        to_status: ExecutionStatus,
    ) -> None:
        """
        Record a single state history entry.
        """

        entry = StateHistoryEntry(
            task_id=task_id,
            from_status=from_status,
            to_status=to_status,
            timestamp=datetime.now(),
        )

        self._history[task_id].append(entry)

    # =========================================================================
    # E-5 Checkpoint Handling
    # =========================================================================

    def create_checkpoint(
        self,
        task_id: int,
    ) -> StateCheckpoint:
        """
        Create an immutable snapshot of the current runtime state.

        The checkpoint captures all runtime fields at the moment the method
        is called.

        The checkpoint is stored in the task's checkpoint history.

        Raises:
            KeyError:
                If the task has not been registered.
        """

        state = self.get_state(task_id)

        checkpoint = StateCheckpoint(
            task_id=state.task_id,
            status=state.status,
            retry_count=state.retry_count,
            progress=state.progress,
            started_at=state.started_at,
            completed_at=state.completed_at,
            execution_time=state.execution_time,
            error_message=state.error_message,
            error_code=state.error_code,
            timestamp=datetime.now(),
        )

        self._checkpoints[task_id].append(checkpoint)

        return checkpoint

    def get_checkpoint(
        self,
        task_id: int,
    ) -> StateCheckpoint:
        """
        Return the most recently created checkpoint for a task.

        Raises:
            KeyError:
                If the task is not registered or has no checkpoint.
        """

        if task_id not in self._states:
            raise KeyError(
                f"Task {task_id} is not registered with the State Manager."
            )

        if not self._checkpoints[task_id]:
            raise KeyError(
                f"Task {task_id} has no checkpoint."
            )

        return self._checkpoints[task_id][-1]

    def get_checkpoints(
        self,
        task_id: int,
    ) -> tuple[StateCheckpoint, ...]:
        """
        Return all checkpoints for a task in creation order.

        The returned tuple is immutable.

        Raises:
            KeyError:
                If the task is not registered.
        """

        if task_id not in self._states:
            raise KeyError(
                f"Task {task_id} is not registered with the State Manager."
            )

        return tuple(self._checkpoints[task_id])

    def checkpoints(
        self,
    ) -> Mapping[
        int,
        tuple[StateCheckpoint, ...],
    ]:
        """
        Return a read-only snapshot of all task checkpoints.

        Both the registry mapping and checkpoint sequences are protected
        from external mutation.
        """

        checkpoint_snapshot = {
            task_id: tuple(entries)
            for task_id, entries in self._checkpoints.items()
        }

        return MappingProxyType(checkpoint_snapshot)

    def restore_checkpoint(
        self,
        task_id: int,
        checkpoint: StateCheckpoint,
    ) -> TaskRuntimeState:
        """
        Restore a task from an existing checkpoint.

        Checkpoint restoration is a recovery operation rather than a normal
        forward execution transition.

        Therefore restoration does NOT use the normal E-3 transition policy.
        A checkpoint may legitimately restore an earlier valid execution
        state, such as:

            RUNNING -> READY
            FAILED -> RUNNING
            WAITING -> RUNNING

        These transitions remain illegal through set_state() because they
        are not normal forward execution transitions.

        The checkpoint must belong to the requested task.

        If the restored status differs from the current status, the
        restoration is recorded in state history.

        Raises:
            KeyError:
                If the task is not registered.

            ValueError:
                If the checkpoint belongs to another task.
        """

        state = self.get_state(task_id)

        if checkpoint.task_id != task_id:
            raise ValueError(
                "Checkpoint task ID does not match the requested task."
            )

        current_status = state.status

        # ---------------------------------------------------------------------
        # Checkpoint restoration intentionally bypasses normal E-3 transition
        # validation. A checkpoint represents a previously recorded runtime
        # state and restoration is a recovery operation, not normal forward
        # execution.
        # ---------------------------------------------------------------------

        if current_status != checkpoint.status:
            state.status = checkpoint.status

            self._record_history(
                task_id=task_id,
                from_status=current_status,
                to_status=checkpoint.status,
            )

        # ---------------------------------------------------------------------
        # Restore all remaining runtime fields from the immutable snapshot.
        # ---------------------------------------------------------------------

        state.retry_count = checkpoint.retry_count
        state.progress = checkpoint.progress
        state.started_at = checkpoint.started_at
        state.completed_at = checkpoint.completed_at
        state.execution_time = checkpoint.execution_time
        state.error_message = checkpoint.error_message
        state.error_code = checkpoint.error_code

        return state

    # =========================================================================
    # Registry Inspection
    # =========================================================================

    def has_task(self, task_id: int) -> bool:
        """
        Return whether a task is registered.
        """

        return task_id in self._states

    def task_ids(self) -> list[int]:
        """
        Return all registered task IDs.
        """

        return list(self._states.keys())

    def states(self) -> Mapping[int, TaskRuntimeState]:
        """
        Return a read-only view of all registered runtime states.
        """

        return MappingProxyType(self._states)

    # =========================================================================
    # Removal
    # =========================================================================

    def remove_task(self, task_id: int) -> None:
        """
        Remove the task from the runtime state, history, and checkpoint
        registries.

        Raises:
            KeyError:
                If the task has not been registered.
        """

        if task_id not in self._states:
            raise KeyError(
                f"Task {task_id} is not registered with the State Manager."
            )

        del self._states[task_id]
        del self._history[task_id]
        del self._checkpoints[task_id]

    def clear(self) -> None:
        """
        Remove all runtime task states, histories, and checkpoints.
        """

        self._states.clear()
        self._history.clear()
        self._checkpoints.clear()

    # =========================================================================
    # E-6 Pause / Resume
    # =========================================================================

    def pause_task(
        self,
        task_id: int,
    ) -> StateCheckpoint:
        """
        Pause a running task and create a checkpoint representing the
        last active execution state.

        The checkpoint is created before the state changes to PAUSED.

        Lifecycle:

            RUNNING -> checkpoint(RUNNING) -> PAUSED

        Returns:
            StateCheckpoint:
                The checkpoint created immediately before pausing.
        """

        state = self.get_state(task_id)

        if state.status != ExecutionStatus.RUNNING:
            StateTransitionPolicy.validate_transition(
                state.status,
                ExecutionStatus.PAUSED,
            )

        checkpoint = self.create_checkpoint(task_id)

        self.set_state(
            task_id,
            ExecutionStatus.PAUSED,
        )

        return checkpoint
    
    def resume_task(
        self,
        task_id: int,
    ) -> TaskRuntimeState:
        """
        Resume a paused task from its latest checkpoint.

        The latest checkpoint is used to restore the runtime fields captured
        immediately before the task was paused.

        The checkpoint's status is intentionally not restored. The task must
        transition through:

            PAUSED -> RUNNING

        using the normal state transition policy.

        Returns:
            TaskRuntimeState:
                The resumed runtime state.

        Raises:
            KeyError:
                If the task is not registered or has no checkpoint.

            InvalidStateTransitionError:
                If the task is not currently PAUSED.
        """

        state = self.get_state(task_id)

        StateTransitionPolicy.validate_transition(
            state.status,
            ExecutionStatus.RUNNING,
        )

        checkpoint = self.get_checkpoint(task_id)

        state.retry_count = checkpoint.retry_count
        state.progress = checkpoint.progress
        state.started_at = checkpoint.started_at
        state.completed_at = checkpoint.completed_at
        state.execution_time = checkpoint.execution_time
        state.error_message = checkpoint.error_message
        state.error_code = checkpoint.error_code

        self.set_state(
            task_id,
            ExecutionStatus.RUNNING,
        )

        return state

    def stop_task(
        self,
        task_id: int,
    ) -> TaskRuntimeState:
        """
        Stop a task from a non-terminal executable state.

        STOPPED is a terminal state.

        Returns:
            TaskRuntimeState:
                The stopped runtime state.

        Raises:
            KeyError:
                If the task is not registered.

            InvalidStateTransitionError:
                If stopping the task is not permitted from its current state.
        """

        return self.set_state(
            task_id,
            ExecutionStatus.STOPPED,
        )