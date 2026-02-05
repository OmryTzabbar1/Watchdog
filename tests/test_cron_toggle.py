# Area: Interactive Menu
# PRD: docs/prd-interactive-menu.md
"""Tests for cron toggle functions."""

import pytest
from unittest.mock import patch, MagicMock

# Import will fail until functions are added
from scripts.install_cron import is_cron_active, toggle_cron, MARKER


class TestIsCronActive:
    def test_returns_true_when_active(self):
        crontab = f"* * * * * some command {MARKER}\n"
        with patch("scripts.install_cron._read_crontab", return_value=crontab):
            assert is_cron_active() is True

    def test_returns_false_when_commented(self):
        crontab = f"# * * * * * some command {MARKER}\n"
        with patch("scripts.install_cron._read_crontab", return_value=crontab):
            assert is_cron_active() is False

    def test_returns_false_when_not_installed(self):
        crontab = "* * * * * other cron job\n"
        with patch("scripts.install_cron._read_crontab", return_value=crontab):
            assert is_cron_active() is False

    def test_returns_false_when_crontab_empty(self):
        with patch("scripts.install_cron._read_crontab", return_value=""):
            assert is_cron_active() is False


class TestToggleCron:
    def test_enable_returns_success_message(self):
        crontab = f"# * * * * * some command {MARKER}\n"
        with patch("scripts.install_cron._read_crontab", return_value=crontab):
            with patch("scripts.install_cron._write_crontab", return_value=True):
                success, message = toggle_cron(enable=True)
                assert success is True
                assert "enabled" in message.lower()

    def test_disable_returns_success_message(self):
        crontab = f"* * * * * some command {MARKER}\n"
        with patch("scripts.install_cron._read_crontab", return_value=crontab):
            with patch("scripts.install_cron._write_crontab", return_value=True):
                success, message = toggle_cron(enable=False)
                assert success is True
                assert "disabled" in message.lower()

    def test_enable_when_already_active(self):
        crontab = f"* * * * * some command {MARKER}\n"
        with patch("scripts.install_cron._read_crontab", return_value=crontab):
            success, message = toggle_cron(enable=True)
            assert success is True
            assert "already" in message.lower()

    def test_disable_when_already_disabled(self):
        crontab = f"# * * * * * some command {MARKER}\n"
        with patch("scripts.install_cron._read_crontab", return_value=crontab):
            success, message = toggle_cron(enable=False)
            assert success is True
            assert "already" in message.lower()

    def test_enable_when_not_installed(self):
        with patch("scripts.install_cron._read_crontab", return_value=""):
            with patch("scripts.install_cron._write_crontab", return_value=True):
                with patch("scripts.install_cron.PROJECT_ROOT") as mock_root:
                    mock_root.__truediv__ = MagicMock(return_value=MagicMock())
                    success, message = toggle_cron(enable=True)
                    assert success is True

    def test_disable_when_not_installed(self):
        with patch("scripts.install_cron._read_crontab", return_value=""):
            success, message = toggle_cron(enable=False)
            assert success is True
            assert "not installed" in message.lower()

    def test_returns_failure_on_write_error(self):
        crontab = f"# * * * * * some command {MARKER}\n"
        with patch("scripts.install_cron._read_crontab", return_value=crontab):
            with patch("scripts.install_cron._write_crontab", return_value=False):
                success, message = toggle_cron(enable=True)
                assert success is False
