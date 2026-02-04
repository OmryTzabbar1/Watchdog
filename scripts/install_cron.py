"""Helper to display or install the Watchdog crontab entry."""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
CRON_INTERVAL = "*/2"  # every 2 minutes


def get_cron_line() -> str:
    """Build the crontab line for Watchdog."""
    log_dir = PROJECT_ROOT / "logs"
    return (
        f"{CRON_INTERVAL} * * * * "
        f"cd {PROJECT_ROOT} && "
        f"{PYTHON} -m src.cli.main "
        f">> {log_dir}/cron.log 2>&1"
    )


def show():
    """Print the cron line to stdout."""
    print("Add this line to your crontab (crontab -e):\n")
    print(get_cron_line())
    print()


def install():
    """Add the cron line to the current user's crontab."""
    line = get_cron_line()
    existing = subprocess.run(
        ["crontab", "-l"],
        capture_output=True, text=True,
    )
    current = existing.stdout if existing.returncode == 0 else ""

    if line in current:
        print("Watchdog cron entry already installed.")
        return

    new_crontab = current.rstrip("\n") + "\n" + line + "\n"
    proc = subprocess.run(
        ["crontab", "-"],
        input=new_crontab, text=True,
        capture_output=True,
    )
    if proc.returncode == 0:
        print("Cron entry installed successfully.")
    else:
        print(f"Failed to install: {proc.stderr}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        install()
    else:
        show()
