# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Dashboard screen for the interactive menu."""

from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Header, Footer
from textual.binding import Binding

from src.cli.menu.widgets import ProcessTable, StatusBar
from src.cli.menu import actions
from src.monitor.checker import check_process


class DashboardScreen(Screen):
    """Main dashboard showing all processes."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "toggle_cron", "Toggle Cron"),
        Binding("f", "refresh", "Refresh"),
        Binding("enter", "select_process", "Details"),
        Binding("s", "start_process", "Start"),
        Binding("k", "kill_process", "Kill"),
        Binding("r", "restart_process", "Restart"),
        Binding("d", "clear_db", "Clear DB"),
        Binding("g", "recover", "Recover"),
        Binding("S", "start_all", "Start All"),
        Binding("K", "stop_all", "Stop All"),
        Binding("R", "restart_all", "Restart All"),
        Binding("D", "clear_db_all", "Clear All DB"),
        Binding("G", "recover_all", "Recover All"),
    ]

    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state

    def compose(self):
        """Create dashboard layout."""
        yield Header()
        yield StatusBar(id="status-bar")
        yield Container(
            ProcessTable(id="process-table"),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize dashboard."""
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh process data."""
        table = self.query_one("#process-table", ProcessTable)
        process_data = self._gather_process_data()
        table.update_processes(process_data)
        self._update_status_bar()

    def _gather_process_data(self) -> list[dict]:
        data = []
        for key in self.state.get_process_keys():
            proc = self.state.get_process_config(key)
            r = check_process(key, proc)
            data.append({"key": key, "display_name": self.state.get_display_name(key),
                         "status": r.health.value, "pid": str(r.pid) if r.pid else "-",
                         "enabled": self.state.is_process_enabled(key)})
        return data

    def _update_status_bar(self) -> None:
        from scripts.install_cron import is_cron_active
        from datetime import datetime
        self.query_one("#status-bar", StatusBar).update_status(
            cron_active=is_cron_active(), last_check=datetime.now().strftime("%H:%M:%S"))

    def _get_selected_process_key(self) -> str | None:
        """Get the process key for the selected row."""
        table = self.query_one("#process-table", ProcessTable)
        if table.cursor_row is None:
            return None
        keys = list(self.state.get_process_keys())
        if table.cursor_row < len(keys):
            return keys[table.cursor_row]
        return None

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_toggle_cron(self) -> None:
        from scripts.install_cron import is_cron_active, toggle_cron
        toggle_cron(enable=not is_cron_active())
        self._update_status_bar()

    def action_refresh(self) -> None:
        """Refresh the display."""
        self.refresh_data()

    def action_select_process(self) -> None:
        from src.cli.menu.detail_screen import ProcessDetailScreen
        key = self._get_selected_process_key()
        if key:
            self.app.push_screen(ProcessDetailScreen(self.state, key))

    def on_process_table_process_selected(self, event: ProcessTable.ProcessSelected):
        from src.cli.menu.detail_screen import ProcessDetailScreen
        self.app.push_screen(ProcessDetailScreen(self.state, event.process_key))

    def action_start_process(self) -> None:
        self._run_selected_action(actions.start_process)

    def action_kill_process(self) -> None:
        self._run_selected_action(actions.kill_process_by_key)

    def action_restart_process(self) -> None:
        self._run_selected_action(actions.restart_process_by_key)

    def action_start_all(self) -> None:
        self._run_bulk_action(actions.start_all, "Started")

    def action_stop_all(self) -> None:
        self._run_bulk_action(actions.stop_all, "Stopped")

    def action_restart_all(self) -> None:
        self._run_bulk_action(actions.restart_all, "Restarted")

    def action_clear_db(self) -> None:
        self._run_selected_action(actions.clear_db_by_key)

    def action_recover(self) -> None:
        self._run_selected_action(actions.recover_process_by_key)

    def action_clear_db_all(self) -> None:
        self._run_bulk_action(actions.clear_db_all, "Cleared DB")

    def action_recover_all(self) -> None:
        self._run_bulk_action(actions.recover_all, "Recovered")

    def _run_selected_action(self, action_fn) -> None:
        key = self._get_selected_process_key()
        if key:
            _, msg = action_fn(key, self.state.get_process_config(key))
            self.notify(msg)
            self.refresh_data()

    def _run_bulk_action(self, action_fn, verb: str) -> None:
        ok, fail, _ = action_fn(self.state)
        self.notify(f"{verb} {ok} processes ({fail} failed)")
        self.refresh_data()
