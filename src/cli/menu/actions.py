# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Action handlers for the interactive menu."""

from pathlib import Path

from src.heartbeat.reader import read_heartbeat
from src.recovery.killer import kill_process
from src.recovery.restarter import restart_process
from src.recovery.cleaner import run_cleanup


def start_process(process_key: str, proc: dict) -> tuple[bool, str]:
    """Start a process. Returns (success, message)."""
    cmd = proc.get("commands", {}).get("start")
    if not cmd:
        return False, f"No start command for {process_key}"

    result = restart_process(cmd, verify_delay=2.0)
    if result.success:
        return True, f"Started {process_key}"
    return False, f"Failed to start {process_key}: {result.error}"


def kill_process_by_key(process_key: str, proc: dict) -> tuple[bool, str]:
    """Kill a process by its key. Returns (success, message)."""
    heartbeat_path = Path(proc.get("heartbeat_path", ""))
    heartbeat = read_heartbeat(heartbeat_path)

    if not heartbeat or not heartbeat.pid:
        return False, f"No running process found for {process_key}"

    result = kill_process(heartbeat.pid, timeout=10.0)
    if result.success:
        return True, f"Killed {process_key} (PID {heartbeat.pid})"
    return False, f"Failed to kill {process_key}: {result.error}"


def restart_process_by_key(process_key: str, proc: dict) -> tuple[bool, str]:
    """Restart a process (kill then start). Returns (success, message)."""
    kill_process_by_key(process_key, proc)  # Continue even if kill fails
    success, msg = start_process(process_key, proc)
    if success:
        return True, f"Restarted {process_key}"
    return False, f"Restart failed: {msg}"


def start_all(state) -> tuple[int, int, list[str]]:
    """Start all enabled processes. Returns (success_count, fail_count, messages)."""
    return _bulk_action(state, start_process)


def stop_all(state) -> tuple[int, int, list[str]]:
    """Stop all enabled processes. Returns (success_count, fail_count, messages)."""
    return _bulk_action(state, kill_process_by_key)


def restart_all(state) -> tuple[int, int, list[str]]:
    """Restart all enabled processes. Returns (success_count, fail_count, messages)."""
    return _bulk_action(state, restart_process_by_key)


def clear_db_by_key(process_key: str, proc: dict) -> tuple[bool, str]:
    """Run clear_db script for a process. Returns (success, message)."""
    cmd = proc.get("commands", {}).get("clear_db")
    if not cmd:
        return False, f"No clear_db command for {process_key}"
    result = run_cleanup(cmd, timeout=60.0, args=["--force"])
    if result.success:
        return True, f"Cleared DB for {process_key}"
    return False, f"Failed to clear DB for {process_key}: {result.error}"


def recover_process_by_key(process_key: str, proc: dict) -> tuple[bool, str]:
    """Full recovery: kill → clear_db → start. Returns (success, message)."""
    kill_process_by_key(process_key, proc)
    clear_db_by_key(process_key, proc)
    success, msg = start_process(process_key, proc)
    if success:
        return True, f"Recovered {process_key}"
    return False, f"Recovery failed for {process_key}: {msg}"


def clear_db_all(state) -> tuple[int, int, list[str]]:
    """Clear DB for all enabled processes."""
    return _bulk_action(state, clear_db_by_key)


def recover_all(state) -> tuple[int, int, list[str]]:
    """Full recovery for all enabled processes."""
    return _bulk_action(state, recover_process_by_key)


def _bulk_action(state, action_fn) -> tuple[int, int, list[str]]:
    """Run an action on all enabled processes."""
    messages, success_count, fail_count = [], 0, 0
    for key in state.get_process_keys():
        if not state.is_process_enabled(key):
            continue
        proc = state.get_process_config(key)
        success, msg = action_fn(key, proc)
        messages.append(msg)
        if success:
            success_count += 1
        else:
            fail_count += 1
    return success_count, fail_count, messages
