# Area: State Management
# PRD: docs/prd-state-management.md
"""SQLite store for tracking process check history and consecutive failures."""

import sqlite3
from datetime import datetime, timezone


_SCHEMA = """
CREATE TABLE IF NOT EXISTS process_state (
    process_key TEXT PRIMARY KEY,
    consecutive_failures INTEGER DEFAULT 0,
    last_check_at TEXT,
    last_health TEXT,
    last_pid INTEGER,
    last_heartbeat_ts TEXT,
    last_iteration INTEGER
);

CREATE TABLE IF NOT EXISTS check_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_key TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    health TEXT NOT NULL,
    pid INTEGER,
    heartbeat_ts TEXT,
    iteration INTEGER,
    action_taken TEXT
);
"""


class WatchdogStore:
    """SQLite-backed store for Watchdog check state and history."""

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def record_check(
        self,
        process_key: str,
        health: str,
        pid: int | None,
        heartbeat_ts: str | None,
        iteration: int | None,
        action: str | None = None,
    ) -> int:
        """Record a check result. Returns consecutive failures after update."""
        now = datetime.now(timezone.utc).isoformat()

        if health == "healthy":
            failures = 0
        else:
            failures = self.get_consecutive_failures(process_key) + 1

        self._conn.execute(
            """INSERT INTO process_state
               (process_key, consecutive_failures, last_check_at,
                last_health, last_pid, last_heartbeat_ts, last_iteration)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(process_key) DO UPDATE SET
                 consecutive_failures = excluded.consecutive_failures,
                 last_check_at = excluded.last_check_at,
                 last_health = excluded.last_health,
                 last_pid = excluded.last_pid,
                 last_heartbeat_ts = excluded.last_heartbeat_ts,
                 last_iteration = excluded.last_iteration""",
            (process_key, failures, now, health, pid, heartbeat_ts, iteration),
        )
        self._conn.execute(
            """INSERT INTO check_history
               (process_key, checked_at, health, pid, heartbeat_ts,
                iteration, action_taken)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (process_key, now, health, pid, heartbeat_ts, iteration, action),
        )
        self._conn.commit()
        return failures

    def get_consecutive_failures(self, process_key: str) -> int:
        """Return current consecutive failure count for a process."""
        row = self._conn.execute(
            "SELECT consecutive_failures FROM process_state WHERE process_key = ?",
            (process_key,),
        ).fetchone()
        return row["consecutive_failures"] if row else 0

    def reset_failures(self, process_key: str) -> None:
        """Reset consecutive failures to 0 after successful recovery."""
        self._conn.execute(
            "UPDATE process_state SET consecutive_failures = 0 WHERE process_key = ?",
            (process_key,),
        )
        self._conn.commit()

    def get_history(self, process_key: str) -> list[dict]:
        """Return check history rows for a process (oldest first)."""
        rows = self._conn.execute(
            "SELECT * FROM check_history WHERE process_key = ? ORDER BY id",
            (process_key,),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
