"""Configurable backoff strategies for process restart delays."""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BackoffConfig:
    """Configuration for backoff behavior."""
    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = False


class ExponentialBackoff:
    """Exponential backoff with optional jitter and configurable ceiling."""

    def __init__(self, config: Optional[BackoffConfig] = None):
        self.config = config or BackoffConfig()
        self._attempt = 0
        self._current_delay = self.config.initial_delay

    @property
    def attempt(self) -> int:
        return self._attempt

    def next_delay(self) -> float:
        """Calculate and return the next delay in seconds."""
        delay = min(self._current_delay, self.config.max_delay)

        if self.config.jitter:
            import random
            delay = random.uniform(0, delay)

        self._attempt += 1
        self._current_delay = min(
            self._current_delay * self.config.multiplier,
            self.config.max_delay,
        )
        return delay

    def reset(self) -> None:
        """Reset backoff state after a successful run."""
        self._attempt = 0
        self._current_delay = self.config.initial_delay

    def wait(self) -> float:
        """Block for the next backoff delay. Returns the delay used."""
        delay = self.next_delay()
        time.sleep(delay)
        return delay
