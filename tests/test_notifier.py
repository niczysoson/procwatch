"""Tests for procwatch.notifier."""

from unittest.mock import MagicMock, patch

import pytest

from procwatch.notifier import NotifierConfig, ProcessNotifier


class TestNotifierConfig:
    def test_defaults(self):
        cfg = NotifierConfig()
        assert cfg.on_start is None
        assert cfg.on_failure is None
        assert cfg.on_restart is None
        assert cfg.timeout == 5.0

    def test_is_configured_empty(self):
        assert NotifierConfig().is_configured() is False

    def test_is_configured_with_on_start(self):
        assert NotifierConfig(on_start="echo start").is_configured() is True

    def test_is_configured_with_on_failure(self):
        assert NotifierConfig(on_failure="echo fail").is_configured() is True

    def test_is_configured_with_on_restart(self):
        assert NotifierConfig(on_restart="echo restart").is_configured() is True


class TestProcessNotifier:
    def _make_notifier(self, **kwargs) -> ProcessNotifier:
        return ProcessNotifier(NotifierConfig(**kwargs))

    @patch("subprocess.run")
    def test_notify_start_runs_hook(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        notifier = self._make_notifier(on_start="echo {name} {event}")
        notifier.notify_start("myservice")
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "myservice" in cmd
        assert "start" in cmd

    @patch("subprocess.run")
    def test_notify_failure_runs_hook(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        notifier = self._make_notifier(on_failure="alert.sh {name}")
        notifier.notify_failure("svc")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_notify_restart_runs_hook(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        notifier = self._make_notifier(on_restart="log.sh {name}")
        notifier.notify_restart("svc")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_no_hook_no_call(self, mock_run):
        notifier = self._make_notifier()
        notifier.notify_start("svc")
        notifier.notify_failure("svc")
        notifier.notify_restart("svc")
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_nonzero_exit_logs_warning(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="oops")
        notifier = self._make_notifier(on_start="bad-cmd")
        # Should not raise
        notifier.notify_start("svc")
        mock_run.assert_called_once()

    @patch("subprocess.run", side_effect=__import__("subprocess").TimeoutExpired("cmd", 5))
    def test_timeout_logs_warning(self, mock_run):
        notifier = self._make_notifier(on_start="slow-cmd", timeout=5.0)
        # Should not raise
        notifier.notify_start("svc")
