"""Tests for the backoff module."""

import pytest
from unittest.mock import patch

from procwatch.backoff import BackoffConfig, ExponentialBackoff


class TestBackoffConfig:
    def test_defaults(self):
        cfg = BackoffConfig()
        assert cfg.initial_delay == 1.0
        assert cfg.max_delay == 60.0
        assert cfg.multiplier == 2.0
        assert cfg.jitter is False

    def test_custom_values(self):
        cfg = BackoffConfig(initial_delay=0.5, max_delay=30.0, multiplier=3.0, jitter=True)
        assert cfg.initial_delay == 0.5
        assert cfg.max_delay == 30.0
        assert cfg.multiplier == 3.0
        assert cfg.jitter is True


class TestExponentialBackoff:
    def test_initial_delay(self):
        bo = ExponentialBackoff(BackoffConfig(initial_delay=2.0))
        assert bo.next_delay() == 2.0

    def test_exponential_growth(self):
        bo = ExponentialBackoff(BackoffConfig(initial_delay=1.0, multiplier=2.0, max_delay=100.0))
        delays = [bo.next_delay() for _ in range(5)]
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_max_delay_ceiling(self):
        bo = ExponentialBackoff(BackoffConfig(initial_delay=1.0, multiplier=2.0, max_delay=5.0))
        delays = [bo.next_delay() for _ in range(5)]
        assert all(d <= 5.0 for d in delays)
        assert delays[-1] == 5.0

    def test_attempt_counter(self):
        bo = ExponentialBackoff()
        assert bo.attempt == 0
        bo.next_delay()
        assert bo.attempt == 1
        bo.next_delay()
        assert bo.attempt == 2

    def test_reset(self):
        bo = ExponentialBackoff(BackoffConfig(initial_delay=1.0))
        bo.next_delay()
        bo.next_delay()
        bo.reset()
        assert bo.attempt == 0
        assert bo.next_delay() == 1.0

    def test_wait_calls_sleep(self):
        bo = ExponentialBackoff(BackoffConfig(initial_delay=3.0))
        with patch("procwatch.backoff.time.sleep") as mock_sleep:
            delay = bo.wait()
        mock_sleep.assert_called_once_with(3.0)
        assert delay == 3.0

    def test_jitter_within_range(self):
        bo = ExponentialBackoff(BackoffConfig(initial_delay=10.0, jitter=True))
        for _ in range(20):
            delay = bo.next_delay()
            assert 0 <= delay <= 10.0
