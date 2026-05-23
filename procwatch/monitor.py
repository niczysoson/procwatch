"""Process monitor that manages multiple services and handles restarts."""

import asyncio
import logging
from typing import Dict, List, Optional

from procwatch.backoff import BackoffConfig, ExponentialBackoff
from procwatch.process import ManagedProcess, ProcessConfig

logger = logging.getLogger(__name__)


class MonitorConfig:
    """Configuration for the process monitor."""

    def __init__(
        self,
        poll_interval: float = 1.0,
        max_restarts: Optional[int] = None,
        backoff: Optional[BackoffConfig] = None,
    ):
        self.poll_interval = poll_interval
        self.max_restarts = max_restarts
        self.backoff = backoff or BackoffConfig()


class ProcessMonitor:
    """Monitors a collection of managed processes and restarts them on failure."""

    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()
        self._processes: Dict[str, ManagedProcess] = {}
        self._backoffs: Dict[str, ExponentialBackoff] = {}
        self._restart_counts: Dict[str, int] = {}
        self._running = False

    def add_process(self, name: str, proc_config: ProcessConfig) -> None:
        """Register a process to be monitored."""
        self._processes[name] = ManagedProcess(proc_config)
        self._backoffs[name] = ExponentialBackoff(self.config.backoff)
        self._restart_counts[name] = 0
        logger.info("Registered process: %s -> %s", name, proc_config.command)

    def remove_process(self, name: str) -> None:
        """Unregister a process from monitoring."""
        if name in self._processes:
            self._processes.pop(name)
            self._backoffs.pop(name)
            self._restart_counts.pop(name)
            logger.info("Removed process: %s", name)

    @property
    def process_names(self) -> List[str]:
        return list(self._processes.keys())

    async def start_all(self) -> None:
        """Start all registered processes."""
        for name, proc in self._processes.items():
            logger.info("Starting process: %s", name)
            await proc.start()

    async def stop_all(self) -> None:
        """Stop all registered processes and halt monitoring."""
        self._running = False
        for name, proc in self._processes.items():
            logger.info("Stopping process: %s", name)
            await proc.stop()

    async def _handle_restart(self, name: str, proc: ManagedProcess) -> None:
        """Apply backoff delay and restart a failed process."""
        backoff = self._backoffs[name]
        delay = backoff.next_delay()
        self._restart_counts[name] += 1
        logger.warning(
            "Process '%s' exited (restart #%d). Retrying in %.1fs.",
            name,
            self._restart_counts[name],
            delay,
        )
        await asyncio.sleep(delay)
        await proc.start()

    async def run(self) -> None:
        """Start all processes and monitor them in a loop."""
        self._running = True
        await self.start_all()
        while self._running:
            await asyncio.sleep(self.config.poll_interval)
            for name, proc in list(self._processes.items()):
                if not proc.is_running():
                    exit_code = proc.return_code()
                    if not proc.config.should_restart(exit_code):
                        logger.info("Process '%s' exited cleanly, not restarting.", name)
                        continue
                    max_r = self.config.max_restarts
                    if max_r is not None and self._restart_counts[name] >= max_r:
                        logger.error("Process '%s' exceeded max restarts (%d).", name, max_r)
                        continue
                    await self._handle_restart(name, proc)
