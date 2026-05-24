"""Watchdog timer that triggers a callback if a process appears stuck."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class WatchdogConfig:
    """Configuration for the watchdog timer."""

    timeout_seconds: float = 30.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


class Watchdog:
    """Monitors a process heartbeat and fires a callback on timeout."""

    def __init__(
        self,
        config: WatchdogConfig,
        on_timeout: Callable[[str], None],
        name: str = "unknown",
    ) -> None:
        self._config = config
        self._on_timeout = on_timeout
        self._name = name
        self._last_beat: float = time.monotonic()
        self._stopped = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def name(self) -> str:
        return self._name

    def start(self) -> None:
        """Start the watchdog background thread."""
        if not self._config.enabled:
            return
        self._stopped.clear()
        self._last_beat = time.monotonic()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name=f"watchdog-{self._name}"
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the watchdog."""
        self._stopped.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def heartbeat(self) -> None:
        """Reset the watchdog timer — call this to signal the process is alive."""
        self._last_beat = time.monotonic()

    def _run(self) -> None:
        interval = max(1.0, self._config.timeout_seconds / 10)
        while not self._stopped.wait(timeout=interval):
            elapsed = time.monotonic() - self._last_beat
            if elapsed >= self._config.timeout_seconds:
                self._on_timeout(self._name)
                self._last_beat = time.monotonic()
