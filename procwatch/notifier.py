"""Event notifier for process state changes."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class NotifierConfig:
    """Configuration for the event notifier."""

    on_start: Optional[str] = None
    on_failure: Optional[str] = None
    on_restart: Optional[str] = None
    timeout: float = 5.0

    def is_configured(self) -> bool:
        """Return True if at least one hook is configured."""
        return any([self.on_start, self.on_failure, self.on_restart])


class ProcessNotifier:
    """Runs shell hooks on process lifecycle events."""

    def __init__(self, config: NotifierConfig) -> None:
        self._config = config

    def _run_hook(self, command: str, process_name: str, event: str) -> None:
        """Execute a shell hook, substituting placeholders."""
        cmd = command.replace("{name}", process_name).replace("{event}", event)
        logger.debug("Running notifier hook: %s", cmd)
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                timeout=self._config.timeout,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.warning(
                    "Notifier hook exited with %d: %s",
                    result.returncode,
                    result.stderr.strip(),
                )
        except subprocess.TimeoutExpired:
            logger.warning("Notifier hook timed out after %.1fs", self._config.timeout)
        except Exception as exc:  # pragma: no cover
            logger.error("Notifier hook error: %s", exc)

    def notify_start(self, process_name: str) -> None:
        """Fire the on_start hook if configured."""
        if self._config.on_start:
            self._run_hook(self._config.on_start, process_name, "start")

    def notify_failure(self, process_name: str) -> None:
        """Fire the on_failure hook if configured."""
        if self._config.on_failure:
            self._run_hook(self._config.on_failure, process_name, "failure")

    def notify_restart(self, process_name: str) -> None:
        """Fire the on_restart hook if configured."""
        if self._config.on_restart:
            self._run_hook(self._config.on_restart, process_name, "restart")
