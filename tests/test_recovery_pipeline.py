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

PROC_CONFIG = {
    "commands": {"start": "python s.py", "clear_db": "/tmp/clean.sh"},
    "recovery_actions": ["kill", "clear_db", "start"],
}


def _config(**overrides):
    """Build a proc_config with overrides."""
    cfg = dict(PROC_CONFIG)
    cfg["commands"] = dict(cfg["commands"])
    cfg.update(overrides)
    return cfg


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

        result = run_recovery("test", 1234, PROC_CONFIG)
        assert result.fully_recovered is True
        assert result.stage_failed is None

    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.run_cleanup")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_stops_on_kill_failure(
        self, mock_kill, mock_clean, mock_restart
    ):
        mock_kill.return_value = KILL_FAIL

        result = run_recovery("test", 1234, PROC_CONFIG)
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

        result = run_recovery("test", 1234, PROC_CONFIG)
        assert result.fully_recovered is True
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

        result = run_recovery("test", 1234, PROC_CONFIG)
        assert result.fully_recovered is False
        assert result.stage_failed == "start"

    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.run_cleanup")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_skip_kill_when_no_pid(
        self, mock_kill, mock_clean, mock_restart
    ):
        mock_clean.return_value = CLEAN_OK
        mock_restart.return_value = RESTART_OK

        result = run_recovery("test", None, PROC_CONFIG)
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

        result = run_recovery("test", 1234, PROC_CONFIG)
        assert result.kill_result is KILL_OK
        assert result.restart_result is RESTART_OK
        assert result.process_key == "test"

    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.run_cleanup")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_custom_action_order(
        self, mock_kill, mock_clean, mock_restart
    ):
        """Actions with clear_email_logs added."""
        mock_kill.return_value = KILL_OK
        mock_clean.return_value = CLEAN_OK
        mock_restart.return_value = RESTART_OK

        cfg = {
            "commands": {
                "start": "python s.py",
                "clear_db": "/tmp/clean.sh",
                "clear_email_logs": "/tmp/clear_emails.sh",
            },
            "recovery_actions": ["kill", "clear_db", "clear_email_logs", "start"],
        }
        result = run_recovery("test", 1234, cfg)
        assert result.fully_recovered is True
        assert mock_clean.call_count == 2  # clear_db + clear_email_logs

    @patch("src.pipeline.recovery_pipeline.restart_process")
    @patch("src.pipeline.recovery_pipeline.kill_process")
    def test_skip_kill_only_config(self, mock_kill, mock_restart):
        """Config with only start (no kill, no cleanup)."""
        mock_restart.return_value = RESTART_OK

        cfg = {
            "commands": {"start": "python s.py"},
            "recovery_actions": ["start"],
        }
        result = run_recovery("test", 1234, cfg)
        assert result.fully_recovered is True
        mock_kill.assert_not_called()
