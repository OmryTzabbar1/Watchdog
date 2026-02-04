"""Read and parse heartbeat files written by monitored processes."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REQUIRED_FIELDS = ["process_key", "pid", "timestamp", "status", "iteration"]


@dataclass
class HeartbeatData:
    process_key: str
    pid: int
    timestamp: datetime
    status: str
    iteration: int
    file_path: Path


def read_heartbeat(file_path: Path) -> HeartbeatData | None:
    """Read and parse a heartbeat JSON file.

    Returns None if the file is missing, corrupt, or incomplete.
    """
    try:
        raw = json.loads(file_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    if not all(field in raw for field in REQUIRED_FIELDS):
        return None

    try:
        timestamp = datetime.fromisoformat(raw["timestamp"])
    except (ValueError, TypeError):
        return None

    return HeartbeatData(
        process_key=raw["process_key"],
        pid=int(raw["pid"]),
        timestamp=timestamp,
        status=raw["status"],
        iteration=int(raw["iteration"]),
        file_path=file_path,
    )


def read_all_heartbeats(heartbeat_dir: Path) -> dict[str, HeartbeatData]:
    """Read all .json heartbeat files in directory.

    Returns dict keyed by filename. Skips corrupt files.
    """
    results = {}
    for path in heartbeat_dir.glob("*.json"):
        data = read_heartbeat(path)
        if data is not None:
            results[path.name] = data
    return results
