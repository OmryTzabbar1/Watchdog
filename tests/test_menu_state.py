# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Tests for menu state management."""

import json
import pytest
from pathlib import Path

from src.cli.menu.state import MenuState


@pytest.fixture
def sample_config():
    return {
        "log_level": "INFO",
        "processes": {
            "gmail_server": {
                "display_name": "GmailAsServer",
                "enabled": True,
                "timeout_seconds": 300,
                "heartbeat_path": "/tmp/server.json",
                "commands": {"start": "echo start", "clear_db": "echo clear"},
                "recovery_actions": ["kill", "clear_db", "start"],
                "disabled_actions": [],
            },
            "gmail_referee": {
                "display_name": "GmailAsReferee",
                "enabled": False,
                "timeout_seconds": 300,
                "heartbeat_path": "/tmp/referee.json",
                "commands": {"start": "echo start"},
                "recovery_actions": ["kill", "start"],
                "disabled_actions": ["kill"],
            },
        },
    }


@pytest.fixture
def config_file(tmp_path, sample_config):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(sample_config, indent=2))
    return path


class TestMenuStateInit:
    def test_loads_config_from_path(self, config_file):
        state = MenuState(str(config_file))
        assert state.config is not None
        assert "processes" in state.config

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            MenuState(str(tmp_path / "nonexistent.json"))

    def test_config_path_stored(self, config_file):
        state = MenuState(str(config_file))
        assert state.config_path == str(config_file)


class TestToggleAction:
    def test_disable_action(self, config_file):
        state = MenuState(str(config_file))
        state.toggle_action("gmail_server", "clear_db")
        assert "clear_db" in state.get_disabled_actions("gmail_server")

    def test_enable_action(self, config_file, sample_config):
        sample_config["processes"]["gmail_server"]["disabled_actions"] = ["clear_db"]
        config_file.write_text(json.dumps(sample_config, indent=2))

        state = MenuState(str(config_file))
        state.toggle_action("gmail_server", "clear_db")
        assert "clear_db" not in state.get_disabled_actions("gmail_server")

    def test_toggle_twice_restores_state(self, config_file):
        state = MenuState(str(config_file))
        state.toggle_action("gmail_server", "clear_db")
        state.toggle_action("gmail_server", "clear_db")
        assert "clear_db" not in state.get_disabled_actions("gmail_server")

    def test_toggle_unknown_process_raises(self, config_file):
        state = MenuState(str(config_file))
        with pytest.raises(KeyError):
            state.toggle_action("unknown_process", "kill")

    def test_creates_disabled_actions_if_missing(self, config_file, sample_config):
        del sample_config["processes"]["gmail_server"]["disabled_actions"]
        config_file.write_text(json.dumps(sample_config, indent=2))

        state = MenuState(str(config_file))
        state.toggle_action("gmail_server", "clear_db")
        assert "clear_db" in state.get_disabled_actions("gmail_server")


class TestToggleProcessEnabled:
    def test_disable_enabled_process(self, config_file):
        state = MenuState(str(config_file))
        state.toggle_process_enabled("gmail_server")
        assert state.is_process_enabled("gmail_server") is False

    def test_enable_disabled_process(self, config_file):
        state = MenuState(str(config_file))
        state.toggle_process_enabled("gmail_referee")
        assert state.is_process_enabled("gmail_referee") is True

    def test_toggle_twice_restores_state(self, config_file):
        state = MenuState(str(config_file))
        original = state.is_process_enabled("gmail_server")
        state.toggle_process_enabled("gmail_server")
        state.toggle_process_enabled("gmail_server")
        assert state.is_process_enabled("gmail_server") == original

    def test_toggle_unknown_process_raises(self, config_file):
        state = MenuState(str(config_file))
        with pytest.raises(KeyError):
            state.toggle_process_enabled("unknown_process")


class TestSave:
    def test_save_persists_changes(self, config_file):
        state = MenuState(str(config_file))
        state.toggle_action("gmail_server", "clear_db")
        state.save()

        loaded = json.loads(config_file.read_text())
        assert "clear_db" in loaded["processes"]["gmail_server"]["disabled_actions"]

    def test_save_preserves_other_fields(self, config_file):
        state = MenuState(str(config_file))
        state.toggle_action("gmail_server", "clear_db")
        state.save()

        loaded = json.loads(config_file.read_text())
        assert loaded["log_level"] == "INFO"
        assert loaded["processes"]["gmail_server"]["display_name"] == "GmailAsServer"


class TestGetters:
    def test_get_process_keys(self, config_file):
        state = MenuState(str(config_file))
        keys = state.get_process_keys()
        assert "gmail_server" in keys
        assert "gmail_referee" in keys

    def test_get_process_config(self, config_file):
        state = MenuState(str(config_file))
        config = state.get_process_config("gmail_server")
        assert config["display_name"] == "GmailAsServer"

    def test_get_recovery_actions(self, config_file):
        state = MenuState(str(config_file))
        actions = state.get_recovery_actions("gmail_server")
        assert actions == ["kill", "clear_db", "start"]

    def test_get_disabled_actions(self, config_file):
        state = MenuState(str(config_file))
        disabled = state.get_disabled_actions("gmail_referee")
        assert disabled == ["kill"]

    def test_is_action_enabled(self, config_file):
        state = MenuState(str(config_file))
        assert state.is_action_enabled("gmail_server", "clear_db") is True
        assert state.is_action_enabled("gmail_referee", "kill") is False

    def test_get_display_name(self, config_file):
        state = MenuState(str(config_file))
        assert state.get_display_name("gmail_server") == "GmailAsServer"
