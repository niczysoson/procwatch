"""Restart throttling: prevent rapid restart loops by tracking restart rate."""

from dataclasses import dataclass, field
from collections import deque
from time import monotonic
from typing import Deque


@dataclass
class ThrottleConfig:
    """Configuration for restart throttling."""
    max_restarts: int = 5
    window_seconds: float = 60.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.max_restarts < 1:
            raise ValueError("max_restarts must be at least 1")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")


class RestartThrottle:
    """Tracks restart timestamps and determines if a process is restart-throttled."""

    def __init__(self, config: ThrottleConfig) -> None:
        self._config = config
        self._timestamps: Deque[float] = deque()

    def record_restart(self) -> None:
        """Record a restart event at the current time."""
        now = monotonic()
        self._timestamps.append(now)
        self._evict_old(now)

    def is_throttled(self) -> bool:
        """Return True if the restart rate exceeds the configured threshold."""
        if not self._config.enabled:
            return False
        now = monotonic()
        self._evict_old(now)
        return len(self._timestamps) >= self._config.max_restarts

    def restart_count_in_window(self) -> int:
        """Return the number of restarts recorded within the current window."""
        self._evict_old(monotonic())
        return len(self._timestamps)

    def reset(self) -> None:
        """Clear all recorded restart timestamps."""
        self._timestamps.clear()

    def _evict_old(self, now: float) -> None:
        cutoff = now - self._config.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
