# Area: Heartbeat Monitoring
# PRD: docs/prd-heartbeat-monitoring.md
"""Timeout detection logic for monitored processes."""

import os
from datetime import datetime, timezone
from pathlib import Path

from src.config.config_loader import get_process_configs
from src.config.constants import ProcessHealth
from src.heartbeat.reader import read_heartbeat
from src.monitor.models import CheckResult, MonitorReport


def is_pid_alive(pid: int) -> bool:
    """Check if a process with the given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def check_process(
    process_key: str,
    process_config: dict,
) -> CheckResult:
    """Check a single process's health via its heartbeat file."""
    heartbeat_path = Path(process_config["heartbeat_path"])
    timeout = process_config["timeout_seconds"]
    display = process_config["display_name"]

    heartbeat = read_heartbeat(heartbeat_path)

    if heartbeat is None:
        return CheckResult(
            process_key=process_key,
            display_name=display,
            health=ProcessHealth.NO_HEARTBEAT,
            pid=None,
            last_heartbeat=None,
            elapsed_seconds=None,
            timeout_seconds=timeout,
        )

    now = datetime.now(timezone.utc)
    elapsed = (now - heartbeat.timestamp).total_seconds()

    if not is_pid_alive(heartbeat.pid):
        health = ProcessHealth.STALE_PID
    elif elapsed > timeout:
        health = ProcessHealth.TIMED_OUT
    else:
        health = ProcessHealth.HEALTHY

    return CheckResult(
        process_key=process_key,
        display_name=display,
        health=health,
        pid=heartbeat.pid,
        last_heartbeat=heartbeat.timestamp,
        elapsed_seconds=elapsed,
        timeout_seconds=timeout,
    )


def check_all_processes(config: dict) -> MonitorReport:
    """Check all enabled processes and return a MonitorReport."""
    enabled = get_process_configs(config)

    report = MonitorReport(timestamp=datetime.now(timezone.utc))
    for key, proc_config in enabled.items():
        result = check_process(key, proc_config)
        report.results.append(result)

    return report
