"""Watchdog CLI entry point — invoked by cron."""

import fcntl
import sys
from io import IOBase
from pathlib import Path

from src.config.config_loader import (
    load_config,
    get_process_configs,
    validate_config,
)
from src.config.constants import ProcessHealth, LOCK_FILE_PATH
from src.logging.logger import setup_logging, get_logger
from src.monitor.checker import check_all_processes
from src.pipeline.recovery_pipeline import run_recovery

logger = get_logger("main")


def acquire_lock(lock_path: str = LOCK_FILE_PATH) -> IOBase | None:
    """Acquire an exclusive lock file. Returns file handle or None."""
    try:
        f = open(lock_path, "w")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except (IOError, OSError):
        return None


def main(config_path: str = "config.json") -> int:
    """Main entry point. Returns 0 on success, 1 on failure, 2 on error."""
    try:
        config = load_config(config_path)
    except (FileNotFoundError, Exception) as e:
        print(f"CRITICAL: Cannot load config: {e}", file=sys.stderr)
        return 2

    setup_logging(config.get("log_level", "INFO"))

    errors = validate_config(config)
    if errors:
        for err in errors:
            logger.error("Config error: %s", err)
        return 2

    lock = acquire_lock()
    if lock is None:
        logger.info("Another Watchdog instance is running, exiting")
        return 0

    try:
        return _run_checks(config)
    finally:
        lock.close()


def _run_checks(config: dict) -> int:
    """Check all processes and recover unhealthy ones."""
    report = check_all_processes(config)
    enabled = get_process_configs(config)
    any_failed = False

    for result in report.results:
        if result.health == ProcessHealth.HEALTHY:
            logger.info("%s: healthy", result.display_name)
            continue

        logger.warning(
            "%s: %s (PID=%s, elapsed=%s)",
            result.display_name, result.health.value,
            result.pid, result.elapsed_seconds,
        )

        proc_config = enabled[result.process_key]
        recovery = run_recovery(
            process_key=result.process_key,
            pid=result.pid,
            cleanup_script=proc_config["cleanup_script"],
            startup_command=proc_config["startup_command"],
        )
        if not recovery.fully_recovered:
            any_failed = True

    logger.info(
        "Check complete: %d checked, %d healthy, %d unhealthy",
        report.processes_checked,
        report.processes_healthy,
        report.processes_unhealthy,
    )
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
