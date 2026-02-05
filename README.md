# Watchdog

A modular, config-driven process supervisor for monitoring and recovering long-running services via heartbeat files.

## Overview

Watchdog monitors processes by reading heartbeat files they write periodically. When a process becomes unhealthy (heartbeat stale, PID dead, or file missing), Watchdog executes a configurable recovery pipeline to restore it.

```
┌─────────────────┐     heartbeat      ┌─────────────────┐
│  Monitored      │ ────────────────▶  │   Watchdog      │
│  Process        │   (JSON file)      │   (cron)        │
│  (Server, etc.) │                    │                 │
└─────────────────┘                    └────────┬────────┘
                                                │
                                    unhealthy?  │
                                    threshold   │
                                    reached?    │
                                                ▼
                                       ┌────────────────┐
                                       │   Recovery     │
                                       │   Pipeline     │
                                       │                │
                                       │  kill → clean  │
                                       │  → start       │
                                       └────────────────┘
```

## Features

- **Heartbeat-based monitoring** — Processes write JSON heartbeats; Watchdog detects staleness
- **Consecutive failure threshold** — Only triggers recovery after N consecutive failures (prevents flapping)
- **Modular recovery actions** — Configure which actions run and in what order per process
- **CLI commands** — Manual process control: `on`, `off`, `restart`, `stop-all`, `start-all`
- **SQLite audit log** — Tracks all health checks and recovery attempts
- **Backward compatible** — Old config format auto-normalized to new format

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLI Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────┐ │
│  │   main.py   │  │  check.py   │  │         handlers.py             │ │
│  │  (argparse) │  │  (cron)     │  │  (on/off/restart/stop/start)    │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────────┬─────────────────┘ │
└─────────┼────────────────┼─────────────────────────┼───────────────────┘
          │                │                         │
          ▼                ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            Logic Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ config_     │  │  checker    │  │   store     │  │   pipeline    │  │
│  │ loader      │  │  (health)   │  │  (SQLite)   │  │  (actions)    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
          │                │                         │
          ▼                ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Action Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │   reader    │  │   killer    │  │  cleaner    │  │  restarter    │  │
│  │ (heartbeat) │  │ (SIGTERM/   │  │ (run script)│  │ (launch proc) │  │
│  │             │  │  SIGKILL)   │  │             │  │               │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Purpose |
|-------|---------|
| **CLI** | Parse commands, dispatch to handlers |
| **Logic** | Decide what to do (thresholds, health checks, action ordering) |
| **Action** | Execute operations (kill process, run script, start process) |

## Installation

```bash
# Clone the repository
git clone https://github.com/OmryTzabbar1/Watchdog.git
cd Watchdog

# Install dependencies (if using uv)
uv sync

# Or with pip
pip install -e .

# Run tests
pytest tests/ -v
```

## Configuration

### Config File (`config.json`)

```json
{
  "log_level": "INFO",
  "db_path": "/path/to/watchdog.db",
  "consecutive_failures_threshold": 2,
  "processes": {
    "my_server": {
      "display_name": "MyServer",
      "timeout_seconds": 300,
      "heartbeat_path": "/path/to/heartbeats/my_server.json",
      "enabled": true,
      "commands": {
        "start": "cd /path/to/project && python3 -m myapp.main",
        "clear_db": "/path/to/project/scripts/reset_db.sh",
        "clear_email_logs": "/path/to/project/scripts/clear_emails.sh"
      },
      "recovery_actions": ["kill", "clear_db", "start"]
    }
  }
}
```

### Configuration Options

| Field | Description |
|-------|-------------|
| `log_level` | Logging verbosity: DEBUG, INFO, WARNING, ERROR |
| `db_path` | Path to SQLite database for state tracking |
| `consecutive_failures_threshold` | Number of consecutive failures before recovery triggers |

### Per-Process Options

| Field | Description |
|-------|-------------|
| `display_name` | Human-readable name for logs |
| `timeout_seconds` | Heartbeat age (in seconds) after which process is considered unhealthy |
| `heartbeat_path` | Absolute path to the heartbeat JSON file |
| `enabled` | Whether to monitor this process |
| `commands` | Map of action names to shell commands/scripts |
| `recovery_actions` | Ordered list of actions to execute during recovery |

### Built-in Actions

