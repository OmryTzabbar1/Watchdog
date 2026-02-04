"""Cron-mode check handler: detect unhealthy processes and recover."""

import fcntl
from io import IOBase

from src.config.config_loader import get_process_configs
from src.config.constants import (
    ProcessHealth,
    LOCK_FILE_PATH,
    DEFAULT_DB_PATH,
    DEFAULT_CONSECUTIVE_FAILURES,
)
from src.database.store import WatchdogStore
from src.logging.logger import get_logger
from src.monitor.checker import check_all_processes
from src.pipeline.recovery_pipeline import run_recovery

logger = get_logger("check")


def acquire_lock(lock_path: str = LOCK_FILE_PATH) -> IOBase | None:
    """Acquire an exclusive lock file. Returns file handle or None."""
    try:
        f = open(lock_path, "w")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except (IOError, OSError):
        return None


def handle_check(config: dict) -> int:
    """Cron mode: check all processes, recover unhealthy ones."""
    lock = acquire_lock()
    if lock is None:
        logger.info("Another Watchdog instance is running, exiting")
        return 0

    db_path = config.get("db_path", DEFAULT_DB_PATH)
    threshold = config.get(
        "consecutive_failures_threshold", DEFAULT_CONSECUTIVE_FAILURES
    )
    store = WatchdogStore(db_path)

    try:
        return _run_checks(config, store, threshold)
    finally:
        store.close()
        lock.close()


def _run_checks(config: dict, store: WatchdogStore, threshold: int) -> int:
    """Check all processes and recover unhealthy ones."""
    report = check_all_processes(config)
    enabled = get_process_configs(config)
    any_failed = False

    for result in report.results:
        heartbeat_ts = (
            result.last_heartbeat.isoformat() if result.last_heartbeat else None
        )

        if result.health == ProcessHealth.HEALTHY:
            store.record_check(
                result.process_key, result.health.value,
                result.pid, heartbeat_ts, None,
            )
            logger.info("%s: healthy", result.display_name)
            continue

        logger.warning(
            "%s: %s (PID=%s, elapsed=%s)",
            result.display_name, result.health.value,
            result.pid, result.elapsed_seconds,
        )

        failures = store.record_check(
            result.process_key, result.health.value,
            result.pid, heartbeat_ts, None,
            action="waiting_for_consecutive" if threshold > 1 else None,
        )

        if failures < threshold:
            logger.info(
                "%s: failure %d/%d, waiting before recovery",
                result.display_name, failures, threshold,
            )
            continue

        logger.warning(
            "%s: %d consecutive failures, triggering recovery",
            result.display_name, failures,
        )

        proc_config = enabled[result.process_key]
        recovery = run_recovery(
            process_key=result.process_key,
            pid=result.pid,
            proc_config=proc_config,
        )
        if recovery.fully_recovered:
            store.reset_failures(result.process_key)
        else:
            any_failed = True

    logger.info(
        "Check complete: %d checked, %d healthy, %d unhealthy",
        report.processes_checked,
        report.processes_healthy,
        report.processes_unhealthy,
    )
    return 1 if any_failed else 0
