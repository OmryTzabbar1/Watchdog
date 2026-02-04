"""Shared test fixtures for Watchdog tests."""

import json
import os
import pytest
from datetime import datetime, timezone
from pathlib import Path


@pytest.fixture
def heartbeat_dir(tmp_path):
    """Create and return a temp heartbeat directory."""
    hb_dir = tmp_path / "heartbeats"
    hb_dir.mkdir()
    return hb_dir


@pytest.fixture
def sample_config(tmp_path):
    """Config dict with heartbeat_dir pointing to tmp_path."""
    return {
        "heartbeat_dir": str(tmp_path / "heartbeats"),
        "log_level": "WARNING",
        "processes": {
            "test_server": {
                "display_name": "TestServer",
                "timeout_seconds": 60,
                "startup_command": "python server.py",
                "cleanup_script": "/tmp/cleanup.sh",
                "heartbeat_filename": "test_server.json",
                "enabled": True,
            },
        },
    }


@pytest.fixture
def config_file(tmp_path, sample_config):
    """Write sample config to a temp file and return its path."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps(sample_config))
    return path


@pytest.fixture
def sample_heartbeat_data():
    """Valid heartbeat JSON dict."""
    return {
        "process_key": "test_server",
        "pid": os.getpid(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "iteration": 1,
    }
