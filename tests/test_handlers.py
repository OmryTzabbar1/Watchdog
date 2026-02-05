"""Tests for CLI command handlers."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from src.pipeline.recovery_pipeline import PipelineResult
from src.recovery.killer import KillResult
from src.recovery.restarter import RestartResult
from src.cli.handlers import (
    handle_on,
    handle_off,
    handle_restart,
    handle_stop_all,
    handle_start_all,
)


@pytest.fixture
def config(tmp_path):
    return {
        "processes": {
            "server": {
                "display_name": "Server",
                "timeout_seconds": 60,
                "heartbeat_path": str(tmp_path / "hb" / "server.json"),
                "enabled": True,
                "commands": {
                    "start": "python server.py",
                    "clear_db": "/tmp/clean.sh",
                },
                "recovery_actions": ["kill", "clear_db", "start"],
            },
            "player": {
                "display_name": "Player",
                "timeout_seconds": 60,
                "heartbeat_path": str(tmp_path / "hb" / "player.json"),
                "enabled": True,
                "commands": {
                    "start": "python player.py",
                    "clear_db": "/tmp/clean2.sh",
                },
                "recovery_actions": ["kill", "clear_db", "start"],
            },
        },
    }


# --- handle_on ---

class TestHandleOn:
    @patch("src.cli.handlers.restart_process")
    def test_starts_process(self, mock_restart, config):
        mock_restart.return_value = RestartResult(
            success=True, pid=9999, command="python server.py"
        )
        code = handle_on(config, "server")
        assert code == 0
        mock_restart.assert_called_once_with("python server.py", verify_delay=2.0)

    @patch("src.cli.handlers.restart_process")
    def test_start_failure(self, mock_restart, config):
        mock_restart.return_value = RestartResult(
            success=False, command="python server.py", error="not found"
        )
        code = handle_on(config, "server")
        assert code == 1

    def test_unknown_process(self, config):
        code = handle_on(config, "nonexistent")
        assert code == 2


# --- handle_off ---

class TestHandleOff:
    @patch("src.cli.handlers.kill_process")
    @patch("src.cli.handlers.read_heartbeat")
    def test_kills_process(self, mock_hb, mock_kill, config):
        mock_hb.return_value = MagicMock(pid=1234)
        mock_kill.return_value = KillResult(success=True, pid=1234)
        code = handle_off(config, "server")
        assert code == 0
        mock_kill.assert_called_once_with(1234, timeout=10.0)

    @patch("src.cli.handlers.read_heartbeat")
    def test_no_heartbeat(self, mock_hb, config):
        mock_hb.return_value = None
        code = handle_off(config, "server")
        assert code == 0

    @patch("src.cli.handlers.kill_process")
    @patch("src.cli.handlers.read_heartbeat")
    def test_kill_failure(self, mock_hb, mock_kill, config):
        mock_hb.return_value = MagicMock(pid=1234)
        mock_kill.return_value = KillResult(
            success=False, pid=1234, error="permission denied"
        )
        code = handle_off(config, "server")
        assert code == 1

    def test_unknown_process(self, config):
        code = handle_off(config, "nonexistent")
        assert code == 2


# --- handle_restart ---

class TestHandleRestart:
    @patch("src.cli.handlers.run_recovery")
    @patch("src.cli.handlers.read_heartbeat")
    def test_runs_recovery(self, mock_hb, mock_recovery, config):
        mock_hb.return_value = MagicMock(pid=1234)
        mock_recovery.return_value = PipelineResult(
            process_key="server", fully_recovered=True
        )
        code = handle_restart(config, "server")
        assert code == 0
        mock_recovery.assert_called_once()

    @patch("src.cli.handlers.run_recovery")
    @patch("src.cli.handlers.read_heartbeat")
    def test_recovery_failure(self, mock_hb, mock_recovery, config):
        mock_hb.return_value = MagicMock(pid=1234)
        mock_recovery.return_value = PipelineResult(
            process_key="server", fully_recovered=False, stage_failed="start"
        )
        code = handle_restart(config, "server")
        assert code == 1

    def test_unknown_process(self, config):
        code = handle_restart(config, "nonexistent")
        assert code == 2


# --- handle_stop_all / handle_start_all ---

class TestBulkCommands:
    @patch("src.cli.handlers.kill_process")
    @patch("src.cli.handlers.read_heartbeat")
    def test_stop_all(self, mock_hb, mock_kill, config):
        mock_hb.return_value = MagicMock(pid=1234)
        mock_kill.return_value = KillResult(success=True, pid=1234)
        code = handle_stop_all(config)
        assert code == 0
        assert mock_kill.call_count == 2

    @patch("src.cli.handlers.restart_process")
    def test_start_all(self, mock_restart, config):
        mock_restart.return_value = RestartResult(
            success=True, pid=9999, command="test"
        )
        code = handle_start_all(config)
        assert code == 0
        assert mock_restart.call_count == 2
