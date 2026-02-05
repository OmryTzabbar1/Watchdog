"""Tests for heartbeat writer library."""

import json
import os
import pytest

from src.heartbeat.writer import HeartbeatWriter


@pytest.fixture
def writer(tmp_path):
    return HeartbeatWriter(
        heartbeat_dir=str(tmp_path),
        process_key="test_process",
    )


def test_beat_creates_file(writer, tmp_path):
    writer.beat()
    path = tmp_path / "test_process.json"
    assert path.exists()


def test_beat_writes_valid_json(writer, tmp_path):
    writer.beat()
    path = tmp_path / "test_process.json"
    data = json.loads(path.read_text())
    assert data["process_key"] == "test_process"
    assert "pid" in data
    assert "timestamp" in data
    assert data["status"] == "running"
    assert data["iteration"] == 1


def test_beat_increments_iteration(writer, tmp_path):
    writer.beat()
    writer.beat()
    writer.beat()
    path = tmp_path / "test_process.json"
    data = json.loads(path.read_text())
    assert data["iteration"] == 3


def test_beat_uses_current_pid(writer, tmp_path):
    writer.beat()
    path = tmp_path / "test_process.json"
    data = json.loads(path.read_text())
    assert data["pid"] == os.getpid()


def test_beat_atomic_write(writer, tmp_path):
    """File should always contain valid JSON (atomic write)."""
    for _ in range(10):
        writer.beat()
        path = tmp_path / "test_process.json"
        data = json.loads(path.read_text())
        assert "process_key" in data


def test_stop_removes_file(writer, tmp_path):
    writer.beat()
    path = tmp_path / "test_process.json"
    assert path.exists()
    writer.stop()
    assert not path.exists()


def test_stop_no_error_if_file_missing(writer):
    writer.stop()


def test_custom_filename(tmp_path):
    writer = HeartbeatWriter(
        heartbeat_dir=str(tmp_path),
        process_key="test_process",
        heartbeat_filename="custom.json",
    )
    writer.beat()
    assert (tmp_path / "custom.json").exists()
    assert not (tmp_path / "test_process.json").exists()


def test_heartbeat_path_property(writer, tmp_path):
    expected = tmp_path / "test_process.json"
    assert writer.heartbeat_path == expected


def test_iteration_count_property(writer):
    assert writer.iteration_count == 0
    writer.beat()
    assert writer.iteration_count == 1


def test_creates_heartbeat_dir_if_missing(tmp_path):
    hb_dir = tmp_path / "nested" / "heartbeats"
    writer = HeartbeatWriter(
        heartbeat_dir=str(hb_dir),
        process_key="test",
    )
    writer.beat()
    assert (hb_dir / "test.json").exists()


def test_beat_with_error_status(writer, tmp_path):
    """Processes can report errors via status parameter."""
    writer.beat(status="error")
    path = tmp_path / "test_process.json"
    data = json.loads(path.read_text())
    assert data["status"] == "error"


def test_beat_status_defaults_to_running(writer, tmp_path):
    """Default status is 'running'."""
    writer.beat()
    path = tmp_path / "test_process.json"
    data = json.loads(path.read_text())
    assert data["status"] == "running"
