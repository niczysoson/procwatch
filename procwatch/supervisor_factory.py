"""Factory helpers for building Supervisor instances from config dicts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from procwatch.backoff import BackoffConfig, ExponentialBackoff
from procwatch.metrics import MetricsRegistry
from procwatch.process import ProcessConfig
from procwatch.supervisor import Supervisor, SupervisorConfig
from procwatch.throttle import ThrottleConfig
from procwatch.watchdog import WatchdogConfig


def _parse_process(data: Dict[str, Any]) -> ProcessConfig:
    return ProcessConfig(
        name=data["name"],
        command=data["command"],
        restart_on_failure=data.get("restart_on_failure", True),
        restart_on_exit_codes=data.get("restart_on_exit_codes", []),
        environment=data.get("environment", {}),
        working_dir=data.get("working_dir"),
    )


def _parse_backoff(data: Dict[str, Any]) -> ExponentialBackoff:
    cfg = BackoffConfig(
        initial_delay=data.get("initial_delay", 1.0),
        max_delay=data.get("max_delay", 60.0),
        multiplier=data.get("multiplier", 2.0),
        jitter=data.get("jitter", False),
    )
    return ExponentialBackoff(cfg)


def _parse_throttle(data: Dict[str, Any]) -> ThrottleConfig:
    return ThrottleConfig(
        max_restarts=data.get("max_restarts", 0),
        window_seconds=data.get("window_seconds", 60),
    )


def _parse_watchdog(data: Dict[str, Any]) -> WatchdogConfig:
    return WatchdogConfig(
        timeout=data.get("timeout", 0),
        check_interval=data.get("check_interval", 10),
    )


def build_supervisor(
    data: Dict[str, Any],
    registry: Optional[MetricsRegistry] = None,
) -> Supervisor:
    """Build a Supervisor from a raw config dictionary."""
    process_cfg = _parse_process(data)
    backoff = _parse_backoff(data.get("backoff", {}))
    throttle_cfg = _parse_throttle(data.get("throttle", {}))
    watchdog_cfg = _parse_watchdog(data.get("watchdog", {}))
    sup_cfg = SupervisorConfig(
        process=process_cfg,
        throttle=throttle_cfg,
        watchdog=watchdog_cfg,
    )
    return Supervisor(sup_cfg, backoff, registry=registry)


def build_supervisors(
    processes: List[Dict[str, Any]],
    registry: Optional[MetricsRegistry] = None,
) -> List[Supervisor]:
    """Build multiple Supervisor instances from a list of process config dicts."""
    return [build_supervisor(p, registry=registry) for p in processes]
