"""Tests for procwatch.watchdog."""

from __future__ import annotations

import time
import threading
from unittest.mock import MagicMock

import pytest

from procwatch.watchdog import Watchdog, WatchdogConfig


class TestWatchdogConfig:
    def test_defaults(self):
        cfg = WatchdogConfig()
        assert cfg.timeout_seconds == 30.0
        assert cfg.enabled is True

    def test_custom_values(self):
        cfg = WatchdogConfig(timeout_seconds=10.0, enabled=False)
        assert cfg.timeout_seconds == 10.0
        assert cfg.enabled is False

    def test_invalid_timeout(self):
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            WatchdogConfig(timeout_seconds=0)

    def test_negative_timeout(self):
        with pytest.raises(ValueError):
            WatchdogConfig(timeout_seconds=-5.0)


class TestWatchdog:
    def _make_watchdog(self, timeout=1.0, enabled=True):
        callback = MagicMock()
        cfg = WatchdogConfig(timeout_seconds=timeout, enabled=enabled)
        wd = Watchdog(cfg, on_timeout=callback, name="test-proc")
        return wd, callback

    def test_name(self):
        wd, _ = self._make_watchdog()
        assert wd.name == "test-proc"

    def test_start_stop_no_timeout(self):
        wd, callback = self._make_watchdog(timeout=5.0)
        wd.start()
        time.sleep(0.05)
        wd.stop()
        callback.assert_not_called()

    def test_disabled_watchdog_does_not_start_thread(self):
        wd, callback = self._make_watchdog(enabled=False)
        wd.start()
        assert wd._thread is None
        callback.assert_not_called()

    def test_heartbeat_resets_timer(self):
        wd, callback = self._make_watchdog(timeout=0.3)
        wd.start()
        for _ in range(5):
            time.sleep(0.1)
            wd.heartbeat()
        wd.stop()
        callback.assert_not_called()

    def test_timeout_fires_callback(self):
        fired = threading.Event()

        def on_timeout(name):
            fired.set()

        cfg = WatchdogConfig(timeout_seconds=0.2)
        wd = Watchdog(cfg, on_timeout=on_timeout, name="slow-proc")
        wd.start()
        assert fired.wait(timeout=2.0), "Watchdog callback was not fired"
        wd.stop()

    def test_timeout_callback_receives_name(self):
        callback = MagicMock()
        cfg = WatchdogConfig(timeout_seconds=0.2)
        wd = Watchdog(cfg, on_timeout=callback, name="my-service")
        wd.start()
        time.sleep(0.5)
        wd.stop()
        callback.assert_called_with("my-service")

    def test_stop_is_idempotent(self):
        wd, _ = self._make_watchdog()
        wd.start()
        wd.stop()
        wd.stop()  # should not raise
