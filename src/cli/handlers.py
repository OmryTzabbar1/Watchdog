"""Command handlers for the Watchdog CLI."""

from pathlib import Path

from src.config.config_loader import get_process_configs, get_single_process_config
from src.heartbeat.reader import read_heartbeat
from src.logging.logger import get_logger
from src.pipeline.recovery_pipeline import run_recovery
from src.recovery.killer import kill_process
from src.recovery.restarter import restart_process

logger = get_logger("handlers")


def handle_on(config: dict, process_key: str) -> int:
    """Start a specific process."""
    proc = get_single_process_config(config, process_key)
    if proc is None:
        logger.error("Unknown process: %s", process_key)
        return 2

    command = proc.get("commands", {}).get("start")
    if not command:
        logger.error("No start command for %s", process_key)
        return 2

    logger.info("Starting %s", process_key)
    result = restart_process(command)
    if result.success:
        logger.info("%s started (PID %d)", process_key, result.pid)
        return 0
    logger.error("Failed to start %s: %s", process_key, result.error)
    return 1


def handle_off(config: dict, process_key: str) -> int:
    """Stop/kill a specific process by reading its heartbeat PID."""
    proc = get_single_process_config(config, process_key)
    if proc is None:
        logger.error("Unknown process: %s", process_key)
        return 2

    heartbeat = read_heartbeat(Path(proc["heartbeat_path"]))
    if heartbeat is None:
        logger.warning("No heartbeat for %s, nothing to kill", process_key)
        return 0

    logger.info("Killing %s (PID %d)", process_key, heartbeat.pid)
    result = kill_process(heartbeat.pid)
    if result.success:
        logger.info("%s stopped", process_key)
        return 0
    logger.error("Failed to stop %s: %s", process_key, result.error)
    return 1


def handle_restart(config: dict, process_key: str) -> int:
    """Run the configured recovery actions for a process."""
    proc = get_single_process_config(config, process_key)
    if proc is None:
        logger.error("Unknown process: %s", process_key)
        return 2

    heartbeat = read_heartbeat(Path(proc["heartbeat_path"]))
    pid = heartbeat.pid if heartbeat else None

    result = run_recovery(process_key, pid, proc)
    return 0 if result.fully_recovered else 1


def handle_stop_all(config: dict) -> int:
    """Stop all enabled processes."""
    enabled = get_process_configs(config)
    any_failed = False
    for key in enabled:
        if handle_off(config, key) != 0:
            any_failed = True
    return 1 if any_failed else 0


def handle_start_all(config: dict) -> int:
    """Start all enabled processes."""
    enabled = get_process_configs(config)
    any_failed = False
    for key in enabled:
        if handle_on(config, key) != 0:
            any_failed = True
    return 1 if any_failed else 0
