"""Tests for process health checker."""

import json
import os
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from src.config.constants import ProcessHealth
from src.monitor.checker import check_process, check_all_processes


@pytest.fixture
def process_config():
    return {
        "display_name": "TestServer",
        "timeout_seconds": 60,
        "startup_command": "python server.py",
        "cleanup_script": "/tmp/cleanup.sh",
        "heartbeat_filename": "test_server.json",
        "enabled": True,
    }


def _write_heartbeat(hb_dir, filename, timestamp, pid=None):
    """Helper to write a heartbeat file for testing."""
    (hb_dir / filename).write_text(json.dumps({
        "process_key": "test_server",
        "pid": pid or os.getpid(),
        "timestamp": timestamp.isoformat(),
        "status": "running",
        "iteration": 1,
    }))


def test_healthy_process(tmp_path, process_config):
    now = datetime.now(timezone.utc)
    _write_heartbeat(tmp_path, "test_server.json", now)

    result = check_process("test_server", process_config, tmp_path)
    assert result.health == ProcessHealth.HEALTHY
    assert result.pid == os.getpid()


def test_timed_out_process(tmp_path, process_config):
    old = datetime.now(timezone.utc) - timedelta(seconds=120)
    _write_heartbeat(tmp_path, "test_server.json", old)

    result = check_process("test_server", process_config, tmp_path)
    assert result.health == ProcessHealth.TIMED_OUT
    assert result.elapsed_seconds >= 120


def test_no_heartbeat_file(tmp_path, process_config):
    result = check_process("test_server", process_config, tmp_path)
    assert result.health == ProcessHealth.NO_HEARTBEAT
    assert result.pid is None


def test_stale_pid(tmp_path, process_config):
    now = datetime.now(timezone.utc)
    _write_heartbeat(tmp_path, "test_server.json", now, pid=999999)

    with patch("src.monitor.checker.is_pid_alive", return_value=False):
        result = check_process("test_server", process_config, tmp_path)
    assert result.health == ProcessHealth.STALE_PID
    assert result.pid == 999999


def test_check_all_processes(tmp_path):
    config = {
        "heartbeat_dir": str(tmp_path),
        "processes": {
            "healthy": {
                "display_name": "Healthy",
                "timeout_seconds": 60,
                "startup_command": "echo",
                "cleanup_script": "echo",
                "heartbeat_filename": "healthy.json",
                "enabled": True,
            },
            "dead": {
                "display_name": "Dead",
                "timeout_seconds": 60,
                "startup_command": "echo",
                "cleanup_script": "echo",
                "heartbeat_filename": "dead.json",
                "enabled": True,
            },
        },
    }
    now = datetime.now(timezone.utc)
    _write_heartbeat(tmp_path, "healthy.json", now)

    report = check_all_processes(config)
    assert report.processes_checked == 2
    assert report.processes_healthy == 1
    assert report.processes_unhealthy == 1


def test_check_all_skips_disabled(tmp_path):
    config = {
        "heartbeat_dir": str(tmp_path),
        "processes": {
            "disabled": {
                "display_name": "Disabled",
                "timeout_seconds": 60,
                "startup_command": "echo",
                "cleanup_script": "echo",
                "heartbeat_filename": "disabled.json",
                "enabled": False,
            },
        },
    }
    report = check_all_processes(config)
    assert report.processes_checked == 0
