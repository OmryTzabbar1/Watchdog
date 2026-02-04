"""Orchestrate the kill -> clean -> restart recovery pipeline."""

from dataclasses import dataclass

from src.logging.logger import get_logger
from src.recovery.killer import KillResult, kill_process
from src.recovery.cleaner import CleanResult, run_cleanup
from src.recovery.restarter import RestartResult, restart_process

logger = get_logger("pipeline")


@dataclass
class PipelineResult:
    process_key: str
    kill_result: KillResult | None = None
    clean_result: CleanResult | None = None
    restart_result: RestartResult | None = None
    fully_recovered: bool = False
    stage_failed: str | None = None


def run_recovery(
    process_key: str,
    pid: int | None,
    cleanup_script: str,
    startup_command: str,
) -> PipelineResult:
    """Execute full recovery: kill -> clean -> restart.

    Stops if kill fails. Continues past cleanup failure.
    """
    result = PipelineResult(process_key=process_key)

    # Step 1: Kill (skip if no PID)
    if pid is not None:
        logger.info("Killing process %s (PID %d)", process_key, pid)
        result.kill_result = kill_process(pid)
        if not result.kill_result.success:
            logger.error(
                "Kill failed for %s: %s",
                process_key, result.kill_result.error,
            )
            result.stage_failed = "kill"
            return result
        logger.info("Process %s killed successfully", process_key)
    else:
        logger.info("No PID for %s, skipping kill", process_key)

    # Step 2: Cleanup
    logger.info("Running cleanup for %s: %s", process_key, cleanup_script)
    result.clean_result = run_cleanup(cleanup_script)
    if not result.clean_result.success:
        detail = (result.clean_result.error
                  or result.clean_result.stderr
                  or f"exit code {result.clean_result.return_code}")
        logger.warning(
            "Cleanup failed for %s: %s (continuing to restart)",
            process_key, detail,
        )

    # Step 3: Restart
    logger.info("Restarting %s: %s", process_key, startup_command)
    result.restart_result = restart_process(startup_command)
    if not result.restart_result.success:
        logger.error(
            "Restart failed for %s: %s",
            process_key, result.restart_result.error,
        )
        result.stage_failed = "restart"
        return result

    logger.info(
        "Process %s recovered (new PID: %d)",
        process_key, result.restart_result.pid,
    )
    result.fully_recovered = True
    return result
