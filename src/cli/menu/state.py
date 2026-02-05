# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""State management for the interactive menu."""

from src.config.config_loader import load_config, save_config


class MenuState:
    """Manages menu state and config persistence."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = load_config(config_path)

    def _get_process(self, process_key: str) -> dict:
        """Get process config, raising KeyError if not found."""
        processes = self.config.get("processes", {})
        if process_key not in processes:
            raise KeyError(f"Unknown process: {process_key}")
        return processes[process_key]

    def toggle_action(self, process_key: str, action: str) -> None:
        """Toggle an action's enabled/disabled state."""
        proc = self._get_process(process_key)
        if "disabled_actions" not in proc:
            proc["disabled_actions"] = []

        disabled = proc["disabled_actions"]
        if action in disabled:
            disabled.remove(action)
        else:
            disabled.append(action)

    def toggle_process_enabled(self, process_key: str) -> None:
        """Toggle a process's enabled state."""
        proc = self._get_process(process_key)
        proc["enabled"] = not proc.get("enabled", False)

    def save(self) -> None:
        """Persist config changes to file."""
        save_config(self.config, self.config_path)

    def get_process_keys(self) -> list[str]:
        """Return list of all process keys."""
        return list(self.config.get("processes", {}).keys())

    def get_process_config(self, process_key: str) -> dict:
        """Get full config for a process."""
        return self._get_process(process_key)

    def get_recovery_actions(self, process_key: str) -> list[str]:
        """Get recovery actions list for a process."""
        proc = self._get_process(process_key)
        return proc.get("recovery_actions", ["kill", "start"])

    def get_disabled_actions(self, process_key: str) -> list[str]:
        """Get disabled actions list for a process."""
        proc = self._get_process(process_key)
        return proc.get("disabled_actions", [])

    def is_action_enabled(self, process_key: str, action: str) -> bool:
        """Check if an action is enabled (not in disabled list)."""
        return action not in self.get_disabled_actions(process_key)

    def is_process_enabled(self, process_key: str) -> bool:
        """Check if a process is enabled."""
        proc = self._get_process(process_key)
        return proc.get("enabled", False)

    def get_display_name(self, process_key: str) -> str:
        """Get display name for a process."""
        proc = self._get_process(process_key)
        return proc.get("display_name", process_key)
