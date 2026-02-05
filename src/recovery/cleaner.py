# Area: Recovery Pipeline
# PRD: docs/prd-recovery-pipeline.md
"""Run per-project cleanup scripts via subprocess."""

import subprocess
from dataclasses import dataclass


@dataclass
class CleanResult:
    success: bool
    script_path: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = -1
    error: str | None = None


def run_cleanup(
    script_path: str, timeout: float = 60.0, args: list[str] | None = None
) -> CleanResult:
    """Execute a cleanup script. Returns CleanResult with output."""
    cmd_args = args if args is not None else ["--force"]
    try:
        result = subprocess.run(
            [script_path] + cmd_args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CleanResult(
            success=result.returncode == 0,
            script_path=script_path,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return CleanResult(
            success=False,
            script_path=script_path,
            error=f"Cleanup script timed out after {timeout}s",
        )
    except FileNotFoundError as e:
        return CleanResult(
            success=False,
            script_path=script_path,
            error=f"Cleanup script not found: {e}",
        )
    except OSError as e:
        return CleanResult(
            success=False,
            script_path=script_path,
            error=f"OS error running cleanup: {e}",
        )
