"""Simple in-memory metrics collection for monitored processes."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ProcessMetrics:
    """Tracks runtime statistics for a single managed process."""

    name: str
    start_count: int = 0
    failure_count: int = 0
    last_exit_code: Optional[int] = None
    last_started_at: Optional[datetime] = None
    last_failed_at: Optional[datetime] = None
    restart_times: List[datetime] = field(default_factory=list)

    def record_start(self) -> None:
        """Record a process start event."""
        self.start_count += 1
        self.last_started_at = datetime.utcnow()

    def record_failure(self, exit_code: int) -> None:
        """Record a process failure with its exit code."""
        self.failure_count += 1
        self.last_exit_code = exit_code
        self.last_failed_at = datetime.utcnow()
        if self.start_count > 1:
            self.restart_times.append(datetime.utcnow())

    @property
    def uptime_seconds(self) -> Optional[float]:
        """Seconds since the process was last started, or None if never started."""
        if self.last_started_at is None:
            return None
        return (datetime.utcnow() - self.last_started_at).total_seconds()


class MetricsRegistry:
    """Central registry holding metrics for all monitored processes."""

    def __init__(self) -> None:
        self._metrics: Dict[str, ProcessMetrics] = {}

    def get_or_create(self, name: str) -> ProcessMetrics:
        """Return existing metrics for *name*, creating them if absent."""
        if name not in self._metrics:
            self._metrics[name] = ProcessMetrics(name=name)
        return self._metrics[name]

    def all(self) -> Dict[str, ProcessMetrics]:
        """Return a shallow copy of the metrics dict."""
        return dict(self._metrics)

    def summary(self) -> List[Dict]:
        """Return a list of summary dicts suitable for logging or display."""
        result = []
        for m in self._metrics.values():
            result.append({
                "name": m.name,
                "start_count": m.start_count,
                "failure_count": m.failure_count,
                "last_exit_code": m.last_exit_code,
                "uptime_seconds": m.uptime_seconds,
            })
        return result
