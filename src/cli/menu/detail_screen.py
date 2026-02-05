# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Process detail screen for the interactive menu."""

from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Label
from textual.binding import Binding

from src.cli.menu.widgets import ActionList, ActionToggle


class ProcessDetailScreen(Screen):
    """Detail view for a single process with action toggles."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("b", "go_back", "Back"),
        Binding("escape", "go_back", "Back"),
        Binding("e", "toggle_enabled", "Enable/Disable"),
        Binding("space", "toggle_action", "Toggle Action"),
        Binding("s", "save", "Save"),
    ]

    def __init__(self, state, process_key: str, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.process_key = process_key
        self._current_action_index = 0

    def compose(self):
        """Create detail screen layout."""
        yield Header()
        yield Container(
            self._create_info_section(),
            self._create_actions_section(),
            id="detail-container",
        )
        yield Footer()

    def _create_info_section(self) -> Vertical:
        """Create the process info section."""
        display_name = self.state.get_display_name(self.process_key)
        enabled = self.state.is_process_enabled(self.process_key)
        enabled_text = "[X] Enabled" if enabled else "[ ] Disabled"

        return Vertical(
            Static(f"Process: {display_name}", id="process-name"),
            Static(f"Key: {self.process_key}", id="process-key"),
            Static(enabled_text, id="enabled-status"),
            id="info-section",
        )

    def _create_actions_section(self) -> Vertical:
        """Create the recovery actions section."""
        actions = self.state.get_recovery_actions(self.process_key)
        action_states = [
            (action, self.state.is_action_enabled(self.process_key, action))
            for action in actions
        ]

        return Vertical(
            Label("Recovery Actions:", id="actions-label"),
            ActionList(action_states, id="action-list"),
            id="actions-section",
        )

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_go_back(self) -> None:
        """Go back to dashboard."""
        self.app.pop_screen()

    def action_toggle_enabled(self) -> None:
        """Toggle process enabled state."""
        self.state.toggle_process_enabled(self.process_key)
        self._update_enabled_display()

    def _update_enabled_display(self) -> None:
        """Update the enabled status display."""
        enabled = self.state.is_process_enabled(self.process_key)
        enabled_text = "[X] Enabled" if enabled else "[ ] Disabled"
        self.query_one("#enabled-status", Static).update(enabled_text)

    def action_toggle_action(self) -> None:
        """Toggle the currently focused action."""
        action_list = self.query_one("#action-list", ActionList)
        actions = self.state.get_recovery_actions(self.process_key)
        if not actions:
            return

        action = actions[self._current_action_index % len(actions)]
        toggle = action_list.get_toggle(action)
        if toggle:
            toggle.toggle()
            self.state.toggle_action(self.process_key, action)

    def action_save(self) -> None:
        """Save changes to config."""
        self.state.save()
        self.notify("Configuration saved")

    def on_action_toggle_toggled(self, event: ActionToggle.Toggled) -> None:
        """Handle action toggle from widget."""
        self.state.toggle_action(self.process_key, event.action)

    def on_key(self, event) -> None:
        """Handle key navigation for actions."""
        actions = self.state.get_recovery_actions(self.process_key)
        if not actions:
            return

        if event.key == "down":
            self._current_action_index = (self._current_action_index + 1) % len(actions)
            self._highlight_current_action()
        elif event.key == "up":
            self._current_action_index = (self._current_action_index - 1) % len(actions)
            self._highlight_current_action()

    def _highlight_current_action(self) -> None:
        """Highlight the current action (visual feedback)."""
        # Visual highlighting handled by CSS
        pass
