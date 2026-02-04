"""Enums and default values for Watchdog."""

from enum import Enum


class ProcessHealth(Enum):
    HEALTHY = "healthy"
    TIMED_OUT = "timed_out"
    NO_HEARTBEAT = "no_heartbeat"
    STALE_PID = "stale_pid"


DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_HEARTBEAT_DIR = "heartbeats"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DB_PATH = "watchdog.db"
DEFAULT_CONSECUTIVE_FAILURES = 2
LOCK_FILE_PATH = "/tmp/watchdog.lock"

REQUIRED_PROCESS_FIELDS = [
    "display_name",
    "timeout_seconds",
    "startup_command",
    "cleanup_script",
    "heartbeat_filename",
    "enabled",
]
