"""Load monitor configuration from dicts or YAML files."""

from __future__ import annotations

from typing import Any, Dict

import yaml

from procwatch.backoff import BackoffConfig
from procwatch.healthcheck import HealthCheckConfig
from procwatch.monitor import MonitorConfig, ProcessMonitor
from procwatch.notifier import NotifierConfig
from procwatch.process import ProcessConfig


def _parse_backoff(data: Dict[str, Any]) -> BackoffConfig:
    return BackoffConfig(
        initial_delay=data.get("initial_delay", 1.0),
        multiplier=data.get("multiplier", 2.0),
        max_delay=data.get("max_delay", 60.0),
        jitter=data.get("jitter", False),
    )


def _parse_monitor_config(data: Dict[str, Any]) -> MonitorConfig:
    return MonitorConfig(
        poll_interval=data.get("poll_interval", 1.0),
        metrics_interval=data.get("metrics_interval", 60.0),
    )


def _parse_process_config(data: Dict[str, Any]) -> ProcessConfig:
    backoff_data = data.get("backoff", {})
    hc_data = data.get("healthcheck", {})
    notifier_data = data.get("notifier", {})
    return ProcessConfig(
        name=data["name"],
        command=data["command"],
        restart_on_failure=data.get("restart_on_failure", True),
        restart_codes=data.get("restart_codes", []),
        backoff=_parse_backoff(backoff_data),
        healthcheck=HealthCheckConfig(
            command=hc_data.get("command"),
            tcp_host=hc_data.get("tcp_host"),
            tcp_port=hc_data.get("tcp_port"),
            interval=hc_data.get("interval", 30.0),
            timeout=hc_data.get("timeout", 5.0),
        ),
        notifier=NotifierConfig(
            on_start=notifier_data.get("on_start"),
            on_failure=notifier_data.get("on_failure"),
            on_restart=notifier_data.get("on_restart"),
            timeout=notifier_data.get("timeout", 5.0),
        ),
    )


def load_monitor_from_dict(data: Dict[str, Any]) -> ProcessMonitor:
    """Build a ProcessMonitor from a configuration dictionary."""
    monitor_cfg = _parse_monitor_config(data.get("monitor", {}))
    monitor = ProcessMonitor(monitor_cfg)
    for proc_data in data.get("processes", []):
        proc_cfg = _parse_process_config(proc_data)
        monitor.add_process(proc_cfg)
    return monitor


def load_monitor_from_file(path: str) -> ProcessMonitor:
    """Load a ProcessMonitor from a YAML configuration file."""
    with open(path, "r") as fh:
        data = yaml.safe_load(fh) or {}
    return load_monitor_from_dict(data)
