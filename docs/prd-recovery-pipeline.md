# PRD: Recovery Pipeline

Version: 1.0.0

## Overview

The Recovery Pipeline feature orchestrates the execution of configurable recovery actions when a process is detected as unhealthy. Actions are executed in order, with failure handling based on action type.

## Modules

| Module | File | Purpose |
|--------|------|---------|
| Pipeline | `src/pipeline/recovery_pipeline.py` | Orchestrate action execution |
| Killer | `src/recovery/killer.py` | Terminate processes (SIGTERM/SIGKILL) |
| Cleaner | `src/recovery/cleaner.py` | Run cleanup scripts |
| Restarter | `src/recovery/restarter.py` | Launch processes in detached sessions |

## Pipeline Flow

```
recovery_actions: ["kill", "clear_db", "start"]

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
       ┌───────┐
       │ start │ ─── failure ───▶ STOP (fatal)
       └───┬───┘
           │ success
           ▼
        RECOVERED
```

## Action Types

| Action | Handler | On Failure |
|--------|---------|------------|
| `kill` | Built-in killer module | Stop pipeline (fatal) |
| `start` | Built-in restarter module | Stop pipeline (fatal) |
| Any other | Cleaner module (script runner) | Warn and continue |

## Killer Behavior

1. Send SIGTERM to PID
2. Wait up to `kill_timeout` seconds (configurable)
3. If still running, send SIGKILL
4. Verify process terminated

## Restarter Behavior

1. Execute start command via bash
2. Detach from parent (survives cron exit)
3. Wait `verify_delay` seconds (configurable)
4. Check if process still running

## Cleaner Behavior

1. Execute script with configurable arguments (default: `--force`)
2. Wait up to `cleanup_timeout` seconds (configurable)
3. Return success/failure based on exit code

## API

```python
from src.pipeline.recovery_pipeline import run_recovery

result = run_recovery(
    process_key="my_server",
    pid=12345,
    proc_config=proc_config,
    global_opts=global_opts,
)
# Returns PipelineResult with action_results and fully_recovered flag
```

## Configuration

Global settings in `config.json`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `kill_timeout` | float | 10.0 | Seconds to wait for SIGTERM |
| `cleanup_timeout` | float | 60.0 | Seconds to wait for cleanup scripts |
| `verify_delay` | float | 2.0 | Seconds to wait before verifying restart |
| `cleanup_args` | list | `["--force"]` | Arguments passed to cleanup scripts |

Per-process settings:

| Field | Type | Description |
|-------|------|-------------|
| `commands` | dict | Map of action names to shell commands |
| `recovery_actions` | list | Ordered list of actions to execute |

## Changelog

- 1.0.0: Initial implementation with config-driven action loop
