# PRD: State Management

Version: 1.0.0

## Overview

The State Management feature uses SQLite to track consecutive failure counts and maintain an audit log of health checks and recovery attempts.

## Modules

| Module | File | Purpose |
|--------|------|---------|
| WatchdogStore | `src/database/store.py` | SQLite state tracking |

## Database Schema

### process_state

Tracks current state per process.

| Column | Type | Description |
|--------|------|-------------|
| `process_key` | TEXT PK | Process identifier |
| `consecutive_failures` | INTEGER | Current failure count |
| `last_check_at` | TEXT | ISO timestamp of last check |
| `last_health` | TEXT | Last health state |
| `last_pid` | INTEGER | Last known PID |
| `last_heartbeat_ts` | TEXT | Last heartbeat timestamp |
| `last_iteration` | INTEGER | Last heartbeat iteration |

### check_history

Audit log of all health checks.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment ID |
| `process_key` | TEXT | Process identifier |
| `checked_at` | TEXT | ISO timestamp |
| `health` | TEXT | Health state |
| `pid` | INTEGER | Process PID |
| `heartbeat_ts` | TEXT | Heartbeat timestamp |
| `iteration` | INTEGER | Heartbeat iteration |
| `action_taken` | TEXT | Action taken (if any) |

## API

```python
from src.database.store import WatchdogStore

store = WatchdogStore("/path/to/watchdog.db")

# Record a health check (returns consecutive failure count)
failures = store.record_check(
    process_key="my_server",
    health="stale_pid",
    pid=12345,
    heartbeat_ts="2026-02-05T12:00:00+00:00",
    iteration=42,
    action="waiting_for_consecutive",
)

# Get current failure count
count = store.get_consecutive_failures("my_server")

# Reset failures after successful recovery
store.reset_failures("my_server")

# Close connection
store.close()
```

## Behavior

### Failure Counting

- Unhealthy check: Increment `consecutive_failures`
- Healthy check: Reset `consecutive_failures` to 0
- Recovery success: Reset `consecutive_failures` to 0

### Threshold Logic

Recovery triggers when:
```
consecutive_failures >= consecutive_failures_threshold
```

Default threshold is 2 (prevents flapping on transient failures).

## Configuration

Global settings in `config.json`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `db_path` | string | `"watchdog.db"` | SQLite database path |
| `consecutive_failures_threshold` | int | 2 | Failures before recovery |

## Changelog

- 1.0.0: Initial implementation with process_state and check_history tables