| Action | Behavior |
|--------|----------|
| `kill` | Terminate process by PID from heartbeat (SIGTERM → SIGKILL) |
| `start` | Run `commands.start` in a detached shell session |
| Any other | Run `commands.<action_name>` as a shell script |

## CLI Commands

```bash
# Cron mode (default) — check all processes, recover unhealthy ones
python -m src.cli.main
python -m src.cli.main check

# Start a specific process
python -m src.cli.main on <process_key>

# Stop a specific process
python -m src.cli.main off <process_key>

# Restart a process (runs full recovery pipeline)
python -m src.cli.main restart <process_key>

# Stop all enabled processes
python -m src.cli.main stop-all

# Start all enabled processes
python -m src.cli.main start-all

# Use a custom config file
python -m src.cli.main -c /path/to/config.json check
```

### Command Flow

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
       ▼                                │
┌─────────────┐                         │
│ checker.py  │                         │
│ check_all   │                         │
│ processes() │                         │
└──────┬──────┘                         │
       │                                │
       ▼                                ▼
┌─────────────┐                  ┌─────────────┐
│ store.py    │                  │ pipeline.py │
│ record_     │ ──── threshold ──▶ run_        │
│ check()     │      reached?    │ recovery()  │
└─────────────┘                  └──────┬──────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              ┌──────────┐        ┌──────────┐        ┌──────────┐
              │  kill    │   ──▶  │ clear_db │   ──▶  │  start   │
              │          │        │          │        │          │
              └──────────┘        └──────────┘        └──────────┘
```

## Heartbeat Format

Monitored processes write a JSON heartbeat file:

```json
{
  "process_key": "my_server",
  "pid": 12345,
  "timestamp": "2026-02-05T06:17:29.601049+00:00",
  "status": "running",
  "iteration": 42
}
```

### Integrating HeartbeatWriter

Copy `src/heartbeat/writer.py` into your project:

```python
from src.heartbeat.writer import HeartbeatWriter

# Initialize
writer = HeartbeatWriter(
    heartbeat_dir="heartbeats",
    process_key="my_server"
)

# In your main loop
while running:
    do_work()
    writer.beat()  # Write heartbeat after each iteration

# On clean shutdown
writer.stop()  # Removes heartbeat file
```

### Health States

| State | Condition |
|-------|-----------|
| `HEALTHY` | Heartbeat exists, PID alive, timestamp within timeout |
| `TIMED_OUT` | Heartbeat exists but timestamp is older than `timeout_seconds` |
| `NO_HEARTBEAT` | Heartbeat file does not exist |
| `STALE_PID` | Heartbeat exists but the PID is no longer running |

## Recovery Pipeline

The pipeline executes actions from `recovery_actions` in order:

```
recovery_actions: ["kill", "clear_db", "clear_email_logs", "start"]

        ┌───────┐
        │ kill  │ ─── failure ───▶ STOP (fatal)
        └───┬───┘
            │ success
            ▼
      ┌──────────┐
      │ clear_db │ ─── failure ───▶ WARN (continue)
      └────┬─────┘
           │ success/warned
           ▼
  ┌────────────────┐
  │clear_email_logs│ ─── failure ───▶ WARN (continue)
  └───────┬────────┘
          │ success/warned
          ▼
      ┌───────┐
      │ start │ ─── failure ───▶ STOP (fatal)
      └───┬───┘
          │ success
          ▼
       RECOVERED
```

### Failure Semantics

| Action | On Failure |
|--------|------------|
| `kill` | Stop pipeline — can't proceed without terminating old process |
| `start` | Stop pipeline — recovery failed |
| Any other | Log warning, continue — best effort cleanup |

## Cron Setup

Run Watchdog every minute:

```bash
# Edit crontab
crontab -e

# Add these lines (adjust paths for your system):
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:/Library/Frameworks/Python.framework/Versions/3.10/bin
* * * * * cd /path/to/Watchdog && python3 -m src.cli.main >> /tmp/watchdog.log 2>&1
```

**Important crontab settings:**

| Setting | Purpose |
|---------|---------|
| `SHELL=/bin/bash` | Enables `source` command in start scripts |
| `PATH=...` | Makes `python3` available to subprocesses |

Without these, recovery may fail because cron uses `/bin/sh` with a minimal PATH.

### Managing the Cron

```bash
# View current crontab
crontab -l

# Disable (remove crontab)
crontab -r

