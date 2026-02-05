# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Tests for menu action handlers."""

import pytest
from unittest.mock import patch, MagicMock

from src.cli.menu.actions import (
    start_process,
    kill_process_by_key,
    restart_process_by_key,
    clear_db_by_key,
    clear_emails_by_key,
    recover_process_by_key,
    start_all,
    stop_all,
    restart_all,
    clear_db_all,
    clear_emails_all,
    recover_all,
)


@pytest.fixture
def mock_proc():
    """Sample process config."""
    return {
        "commands": {"start": "echo start", "clear_db": "echo clear", "clear_emails": "echo emails"},
        "heartbeat_path": "/tmp/test.json",
    }


@pytest.fixture
def mock_state():
    """Mock MenuState with two processes."""
    state = MagicMock()
    state.get_process_keys.return_value = ["proc_a", "proc_b"]
    state.is_process_enabled.return_value = True
    state.get_process_config.side_effect = lambda k: {
        "commands": {"start": f"echo {k}", "clear_db": f"echo clear {k}", "clear_emails": f"echo emails {k}"},
        "heartbeat_path": f"/tmp/{k}.json",
    }
    return state


class TestRestartProcessByKey:
    """Tests for restart_process_by_key."""

    @patch("src.cli.menu.actions.start_process")
    @patch("src.cli.menu.actions.kill_process_by_key")
    def test_restart_calls_kill_then_start(self, mock_kill, mock_start, mock_proc):
        mock_kill.return_value = (True, "Killed")
        mock_start.return_value = (True, "Started")

        success, msg = restart_process_by_key("test", mock_proc)

        assert success is True
        assert "Restarted" in msg
        mock_kill.assert_called_once_with("test", mock_proc)
        mock_start.assert_called_once_with("test", mock_proc)

    @patch("src.cli.menu.actions.start_process")
    @patch("src.cli.menu.actions.kill_process_by_key")
    def test_restart_continues_if_kill_fails(self, mock_kill, mock_start, mock_proc):
        mock_kill.return_value = (False, "No process")
        mock_start.return_value = (True, "Started")

        success, msg = restart_process_by_key("test", mock_proc)

        assert success is True
        mock_start.assert_called_once()

    @patch("src.cli.menu.actions.start_process")
    @patch("src.cli.menu.actions.kill_process_by_key")
    def test_restart_fails_if_start_fails(self, mock_kill, mock_start, mock_proc):
        mock_kill.return_value = (True, "Killed")
        mock_start.return_value = (False, "Start failed")

        success, msg = restart_process_by_key("test", mock_proc)

        assert success is False
        assert "failed" in msg.lower()


class TestStartAll:
    """Tests for start_all."""

    @patch("src.cli.menu.actions.start_process")
    def test_start_all_starts_enabled_processes(self, mock_start, mock_state):
        mock_start.return_value = (True, "Started")

        ok, fail, msgs = start_all(mock_state)

        assert ok == 2
        assert fail == 0
        assert mock_start.call_count == 2

    @patch("src.cli.menu.actions.start_process")
    def test_start_all_skips_disabled(self, mock_start, mock_state):
        mock_state.is_process_enabled.side_effect = lambda k: k == "proc_a"
        mock_start.return_value = (True, "Started")

        ok, fail, msgs = start_all(mock_state)

        assert ok == 1
        assert mock_start.call_count == 1

    @patch("src.cli.menu.actions.start_process")
    def test_start_all_counts_failures(self, mock_start, mock_state):
        mock_start.side_effect = [(True, "OK"), (False, "Fail")]

        ok, fail, msgs = start_all(mock_state)

        assert ok == 1
        assert fail == 1


class TestStopAll:
    """Tests for stop_all."""

    @patch("src.cli.menu.actions.kill_process_by_key")
    def test_stop_all_kills_enabled_processes(self, mock_kill, mock_state):
        mock_kill.return_value = (True, "Killed")

        ok, fail, msgs = stop_all(mock_state)

        assert ok == 2
        assert fail == 0

    @patch("src.cli.menu.actions.kill_process_by_key")
    def test_stop_all_skips_disabled(self, mock_kill, mock_state):
        mock_state.is_process_enabled.side_effect = lambda k: k == "proc_a"
        mock_kill.return_value = (True, "Killed")

        ok, fail, msgs = stop_all(mock_state)

        assert ok == 1


