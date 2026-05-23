"""Tests for the procwatch CLI module."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from procwatch.cli import _build_parser, _setup_logging, main


class TestBuildParser:
    def test_requires_config_argument(self):
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_config_path(self):
        parser = _build_parser()
        args = parser.parse_args(["myconfig.yaml"])
        assert args.config == "myconfig.yaml"

    def test_verbose_flag_default_false(self):
        parser = _build_parser()
        args = parser.parse_args(["cfg.yaml"])
        assert args.verbose is False

    def test_verbose_flag_short(self):
        parser = _build_parser()
        args = parser.parse_args(["-v", "cfg.yaml"])
        assert args.verbose is True

    def test_verbose_flag_long(self):
        parser = _build_parser()
        args = parser.parse_args(["--verbose", "cfg.yaml"])
        assert args.verbose is True


class TestSetupLogging:
    def test_info_level_by_default(self, caplog):
        _setup_logging(verbose=False)
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_debug_level_when_verbose(self):
        _setup_logging(verbose=True)
        root = logging.getLogger()
        assert root.level == logging.DEBUG


class TestMain:
    def test_missing_config_file_returns_1(self, tmp_path):
        result = main([str(tmp_path / "nonexistent.yaml")])
        assert result == 1

    def test_invalid_yaml_returns_1(self, tmp_path):
        bad_cfg = tmp_path / "bad.yaml"
        bad_cfg.write_text(":::invalid yaml:::")
        result = main([str(bad_cfg)])
        assert result == 1

    def test_valid_config_runs_monitor(self, tmp_path):
        cfg = tmp_path / "procwatch.yaml"
        cfg.write_text(
            "processes:\n"
            "  - name: dummy\n"
            "    command: echo hello\n"
        )
        mock_monitor = MagicMock()
        with patch("procwatch.cli.load_monitor_from_file", return_value=mock_monitor):
            result = main([str(cfg)])
        mock_monitor.run.assert_called_once()
        assert result == 0

    def test_keyboard_interrupt_returns_0(self, tmp_path):
        cfg = tmp_path / "procwatch.yaml"
        cfg.write_text(
            "processes:\n"
            "  - name: dummy\n"
            "    command: echo hello\n"
        )
        mock_monitor = MagicMock()
        mock_monitor.run.side_effect = KeyboardInterrupt
        with patch("procwatch.cli.load_monitor_from_file", return_value=mock_monitor):
            result = main([str(cfg)])
        assert result == 0
