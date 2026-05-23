"""Lifecycle manager: wires together monitor, signals, and reporter."""

import logging
import time
from typing import Optional

from procwatch.monitor import ProcessMonitor
from procwatch.reporter import MetricsReporter
from procwatch.signals import SignalHandler

logger = logging.getLogger(__name__)

POLL_INTERVAL = 0.5  # seconds between monitor ticks


class Lifecycle:
    """Coordinates startup, run-loop, and shutdown of procwatch."""

    def __init__(
        self,
        monitor: ProcessMonitor,
        reporter: Optional[MetricsReporter] = None,
        poll_interval: float = POLL_INTERVAL,
    ) -> None:
        self._monitor = monitor
        self._reporter = reporter
        self._poll_interval = poll_interval
        self._signal_handler = SignalHandler(
            on_shutdown=self._request_stop,
            on_reload=self._reload,
        )
        self._running = False

    def run(self) -> None:
        """Start all services and block until shutdown is requested."""
        logger.info("procwatch starting")
        self._signal_handler.register()
        self._monitor.start()
        if self._reporter is not None:
            self._reporter.start()
        self._running = True
        try:
            while self._running and not self._signal_handler.shutdown_requested:
                time.sleep(self._poll_interval)
        finally:
            self._shutdown()

    def _request_stop(self) -> None:
        self._running = False

    def _reload(self) -> None:
        logger.info("Reload requested — re-reading config is not yet implemented")

    def _shutdown(self) -> None:
        logger.info("procwatch shutting down")
        self._monitor.stop()
        if self._reporter is not None:
            self._reporter.stop()
        self._signal_handler.reset()
        logger.info("procwatch stopped")
