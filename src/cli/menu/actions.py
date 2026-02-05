# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Action handlers for the interactive menu."""

from pathlib import Path

from src.heartbeat.reader import read_heartbeat
from src.recovery.killer import kill_process
from src.recovery.restarter import restart_process


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
