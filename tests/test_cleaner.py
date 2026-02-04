"""Tests for cleanup script runner."""

import subprocess
import pytest
from unittest.mock import patch, MagicMock

from src.recovery.cleaner import CleanResult, run_cleanup


class TestRunCleanup:
    @patch("src.recovery.cleaner.subprocess.run")
    def test_cleanup_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="ok", stderr=""
        )
        result = run_cleanup("/tmp/cleanup.sh")
        assert result.success is True
        assert result.return_code == 0
        assert result.stdout == "ok"

    @patch("src.recovery.cleaner.subprocess.run")
    def test_cleanup_failure_exit_code(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="db error"
        )
        result = run_cleanup("/tmp/cleanup.sh")
        assert result.success is False
        assert result.return_code == 1
        assert result.stderr == "db error"

    @patch("src.recovery.cleaner.subprocess.run")
    def test_cleanup_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="/tmp/cleanup.sh", timeout=60
        )
        result = run_cleanup("/tmp/cleanup.sh")
        assert result.success is False
        assert "timed out" in result.error.lower()

    @patch("src.recovery.cleaner.subprocess.run")
    def test_cleanup_script_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("No such file")
        result = run_cleanup("/tmp/nonexistent.sh")
        assert result.success is False
        assert result.error is not None

    @patch("src.recovery.cleaner.subprocess.run")
    def test_cleanup_passes_correct_timeout(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr=""
        )
        run_cleanup("/tmp/cleanup.sh", timeout=30.0)
        mock_run.assert_called_once()
        assert mock_run.call_args.kwargs["timeout"] == 30.0

    @patch("src.recovery.cleaner.subprocess.run")
    def test_cleanup_captures_output(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr=""
        )
        run_cleanup("/tmp/cleanup.sh")
        assert mock_run.call_args.kwargs["capture_output"] is True
        assert mock_run.call_args.kwargs["text"] is True

    @patch("src.recovery.cleaner.subprocess.run")
    def test_cleanup_passes_force_flag(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr=""
        )
        run_cleanup("/tmp/cleanup.sh")
        assert mock_run.call_args[0][0] == ["/tmp/cleanup.sh", "--force"]
