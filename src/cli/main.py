# Area: CLI Commands
# PRD: docs/prd-cli-commands.md
"""Watchdog CLI — process supervisor with subcommands."""

import argparse
import sys

from src.config.config_loader import load_config, validate_config
from src.logging.logger import setup_logging, get_logger

logger = get_logger("main")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="watchdog",
        description="Process supervisor for Gmail league system",
    )
    parser.add_argument(
        "-c", "--config", default="config.json",
        help="Path to config.json",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="Check all processes (cron mode)")

    p_on = sub.add_parser("on", help="Start a process")
    p_on.add_argument("process", help="Process key from config")

    p_off = sub.add_parser("off", help="Stop a process")
    p_off.add_argument("process", help="Process key from config")

    p_restart = sub.add_parser("restart", help="Restart a process")
    p_restart.add_argument("process", help="Process key from config")

    sub.add_parser("stop-all", help="Stop all enabled processes")
    sub.add_parser("start-all", help="Start all enabled processes")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point. Returns 0 on success, 1 on failure, 2 on error."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, Exception) as e:
        print(f"CRITICAL: Cannot load config: {e}", file=sys.stderr)
        return 2

    setup_logging(config.get("log_level", "INFO"))

    errors = validate_config(config)
    if errors:
        for err in errors:
            logger.error("Config error: %s", err)
        return 2

    from src.cli.check import handle_check
    from src.cli.handlers import (
        handle_on, handle_off, handle_restart,
        handle_stop_all, handle_start_all,
    )

    command = args.command or "check"
    dispatch = {
        "check": lambda: handle_check(config),
        "on": lambda: handle_on(config, args.process),
        "off": lambda: handle_off(config, args.process),
        "restart": lambda: handle_restart(config, args.process),
        "stop-all": lambda: handle_stop_all(config),
        "start-all": lambda: handle_start_all(config),
    }
    return dispatch[command]()


if __name__ == "__main__":
    sys.exit(main())
