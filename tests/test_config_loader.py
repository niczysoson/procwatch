"""Tests for procwatch.config_loader."""

import textwrap
import tempfile
import os

import pytest

from procwatch.config_loader import load_monitor_from_dict, load_monitor_from_file
from procwatch.monitor import ProcessMonitor


class TestLoadMonitorFromDict:
    def test_minimal_config_creates_monitor(self):
        monitor = load_monitor_from_dict({})
        assert isinstance(monitor, ProcessMonitor)

    def test_full_config_monitor_settings(self):
        data = {"monitor": {"poll_interval": 2.0, "metrics_interval": 30.0}}
        monitor = load_monitor_from_dict(data)
        assert monitor._config.poll_interval == 2.0
        assert monitor._config.metrics_interval == 30.0

    def test_full_config_processes(self):
        data = {
            "processes": [
                {"name": "web", "command": "python app.py"},
                {"name": "worker", "command": "python worker.py"},
            ]
        }
        monitor = load_monitor_from_dict(data)
        assert len(monitor._processes) == 2

    def test_process_config_fields(self):
        data = {
            "processes": [
                {
                    "name": "svc",
                    "command": "run.sh",
                    "restart_on_failure": False,
                    "restart_codes": [1, 2],
                    "backoff": {"initial_delay": 3.0, "max_delay": 30.0},
                }
            ]
        }
        monitor = load_monitor_from_dict(data)
        proc = monitor._processes[0]
        assert proc.config.name == "svc"
        assert proc.config.restart_on_failure is False
        assert proc.config.restart_codes == [1, 2]
        assert proc.config.backoff.initial_delay == 3.0
        assert proc.config.backoff.max_delay == 30.0

    def test_notifier_config_fields(self):
        data = {
            "processes": [
                {
                    "name": "svc",
                    "command": "run.sh",
                    "notifier": {
                        "on_start": "echo start",
                        "on_failure": "echo fail",
                        "on_restart": "echo restart",
                        "timeout": 3.0,
                    },
                }
            ]
        }
        monitor = load_monitor_from_dict(data)
        notifier_cfg = monitor._processes[0].config.notifier
        assert notifier_cfg.on_start == "echo start"
        assert notifier_cfg.on_failure == "echo fail"
        assert notifier_cfg.on_restart == "echo restart"
        assert notifier_cfg.timeout == 3.0

    def test_load_from_file(self):
        yaml_content = textwrap.dedent("""
            monitor:
              poll_interval: 0.5
            processes:
              - name: app
                command: python main.py
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            tmp_path = f.name
        try:
            monitor = load_monitor_from_file(tmp_path)
            assert isinstance(monitor, ProcessMonitor)
            assert monitor._config.poll_interval == 0.5
            assert len(monitor._processes) == 1
        finally:
            os.unlink(tmp_path)
