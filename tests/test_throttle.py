"""Tests for procwatch.throttle module."""

import pytest
from unittest.mock import patch
from procwatch.throttle import ThrottleConfig, RestartThrottle


class TestThrottleConfig:
    def test_defaults(self):
        cfg = ThrottleConfig()
        assert cfg.max_restarts == 5
        assert cfg.window_seconds == 60.0
        assert cfg.enabled is True

    def test_custom_values(self):
        cfg = ThrottleConfig(max_restarts=3, window_seconds=30.0, enabled=False)
        assert cfg.max_restarts == 3
        assert cfg.window_seconds == 30.0
        assert cfg.enabled is False

    def test_invalid_max_restarts(self):
        with pytest.raises(ValueError, match="max_restarts"):
            ThrottleConfig(max_restarts=0)

    def test_invalid_window_seconds(self):
        with pytest.raises(ValueError, match="window_seconds"):
            ThrottleConfig(window_seconds=0)


class TestRestartThrottle:
    def _make_throttle(self, max_restarts=3, window_seconds=60.0, enabled=True):
        cfg = ThrottleConfig(max_restarts=max_restarts, window_seconds=window_seconds, enabled=enabled)
        return RestartThrottle(cfg)

    def test_not_throttled_initially(self):
        t = self._make_throttle()
        assert t.is_throttled() is False

    def test_throttled_after_max_restarts(self):
        t = self._make_throttle(max_restarts=3)
        for _ in range(3):
            t.record_restart()
        assert t.is_throttled() is True

    def test_not_throttled_below_max(self):
        t = self._make_throttle(max_restarts=3)
        for _ in range(2):
            t.record_restart()
        assert t.is_throttled() is False

    def test_disabled_throttle_never_throttled(self):
        t = self._make_throttle(max_restarts=1, enabled=False)
        t.record_restart()
        t.record_restart()
        assert t.is_throttled() is False

    def test_reset_clears_history(self):
        t = self._make_throttle(max_restarts=2)
        t.record_restart()
        t.record_restart()
        assert t.is_throttled() is True
        t.reset()
        assert t.is_throttled() is False

    def test_old_restarts_evicted(self):
        t = self._make_throttle(max_restarts=2, window_seconds=10.0)
        with patch("procwatch.throttle.monotonic", return_value=0.0):
            t.record_restart()
            t.record_restart()
        # Advance time beyond window
        with patch("procwatch.throttle.monotonic", return_value=11.0):
            assert t.is_throttled() is False

    def test_restart_count_in_window(self):
        t = self._make_throttle(max_restarts=10)
        t.record_restart()
        t.record_restart()
        assert t.restart_count_in_window() == 2
