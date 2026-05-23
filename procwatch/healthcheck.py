"""Health check support for monitored processes."""

import socket
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HealthCheckConfig:
    """Configuration for a process health check."""

    command: Optional[str] = None
    tcp_host: Optional[str] = None
    tcp_port: Optional[int] = None
    interval: float = 10.0
    timeout: float = 5.0
    retries: int = 3

    def is_configured(self) -> bool:
        """Return True if at least one health check method is set."""
        return self.command is not None or (
            self.tcp_host is not None and self.tcp_port is not None
        )


class HealthChecker:
    """Runs health checks against a managed process."""

    def __init__(self, config: HealthCheckConfig) -> None:
        self.config = config
        self._consecutive_failures: int = 0

    def check(self) -> bool:
        """Run the configured health check. Returns True if healthy."""
        if not self.config.is_configured():
            return True

        if self.config.command is not None:
            result = self._check_command()
        else:
            result = self._check_tcp()

        if result:
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1

        return result

    def is_unhealthy(self) -> bool:
        """Return True if failures exceed the retry threshold."""
        return self._consecutive_failures >= self.config.retries

    def reset(self) -> None:
        """Reset failure counter (e.g. after a restart)."""
        self._consecutive_failures = 0

    def _check_command(self) -> bool:
        try:
            result = subprocess.run(
                self.config.command,
                shell=True,
                timeout=self.config.timeout,
                capture_output=True,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    def _check_tcp(self) -> bool:
        try:
            with socket.create_connection(
                (self.config.tcp_host, self.config.tcp_port),
                timeout=self.config.timeout,
            ):
                return True
        except (OSError, socket.timeout):
            return False