class TestRestartAll:
    """Tests for restart_all."""

    @patch("src.cli.menu.actions.restart_process_by_key")
    def test_restart_all_restarts_enabled_processes(self, mock_restart, mock_state):
        mock_restart.return_value = (True, "Restarted")
        ok, fail, msgs = restart_all(mock_state)
        assert ok == 2 and fail == 0

    @patch("src.cli.menu.actions.restart_process_by_key")
    def test_restart_all_counts_failures(self, mock_restart, mock_state):
        mock_restart.side_effect = [(True, "OK"), (False, "Fail")]
        ok, fail, msgs = restart_all(mock_state)
        assert ok == 1 and fail == 1


class TestClearDbByKey:
    """Tests for clear_db_by_key."""

    @patch("src.cli.menu.actions.run_cleanup")
    def test_clear_db_runs_command(self, mock_cleanup, mock_proc):
        mock_cleanup.return_value = MagicMock(success=True)
        success, msg = clear_db_by_key("test", mock_proc)
        assert success is True
        mock_cleanup.assert_called_once()

    def test_clear_db_no_command(self):
        proc = {"commands": {}}
        success, msg = clear_db_by_key("test", proc)
        assert success is False and "No clear_db" in msg


class TestRecoverProcessByKey:
    """Tests for recover_process_by_key."""

    @patch("src.cli.menu.actions.start_process")
    @patch("src.cli.menu.actions.clear_db_by_key")
    @patch("src.cli.menu.actions.kill_process_by_key")
    def test_recover_runs_full_pipeline(self, mock_kill, mock_clear, mock_start, mock_proc):
        mock_kill.return_value = (True, "Killed")
        mock_clear.return_value = (True, "Cleared")
        mock_start.return_value = (True, "Started")
        success, msg = recover_process_by_key("test", mock_proc)
        assert success is True and "Recovered" in msg

    @patch("src.cli.menu.actions.start_process")
    @patch("src.cli.menu.actions.clear_db_by_key")
    @patch("src.cli.menu.actions.kill_process_by_key")
    def test_recover_fails_if_start_fails(self, mock_kill, mock_clear, mock_start, mock_proc):
        mock_kill.return_value = (True, "Killed")
        mock_clear.return_value = (True, "Cleared")
        mock_start.return_value = (False, "Failed")
        success, msg = recover_process_by_key("test", mock_proc)
        assert success is False


class TestClearDbAll:
    """Tests for clear_db_all."""

    @patch("src.cli.menu.actions.clear_db_by_key")
    def test_clear_db_all_clears_enabled(self, mock_clear, mock_state):
        mock_clear.return_value = (True, "Cleared")
        ok, fail, msgs = clear_db_all(mock_state)
        assert ok == 2 and mock_clear.call_count == 2


class TestRecoverAll:
    """Tests for recover_all."""

    @patch("src.cli.menu.actions.recover_process_by_key")
    def test_recover_all_recovers_enabled(self, mock_recover, mock_state):
        mock_recover.return_value = (True, "Recovered")
        ok, fail, msgs = recover_all(mock_state)
        assert ok == 2 and fail == 0


class TestClearEmailsByKey:
    """Tests for clear_emails_by_key."""

    @patch("src.cli.menu.actions.run_shell_command")
    def test_clear_emails_runs_command(self, mock_run, mock_proc):
        mock_run.return_value = (True, "OK")
        success, msg = clear_emails_by_key("test", mock_proc)
        assert success is True
        mock_run.assert_called_once()

    def test_clear_emails_no_command(self):
        proc = {"commands": {}}
        success, msg = clear_emails_by_key("test", proc)
        assert success is False and "No clear_emails" in msg


class TestClearEmailsAll:
    """Tests for clear_emails_all."""

    @patch("src.cli.menu.actions.clear_emails_by_key")
    def test_clear_emails_all_clears_enabled(self, mock_clear, mock_state):
        mock_clear.return_value = (True, "Cleared")
        ok, fail, msgs = clear_emails_all(mock_state)
        assert ok == 2 and mock_clear.call_count == 2
