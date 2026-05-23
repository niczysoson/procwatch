"""Tests for procwatch.lifecycle module."""

from unittest.mock import MagicMock, call, patch

import pytest

from procwatch.lifecycle import Lifecycle


def _make_lifecycle(with_reporter=False, poll_interval=0.01):
    monitor = MagicMock()
    reporter = MagicMock() if with_reporter else None
    lc = Lifecycle(monitor=monitor, reporter=reporter, poll_interval=poll_interval)
    return lc, monitor, reporter


class TestLifecycle:
    def test_run_starts_monitor(self):
        lc, monitor, _ = _make_lifecycle()
        # Trigger immediate shutdown via signal handler
        with patch.object(lc._signal_handler, "register"):
            lc._signal_handler._shutdown_requested = True
            lc.run()
        monitor.start.assert_called_once()

    def test_run_stops_monitor_on_exit(self):
        lc, monitor, _ = _make_lifecycle()
        with patch.object(lc._signal_handler, "register"):
            lc._signal_handler._shutdown_requested = True
            lc.run()
        monitor.stop.assert_called_once()

    def test_run_starts_reporter_when_present(self):
        lc, _, reporter = _make_lifecycle(with_reporter=True)
        with patch.object(lc._signal_handler, "register"):
            lc._signal_handler._shutdown_requested = True
            lc.run()
        reporter.start.assert_called_once()

    def test_run_stops_reporter_when_present(self):
        lc, _, reporter = _make_lifecycle(with_reporter=True)
        with patch.object(lc._signal_handler, "register"):
            lc._signal_handler._shutdown_requested = True
            lc.run()
        reporter.stop.assert_called_once()

    def test_run_without_reporter_no_error(self):
        lc, _, reporter = _make_lifecycle(with_reporter=False)
        assert reporter is None
        with patch.object(lc._signal_handler, "register"):
            lc._signal_handler._shutdown_requested = True
            lc.run()  # should not raise

    def test_request_stop_sets_running_false(self):
        lc, _, _ = _make_lifecycle()
        lc._running = True
        lc._request_stop()
        assert lc._running is False

    def test_shutdown_resets_signal_handler(self):
        lc, _, _ = _make_lifecycle()
        with patch.object(lc._signal_handler, "reset") as mock_reset:
            lc._monitor = MagicMock()
            lc._shutdown()
            mock_reset.assert_called_once()
