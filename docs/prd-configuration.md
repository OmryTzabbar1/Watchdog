# PRD: Configuration

Version: 1.0.0

## Overview

The Configuration feature handles loading, validating, and normalizing configuration from JSON files. It supports backward compatibility with old config formats.

## Modules

| Module | File | Purpose |
|--------|------|---------|
| ConfigLoader | `src/config/config_loader.py` | Load, validate, normalize config |
| Constants | `src/config/constants.py` | Enums, defaults, required fields |

## Config File Structure

```json
{
  "log_level": "INFO",
  "db_path": "/path/to/watchdog.db",
  "lock_path": "/tmp/watchdog.lock",
  "log_dir": "logs",
  "consecutive_failures_threshold": 2,
  "kill_timeout": 10.0,
  "cleanup_timeout": 60.0,
  "verify_delay": 2.0,
  "cleanup_args": ["--force"],
  "processes": {
    "my_server": {
      "display_name": "MyServer",
      "timeout_seconds": 300,
      "heartbeat_path": "/path/to/heartbeat.json",
      "enabled": true,
      "commands": {
        "start": "python -m myapp.main",
        "clear_db": "/path/to/reset_db.sh"
      },
      "recovery_actions": ["kill", "clear_db", "start"]
    }
  }
}
```

## Global Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `log_level` | string | `"INFO"` | Logging verbosity |
| `db_path` | string | `"watchdog.db"` | SQLite database path |
| `lock_path` | string | `"/tmp/watchdog.lock"` | Lock file path |
| `log_dir` | string | `"logs"` | Log directory path |
| `consecutive_failures_threshold` | int | 2 | Failures before recovery |
| `kill_timeout` | float | 10.0 | SIGTERM wait time (seconds) |
| `cleanup_timeout` | float | 60.0 | Cleanup script timeout (seconds) |
| `verify_delay` | float | 2.0 | Restart verification delay (seconds) |
| `cleanup_args` | list | `["--force"]` | Arguments for cleanup scripts |

## Per-Process Options

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | Yes | Human-readable name |
| `timeout_seconds` | int | Yes | Heartbeat staleness threshold |
| `heartbeat_path` | string | Yes | Path to heartbeat file |
| `enabled` | bool | Yes | Whether to monitor this process |
| `commands` | dict | Yes | Action name to command mapping |
| `recovery_actions` | list | No | Actions to run on recovery |

## Backward Compatibility

Old format (deprecated):
```json
{
  "startup_command": "python main.py",
  "cleanup_script": "/path/to/cleanup.sh"
}
```

Auto-normalized to:
```json
{
  "commands": {
    "start": "python main.py",
    "clear_db": "/path/to/cleanup.sh"
  },
  "recovery_actions": ["kill", "clear_db", "start"]
}
```

## API

```python
from src.config.config_loader import (
    load_config,
    validate_config,
    get_process_configs,
    get_single_process_config,
    get_global_options,
)

config = load_config("config.json")
errors = validate_config(config)
enabled = get_process_configs(config)
proc = get_single_process_config(config, "my_server")
opts = get_global_options(config)
```

## Validation Rules

1. `processes` field must exist
2. Each process must have all required fields
3. Each process must have `commands.start`
4. Each `recovery_action` must have a matching command (except `kill`)

## Changelog

- 1.0.0: Initial implementation with normalization and validation
