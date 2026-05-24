"""Tests for procwatch.config_loader module."""

import pytest
from procwatch.config_loader import (
    load_monitor_from_dict,
    _parse_backoff,
    _parse_throttle,
    _parse_process_config,
)


class TestLoadMonitorFromDict:
    def test_minimal_config_creates_monitor(self):
        monitor = load_monitor_from_dict({})
        assert monitor is not None

    def test_full_config_monitor_settings(self):
        data = {"monitor": {"poll_interval": 2.0, "max_restarts": 10}}
        monitor = load_monitor_from_dict(data)
        assert monitor.config.poll_interval == 2.0
        assert monitor.config.max_restarts == 10

    def test_full_config_processes(self):
        data = {
            "processes": [
                {"name": "web", "command": "python app.py"},
                {"name": "worker", "command": "python worker.py"},
            ]
        }
        monitor = load_monitor_from_dict(data)
        assert len(monitor.processes) == 2

    def test_process_config_fields(self):
        data = {
            "processes": [
                {
                    "name": "svc",
                    "command": "./run.sh",
                    "restart_on_failure": False,
                    "restart_codes": [1, 2],
                }
            ]
        }
        monitor = load_monitor_from_dict(data)
        proc = monitor.processes[0]
        assert proc.config.name == "svc"
        assert proc.config.restart_on_failure is False
        assert proc.config.restart_codes == [1, 2]

    def test_backoff_config_parsed(self):
        data = {
            "processes": [
                {
                    "name": "svc",
                    "command": "./run.sh",
                    "backoff": {"initial_delay": 3.0, "multiplier": 1.5},
                }
            ]
        }
        monitor = load_monitor_from_dict(data)
        backoff_cfg = monitor.processes[0].config.backoff
        assert backoff_cfg.initial_delay == 3.0
        assert backoff_cfg.multiplier == 1.5

    def test_throttle_config_parsed(self):
        data = {
            "processes": [
                {
                    "name": "svc",
                    "command": "./run.sh",
                    "throttle": {"max_restarts": 2, "window_seconds": 30.0},
                }
            ]
        }
        monitor = load_monitor_from_dict(data)
        throttle_cfg = monitor.processes[0].config.throttle
        assert throttle_cfg.max_restarts == 2
        assert throttle_cfg.window_seconds == 30.0


class TestParseThrottle:
    def test_defaults(self):
        cfg = _parse_throttle({})
        assert cfg.max_restarts == 5
        assert cfg.window_seconds == 60.0
        assert cfg.enabled is True

    def test_custom(self):
        cfg = _parse_throttle({"max_restarts": 3, "window_seconds": 20.0, "enabled": False})
        assert cfg.max_restarts == 3
        assert cfg.window_seconds == 20.0
        assert cfg.enabled is False
