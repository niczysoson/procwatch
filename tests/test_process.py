import sys
import subprocess
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from procwatch.process import ProcessConfig, ManagedProcess
from procwatch.backoff import BackoffConfig


class TestProcessConfig(unittest.TestCase):
    def test_defaults(self):
        config = ProcessConfig(name="svc", command=["echo", "hello"])
        self.assertEqual(config.max_restarts, 5)
        self.assertIsNone(config.restart_on_exit_codes)
        self.assertIsInstance(config.backoff, BackoffConfig)

    def test_should_restart_nonzero(self):
        config = ProcessConfig(name="svc", command=["echo"])
        self.assertTrue(config.should_restart(1))
        self.assertFalse(config.should_restart(0))

    def test_should_restart_with_codes(self):
        config = ProcessConfig(name="svc", command=["echo"], restart_on_exit_codes=[1, 2])
        self.assertTrue(config.should_restart(1))
        self.assertTrue(config.should_restart(2))
        self.assertFalse(config.should_restart(0))
        self.assertFalse(config.should_restart(3))


class TestManagedProcess(unittest.TestCase):
    def _make_process(self, max_restarts=3):
        config = ProcessConfig(
            name="test-svc",
            command=[sys.executable, "-c", "exit(1)"],
            backoff=BackoffConfig(initial_delay=0.01, max_delay=0.05),
            max_restarts=max_restarts,
        )
        return ManagedProcess(config)

    def test_initial_state(self):
        mp = self._make_process()
        self.assertEqual(mp.restart_count, 0)
        self.assertFalse(mp.running)
        self.assertIsNone(mp._process)

    @patch("procwatch.process.subprocess.Popen")
    def test_start_sets_running(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_popen.return_value = mock_proc
        mp = self._make_process()
        mp.start()
        self.assertTrue(mp.running)
        mock_popen.assert_called_once()

    @patch("procwatch.process.subprocess.Popen")
    def test_stop_terminates_process(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        mp = self._make_process()
        mp.start()
        mp.stop()
        mock_proc.terminate.assert_called_once()
        self.assertFalse(mp.running)

    @patch("procwatch.process.time.sleep", return_value=None)
    @patch("procwatch.process.subprocess.Popen")
    def test_monitor_stops_after_max_restarts(self, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.pid = 9999
        mock_proc.poll.return_value = 1
        mock_popen.return_value = mock_proc
        mp = self._make_process(max_restarts=2)
        mp.monitor()
        self.assertFalse(mp.running)
        self.assertEqual(mp.restart_count, 2)


if __name__ == "__main__":
    unittest.main()
