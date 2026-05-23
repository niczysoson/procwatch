"""Signal handling for graceful shutdown and reload of procwatch."""

import logging
import signal
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class SignalHandler:
    """Manages OS signal handling for the process monitor."""

    def __init__(
        self,
        on_shutdown: Optional[Callable[[], None]] = None,
        on_reload: Optional[Callable[[], None]] = None,
    ) -> None:
        self._on_shutdown = on_shutdown
        self._on_reload = on_reload
        self._shutdown_requested = False

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    def register(self) -> None:
        """Register signal handlers for SIGTERM, SIGINT, and SIGHUP."""
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGHUP, self._handle_reload)
        logger.debug("Signal handlers registered (SIGTERM, SIGINT, SIGHUP)")

    def _handle_shutdown(self, signum: int, frame: object) -> None:
        sig_name = signal.Signals(signum).name
        logger.info("Received %s, initiating graceful shutdown", sig_name)
        self._shutdown_requested = True
        if self._on_shutdown is not None:
            self._on_shutdown()

    def _handle_reload(self, signum: int, frame: object) -> None:
        logger.info("Received SIGHUP, triggering reload")
        if self._on_reload is not None:
            self._on_reload()

    def reset(self) -> None:
        """Restore default signal handlers."""
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGHUP, signal.SIG_DFL)
        self._shutdown_requested = False
        logger.debug("Signal handlers reset to defaults")
