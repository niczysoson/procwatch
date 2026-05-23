"""Tests for procwatch.signals module."""

import signal
from unittest.mock import MagicMock, patch

import pytest

from procwatch.signals import SignalHandler


class TestSignalHandler:
    def _make_handler(self, on_shutdown=None, on_reload=None):
        return SignalHandler(on_shutdown=on_shutdown, on_reload=on_reload)

    def test_initial_shutdown_requested_is_false(self):
        h = self._make_handler()
        assert h.shutdown_requested is False

    def test_register_sets_signal_handlers(self):
        h = self._make_handler()
        with patch("signal.signal") as mock_signal:
            h.register()
            calls = {c.args[0] for c in mock_signal.call_args_list}
            assert signal.SIGTERM in calls
            assert signal.SIGINT in calls
            assert signal.SIGHUP in calls

    def test_handle_shutdown_sets_flag(self):
        h = self._make_handler()
        h._handle_shutdown(signal.SIGTERM, None)
        assert h.shutdown_requested is True

    def test_handle_shutdown_calls_callback(self):
        cb = MagicMock()
        h = self._make_handler(on_shutdown=cb)
        h._handle_shutdown(signal.SIGTERM, None)
        cb.assert_called_once()

    def test_handle_shutdown_no_callback_no_error(self):
        h = self._make_handler()
        h._handle_shutdown(signal.SIGINT, None)  # should not raise

    def test_handle_reload_calls_callback(self):
        cb = MagicMock()
        h = self._make_handler(on_reload=cb)
        h._handle_reload(signal.SIGHUP, None)
        cb.assert_called_once()

    def test_handle_reload_no_callback_no_error(self):
        h = self._make_handler()
        h._handle_reload(signal.SIGHUP, None)  # should not raise

    def test_reset_clears_shutdown_flag(self):
        h = self._make_handler()
        h._shutdown_requested = True
        with patch("signal.signal"):
            h.reset()
        assert h.shutdown_requested is False

    def test_reset_restores_default_handlers(self):
        h = self._make_handler()
        with patch("signal.signal") as mock_signal:
            h.reset()
            calls = {c.args: c.args[1] for c in mock_signal.call_args_list}
            for args, handler in calls.items():
                assert handler is signal.SIG_DFL
