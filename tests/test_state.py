"""Tests for procwatch.state module."""

import pytest
from procwatch.state import ProcessState, StateTransition, StateTracker


class TestProcessState:
    def test_all_states_defined(self):
        names = {s.name for s in ProcessState}
        assert names == {"PENDING", "STARTING", "RUNNING", "STOPPING", "STOPPED", "FAILED", "BACKOFF"}


class TestStateTransition:
    def test_str_without_reason(self):
        t = StateTransition(ProcessState.PENDING, ProcessState.STARTING)
        assert "PENDING -> STARTING" in str(t)

    def test_str_with_reason(self):
        t = StateTransition(ProcessState.RUNNING, ProcessState.FAILED, reason="exit code 1")
        assert "exit code 1" in str(t)

    def test_timestamp_is_set(self):
        t = StateTransition(ProcessState.PENDING, ProcessState.STARTING)
        assert t.timestamp is not None


class TestStateTracker:
    def _make_tracker(self) -> StateTracker:
        return StateTracker()

    def test_initial_state_is_pending(self):
        tracker = self._make_tracker()
        assert tracker.current == ProcessState.PENDING

    def test_valid_transition_pending_to_starting(self):
        tracker = self._make_tracker()
        event = tracker.transition(ProcessState.STARTING)
        assert tracker.current == ProcessState.STARTING
        assert event.from_state == ProcessState.PENDING
        assert event.to_state == ProcessState.STARTING

    def test_invalid_transition_raises(self):
        tracker = self._make_tracker()
        with pytest.raises(ValueError, match="Invalid transition"):
            tracker.transition(ProcessState.RUNNING)

    def test_transition_records_history(self):
        tracker = self._make_tracker()
        tracker.transition(ProcessState.STARTING)
        tracker.transition(ProcessState.RUNNING)
        assert len(tracker.history) == 2

    def test_history_is_copy(self):
        tracker = self._make_tracker()
        tracker.transition(ProcessState.STARTING)
        h = tracker.history
        h.clear()
        assert len(tracker.history) == 1

    def test_transition_with_reason(self):
        tracker = self._make_tracker()
        tracker.transition(ProcessState.STARTING, reason="initial launch")
        assert tracker.history[0].reason == "initial launch"

    def test_failed_to_backoff(self):
        tracker = self._make_tracker()
        tracker.transition(ProcessState.STARTING)
        tracker.transition(ProcessState.RUNNING)
        tracker.transition(ProcessState.FAILED, reason="segfault")
        tracker.transition(ProcessState.BACKOFF)
        assert tracker.current == ProcessState.BACKOFF

    def test_is_terminal_false_when_running(self):
        tracker = self._make_tracker()
        tracker.transition(ProcessState.STARTING)
        tracker.transition(ProcessState.RUNNING)
        assert not tracker.is_terminal()

    def test_is_terminal_true_when_stopped(self):
        tracker = self._make_tracker()
        tracker.transition(ProcessState.STARTING)
        tracker.transition(ProcessState.RUNNING)
        tracker.transition(ProcessState.STOPPING)
        tracker.transition(ProcessState.STOPPED)
        assert tracker.is_terminal()

    def test_stopped_can_restart(self):
        tracker = self._make_tracker()
        tracker.transition(ProcessState.STARTING)
        tracker.transition(ProcessState.RUNNING)
        tracker.transition(ProcessState.STOPPING)
        tracker.transition(ProcessState.STOPPED)
        tracker.transition(ProcessState.STARTING)
        assert tracker.current == ProcessState.STARTING
