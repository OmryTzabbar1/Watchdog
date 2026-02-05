# Area: Recovery Pipeline
# PRD: docs/prd-recovery-pipeline.md
"""Restart a process using a shell command (detached)."""

import subprocess
import time
from dataclasses import dataclass


@dataclass
class RestartResult:
    success: bool
    pid: int | None = None
    command: str = ""
    error: str | None = None


def restart_process(
    command: str, verify_delay: float = 2.0
) -> RestartResult:
    """Start a process via shell command, detached from Watchdog.

    Uses start_new_session=True so the child survives after
    Watchdog (cron) exits. Waits verify_delay seconds, then
    checks if the process is still alive.
    """
    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            executable="/bin/bash",
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError) as e:
        return RestartResult(
            success=False, command=command, error=str(e)
        )

    time.sleep(verify_delay)

    if proc.poll() is not None:
        return RestartResult(
            success=False,
            pid=proc.pid,
            command=command,
            error=f"Process exited immediately with code {proc.poll()}",
        )

    return RestartResult(success=True, pid=proc.pid, command=command)
