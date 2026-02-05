# PRD: CLI Commands

Version: 1.0.0

## Overview

The CLI Commands feature provides a command-line interface for manual process control and automated cron-based health checking.

## Modules

| Module | File | Purpose |
|--------|------|---------|
| Main | `src/cli/main.py` | Argparse dispatcher |
| Check | `src/cli/check.py` | Cron mode handler |
| Handlers | `src/cli/handlers.py` | Process management handlers |

## Commands

| Command | Description |
|---------|-------------|
| `check` | Default. Check all processes, recover unhealthy ones |
| `on <process>` | Start a specific process |
| `off <process>` | Stop a specific process |
| `restart <process>` | Run full recovery pipeline for a process |
| `stop-all` | Stop all enabled processes |
| `start-all` | Start all enabled processes |

## Usage

```bash
# Cron mode (default)
python -m src.cli.main
python -m src.cli.main check

# Process control
python -m src.cli.main on my_server
python -m src.cli.main off my_server
python -m src.cli.main restart my_server

# Bulk operations
python -m src.cli.main stop-all
python -m src.cli.main start-all

# Custom config
python -m src.cli.main -c /path/to/config.json check
```

## Command Flow

```
watchdog check                    watchdog restart my_server
    │                                 │
    ▼                                 ▼
┌─────────────┐                  ┌─────────────┐
│ check.py    │                  │ handlers.py │
│ handle_     │                  │ handle_     │
│ check()     │                  │ restart()   │
└──────┬──────┘                  └──────┬──────┘
       │                                │
       ▼                                ▼
┌─────────────┐                  ┌─────────────┐
│ checker.py  │                  │ pipeline.py │
│ check_all   │                  │ run_        │
│ processes() │                  │ recovery()  │
└─────────────┘                  └─────────────┘
```

## Lock Mechanism

The `check` command uses file-based locking to prevent concurrent execution:

1. Acquire exclusive lock on `lock_path` (configurable)
2. If lock already held, exit gracefully with code 0
3. Release lock when check completes

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (or locked, skipped) |
| 1 | Recovery failed |
| 2 | Configuration error |

## Configuration

Global settings in `config.json`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `lock_path` | string | `/tmp/watchdog.lock` | Path to lock file |

## Changelog

- 1.0.0: Initial implementation with check, on, off, restart, stop-all, start-all
