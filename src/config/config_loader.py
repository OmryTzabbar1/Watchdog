"""Load and validate Watchdog configuration from JSON."""

import json
from pathlib import Path

from src.config.constants import (
    BUILTIN_ACTIONS,
    DEFAULT_RECOVERY_ACTIONS,
    REQUIRED_PROCESS_FIELDS,
)


def load_config(config_path: str) -> dict:
    """Load config dict from a JSON file. Raises on missing/invalid file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path) as f:
        return json.load(f)


def normalize_process_config(proc: dict) -> dict:
    """Convert old-style flat config to new commands/recovery_actions format.

    If 'commands' already exists, returns as-is.
    Old fields: startup_command -> commands.start, cleanup_script -> commands.clear_db.
    """
    if "commands" in proc:
        return proc

    normalized = dict(proc)
    commands = {}

    if "startup_command" in normalized:
        commands["start"] = normalized.pop("startup_command")
    if "cleanup_script" in normalized:
        commands["clear_db"] = normalized.pop("cleanup_script")

    if commands:
        normalized["commands"] = commands

    if "recovery_actions" not in normalized:
        normalized["recovery_actions"] = list(DEFAULT_RECOVERY_ACTIONS)

    return normalized


def get_process_configs(config: dict) -> dict[str, dict]:
    """Return only enabled process configs, normalized."""
    return {
        key: normalize_process_config(proc)
        for key, proc in config.get("processes", {}).items()
        if proc.get("enabled", False)
    }


def get_single_process_config(config: dict, process_key: str) -> dict | None:
    """Get a single process config by key, normalized. Returns None if not found."""
    proc = config.get("processes", {}).get(process_key)
    if proc is None:
        return None
    return normalize_process_config(proc)


def validate_config(config: dict) -> list[str]:
    """Validate config schema. Returns list of error strings (empty = valid)."""
    errors = []

    if "processes" not in config:
        errors.append("Missing required field: processes")
        return errors

    for key, raw_proc in config["processes"].items():
        proc = normalize_process_config(raw_proc)

        for field in REQUIRED_PROCESS_FIELDS:
            if field not in proc:
                errors.append(
                    f"Process '{key}' missing required field: {field}"
                )

        commands = proc.get("commands", {})
        if "start" not in commands:
            errors.append(
                f"Process '{key}' missing 'start' in commands"
            )

        for action in proc.get("recovery_actions", []):
            if action not in BUILTIN_ACTIONS and action not in commands:
                errors.append(
                    f"Process '{key}' recovery action '{action}' "
                    f"has no matching command"
                )

    return errors
