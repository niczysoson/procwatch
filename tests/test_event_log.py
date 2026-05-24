"""Tests for procwatch.event_log."""

import pytest

from procwatch.event_log import Event, EventKind, EventLog


def _make_event(kind: EventKind = EventKind.STARTED, name: str = "svc", **kwargs) -> Event:
    return Event(kind=kind, process_name=name, **kwargs)


class TestEvent:
    def test_str_minimal(self):
        e = _make_event(EventKind.STARTED)
        assert "started" in str(e)
        assert "svc" in str(e)

    def test_str_with_exit_code(self):
        e = _make_event(EventKind.FAILED, exit_code=1)
        assert "exit=1" in str(e)

    def test_str_with_reason(self):
        e = _make_event(EventKind.THROTTLED, reason="too many restarts")
        assert "too many restarts" in str(e)

    def test_str_all_fields(self):
        e = _make_event(EventKind.FAILED, exit_code=2, reason="oom")
        s = str(e)
        assert "failed" in s
        assert "exit=2" in s
        assert "oom" in s


class TestEventLog:
    def test_default_max_events(self):
        log = EventLog()
        assert len(log) == 0

    def test_invalid_max_events(self):
        with pytest.raises(ValueError):
            EventLog(max_events=0)

    def test_record_increases_length(self):
        log = EventLog()
        log.record(_make_event())
        assert len(log) == 1

    def test_evicts_oldest_at_capacity(self):
        log = EventLog(max_events=3)
        for i in range(4):
            log.record(_make_event(name=f"svc{i}"))
        assert len(log) == 3
        names = [e.process_name for e in log.all()]
        assert "svc0" not in names
        assert "svc3" in names

    def test_all_returns_snapshot(self):
        log = EventLog()
        log.record(_make_event())
        snapshot = log.all()
        log.record(_make_event(name="other"))
        assert len(snapshot) == 1

    def test_for_process_filters_by_name(self):
        log = EventLog()
        log.record(_make_event(name="web"))
        log.record(_make_event(name="worker"))
        log.record(_make_event(name="web", kind=EventKind.FAILED))
        result = log.for_process("web")
        assert len(result) == 2
        assert all(e.process_name == "web" for e in result)

    def test_last_returns_most_recent(self):
        log = EventLog()
        for i in range(10):
            log.record(_make_event(name=f"svc{i}"))
        recent = log.last(3)
        assert len(recent) == 3
        assert recent[-1].process_name == "svc9"

    def test_last_clamps_to_available(self):
        log = EventLog()
        log.record(_make_event())
        assert len(log.last(100)) == 1

    def test_clear_removes_all_events(self):
        log = EventLog()
        log.record(_make_event())
        log.clear()
        assert len(log) == 0
