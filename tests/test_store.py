"""Tests for the SQLite watchdog store."""

import pytest

from src.database.store import WatchdogStore


@pytest.fixture
def store(tmp_path):
    db_path = str(tmp_path / "test.db")
    s = WatchdogStore(db_path)
    yield s
    s.close()


class TestRecordCheck:
    def test_healthy_resets_counter(self, store):
        store.record_check("proc_a", "timed_out", 100, None, None)
        failures = store.record_check("proc_a", "healthy", 100, "2026-01-01T00:00:00", 5)
        assert failures == 0

    def test_unhealthy_increments_counter(self, store):
        f1 = store.record_check("proc_a", "timed_out", 100, None, None)
        f2 = store.record_check("proc_a", "timed_out", 100, None, None)
        assert f1 == 1
        assert f2 == 2

    def test_consecutive_failures_across_states(self, store):
        store.record_check("proc_a", "no_heartbeat", None, None, None)
        failures = store.record_check("proc_a", "stale_pid", 100, "2026-01-01", 3)
        assert failures == 2

    def test_independent_processes(self, store):
        store.record_check("proc_a", "timed_out", 100, None, None)
        failures_b = store.record_check("proc_b", "timed_out", 200, None, None)
        assert failures_b == 1

    def test_healthy_after_failures_resets(self, store):
        store.record_check("proc_a", "timed_out", 100, None, None)
        store.record_check("proc_a", "timed_out", 100, None, None)
        store.record_check("proc_a", "healthy", 100, "2026-01-01", 10)
        failures = store.record_check("proc_a", "timed_out", 100, None, None)
        assert failures == 1


class TestGetConsecutiveFailures:
    def test_unknown_process_returns_zero(self, store):
        assert store.get_consecutive_failures("unknown") == 0

    def test_returns_current_count(self, store):
        store.record_check("proc_a", "timed_out", 100, None, None)
        store.record_check("proc_a", "timed_out", 100, None, None)
        assert store.get_consecutive_failures("proc_a") == 2


class TestResetFailures:
    def test_reset_clears_counter(self, store):
        store.record_check("proc_a", "timed_out", 100, None, None)
        store.record_check("proc_a", "timed_out", 100, None, None)
        store.reset_failures("proc_a")
        assert store.get_consecutive_failures("proc_a") == 0

    def test_reset_unknown_process_no_error(self, store):
        store.reset_failures("unknown")


class TestCheckHistory:
    def test_history_rows_created(self, store):
        store.record_check("proc_a", "healthy", 100, "2026-01-01", 1)
        store.record_check("proc_a", "timed_out", 100, None, None)
        rows = store.get_history("proc_a")
        assert len(rows) == 2
        assert rows[0]["health"] == "healthy"
        assert rows[1]["health"] == "timed_out"

    def test_history_records_action(self, store):
        store.record_check("proc_a", "timed_out", 100, None, None,
                           action="waiting_for_consecutive")
        rows = store.get_history("proc_a")
        assert rows[0]["action_taken"] == "waiting_for_consecutive"


class TestCreatesTables:
    def test_creates_db_file(self, tmp_path):
        db_path = tmp_path / "new.db"
        s = WatchdogStore(str(db_path))
        assert db_path.exists()
        s.close()
