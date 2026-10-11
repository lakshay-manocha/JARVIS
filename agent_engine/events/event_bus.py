"""Phase F-4: lightweight synchronous event bus."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentEvent:
    """Immutable event emitted by the orchestration layer."""

    name: str
    request_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    task_id: int | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)


EventHandler = Callable[[AgentEvent], None]


class EventBus:
    """Thread-safe in-process event bus.

    Event handlers are deliberately synchronous and isolated: one failing
    subscriber cannot stop orchestration or prevent other subscribers from
    receiving the event.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = RLock()

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        if not event_name:
            raise ValueError("event_name cannot be empty")
        with self._lock:
            if handler not in self._handlers[event_name]:
                self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        with self._lock:
            handlers = self._handlers.get(event_name, [])
            if handler in handlers:
                handlers.remove(handler)
            if not handlers and event_name in self._handlers:
                del self._handlers[event_name]

    def publish(self, event: AgentEvent) -> None:
        with self._lock:
            handlers = tuple(self._handlers.get(event.name, ()))
            wildcard = tuple(self._handlers.get("*", ()))

        for handler in handlers + wildcard:
            try:
                handler(event)
            except Exception:
                # Event consumers are observability integrations.  They must
                # never become a hidden execution dependency.
                continue
