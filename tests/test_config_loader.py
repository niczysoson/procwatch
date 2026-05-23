"""Tests for config_loader module."""

import pytest

from procwatch.config_loader import load_monitor_from_dict
from procwatch.monitor import ProcessMonitor


MINIMAL_CONFIG = {
    "processes": {
        "web": {"command": "python app.py"},
    }
}

FULL_CONFIG = {
    "monitor": {
        "poll_interval": 0.5,
        "max_restarts": 5,
        "backoff": {
            "initial_delay": 2.0,
            "max_delay": 30.0,
            "multiplier": 1.5,
            "jitter": True,
        },
    },
    "processes": {
        "worker": {
            "command": "celery worker",
            "restart_on_exit": True,
            "restart_codes": [1, 2],
            "env": {"CELERY_BROKER": "redis://localhost"},
            "cwd": "/app",
        },
        "beat": {
            "command": "celery beat",
            "restart_on_exit": False,
        },
    },
}


class TestLoadMonitorFromDict:
    def test_minimal_config_creates_monitor(self):
        monitor = load_monitor_from_dict(MINIMAL_CONFIG)
        assert isinstance(monitor, ProcessMonitor)
        assert "web" in monitor.process_names

    def test_full_config_monitor_settings(self):
        monitor = load_monitor_from_dict(FULL_CONFIG)
        assert monitor.config.poll_interval == 0.5
        assert monitor.config.max_restarts == 5
        assert monitor.config.backoff.initial_delay == 2.0
        assert monitor.config.backoff.max_delay == 30.0
        assert monitor.config.backoff.multiplier == 1.5
        assert monitor.config.backoff.jitter is True

    def test_full_config_processes(self):
        monitor = load_monitor_from_dict(FULL_CONFIG)
        assert "worker" in monitor.process_names
        assert "beat" in monitor.process_names

    def test_process_config_fields(self):
        monitor = load_monitor_from_dict(FULL_CONFIG)
        worker = monitor._processes["worker"]
        assert worker.config.command == "celery worker"
        assert worker.config.restart_on_exit is True
        assert worker.config.restart_codes == [1, 2]
        assert worker.config.cwd == "/app"

    def test_empty_processes(self):
        monitor = load_monitor_from_dict({"processes": {}})
        assert monitor.process_names == []

    def test_missing_command_raises(self):
        with pytest.raises(KeyError):
            load_monitor_from_dict({"processes": {"bad": {}}})

    def test_file_not_found_raises(self):
        from procwatch.config_loader import load_monitor_from_file
        with pytest.raises(FileNotFoundError):
            load_monitor_from_file("/nonexistent/path/config.toml")
