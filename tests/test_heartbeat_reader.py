"""Tests for heartbeat reader."""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.heartbeat.reader import HeartbeatData, read_heartbeat, read_all_heartbeats


@pytest.fixture
def valid_heartbeat_data():
    return {
        "process_key": "test_server",
        "pid": 12345,
        "timestamp": "2026-02-04T10:00:00+00:00",
        "status": "running",
        "iteration": 42,
    }


@pytest.fixture
def heartbeat_file(tmp_path, valid_heartbeat_data):
    path = tmp_path / "test_server.json"
    path.write_text(json.dumps(valid_heartbeat_data))
    return path


def test_read_valid_heartbeat(heartbeat_file):
    result = read_heartbeat(heartbeat_file)
    assert result is not None
    assert result.process_key == "test_server"
    assert result.pid == 12345
    assert result.status == "running"
    assert result.iteration == 42
    assert isinstance(result.timestamp, datetime)


def test_read_heartbeat_timestamp_is_aware(heartbeat_file):
    result = read_heartbeat(heartbeat_file)
    assert result.timestamp.tzinfo is not None


def test_read_missing_file(tmp_path):
    result = read_heartbeat(tmp_path / "nonexistent.json")
    assert result is None


def test_read_corrupt_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{{")
    result = read_heartbeat(bad)
    assert result is None


def test_read_incomplete_json(tmp_path):
    incomplete = tmp_path / "incomplete.json"
    incomplete.write_text(json.dumps({"process_key": "x"}))
    result = read_heartbeat(incomplete)
    assert result is None


def test_read_all_heartbeats(tmp_path):
    for name in ["server.json", "player.json"]:
        (tmp_path / name).write_text(json.dumps({
            "process_key": name.replace(".json", ""),
            "pid": 100,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "iteration": 1,
        }))
    results = read_all_heartbeats(tmp_path)
    assert len(results) == 2
    assert "server.json" in results
    assert "player.json" in results


def test_read_all_heartbeats_skips_corrupt(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps({
        "process_key": "good",
        "pid": 100,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "iteration": 1,
    }))
    bad = tmp_path / "bad.json"
    bad.write_text("corrupt")

    results = read_all_heartbeats(tmp_path)
    assert len(results) == 1
    assert "good.json" in results


def test_read_all_heartbeats_empty_dir(tmp_path):
    results = read_all_heartbeats(tmp_path)
    assert results == {}


def test_heartbeat_data_file_path(heartbeat_file):
    result = read_heartbeat(heartbeat_file)
    assert result.file_path == heartbeat_file
