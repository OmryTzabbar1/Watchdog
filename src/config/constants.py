# Area: Configuration
# PRD: docs/prd-configuration.md
"""Enums and default values for Watchdog."""

from enum import Enum


class ProcessHealth(Enum):
    HEALTHY = "healthy"
    TIMED_OUT = "timed_out"
    NO_HEARTBEAT = "no_heartbeat"
    STALE_PID = "stale_pid"
    ERROR_STATUS = "error_status"


DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DB_PATH = "watchdog.db"
DEFAULT_CONSECUTIVE_FAILURES = 2
DEFAULT_LOCK_PATH = "/tmp/watchdog.lock"
DEFAULT_LOG_DIR = "logs"
DEFAULT_KILL_TIMEOUT = 10.0
DEFAULT_CLEANUP_TIMEOUT = 60.0
DEFAULT_VERIFY_DELAY = 2.0
DEFAULT_CLEANUP_ARGS = ["--force"]

REQUIRED_PROCESS_FIELDS = [
    "display_name",
    "timeout_seconds",
    "heartbeat_path",
    "enabled",
]

BUILTIN_ACTIONS = {"kill"}
DEFAULT_RECOVERY_ACTIONS = ["kill", "clear_db", "start"]
