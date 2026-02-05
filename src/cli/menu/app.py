# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Main Textual application for the interactive menu."""

from pathlib import Path

from textual.app import App

from src.cli.menu.state import MenuState
from src.cli.menu.screens import DashboardScreen


class WatchdogApp(App):
    """Interactive TUI for Watchdog process management."""

    TITLE = "Watchdog Process Monitor"
    CSS_PATH = "app.tcss"

    def __init__(self, config_path: str | None = None, **kwargs):
        super().__init__(**kwargs)
        if config_path is None:
            config_path = str(Path(__file__).parent.parent.parent.parent / "config.json")
        self.config_path = config_path
        self.state: MenuState | None = None

    def on_mount(self) -> None:
        """Initialize app state and push dashboard."""
        try:
            self.state = MenuState(self.config_path)
            self.push_screen(DashboardScreen(self.state))
        except FileNotFoundError:
            self.exit(message=f"Config not found: {self.config_path}")
        except Exception as e:
            self.exit(message=f"Error loading config: {e}")


def run_menu(config_path: str | None = None) -> None:
    """Run the interactive menu application."""
    app = WatchdogApp(config_path=config_path)
    app.run()


if __name__ == "__main__":
    run_menu()
