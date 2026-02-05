# PRD: Interactive Menu

Version: 1.2.0

## Overview

The Interactive Menu feature provides a Terminal User Interface (TUI) for managing Watchdog processes, toggling recovery actions, and controlling cron monitoring. Accessible via `watchdog menu`.

## Modules

| Module | File | Purpose |
|--------|------|---------|
| MenuApp | `src/cli/menu/app.py` | Main Textual application |
| Screens | `src/cli/menu/screens.py` | Dashboard screen |
| DetailScreen | `src/cli/menu/detail_screen.py` | Process detail screen |
| Widgets | `src/cli/menu/widgets.py` | Custom TUI widgets |
| State | `src/cli/menu/state.py` | State management and persistence |
| Actions | `src/cli/menu/actions.py` | Process control action handlers |

## Features

### Process Controls
- Start/stop/restart individual processes
- Bulk actions: Start All, Stop All, Restart All (Shift+S/K/R)
- Toggle process enabled/disabled state
- View real-time health status with auto-refresh

### Action Toggles
- Enable/disable specific recovery actions per process
- Actions stored in `disabled_actions` list in config.json
- Disabled actions skipped during recovery pipeline

### Cron Management
- View cron status (active/inactive)
- Toggle cron on/off from menu

### Live Status
- 2-second refresh interval
- Shows: status, PID, elapsed time since heartbeat

## Config Schema

Per-process `disabled_actions` field:

```json
{
  "recovery_actions": ["kill", "clear_db", "start"],
  "disabled_actions": ["clear_db"]
}
```

## Key Bindings

| Key | Dashboard | Detail Screen |
|-----|-----------|---------------|
| Up/Down | Navigate processes | Navigate actions |
| Enter | Open details | - |
| s | Start process | Start process |
| k | Kill process | Kill process |
| r | Restart process | Restart process |
| d | Clear DB | - |
| g | Recover (kill→clear→start) | - |
| S (Shift) | Start all | - |
| K (Shift) | Stop all | - |
| R (Shift) | Restart all | - |
| D (Shift) | Clear all DBs | - |
| G (Shift) | Recover all | - |
| f | Refresh display | - |
| Space | - | Toggle action |
| e | Toggle enabled | Toggle enabled |
| c | Toggle cron | - |
| b | - | Back |
| q | Quit | Quit |

## Dependencies

- `textual>=0.47.0` - TUI framework

## API

### Config Loader Additions

```python
def save_config(config: dict, config_path: str) -> None:
    """Save config dict to JSON file."""

def get_effective_recovery_actions(proc: dict) -> list[str]:
    """Return recovery actions with disabled ones filtered out."""
```

### Cron Control Functions

```python
def is_cron_active() -> bool:
    """Check if Watchdog cron is currently active."""

def toggle_cron(enable: bool) -> tuple[bool, str]:
    """Enable or disable cron. Returns (success, message)."""
```

## Changelog

- 1.2.0: Add Clear DB and Recover actions (d/g single, D/G bulk)
- 1.1.0: Add bulk actions (Start All, Stop All, Restart All) and actions module
- 1.0.0: Initial PRD for interactive menu feature
