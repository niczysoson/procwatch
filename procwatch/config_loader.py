"""Load monitor and process configurations from a TOML or dict source."""

import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

from procwatch.backoff import BackoffConfig
from procwatch.monitor import MonitorConfig, ProcessMonitor
from procwatch.process import ProcessConfig


def _parse_backoff(data: Dict[str, Any]) -> BackoffConfig:
    return BackoffConfig(
        initial_delay=data.get("initial_delay", 1.0),
        max_delay=data.get("max_delay", 60.0),
        multiplier=data.get("multiplier", 2.0),
        jitter=data.get("jitter", False),
    )


def _parse_monitor_config(data: Dict[str, Any]) -> MonitorConfig:
    backoff_data = data.get("backoff", {})
    return MonitorConfig(
        poll_interval=data.get("poll_interval", 1.0),
        max_restarts=data.get("max_restarts", None),
        backoff=_parse_backoff(backoff_data),
    )


def _parse_process_config(data: Dict[str, Any]) -> ProcessConfig:
    return ProcessConfig(
        command=data["command"],
        restart_on_exit=data.get("restart_on_exit", True),
        restart_codes=data.get("restart_codes", None),
        env=data.get("env", None),
        cwd=data.get("cwd", None),
    )


def load_monitor_from_dict(data: Dict[str, Any]) -> ProcessMonitor:
    """Build a ProcessMonitor from a configuration dictionary."""
    monitor_cfg = _parse_monitor_config(data.get("monitor", {}))
    monitor = ProcessMonitor(config=monitor_cfg)

    for name, proc_data in data.get("processes", {}).items():
        proc_cfg = _parse_process_config(proc_data)
        monitor.add_process(name, proc_cfg)

    return monitor


def load_monitor_from_file(path: str) -> ProcessMonitor:
    """Load a ProcessMonitor configuration from a TOML file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(config_path, "rb") as fh:
        data = tomllib.load(fh)
    return load_monitor_from_dict(data)
