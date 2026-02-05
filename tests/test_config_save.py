# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Tests for config saving and effective recovery actions."""

import json
import pytest
from pathlib import Path

from src.config.config_loader import save_config, get_effective_recovery_actions


@pytest.fixture
def sample_process_config():
    return {
        "display_name": "TestProcess",
        "timeout_seconds": 300,
        "heartbeat_path": "/tmp/test.json",
        "enabled": True,
        "commands": {"start": "echo start", "clear_db": "echo clear"},
        "recovery_actions": ["kill", "clear_db", "start"],
        "disabled_actions": [],
    }


class TestSaveConfig:
    def test_save_config_creates_valid_json(self, tmp_path):
        config = {"log_level": "INFO", "processes": {}}
        config_path = tmp_path / "config.json"

        save_config(config, str(config_path))

        assert config_path.exists()
        loaded = json.loads(config_path.read_text())
        assert loaded == config

    def test_save_config_preserves_all_fields(self, tmp_path):
        config = {
            "log_level": "DEBUG",
            "db_path": "/tmp/test.db",
            "processes": {
                "test": {
                    "display_name": "Test",
                    "enabled": True,
                    "recovery_actions": ["kill", "start"],
                    "disabled_actions": ["clear_db"],
                }
            },
        }
        config_path = tmp_path / "config.json"

        save_config(config, str(config_path))

        loaded = json.loads(config_path.read_text())
        assert loaded["processes"]["test"]["disabled_actions"] == ["clear_db"]

    def test_save_config_overwrites_existing(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text('{"old": "data"}')

        new_config = {"new": "data"}
        save_config(new_config, str(config_path))

        loaded = json.loads(config_path.read_text())
        assert loaded == new_config
        assert "old" not in loaded

    def test_save_config_adds_trailing_newline(self, tmp_path):
        config = {"test": True}
        config_path = tmp_path / "config.json"

        save_config(config, str(config_path))

        content = config_path.read_text()
        assert content.endswith("\n")


class TestGetEffectiveRecoveryActions:
    def test_returns_all_actions_when_none_disabled(self, sample_process_config):
        result = get_effective_recovery_actions(sample_process_config)
        assert result == ["kill", "clear_db", "start"]

    def test_filters_out_disabled_actions(self, sample_process_config):
        sample_process_config["disabled_actions"] = ["clear_db"]

        result = get_effective_recovery_actions(sample_process_config)

        assert result == ["kill", "start"]
        assert "clear_db" not in result

    def test_filters_multiple_disabled_actions(self, sample_process_config):
        sample_process_config["disabled_actions"] = ["clear_db", "kill"]

        result = get_effective_recovery_actions(sample_process_config)

        assert result == ["start"]

    def test_handles_missing_disabled_actions_field(self):
        proc = {
            "recovery_actions": ["kill", "clear_db", "start"],
        }

        result = get_effective_recovery_actions(proc)

        assert result == ["kill", "clear_db", "start"]

    def test_handles_empty_recovery_actions(self):
        proc = {
            "recovery_actions": [],
            "disabled_actions": ["clear_db"],
        }

        result = get_effective_recovery_actions(proc)

        assert result == []

    def test_preserves_action_order(self, sample_process_config):
        sample_process_config["recovery_actions"] = ["start", "clear_db", "kill"]
        sample_process_config["disabled_actions"] = ["clear_db"]

        result = get_effective_recovery_actions(sample_process_config)

        assert result == ["start", "kill"]
