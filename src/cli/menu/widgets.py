# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Custom widgets for the interactive menu."""

from textual.widgets import DataTable, Static
from textual.widget import Widget
from textual.containers import Vertical
from textual.message import Message


class ProcessTable(DataTable):
    """Table displaying process status information."""

    class ProcessSelected(Message):
        """Emitted when a process row is selected."""

        def __init__(self, process_key: str) -> None:
            self.process_key = process_key
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cursor_type = "row"

    def on_mount(self) -> None:
        """Set up table columns."""
        self.add_columns("Process", "Status", "PID", "Enabled")

    def update_processes(self, process_data: list[dict]) -> None:
        """Update table with process data."""
        self.clear()
        for proc in process_data:
            self.add_row(
                proc.get("display_name", proc["key"]),
                proc.get("status", "UNKNOWN"),
                str(proc.get("pid", "-")),
                "Yes" if proc.get("enabled", False) else "No",
                key=proc["key"],
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        if event.row_key:
            self.post_message(self.ProcessSelected(str(event.row_key.value)))


class ActionToggle(Static):
    """A single toggleable action item."""

    class Toggled(Message):
        """Emitted when action is toggled."""

        def __init__(self, action: str, enabled: bool) -> None:
            self.action = action
            self.enabled = enabled
            super().__init__()

    def __init__(self, action: str, enabled: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.action = action
        self._enabled = enabled

    def compose(self):
        """No child widgets."""
        return []

    def on_mount(self) -> None:
        """Initial render."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the display text."""
        checkbox = "[X]" if self._enabled else "[ ]"
        self.update(f"{checkbox} {self.action}")

    def toggle(self) -> None:
        """Toggle the enabled state."""
        self._enabled = not self._enabled
        self._update_display()
        self.post_message(self.Toggled(self.action, self._enabled))

    @property
    def enabled(self) -> bool:
        """Return current enabled state."""
        return self._enabled


class ActionList(Vertical):
    """List of toggleable recovery actions."""

    def __init__(self, actions: list[tuple[str, bool]], **kwargs):
        """Initialize with list of (action_name, is_enabled) tuples."""
        super().__init__(**kwargs)
        self._actions = actions

    def compose(self):
        """Create action toggle widgets."""
        for action, enabled in self._actions:
            yield ActionToggle(action, enabled, id=f"action-{action}")

    def get_toggle(self, action: str) -> ActionToggle | None:
        """Get toggle widget by action name."""
        try:
            return self.query_one(f"#action-{action}", ActionToggle)
        except Exception:
            return None


class StatusBar(Static):
    """Status bar showing cron state and last check time."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cron_active = False
        self._last_check = "Never"

    def update_status(self, cron_active: bool, last_check: str) -> None:
        """Update status bar display."""
        self._cron_active = cron_active
        self._last_check = last_check
        cron_status = "ON" if cron_active else "OFF"
        self.update(f"Cron: [{cron_status}]  |  Last check: {self._last_check}")
