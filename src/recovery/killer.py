"""Kill a process by PID with SIGTERM -> SIGKILL escalation."""

import os
import signal
import time
from dataclasses import dataclass


@dataclass
class KillResult:
    success: bool
    pid: int
    error: str | None = None


def is_process_running(pid: int) -> bool:
    """Check if a PID is still alive."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def kill_process(pid: int, timeout: float = 10.0) -> KillResult:
    """Kill a process: SIGTERM first, then SIGKILL after timeout.

    Returns KillResult. If the process is already dead, returns success.
    """
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return KillResult(success=True, pid=pid)
    except PermissionError as e:
        return KillResult(success=False, pid=pid, error=str(e))

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_process_running(pid):
            return KillResult(success=True, pid=pid)
        time.sleep(0.5)

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return KillResult(success=True, pid=pid)
    except PermissionError as e:
        return KillResult(success=False, pid=pid, error=str(e))

    time.sleep(1.0)
    if is_process_running(pid):
        return KillResult(
            success=False, pid=pid, error="Process survived SIGKILL"
        )
    return KillResult(success=True, pid=pid)
