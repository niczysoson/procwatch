"""Structured event log for process lifecycle events."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class EventKind(str, Enum):
    STARTED = "started"
    STOPPED = "stopped"
    FAILED = "failed"
    RESTARTING = "restarting"
    THROTTLED = "throttled"
    HEALTH_FAIL = "health_fail"
    HEALTH_PASS = "health_pass"


@dataclass
class Event:
    kind: EventKind
    process_name: str
    timestamp: float = field(default_factory=time.monotonic)
    reason: Optional[str] = None
    exit_code: Optional[int] = None

    def __str__(self) -> str:
        parts = [f"[{self.kind.value}] {self.process_name}"]
        if self.exit_code is not None:
            parts.append(f"exit={self.exit_code}")
        if self.reason:
            parts.append(self.reason)
        return " | ".join(parts)


class EventLog:
    """In-memory ring buffer of recent process events."""

    def __init__(self, max_events: int = 500) -> None:
        if max_events < 1:
            raise ValueError("max_events must be at least 1")
        self._max = max_events
        self._events: List[Event] = []

    def record(self, event: Event) -> None:
        """Append an event, evicting the oldest if at capacity."""
        if len(self._events) >= self._max:
            self._events.pop(0)
        self._events.append(event)

    def all(self) -> List[Event]:
        """Return a snapshot of all recorded events."""
        return list(self._events)

    def for_process(self, name: str) -> List[Event]:
        """Return events filtered by process name."""
        return [e for e in self._events if e.process_name == name]

    def last(self, n: int = 10) -> List[Event]:
        """Return the n most recent events."""
        return list(self._events[-n:])

    def clear(self) -> None:
        """Remove all recorded events."""
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)
