"""Tests for the CLI entry point."""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config.constants import ProcessHealth
from src.monitor.models import CheckResult, MonitorReport
from src.pipeline.recovery_pipeline import PipelineResult
from src.cli.main import main
from src.cli.check import acquire_lock


@pytest.fixture
def config_file(tmp_path):
    db_path = str(tmp_path / "test_watchdog.db")
    config = {
        "log_level": "WARNING",
        "db_path": db_path,
        "consecutive_failures_threshold": 2,
        "processes": {
            "server": {
                "display_name": "Server",
                "timeout_seconds": 60,
                "heartbeat_path": str(tmp_path / "heartbeats" / "server.json"),
                "enabled": True,
                "commands": {
                    "start": "python server.py",
                    "clear_db": "/tmp/clean.sh",
                },
                "recovery_actions": ["kill", "clear_db", "start"],
            },
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    return str(path)


def _make_report(health=ProcessHealth.HEALTHY):
    return MonitorReport(
        timestamp=datetime.now(timezone.utc),
        results=[
            CheckResult(
                process_key="server",
                display_name="Server",
                health=health,
                pid=1234,
                last_heartbeat=datetime.now(timezone.utc),
                elapsed_seconds=10.0,
                timeout_seconds=60,
            )
        ],
    )


class TestMain:
    @patch("src.cli.check.acquire_lock")
    @patch("src.cli.check.run_recovery")
    @patch("src.cli.check.check_all_processes")
    def test_all_healthy_no_recovery(
        self, mock_check, mock_recover, mock_lock, config_file
    ):
        mock_lock.return_value = MagicMock()
        mock_check.return_value = _make_report(ProcessHealth.HEALTHY)

        exit_code = main(["-c", config_file])
        assert exit_code == 0
        mock_recover.assert_not_called()

    @patch("src.cli.check.acquire_lock")
    @patch("src.cli.check.run_recovery")
    @patch("src.cli.check.check_all_processes")
    def test_first_failure_no_recovery(
        self, mock_check, mock_recover, mock_lock, config_file
    ):
        """First failure should NOT trigger recovery (threshold=2)."""
        mock_lock.return_value = MagicMock()
        mock_check.return_value = _make_report(ProcessHealth.TIMED_OUT)

        exit_code = main(["-c", config_file])
        assert exit_code == 0
        mock_recover.assert_not_called()

    @patch("src.cli.check.acquire_lock")
    @patch("src.cli.check.run_recovery")
    @patch("src.cli.check.check_all_processes")
    def test_second_failure_triggers_recovery(
        self, mock_check, mock_recover, mock_lock, config_file
    ):
        """Second consecutive failure SHOULD trigger recovery."""
        mock_lock.return_value = MagicMock()
        mock_check.return_value = _make_report(ProcessHealth.TIMED_OUT)
        mock_recover.return_value = PipelineResult(
            process_key="server", fully_recovered=True
        )

        main(["-c", config_file])
        mock_recover.assert_not_called()

        main(["-c", config_file])
        mock_recover.assert_called_once()

    @patch("src.cli.check.acquire_lock")
    @patch("src.cli.check.run_recovery")
    @patch("src.cli.check.check_all_processes")
    def test_healthy_resets_failure_counter(
        self, mock_check, mock_recover, mock_lock, config_file
    ):
        """Healthy check resets counter — next failure starts from 1 again."""
        mock_lock.return_value = MagicMock()
        mock_recover.return_value = PipelineResult(
            process_key="server", fully_recovered=True
        )

        mock_check.return_value = _make_report(ProcessHealth.TIMED_OUT)
        main(["-c", config_file])

        mock_check.return_value = _make_report(ProcessHealth.HEALTHY)
        main(["-c", config_file])

        mock_check.return_value = _make_report(ProcessHealth.TIMED_OUT)
        main(["-c", config_file])
        mock_recover.assert_not_called()

    @patch("src.cli.check.acquire_lock")
    @patch("src.cli.check.run_recovery")
    @patch("src.cli.check.check_all_processes")
    def test_no_heartbeat_triggers_after_threshold(
        self, mock_check, mock_recover, mock_lock, config_file
    ):
        mock_lock.return_value = MagicMock()
        report = _make_report(ProcessHealth.NO_HEARTBEAT)
        report.results[0].pid = None
        report.results[0].last_heartbeat = None
        mock_check.return_value = report
        mock_recover.return_value = PipelineResult(
            process_key="server", fully_recovered=True
        )

        main(["-c", config_file])
        mock_recover.assert_not_called()

        main(["-c", config_file])
        mock_recover.assert_called_once()

    @patch("src.cli.check.acquire_lock")
    @patch("src.cli.check.run_recovery")
    @patch("src.cli.check.check_all_processes")
    def test_recovery_failure_returns_1(
        self, mock_check, mock_recover, mock_lock, config_file
    ):
        mock_lock.return_value = MagicMock()
        mock_check.return_value = _make_report(ProcessHealth.TIMED_OUT)
        mock_recover.return_value = PipelineResult(
            process_key="server",
            fully_recovered=False,
            stage_failed="start",
        )

        exit_code = main(["-c", config_file])
        assert exit_code == 0

        exit_code = main(["-c", config_file])
        assert exit_code == 1

    @patch("src.cli.check.acquire_lock")
    @patch("src.cli.check.run_recovery")
    @patch("src.cli.check.check_all_processes")
    def test_successful_recovery_resets_counter(
        self, mock_check, mock_recover, mock_lock, config_file
    ):
        """After successful recovery, counter resets — need 2 more failures."""
        mock_lock.return_value = MagicMock()
        mock_check.return_value = _make_report(ProcessHealth.TIMED_OUT)
        mock_recover.return_value = PipelineResult(
            process_key="server", fully_recovered=True
        )

        main(["-c", config_file])
        main(["-c", config_file])
        assert mock_recover.call_count == 1

        main(["-c", config_file])
        assert mock_recover.call_count == 1

        main(["-c", config_file])
        assert mock_recover.call_count == 2

    def test_missing_config_returns_2(self):
        exit_code = main(["-c", "/nonexistent/config.json"])
        assert exit_code == 2

    @patch("src.cli.check.acquire_lock", return_value=None)
    def test_locked_returns_0(self, mock_lock, config_file):
        exit_code = main(["-c", config_file])
        assert exit_code == 0


class TestAcquireLock:
    def test_acquires_lock(self, tmp_path):
        lock_path = str(tmp_path / "test.lock")
        lock = acquire_lock(lock_path)
        assert lock is not None
        lock.close()

    def test_returns_none_if_locked(self, tmp_path):
        import fcntl
        lock_path = str(tmp_path / "test.lock")
        f1 = open(lock_path, "w")
        fcntl.flock(f1, fcntl.LOCK_EX | fcntl.LOCK_NB)

        lock = acquire_lock(lock_path)
        assert lock is None
        f1.close()
