"""Supervisor: coordinates process lifecycle with backoff, throttle, and watchdog."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from procwatch.backoff import ExponentialBackoff
from procwatch.metrics import MetricsRegistry
from procwatch.process import ManagedProcess, ProcessConfig
from procwatch.throttle import RestartThrottle, ThrottleConfig
from procwatch.watchdog import Watchdog, WatchdogConfig

logger = logging.getLogger(__name__)


@dataclass
class SupervisorConfig:
    """Configuration for a single supervised process."""

    process: ProcessConfig
    throttle: ThrottleConfig = field(default_factory=ThrottleConfig)
    watchdog: WatchdogConfig = field(default_factory=WatchdogConfig)


class Supervisor:
    """Manages a single process: starts it, watches it, and restarts on failure."""

    def __init__(
        self,
        config: SupervisorConfig,
        backoff: ExponentialBackoff,
        registry: Optional[MetricsRegistry] = None,
    ) -> None:
        self._config = config
        self._backoff = backoff
        self._throttle = RestartThrottle(config.throttle)
        self._watchdog = Watchdog(config.watchdog)
        self._registry = registry
        self._process: Optional[ManagedProcess] = None
        self._stopped = False

    @property
    def name(self) -> str:
        return self._config.process.name

    def start(self) -> None:
        """Launch the managed process and begin supervision."""
        self._stopped = False
        self._launch()

    def stop(self) -> None:
        """Signal the supervisor to stop and terminate the process."""
        self._stopped = True
        if self._process is not None:
            self._process.stop()
            logger.info("Supervisor stopped process '%s'", self.name)

    def tick(self) -> None:
        """Called periodically to check process health and restart if needed."""
        if self._stopped or self._process is None:
            return

        if self._watchdog.is_configured() and not self._watchdog.check(self._process):
            logger.warning("Watchdog triggered for '%s', restarting", self.name)
            self._process.stop()

        if not self._process.is_running():
            exit_code = self._process.returncode
            if self._config.process.should_restart(exit_code):
                self._attempt_restart(exit_code)

    def _launch(self) -> None:
        self._process = ManagedProcess(self._config.process)
        self._process.start()
        if self._registry:
            self._registry.get(self.name).record_start()
        logger.info("Supervisor launched '%s'", self.name)

    def _attempt_restart(self, exit_code: Optional[int]) -> None:
        if not self._throttle.allow_restart():
            logger.error("Throttle limit reached for '%s', not restarting", self.name)
            self._stopped = True
            return

        delay = self._backoff.next_delay()
        logger.info(
            "Process '%s' exited (code=%s), restarting in %.1fs",
            self.name,
            exit_code,
            delay,
        )
        time.sleep(delay)
        self._throttle.record_restart()
        if self._registry:
            self._registry.get(self.name).record_failure()
        self._launch()
