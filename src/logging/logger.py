"""Logging setup for Watchdog with console and file handlers."""

import logging
from datetime import datetime
from pathlib import Path

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger with console and daily file handlers."""
    LOG_DIR.mkdir(exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)
    root = logging.getLogger("watchdog")
    root.setLevel(level)

    if root.handlers:
        return

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(console)

    today = datetime.now().strftime("%Y%m%d")
    log_file = LOG_DIR / f"watchdog_{today}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a named child logger under the watchdog namespace."""
    return logging.getLogger(f"watchdog.{name}")
