"""Tests for config loading and validation."""

import json
import pytest
from pathlib import Path

from src.config.config_loader import load_config, get_process_configs, validate_config


@pytest.fixture
def valid_config(tmp_path):
    return {
        "heartbeat_dir": str(tmp_path / "heartbeats"),
        "log_level": "INFO",
        "processes": {
            "test_server": {
                "display_name": "TestServer",
                "timeout_seconds": 300,
                "startup_command": "python server.py",
                "cleanup_script": "/tmp/cleanup.sh",
                "heartbeat_filename": "test_server.json",
                "enabled": True,
            },
            "test_player": {
                "display_name": "TestPlayer",
                "timeout_seconds": 120,
                "startup_command": "python player.py",
                "cleanup_script": "/tmp/cleanup2.sh",
                "heartbeat_filename": "test_player.json",
                "enabled": False,
            },
        },
    }


@pytest.fixture
def config_file(tmp_path, valid_config):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(valid_config))
    return path


def test_loads_valid_config(config_file, valid_config):
    config = load_config(str(config_file))
    assert config["heartbeat_dir"] == valid_config["heartbeat_dir"]
    assert "processes" in config
    assert len(config["processes"]) == 2


def test_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.json")


def test_raises_on_invalid_json(tmp_path):
    bad_file = tmp_path / "config.json"
    bad_file.write_text("not valid json {{{")
    with pytest.raises(json.JSONDecodeError):
        load_config(str(bad_file))


def test_get_process_configs_filters_disabled(valid_config):
    enabled = get_process_configs(valid_config)
    assert "test_server" in enabled
    assert "test_player" not in enabled


def test_get_process_configs_returns_all_when_all_enabled(valid_config):
    valid_config["processes"]["test_player"]["enabled"] = True
    enabled = get_process_configs(valid_config)
    assert len(enabled) == 2


def test_validate_config_valid(valid_config):
    errors = validate_config(valid_config)
    assert errors == []


def test_validate_config_missing_heartbeat_dir(valid_config):
    del valid_config["heartbeat_dir"]
    errors = validate_config(valid_config)
    assert any("heartbeat_dir" in e for e in errors)


def test_validate_config_missing_processes(valid_config):
    del valid_config["processes"]
    errors = validate_config(valid_config)
    assert any("processes" in e for e in errors)


def test_validate_config_missing_process_fields(valid_config):
    del valid_config["processes"]["test_server"]["startup_command"]
    errors = validate_config(valid_config)
    assert any("startup_command" in e for e in errors)


def test_validate_config_empty_processes(valid_config):
    valid_config["processes"] = {}
    errors = validate_config(valid_config)
    assert errors == []
