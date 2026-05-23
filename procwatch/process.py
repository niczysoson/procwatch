import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List
from procwatch.backoff import ExponentialBackoff, BackoffConfig

logger = logging.getLogger(__name__)


@dataclass
class ProcessConfig:
    name: str
    command: List[str]
    backoff: BackoffConfig = field(default_factory=BackoffConfig)
    max_restarts: int = 5
    restart_on_exit_codes: Optional[List[int]] = None

    def should_restart(self, exit_code: int) -> bool:
        if self.restart_on_exit_codes is None:
            return exit_code != 0
        return exit_code in self.restart_on_exit_codes


class ManagedProcess:
    def __init__(self, config: ProcessConfig):
        self.config = config
        self.backoff = ExponentialBackoff(config.backoff)
        self._process: Optional[subprocess.Popen] = None
        self.restart_count: int = 0
        self.running: bool = False

    def start(self) -> None:
        logger.info("Starting process '%s': %s", self.config.name, self.config.command)
        self._process = subprocess.Popen(
            self.config.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.running = True
        logger.info("Process '%s' started with PID %d", self.config.name, self._process.pid)

    def stop(self) -> None:
        if self._process and self._process.poll() is None:
            logger.info("Stopping process '%s' (PID %d)", self.config.name, self._process.pid)
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Force killing process '%s'", self.config.name)
                self._process.kill()
        self.running = False

    def poll(self) -> Optional[int]:
        if self._process is None:
            return None
        return self._process.poll()

    def monitor(self) -> None:
        self.start()
        while self.running:
            exit_code = self.poll()
            if exit_code is not None:
                logger.warning(
                    "Process '%s' exited with code %d (restarts: %d/%d)",
                    self.config.name, exit_code, self.restart_count, self.config.max_restarts
                )
                if not self.config.should_restart(exit_code):
                    logger.info("Process '%s' exited cleanly, not restarting.", self.config.name)
                    self.running = False
                    break
                if self.restart_count >= self.config.max_restarts:
                    logger.error("Process '%s' exceeded max restarts.", self.config.name)
                    self.running = False
                    break
                delay = self.backoff.next_delay()
                logger.info("Restarting '%s' in %.2fs...", self.config.name, delay)
                time.sleep(delay)
                self.restart_count += 1
                self.backoff.attempt()
                self.start()
            else:
                time.sleep(0.5)
