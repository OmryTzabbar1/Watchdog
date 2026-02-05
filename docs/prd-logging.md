# PRD: Logging

Version: 1.0.0

## Overview

The Logging feature provides consistent, configurable logging across all Watchdog modules with daily rotating log files.

## Modules

| Module | File | Purpose |
|--------|------|---------|
| Logger | `src/logging/logger.py` | Logger factory and configuration |

## Log Format

```
[2026-02-05 09:17:00,123] [INFO] [watchdog.check] GmailAsServer: healthy
```

Format: `[timestamp] [level] [logger_name] message`

## Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Detailed diagnostic information |
| `INFO` | Normal operation events |
| `WARNING` | Unhealthy states, non-fatal failures |
| `ERROR` | Fatal failures (recovery failed, etc.) |

## Log Files

- Location: `{log_dir}/watchdog_YYYY-MM-DD.log` (configurable)
- Rotation: Daily (new file each day)
- Console: Also outputs to stderr

## API

```python
from src.logging.logger import get_logger

logger = get_logger("check")  # Creates "watchdog.check" logger
logger.info("Process started")
logger.warning("Process unhealthy: %s", reason)
logger.error("Recovery failed: %s", error)
```

## Configuration

Global settings in `config.json`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `log_level` | string | `"INFO"` | Minimum log level |
| `log_dir` | string | `"logs"` | Directory for log files |

## Logger Hierarchy

```
watchdog (root)
├── watchdog.check
├── watchdog.handlers
├── watchdog.pipeline
├── watchdog.checker
└── watchdog.store
```

All loggers inherit from the `watchdog` root logger.

## Changelog

- 1.0.0: Initial implementation with daily rotation and configurable log directory
