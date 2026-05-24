"""Tests for procwatch.supervisor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from procwatch.backoff import BackoffConfig, ExponentialBackoff
from procwatch.metrics import MetricsRegistry
from procwatch.process import ProcessConfig
from procwatch.supervisor import Supervisor, SupervisorConfig
from procwatch.throttle import ThrottleConfig
from procwatch.watchdog import WatchdogConfig


def _make_supervisor(
    name: str = "svc",
    cmd: str = "echo hello",
    restart_on_failure: bool = True,
    max_restarts: int = 5,
) -> Supervisor:
    proc_cfg = ProcessConfig(name=name, command=cmd, restart_on_failure=restart_on_failure)
    sup_cfg = SupervisorConfig(
        process=proc_cfg,
        throttle=ThrottleConfig(max_restarts=max_restarts),
        watchdog=WatchdogConfig(),
    )
    backoff = ExponentialBackoff(BackoffConfig(initial_delay=0.0, max_delay=0.0))
    return Supervisor(sup_cfg, backoff)


class TestSupervisorName:
    def test_name_matches_process_config(self):
        sup = _make_supervisor(name="myservice")
        assert sup.name == "myservice"


class TestSupervisorStart:
    def test_start_launches_process(self):
        sup = _make_supervisor()
        with patch.object(sup, "_launch") as mock_launch:
            sup.start()
            mock_launch.assert_called_once()

    def test_start_clears_stopped_flag(self):
        sup = _make_supervisor()
        sup._stopped = True
        with patch.object(sup, "_launch"):
            sup.start()
        assert sup._stopped is False


class TestSupervisorStop:
    def test_stop_sets_stopped_flag(self):
        sup = _make_supervisor()
        mock_proc = MagicMock()
        sup._process = mock_proc
        sup.stop()
        assert sup._stopped is True

    def test_stop_calls_process_stop(self):
        sup = _make_supervisor()
        mock_proc = MagicMock()
        sup._process = mock_proc
        sup.stop()
        mock_proc.stop.assert_called_once()

    def test_stop_without_process_does_not_raise(self):
        sup = _make_supervisor()
        sup._process = None
        sup.stop()  # should not raise


class TestSupervisorTick:
    def test_tick_does_nothing_when_stopped(self):
        sup = _make_supervisor()
        sup._stopped = True
        sup._process = MagicMock()
        sup.tick()  # should not raise or call anything meaningful
        sup._process.is_running.assert_not_called()

    def test_tick_restarts_on_unexpected_exit(self):
        sup = _make_supervisor(restart_on_failure=True)
        mock_proc = MagicMock()
        mock_proc.is_running.return_value = False
        mock_proc.returncode = 1
        sup._process = mock_proc
        with patch.object(sup, "_attempt_restart") as mock_restart:
            sup.tick()
            mock_restart.assert_called_once_with(1)

    def test_tick_no_restart_when_clean_exit_and_no_restart_flag(self):
        sup = _make_supervisor(restart_on_failure=False)
        mock_proc = MagicMock()
        mock_proc.is_running.return_value = False
        mock_proc.returncode = 0
        sup._process = mock_proc
        with patch.object(sup, "_attempt_restart") as mock_restart:
            sup.tick()
            mock_restart.assert_not_called()


class TestSupervisorMetrics:
    def test_start_records_metric(self):
        registry = MetricsRegistry()
        sup = _make_supervisor()
        sup._registry = registry
        with patch.object(sup._process.__class__ if sup._process else MagicMock, "start"):
            with patch("procwatch.supervisor.ManagedProcess") as MockProc:
                MockProc.return_value = MagicMock()
                sup.start()
        assert registry.get("svc").start_count >= 1
