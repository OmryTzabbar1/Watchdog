"""Tests for config loading and validation."""

import json
import pytest
from pathlib import Path

from src.config.config_loader import (
    load_config,
    get_process_configs,
    get_single_process_config,
    normalize_process_config,
    validate_config,
)


@pytest.fixture
def valid_config(tmp_path):
    return {
        "log_level": "INFO",
        "processes": {
            "test_server": {
                "display_name": "TestServer",
                "timeout_seconds": 300,
                "heartbeat_path": str(tmp_path / "heartbeats" / "test_server.json"),
                "enabled": True,
                "commands": {
                    "start": "python server.py",
                    "clear_db": "/tmp/cleanup.sh",
                },
                "recovery_actions": ["kill", "clear_db", "start"],
            },
            "test_player": {
                "display_name": "TestPlayer",
                "timeout_seconds": 120,
                "heartbeat_path": str(tmp_path / "heartbeats" / "test_player.json"),
                "enabled": False,
                "commands": {
                    "start": "python player.py",
                    "clear_db": "/tmp/cleanup2.sh",
                },
                "recovery_actions": ["kill", "clear_db", "start"],
            },
        },
    }


@pytest.fixture
def old_format_config(tmp_path):
    """Config using old flat fields (startup_command, cleanup_script)."""
    return {
        "display_name": "OldServer",
        "timeout_seconds": 300,
        "heartbeat_path": str(tmp_path / "heartbeats" / "old.json"),
        "enabled": True,
        "startup_command": "python server.py",
        "cleanup_script": "/tmp/cleanup.sh",
    }


@pytest.fixture
def config_file(tmp_path, valid_config):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(valid_config))
    return path


# --- load_config ---

def test_loads_valid_config(config_file, valid_config):
    config = load_config(str(config_file))
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


# --- get_process_configs ---

def test_get_process_configs_filters_disabled(valid_config):
    enabled = get_process_configs(valid_config)
    assert "test_server" in enabled
    assert "test_player" not in enabled


def test_get_process_configs_returns_all_when_all_enabled(valid_config):
    valid_config["processes"]["test_player"]["enabled"] = True
    enabled = get_process_configs(valid_config)
    assert len(enabled) == 2


def test_get_process_configs_normalizes(old_format_config):
    """get_process_configs should normalize old-format configs."""
    config = {"processes": {"old": old_format_config}}
    enabled = get_process_configs(config)
    assert "commands" in enabled["old"]
    assert "start" in enabled["old"]["commands"]


# --- get_single_process_config ---

def test_get_single_process_config(valid_config):
    proc = get_single_process_config(valid_config, "test_server")
    assert proc is not None
    assert proc["display_name"] == "TestServer"
    assert "commands" in proc


def test_get_single_process_config_unknown(valid_config):
    proc = get_single_process_config(valid_config, "nonexistent")
    assert proc is None


def test_get_single_process_config_normalizes(old_format_config):
    config = {"processes": {"old": old_format_config}}
    proc = get_single_process_config(config, "old")
    assert "commands" in proc
    assert proc["commands"]["start"] == "python server.py"


# --- normalize_process_config ---

def test_normalize_new_format_untouched(valid_config):
    proc = valid_config["processes"]["test_server"]
    normalized = normalize_process_config(proc)
    assert normalized is proc  # same object, no changes


def test_normalize_old_format(old_format_config):
    normalized = normalize_process_config(old_format_config)
    assert "commands" in normalized
    assert normalized["commands"]["start"] == "python server.py"
    assert normalized["commands"]["clear_db"] == "/tmp/cleanup.sh"
    assert "startup_command" not in normalized
    assert "cleanup_script" not in normalized


def test_normalize_default_recovery_actions(old_format_config):
    normalized = normalize_process_config(old_format_config)
    assert normalized["recovery_actions"] == ["kill", "clear_db", "start"]


def test_normalize_preserves_existing_recovery_actions():
    proc = {
        "display_name": "X",
        "timeout_seconds": 60,
        "heartbeat_path": "/tmp/x.json",
        "enabled": True,
        "startup_command": "echo hi",
        "cleanup_script": "/tmp/clean.sh",
        "recovery_actions": ["kill", "start"],
    }
    normalized = normalize_process_config(proc)
    assert normalized["recovery_actions"] == ["kill", "start"]


# --- validate_config ---

def test_validate_config_valid(valid_config):
    errors = validate_config(valid_config)
    assert errors == []


def test_validate_config_missing_processes(valid_config):
    del valid_config["processes"]
    errors = validate_config(valid_config)
    assert any("processes" in e for e in errors)


def test_validate_config_missing_base_field(valid_config):
    del valid_config["processes"]["test_server"]["display_name"]
    errors = validate_config(valid_config)
    assert any("display_name" in e for e in errors)


def test_validate_config_empty_processes(valid_config):
    valid_config["processes"] = {}
    errors = validate_config(valid_config)
    assert errors == []


def test_validate_config_missing_start_command(valid_config):
    del valid_config["processes"]["test_server"]["commands"]["start"]
    errors = validate_config(valid_config)
    assert any("start" in e for e in errors)


def test_validate_config_action_without_command(valid_config):
    valid_config["processes"]["test_server"]["recovery_actions"] = [
        "kill", "clear_email_logs", "start"
    ]
    errors = validate_config(valid_config)
    assert any("clear_email_logs" in e for e in errors)


def test_validate_old_format_valid(old_format_config):
    """Old-format config should pass validation after normalization."""
    config = {"processes": {"old": old_format_config}}
    errors = validate_config(config)
    assert errors == []
