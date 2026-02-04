"""Load and validate Watchdog configuration from JSON."""

import json
from pathlib import Path

from src.config.constants import REQUIRED_PROCESS_FIELDS


def load_config(config_path: str) -> dict:
    """Load config dict from a JSON file. Raises on missing/invalid file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path) as f:
        return json.load(f)


def get_process_configs(config: dict) -> dict[str, dict]:
    """Return only enabled process configs from the full config."""
    return {
        key: proc
        for key, proc in config.get("processes", {}).items()
        if proc.get("enabled", False)
    }


def validate_config(config: dict) -> list[str]:
    """Validate config schema. Returns list of error strings (empty = valid)."""
    errors = []

    if "heartbeat_dir" not in config:
        errors.append("Missing required field: heartbeat_dir")

    if "processes" not in config:
        errors.append("Missing required field: processes")
        return errors

    for key, proc in config["processes"].items():
        for field in REQUIRED_PROCESS_FIELDS:
            if field not in proc:
                errors.append(
                    f"Process '{key}' missing required field: {field}"
                )

    return errors