# Quick toggle (comment/uncomment the watchdog line)
crontab -l | sed 's/^\(\* \* \* \* \* .*watchdog.*\)$/# \1/' | crontab -  # disable
crontab -l | sed 's/^# \(\* \* \* \* \* .*watchdog.*\)$/\1/' | crontab -  # enable
```

## Project Structure

```
Watchdog/
├── config.json              # Main configuration
├── watchdog.db              # SQLite state database
├── logs/                    # Daily log files
├── src/
│   ├── cli/
│   │   ├── main.py          # CLI argparse dispatcher (79 lines)
│   │   ├── check.py         # Cron check handler (111 lines)
│   │   └── handlers.py      # Process management handlers (88 lines)
│   ├── config/
│   │   ├── constants.py     # Enums, defaults (27 lines)
│   │   └── config_loader.py # Load/normalize/validate (95 lines)
│   ├── database/
│   │   └── store.py         # SQLite state tracking (106 lines)
│   ├── heartbeat/
│   │   ├── reader.py        # Parse heartbeat files (59 lines)
│   │   └── writer.py        # Write heartbeats (80 lines)
│   ├── logging/
│   │   └── logger.py        # Logging setup (37 lines)
│   ├── monitor/
│   │   ├── checker.py       # Health detection (74 lines)
│   │   └── models.py        # Data models (37 lines)
│   ├── pipeline/
│   │   └── recovery_pipeline.py  # Config-driven action loop (95 lines)
│   └── recovery/
│       ├── killer.py        # Process termination (57 lines)
│       ├── cleaner.py       # Script runner (50 lines)
│       └── restarter.py     # Process launcher (48 lines)
└── tests/
    ├── test_checker.py
    ├── test_cleaner.py
    ├── test_config_loader.py
    ├── test_handlers.py
    ├── test_heartbeat_reader.py
    ├── test_heartbeat_writer.py
    ├── test_killer.py
    ├── test_main.py
    ├── test_recovery_pipeline.py
    ├── test_restarter.py
    └── test_store.py
```

## Adding Custom Recovery Actions

To add a new action (e.g., `clear_email_logs`):

### 1. Create the script in your monitored project

```bash
#!/usr/bin/env bash
# /path/to/project/scripts/clear_emails.sh
# Called with --force flag by Watchdog

set -euo pipefail

if [ "${1:-}" != "--force" ]; then
    read -rp "Clear all email logs? [y/N] " answer
    [ "$answer" != "y" ] && exit 0
fi

# Your cleanup logic here
echo "Clearing email logs..."
# gmail_api_cleanup --all-logs
echo "Done."
```

### 2. Add to config.json

```json
{
  "commands": {
    "start": "...",
    "clear_db": "/path/scripts/reset_db.sh",
    "clear_email_logs": "/path/scripts/clear_emails.sh"
  },
  "recovery_actions": ["kill", "clear_db", "clear_email_logs", "start"]
}
```

**No code changes required.** The pipeline automatically executes any action listed in `recovery_actions` by looking up its script in `commands`.

## Development

### Guidelines (from CLAUDE.md)

1. **150-line file limit** — All Python files must stay under 150 lines
2. **TDD** — Write tests first, then implement
3. **Modularity** — Small, focused modules with clear responsibilities
4. **No hardcoded paths** — All paths come from config.json or environment

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_recovery_pipeline.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Test Coverage

109 tests covering:
- Config loading and normalization (20 tests)
- Health checking (6 tests)
- Recovery pipeline (8 tests)
- CLI handlers (12 tests)
- Main CLI flow (11 tests)
- Process killer/cleaner/restarter (17 tests)
- Heartbeat reader/writer (21 tests)
- SQLite store (14 tests)

## Troubleshooting

### Process not recovering

1. Check `consecutive_failures_threshold` — default is 2, meaning recovery only triggers after 2 consecutive failures
2. Verify heartbeat file path matches config
3. Check logs: `tail -f logs/watchdog_*.log`

### Lock contention

If you see "Another Watchdog instance is running", a previous instance may have crashed without releasing the lock:

```bash
rm /tmp/watchdog.lock
```

### Cleanup script failing

Cleanup failures are non-fatal (pipeline continues). Check the script:
- Must be executable (`chmod +x`)
- Must accept `--force` flag
- Check stderr in Watchdog logs

## License

MIT
