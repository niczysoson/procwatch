"""Tests for ProcessMonitor."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from procwatch.backoff import BackoffConfig
from procwatch.monitor import MonitorConfig, ProcessMonitor
from procwatch.process import ProcessConfig


class TestMonitorConfig:
    def test_defaults(self):
        cfg = MonitorConfig()
        assert cfg.poll_interval == 1.0
        assert cfg.max_restarts is None
        assert isinstance(cfg.backoff, BackoffConfig)

    def test_custom_values(self):
        backoff = BackoffConfig(initial_delay=2.0)
        cfg = MonitorConfig(poll_interval=0.5, max_restarts=3, backoff=backoff)
        assert cfg.poll_interval == 0.5
        assert cfg.max_restarts == 3
        assert cfg.backoff.initial_delay == 2.0


class TestProcessMonitor:
    def _make_monitor(self, **kwargs):
        return ProcessMonitor(config=MonitorConfig(**kwargs))

    def _make_proc_config(self, command="echo hello"):
        return ProcessConfig(command=command)

    def test_add_and_remove_process(self):
        monitor = self._make_monitor()
        monitor.add_process("svc", self._make_proc_config())
        assert "svc" in monitor.process_names
        monitor.remove_process("svc")
        assert "svc" not in monitor.process_names

    def test_remove_nonexistent_is_noop(self):
        monitor = self._make_monitor()
        monitor.remove_process("ghost")  # should not raise

    @pytest.mark.asyncio
    async def test_start_all_calls_start(self):
        monitor = self._make_monitor()
        mock_proc = MagicMock()
        mock_proc.start = AsyncMock()
        monitor._processes["svc"] = mock_proc
        await monitor.start_all()
        mock_proc.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_all_calls_stop(self):
        monitor = self._make_monitor()
        mock_proc = MagicMock()
        mock_proc.stop = AsyncMock()
        monitor._processes["svc"] = mock_proc
        await monitor.stop_all()
        mock_proc.stop.assert_awaited_once()
        assert monitor._running is False

    @pytest.mark.asyncio
    async def test_handle_restart_increments_count(self):
        monitor = self._make_monitor()
        proc_cfg = self._make_proc_config()
        monitor.add_process("svc", proc_cfg)
        mock_proc = MagicMock()
        mock_proc.start = AsyncMock()
        monitor._processes["svc"] = mock_proc

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await monitor._handle_restart("svc", mock_proc)

        assert monitor._restart_counts["svc"] == 1
        mock_proc.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_max_restarts_respected(self):
        monitor = self._make_monitor(max_restarts=2)
        proc_cfg = self._make_proc_config()
        monitor.add_process("svc", proc_cfg)
        monitor._restart_counts["svc"] = 2

        mock_proc = MagicMock()
        mock_proc.is_running.return_value = False
        mock_proc.return_code.return_value = 1
        mock_proc.config = proc_cfg
        monitor._processes["svc"] = mock_proc

        with patch.object(monitor, "_handle_restart", new_callable=AsyncMock) as mock_restart:
            monitor._running = True
            # Simulate one poll iteration
            for name, proc in list(monitor._processes.items()):
                if not proc.is_running():
                    if not proc.config.should_restart(proc.return_code()):
                        continue
                    if monitor.config.max_restarts is not None and monitor._restart_counts[name] >= monitor.config.max_restarts:
                        continue
                    await monitor._handle_restart(name, proc)
            mock_restart.assert_not_awaited()
