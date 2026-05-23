"""Periodic metrics reporter for procwatch."""

import logging
import threading
from typing import Optional

from procwatch.metrics import MetricsRegistry

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL = 60  # seconds


class MetricsReporter:
    """Logs metrics for all tracked processes at a fixed interval."""

    def __init__(
        self,
        registry: MetricsRegistry,
        interval: float = DEFAULT_INTERVAL,
    ) -> None:
        self._registry = registry
        self._interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the background reporting thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="metrics-reporter", daemon=True
        )
        self._thread.start()
        logger.debug("MetricsReporter started (interval=%ss)", self._interval)

    def stop(self) -> None:
        """Stop the background reporting thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._interval + 1)
            self._thread = None
        logger.debug("MetricsReporter stopped")

    def report_now(self) -> None:
        """Emit a metrics snapshot immediately (can be called from any thread)."""
        for name, metrics in self._registry.all().items():
            logger.info(
                "[metrics] process=%s starts=%d failures=%d uptime=%.1fs",
                name,
                metrics.start_count,
                metrics.failure_count,
                metrics.uptime_seconds(),
            )

    def _run(self) -> None:
        while not self._stop_event.wait(timeout=self._interval):
            self.report_now()
