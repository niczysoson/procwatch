"""Registry for tracking active supervisors by process name."""

from __future__ import annotations

from threading import Lock
from typing import Dict, Iterator, List, Optional

from procwatch.supervisor import Supervisor


class SupervisorRegistry:
    """Thread-safe registry of active Supervisor instances."""

    def __init__(self) -> None:
        self._supervisors: Dict[str, Supervisor] = {}
        self._lock = Lock()

    def register(self, supervisor: Supervisor) -> None:
        """Add a supervisor to the registry.

        Raises ValueError if a supervisor with the same name already exists.
        """
        with self._lock:
            name = supervisor.name
            if name in self._supervisors:
                raise ValueError(f"Supervisor '{name}' is already registered")
            self._supervisors[name] = supervisor

    def unregister(self, name: str) -> None:
        """Remove a supervisor by process name. No-op if not found."""
        with self._lock:
            self._supervisors.pop(name, None)

    def get(self, name: str) -> Optional[Supervisor]:
        """Return the supervisor for the given name, or None."""
        with self._lock:
            return self._supervisors.get(name)

    def all(self) -> List[Supervisor]:
        """Return a snapshot list of all registered supervisors."""
        with self._lock:
            return list(self._supervisors.values())

    def names(self) -> List[str]:
        """Return a snapshot list of all registered process names."""
        with self._lock:
            return list(self._supervisors.keys())

    def __len__(self) -> int:
        with self._lock:
            return len(self._supervisors)

    def __iter__(self) -> Iterator[Supervisor]:
        return iter(self.all())

    def clear(self) -> None:
        """Remove all supervisors from the registry."""
        with self._lock:
            self._supervisors.clear()
