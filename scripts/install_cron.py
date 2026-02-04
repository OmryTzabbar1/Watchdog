"""Manage the Watchdog crontab entry.

Usage:
    python scripts/install_cron.py --show       Preview the cron line
    python scripts/install_cron.py --enable      Add to crontab (or re-enable)
    python scripts/install_cron.py --disable     Comment out in crontab
    python scripts/install_cron.py --remove      Delete from crontab entirely
    python scripts/install_cron.py --status      Check if currently active
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRON_INTERVAL = "*/2"
MARKER = "# watchdog-supervisor"


def get_cron_line() -> str:
    """Build the active crontab line."""
    log_dir = PROJECT_ROOT / "logs"
    return (
        f"{CRON_INTERVAL} * * * * "
        f"cd {PROJECT_ROOT} && "
        f"{sys.executable} -m src.cli.main "
        f">> {log_dir}/cron.log 2>&1 {MARKER}"
    )


def _read_crontab() -> str:
    result = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else ""


def _write_crontab(content: str) -> bool:
    proc = subprocess.run(
        ["crontab", "-"], input=content, text=True, capture_output=True
    )
    if proc.returncode != 0:
        print(f"Failed: {proc.stderr}", file=sys.stderr)
        return False
    return True


def _find_line(crontab: str) -> tuple[int, str] | None:
    """Find our marker line. Returns (index, line) or None."""
    for i, line in enumerate(crontab.splitlines()):
        if MARKER in line:
            return i, line
    return None


def show():
    print("Cron line:\n")
    print(get_cron_line())
    print()


def status():
    found = _find_line(_read_crontab())
    if found is None:
        print("Watchdog cron: NOT INSTALLED")
        return
    _, line = found
    if line.lstrip().startswith("#"):
        print("Watchdog cron: DISABLED (commented out)")
    else:
        print("Watchdog cron: ACTIVE")
    print(f"  {line.strip()}")


def enable():
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    crontab = _read_crontab()
    active_line = get_cron_line()
    found = _find_line(crontab)

    if found is not None:
        idx, existing = found
        if not existing.lstrip().startswith("#"):
            print("Watchdog cron is already active.")
            return
        lines = crontab.splitlines()
        lines[idx] = active_line
        new = "\n".join(lines) + "\n"
    else:
        new = crontab.rstrip("\n") + "\n" + active_line + "\n"

    if _write_crontab(new):
        print("Watchdog cron ENABLED (runs every 2 minutes).")


def disable():
    crontab = _read_crontab()
    found = _find_line(crontab)
    if found is None:
        print("Watchdog cron is not installed.")
        return
    idx, existing = found
    if existing.lstrip().startswith("#"):
        print("Watchdog cron is already disabled.")
        return

    lines = crontab.splitlines()
    lines[idx] = f"# {existing}"
    if _write_crontab("\n".join(lines) + "\n"):
        print("Watchdog cron DISABLED.")


def remove():
    crontab = _read_crontab()
    found = _find_line(crontab)
    if found is None:
        print("Watchdog cron is not installed.")
        return

    lines = crontab.splitlines()
    del lines[found[0]]
    if _write_crontab("\n".join(lines) + "\n"):
        print("Watchdog cron REMOVED from crontab.")


COMMANDS = {
    "--show": show,
    "--enable": enable,
    "--disable": disable,
    "--remove": remove,
    "--status": status,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
