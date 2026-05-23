"""Periodic metrics reporter that logs a summary of all monitored processes."""

import logging
import threading
from typing import Optional

from procwatch.metrics import MetricsRegistry

logger = logging.getLogger(__name__)


class MetricsReporter:
    """Logs a metrics summary on a fixed interval using a background thread."""

    def __init__(
        self,
        registry: MetricsRegistry,
        interval_seconds: float = 60.0,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self._registry = registry
        self._interval = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background reporting thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="metrics-reporter", daemon=True
        )
        self._thread.start()
        logger.debug("MetricsReporter started (interval=%.1fs)", self._interval)

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the background thread to stop and wait for it to finish."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.debug("MetricsReporter stopped")

    def report_now(self) -> None:
        """Emit a metrics summary immediately (may be called from any thread)."""
        summary = self._registry.summary()
        if not summary:
            logger.info("[procwatch] no processes tracked yet")
            return
        for entry in summary:
            logger.info(
                "[procwatch] process=%s starts=%d failures=%d "
                "last_exit=%s uptime=%.1fs",
                entry["name"],
                entry["start_count"],
                entry["failure_count"],
                entry["last_exit_code"],
                entry["uptime_seconds"] or 0.0,
            )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop_event.wait(timeout=self._interval):
            self.report_now()
