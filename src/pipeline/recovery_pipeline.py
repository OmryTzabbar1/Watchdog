# Area: Recovery Pipeline
# PRD: docs/prd-recovery-pipeline.md
"""Orchestrate config-driven recovery pipeline."""

from dataclasses import dataclass, field

from src.config.config_loader import get_effective_recovery_actions
from src.logging.logger import get_logger
from src.recovery.killer import KillResult, kill_process
from src.recovery.cleaner import CleanResult, run_cleanup
from src.recovery.restarter import RestartResult, restart_process

logger = get_logger("pipeline")


@dataclass
class PipelineResult:
    process_key: str
    action_results: list[tuple[str, object]] = field(default_factory=list)
    fully_recovered: bool = False
    stage_failed: str | None = None

    @property
    def kill_result(self) -> KillResult | None:
        for name, res in self.action_results:
            if name == "kill":
                return res
        return None

    @property
    def restart_result(self) -> RestartResult | None:
        for name, res in self.action_results:
            if name == "start":
                return res
        return None


def run_recovery(
    process_key: str,
    pid: int | None,
    proc_config: dict,
    global_opts: dict | None = None,
) -> PipelineResult:
    """Execute recovery actions defined in proc_config.

    Actions are read from proc_config["recovery_actions"].
    'kill' and 'start' failures stop the pipeline.
    Other action failures warn but continue.
    """
    result = PipelineResult(process_key=process_key)
    actions = get_effective_recovery_actions(proc_config)
    commands = proc_config.get("commands", {})
    opts = global_opts or {}

    for action in actions:
        action_result = _execute_action(action, process_key, pid, commands, opts)
        result.action_results.append((action, action_result))

        if not action_result.success:
            if action in ("kill", "start"):
                logger.error(
                    "%s failed for %s: %s",
                    action, process_key, action_result.error,
                )
                result.stage_failed = action
                return result
            logger.warning(
                "Action '%s' failed for %s (continuing)",
                action, process_key,
            )

    result.fully_recovered = True
    logger.info("Process %s recovered", process_key)
    return result


def _execute_action(
    action: str,
    process_key: str,
    pid: int | None,
    commands: dict,
    opts: dict,
) -> KillResult | CleanResult | RestartResult:
    """Execute a single recovery action."""
    if action == "kill":
        if pid is not None:
            logger.info("Killing %s (PID %d)", process_key, pid)
            timeout = opts.get("kill_timeout", 10.0)
            return kill_process(pid, timeout=timeout)
        logger.info("No PID for %s, skipping kill", process_key)
        return KillResult(success=True, pid=0)

    if action == "start":
        cmd = commands["start"]
        logger.info("Starting %s: %s", process_key, cmd)
        verify_delay = opts.get("verify_delay", 2.0)
        return restart_process(cmd, verify_delay=verify_delay)

    # Generic script action (clear_db, clear_email_logs, etc.)
    script = commands[action]
    logger.info("Running %s for %s: %s", action, process_key, script)
    timeout = opts.get("cleanup_timeout", 60.0)
    args = opts.get("cleanup_args")
    return run_cleanup(script, timeout=timeout, args=args)
