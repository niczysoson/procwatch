"""Load monitor configuration from a plain Python dictionary (e.g. parsed YAML/JSON)."""

from __future__ import annotations

from typing import Any, Dict

from procwatch.backoff import BackoffConfig
from procwatch.monitor import MonitorConfig, ProcessMonitor
from procwatch.process import ProcessConfig
from procwatch.throttle import ThrottleConfig
from procwatch.watchdog import WatchdogConfig


def _parse_backoff(data: Dict[str, Any]) -> BackoffConfig:
    return BackoffConfig(
        initial_delay=data.get("initial_delay", 1.0),
        multiplier=data.get("multiplier", 2.0),
        max_delay=data.get("max_delay", 60.0),
        jitter=data.get("jitter", False),
    )


def _parse_throttle(data: Dict[str, Any]) -> ThrottleConfig:
    return ThrottleConfig(
        max_restarts=data.get("max_restarts", 5),
        window_seconds=data.get("window_seconds", 60.0),
    )


def _parse_watchdog(data: Dict[str, Any]) -> WatchdogConfig:
    return WatchdogConfig(
        timeout_seconds=data.get("timeout_seconds", 30.0),
        enabled=data.get("enabled", True),
    )


def _parse_monitor_config(data: Dict[str, Any]) -> MonitorConfig:
    return MonitorConfig(
        poll_interval=data.get("poll_interval", 1.0),
        max_respawn_attempts=data.get("max_respawn_attempts", 0),
    )


def _parse_process_config(data: Dict[str, Any]) -> ProcessConfig:
    backoff_data = data.get("backoff", {})
    throttle_data = data.get("throttle", {})
    return ProcessConfig(
        name=data["name"],
        command=data["command"],
        restart_on_failure=data.get("restart_on_failure", True),
        restart_codes=data.get("restart_codes", []),
        backoff=_parse_backoff(backoff_data),
        throttle=_parse_throttle(throttle_data),
    )


def load_monitor_from_dict(data: Dict[str, Any]) -> ProcessMonitor:
    """Build a fully configured ProcessMonitor from a config dictionary."""
    monitor_cfg = _parse_monitor_config(data.get("monitor", {}))
    monitor = ProcessMonitor(monitor_cfg)

    for proc_data in data.get("processes", []):
        proc_cfg = _parse_process_config(proc_data)
        monitor.add_process(proc_cfg)

    return monitor


def load_monitor_from_file(path: str) -> ProcessMonitor:
    """Parse a YAML config file and return a configured ProcessMonitor."""
    import yaml  # optional dependency

    with open(path, "r") as fh:
        data = yaml.safe_load(fh) or {}
    return load_monitor_from_dict(data)
