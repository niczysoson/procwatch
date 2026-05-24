"""Managed process definition and state."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

from procwatch.backoff import BackoffConfig
from procwatch.healthcheck import HealthCheckConfig
from procwatch.notifier import NotifierConfig

logger = logging.getLogger(__name__)


@dataclass
class ProcessConfig:
    """Static configuration for a managed process."""

    name: str
    command: str
    restart_on_failure: bool = True
    restart_codes: List[int] = field(default_factory=list)
    backoff: BackoffConfig = field(default_factory=BackoffConfig)
    healthcheck: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    notifier: NotifierConfig = field(default_factory=NotifierConfig)

    def should_restart(self, exit_code: int) -> bool:
        """Return True if the process should be restarted given exit_code."""
        if self.restart_codes:
            return exit_code in self.restart_codes
        return self.restart_on_failure and exit_code != 0


class ManagedProcess:
    """Wraps a subprocess and manages its lifecycle."""

    def __init__(self, config: ProcessConfig) -> None:
        self._config = config
        self._process: Optional[subprocess.Popen] = None
        self._notifier_inst = __import__(
            "procwatch.notifier", fromlist=["ProcessNotifier"]
        ).ProcessNotifier(config.notifier)

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def config(self) -> ProcessConfig:
        return self._config

    def start(self) -> None:
        """Start the underlying process."""
        logger.info("Starting process: %s", self._config.name)
        self._process = subprocess.Popen(
            self._config.command,
            shell=True,
        )
        self._notifier_inst.notify_start(self._config.name)

    def poll(self) -> Optional[int]:
        """Return exit code if process has terminated, else None."""
        if self._process is None:
            return None
        return self._process.poll()

    def stop(self) -> None:
        """Terminate the process if running."""
        if self._process and self._process.poll() is None:
            logger.info("Stopping process: %s", self._config.name)
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def notify_failure(self) -> None:
        """Fire failure notification hook."""
        self._notifier_inst.notify_failure(self._config.name)

    def notify_restart(self) -> None:
        """Fire restart notification hook."""
        self._notifier_inst.notify_restart(self._config.name)
