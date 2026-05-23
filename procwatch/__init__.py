"""procwatch — Minimal process monitor that restarts services on failure."""

from procwatch.backoff import BackoffConfig, ExponentialBackoff
from procwatch.config_loader import load_monitor_from_dict, load_monitor_from_file
from procwatch.monitor import MonitorConfig, ProcessMonitor
from procwatch.process import ManagedProcess, ProcessConfig

__all__ = [
    "BackoffConfig",
    "ExponentialBackoff",
    "ProcessConfig",
    "ManagedProcess",
    "MonitorConfig",
    "ProcessMonitor",
    "load_monitor_from_dict",
    "load_monitor_from_file",
]

__version__ = "0.1.0"
