# Area: Heartbeat Monitoring
# PRD: docs/prd-heartbeat-monitoring.md
"""Heartbeat writer library for monitored processes.

This module is designed to be imported by sibling projects.
It has NO dependencies on other Watchdog modules.

Usage:
    from src.heartbeat.writer import HeartbeatWriter

    writer = HeartbeatWriter(
        heartbeat_dir="/path/to/heartbeats",
        process_key="gmail_as_referee",
    )
    # In your polling loop:
    writer.beat()
    # On shutdown:
    writer.stop()
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class HeartbeatWriter:
    """Writes heartbeat files for process health monitoring."""

    def __init__(
        self,
        heartbeat_dir: str,
        process_key: str,
        heartbeat_filename: str | None = None,
    ) -> None:
        self._dir = Path(heartbeat_dir)
        self._process_key = process_key
        filename = heartbeat_filename or f"{process_key}.json"
        self._path = self._dir / filename
        self._iteration = 0

    def beat(self) -> None:
        """Write a heartbeat. Call this on every polling iteration."""
        self._dir.mkdir(parents=True, exist_ok=True)
        self._iteration += 1
        data = {
            "process_key": self._process_key,
            "pid": os.getpid(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "iteration": self._iteration,
        }
        self._write_atomic(data)

    def stop(self) -> None:
        """Remove heartbeat file on clean shutdown."""
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass

    def _write_atomic(self, data: dict) -> None:
        """Write JSON file atomically using tempfile + os.replace."""
        fd, tmp = tempfile.mkstemp(
            dir=str(self._dir), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f)
            os.replace(tmp, str(self._path))
        except Exception:
            os.unlink(tmp)
            raise

    @property
    def heartbeat_path(self) -> Path:
        return self._path

    @property
    def iteration_count(self) -> int:
        return self._iteration
