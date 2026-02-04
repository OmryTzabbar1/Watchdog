"""Tests for process restarter module."""

import pytest
from unittest.mock import patch, MagicMock

from src.recovery.restarter import RestartResult, restart_process


class TestRestartProcess:
    @patch("src.recovery.restarter.time.sleep")
    @patch("src.recovery.restarter.subprocess.Popen")
    def test_restart_success(self, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.pid = 9999
        mock_proc.poll.return_value = None  # still running
        mock_popen.return_value = mock_proc

        result = restart_process("python server.py")
        assert result.success is True
        assert result.pid == 9999

    @patch("src.recovery.restarter.time.sleep")
    @patch("src.recovery.restarter.subprocess.Popen")
    def test_restart_command_not_found(self, mock_popen, mock_sleep):
        mock_popen.side_effect = FileNotFoundError("not found")
        result = restart_process("nonexistent_cmd")
        assert result.success is False
        assert result.error is not None

    @patch("src.recovery.restarter.time.sleep")
    @patch("src.recovery.restarter.subprocess.Popen")
    def test_restart_process_detached(self, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.pid = 9999
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        restart_process("python server.py")
        assert mock_popen.call_args.kwargs["start_new_session"] is True

    @patch("src.recovery.restarter.time.sleep")
    @patch("src.recovery.restarter.subprocess.Popen")
    def test_restart_process_dies_immediately(self, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.pid = 9999
        mock_proc.poll.return_value = 1  # exited with error
        mock_popen.return_value = mock_proc

        result = restart_process("python server.py")
        assert result.success is False
        assert "exited immediately" in result.error.lower()

    @patch("src.recovery.restarter.time.sleep")
    @patch("src.recovery.restarter.subprocess.Popen")
    def test_restart_uses_shell(self, mock_popen, mock_sleep):
        mock_proc = MagicMock()
        mock_proc.pid = 9999
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        restart_process("cd /tmp && python server.py")
        assert mock_popen.call_args.kwargs["shell"] is True
