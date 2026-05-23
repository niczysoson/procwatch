"""Tests for procwatch.healthcheck module."""

import unittest
from unittest.mock import MagicMock, patch

from procwatch.healthcheck import HealthCheckConfig, HealthChecker


class TestHealthCheckConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = HealthCheckConfig()
        self.assertIsNone(cfg.command)
        self.assertIsNone(cfg.tcp_host)
        self.assertIsNone(cfg.tcp_port)
        self.assertEqual(cfg.interval, 10.0)
        self.assertEqual(cfg.timeout, 5.0)
        self.assertEqual(cfg.retries, 3)

    def test_is_configured_empty(self):
        cfg = HealthCheckConfig()
        self.assertFalse(cfg.is_configured())

    def test_is_configured_with_command(self):
        cfg = HealthCheckConfig(command="echo ok")
        self.assertTrue(cfg.is_configured())

    def test_is_configured_with_tcp(self):
        cfg = HealthCheckConfig(tcp_host="localhost", tcp_port=8080)
        self.assertTrue(cfg.is_configured())

    def test_is_configured_tcp_requires_both(self):
        cfg = HealthCheckConfig(tcp_host="localhost")
        self.assertFalse(cfg.is_configured())


class TestHealthChecker(unittest.TestCase):
    def test_check_returns_true_when_not_configured(self):
        checker = HealthChecker(HealthCheckConfig())
        self.assertTrue(checker.check())

    def test_check_command_success(self):
        cfg = HealthCheckConfig(command="true")
        checker = HealthChecker(cfg)
        with patch("procwatch.healthcheck.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            self.assertTrue(checker.check())

    def test_check_command_failure(self):
        cfg = HealthCheckConfig(command="false")
        checker = HealthChecker(cfg)
        with patch("procwatch.healthcheck.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            self.assertFalse(checker.check())

    def test_consecutive_failures_tracked(self):
        cfg = HealthCheckConfig(command="false", retries=3)
        checker = HealthChecker(cfg)
        with patch("procwatch.healthcheck.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            checker.check()
            checker.check()
            self.assertFalse(checker.is_unhealthy())
            checker.check()
            self.assertTrue(checker.is_unhealthy())

    def test_reset_clears_failures(self):
        cfg = HealthCheckConfig(command="false", retries=1)
        checker = HealthChecker(cfg)
        with patch("procwatch.healthcheck.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            checker.check()
            self.assertTrue(checker.is_unhealthy())
        checker.reset()
        self.assertFalse(checker.is_unhealthy())

    def test_check_tcp_failure(self):
        cfg = HealthCheckConfig(tcp_host="127.0.0.1", tcp_port=19999)
        checker = HealthChecker(cfg)
        with patch("procwatch.healthcheck.socket.create_connection") as mock_conn:
            mock_conn.side_effect = OSError("refused")
            self.assertFalse(checker.check())
