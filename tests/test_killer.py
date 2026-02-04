"""Tests for process killer module."""

import pytest
from unittest.mock import patch, call

from src.recovery.killer import KillResult, kill_process, is_process_running


class TestIsProcessRunning:
    @patch("src.recovery.killer.os.kill")
    def test_running(self, mock_kill):
        mock_kill.return_value = None
        assert is_process_running(1234) is True
        mock_kill.assert_called_once_with(1234, 0)

    @patch("src.recovery.killer.os.kill", side_effect=ProcessLookupError)
    def test_not_running(self, mock_kill):
        assert is_process_running(1234) is False

    @patch("src.recovery.killer.os.kill", side_effect=PermissionError)
    def test_permission_error_means_running(self, mock_kill):
        assert is_process_running(1234) is True


class TestKillProcess:
    @patch("src.recovery.killer.time.sleep")
    @patch("src.recovery.killer.is_process_running")
    @patch("src.recovery.killer.os.kill")
    def test_kill_sends_sigterm(self, mock_kill, mock_running, mock_sleep):
        mock_running.side_effect = [True, False]
        result = kill_process(1234)
        assert result.success is True
        assert mock_kill.call_args_list[0][0][1] == 15  # SIGTERM

    @patch("src.recovery.killer.time.sleep")
    @patch("src.recovery.killer.time.monotonic")
    @patch("src.recovery.killer.is_process_running", return_value=True)
    @patch("src.recovery.killer.os.kill")
    def test_kill_escalates_to_sigkill(
        self, mock_kill, mock_running, mock_mono, mock_sleep
    ):
        # Simulate time passing: start=0, first check=0.5, past deadline=11
        mock_mono.side_effect = [0.0, 0.5, 11.0]
        # After SIGKILL, process is dead
        mock_running.side_effect = [True, False]
        result = kill_process(1234, timeout=1.0)
        assert result.success is True
        kill_signals = [c[0][1] for c in mock_kill.call_args_list]
        assert 15 in kill_signals  # SIGTERM
        assert 9 in kill_signals   # SIGKILL

    @patch("src.recovery.killer.time.sleep")
    @patch("src.recovery.killer.is_process_running", return_value=False)
    @patch("src.recovery.killer.os.kill")
    def test_kill_success_immediate(
        self, mock_kill, mock_running, mock_sleep
    ):
        result = kill_process(1234)
        assert result.success is True
        assert result.pid == 1234

    @patch("src.recovery.killer.os.kill", side_effect=ProcessLookupError)
    def test_kill_process_already_dead(self, mock_kill):
        result = kill_process(1234)
        assert result.success is True

    @patch("src.recovery.killer.os.kill", side_effect=PermissionError("denied"))
    def test_kill_permission_denied(self, mock_kill):
        result = kill_process(1234)
        assert result.success is False
        assert "denied" in result.error
