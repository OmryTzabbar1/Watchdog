# PRD: Heartbeat Monitoring

Version: 1.1.0

## Overview

The Heartbeat Monitoring feature enables Watchdog to detect process health by reading JSON heartbeat files that monitored processes write periodically.

## Modules

| Module | File | Purpose |
|--------|------|---------|
| HeartbeatWriter | `src/heartbeat/writer.py` | Write heartbeat files (for monitored processes) |
| HeartbeatReader | `src/heartbeat/reader.py` | Read and parse heartbeat files |
| Checker | `src/monitor/checker.py` | Determine process health state |
| Models | `src/monitor/models.py` | Data classes for check results |

## Heartbeat File Format

```json
{
  "process_key": "my_server",
  "pid": 12345,
  "timestamp": "2026-02-05T06:17:29.601049+00:00",
  "status": "running",
  "iteration": 42
}
```

## Health States

| State | Condition |
|-------|-----------|
| `HEALTHY` | Heartbeat exists, PID alive, timestamp within timeout, status is "running" |
| `TIMED_OUT` | Heartbeat exists but timestamp older than `timeout_seconds` |
| `NO_HEARTBEAT` | Heartbeat file does not exist or is corrupted |
| `STALE_PID` | Heartbeat exists but PID is no longer running |
| `ERROR_STATUS` | Heartbeat exists but status field is not "running" (e.g., "error") |

## HeartbeatWriter API

```python
from src.heartbeat.writer import HeartbeatWriter

writer = HeartbeatWriter(heartbeat_dir="heartbeats", process_key="my_server")
writer.beat()  # Write heartbeat
writer.stop()  # Remove heartbeat file on clean shutdown
```

## HeartbeatReader API

```python
from src.heartbeat.reader import read_heartbeat

data = read_heartbeat("/path/to/heartbeat.json")
# Returns HeartbeatData or None if missing/corrupt
```

## Checker API

```python
from src.monitor.checker import check_all_processes

report = check_all_processes(config)
# Returns MonitorReport with list of CheckResult
```

## Configuration

Per-process settings in `config.json`:

| Field | Type | Description |
|-------|------|-------------|
| `heartbeat_path` | string | Absolute path to heartbeat JSON file |
| `timeout_seconds` | int | Seconds before heartbeat considered stale |

## Changelog

- 1.1.0: Add ERROR_STATUS health state for detecting processes reporting errors via status field
- 1.0.0: Initial implementation with writer, reader, and checker
