"""Tests for the recovery pipeline orchestrator."""

import pytest
from unittest.mock import patch

from src.recovery.killer import KillResult
from src.recovery.cleaner import CleanResult
from src.recovery.restarter import RestartResult
from src.pipeline.recovery_pipeline import PipelineResult, run_recovery


KILL_OK = KillResult(success=True, pid=1234)
KILL_FAIL = KillResult(success=False, pid=1234, error="permission denied")
CLEAN_OK = CleanResult(success=True, script_path="/tmp/clean.sh")
CLEAN_FAIL = CleanResult(
    success=False, script_path="/tmp/clean.sh", error="db error"
)
RESTART_OK = RestartResult(success=True, pid=5678, command="python s.py")
RESTART_FAIL = RestartResult(
    success=False, command="python s.py", error="not found"
)


class TestRunRecovery:
    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.run_cleanup")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_full_recovery_success(
        self, mock_kill, mock_clean, mock_restart
    ):
        mock_kill.return_value = KILL_OK
        mock_clean.return_value = CLEAN_OK
        mock_restart.return_value = RESTART_OK

        result = run_recovery("test", 1234, "/tmp/clean.sh", "python s.py")
        assert result.fully_recovered is True
        assert result.stage_failed is None

    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.run_cleanup")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_stops_on_kill_failure(
        self, mock_kill, mock_clean, mock_restart
    ):
        mock_kill.return_value = KILL_FAIL

        result = run_recovery("test", 1234, "/tmp/clean.sh", "python s.py")
        assert result.fully_recovered is False
        assert result.stage_failed == "kill"
        mock_clean.assert_not_called()
        mock_restart.assert_not_called()

    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.run_cleanup")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_continues_on_cleanup_failure(
        self, mock_kill, mock_clean, mock_restart
    ):
        mock_kill.return_value = KILL_OK
        mock_clean.return_value = CLEAN_FAIL
        mock_restart.return_value = RESTART_OK

        result = run_recovery("test", 1234, "/tmp/clean.sh", "python s.py")
        assert result.fully_recovered is True
        assert result.clean_result.success is False
        mock_restart.assert_called_once()

    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.run_cleanup")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_restart_failure(
        self, mock_kill, mock_clean, mock_restart
    ):
        mock_kill.return_value = KILL_OK
        mock_clean.return_value = CLEAN_OK
        mock_restart.return_value = RESTART_FAIL

        result = run_recovery("test", 1234, "/tmp/clean.sh", "python s.py")
        assert result.fully_recovered is False
        assert result.stage_failed == "restart"

    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.run_cleanup")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_skip_kill_when_no_pid(
        self, mock_kill, mock_clean, mock_restart
    ):
        mock_clean.return_value = CLEAN_OK
        mock_restart.return_value = RESTART_OK

        result = run_recovery("test", None, "/tmp/clean.sh", "python s.py")
        assert result.fully_recovered is True
        mock_kill.assert_not_called()

    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.run_cleanup")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_records_all_results(
        self, mock_kill, mock_clean, mock_restart
    ):
        mock_kill.return_value = KILL_OK
        mock_clean.return_value = CLEAN_OK
        mock_restart.return_value = RESTART_OK

        result = run_recovery("test", 1234, "/tmp/clean.sh", "python s.py")
        assert result.kill_result is KILL_OK
        assert result.clean_result is CLEAN_OK
        assert result.restart_result is RESTART_OK
        assert result.process_key == "test"
