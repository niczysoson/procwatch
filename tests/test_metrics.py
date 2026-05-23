"""Tests for procwatch.metrics module."""

from datetime import datetime
from unittest.mock import patch

import pytest

from procwatch.metrics import MetricsRegistry, ProcessMetrics


class TestProcessMetrics:
    def test_defaults(self):
        m = ProcessMetrics(name="svc")
        assert m.start_count == 0
        assert m.failure_count == 0
        assert m.last_exit_code is None
        assert m.last_started_at is None
        assert m.last_failed_at is None
        assert m.restart_times == []

    def test_record_start_increments_count(self):
        m = ProcessMetrics(name="svc")
        m.record_start()
        assert m.start_count == 1
        assert m.last_started_at is not None

    def test_record_failure_increments_count(self):
        m = ProcessMetrics(name="svc")
        m.record_start()
        m.record_failure(exit_code=1)
        assert m.failure_count == 1
        assert m.last_exit_code == 1
        assert m.last_failed_at is not None

    def test_restart_times_only_after_first_start(self):
        m = ProcessMetrics(name="svc")
        # First start then failure — not a restart yet
        m.record_start()
        m.record_failure(exit_code=2)
        assert m.restart_times == []

        # Second start then failure — counts as restart
        m.record_start()
        m.record_failure(exit_code=2)
        assert len(m.restart_times) == 1

    def test_uptime_seconds_none_when_never_started(self):
        m = ProcessMetrics(name="svc")
        assert m.uptime_seconds is None

    def test_uptime_seconds_positive_after_start(self):
        m = ProcessMetrics(name="svc")
        m.record_start()
        assert m.uptime_seconds is not None
        assert m.uptime_seconds >= 0.0


class TestMetricsRegistry:
    def test_get_or_create_new(self):
        reg = MetricsRegistry()
        m = reg.get_or_create("worker")
        assert isinstance(m, ProcessMetrics)
        assert m.name == "worker"

    def test_get_or_create_returns_same_instance(self):
        reg = MetricsRegistry()
        m1 = reg.get_or_create("worker")
        m2 = reg.get_or_create("worker")
        assert m1 is m2

    def test_all_returns_copy(self):
        reg = MetricsRegistry()
        reg.get_or_create("a")
        reg.get_or_create("b")
        snapshot = reg.all()
        assert set(snapshot.keys()) == {"a", "b"}
        snapshot["c"] = ProcessMetrics(name="c")
        assert "c" not in reg.all()

    def test_summary_structure(self):
        reg = MetricsRegistry()
        m = reg.get_or_create("api")
        m.record_start()
        m.record_failure(exit_code=137)
        summary = reg.summary()
        assert len(summary) == 1
        entry = summary[0]
        assert entry["name"] == "api"
        assert entry["start_count"] == 1
        assert entry["failure_count"] == 1
        assert entry["last_exit_code"] == 137
