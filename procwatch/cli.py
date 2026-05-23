"""Command-line interface for procwatch."""

import argparse
import logging
import sys
from pathlib import Path

from procwatch.config_loader import load_monitor_from_file

logger = logging.getLogger(__name__)


def _setup_logging(verbose: bool = False) -> None:
    """Configure root logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="procwatch",
        description="Minimal process monitor that restarts services on failure.",
    )
    parser.add_argument(
        "config",
        metavar="CONFIG",
        help="Path to the YAML configuration file.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Enable debug logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the procwatch CLI.

    Returns an exit code (0 on success, non-zero on error).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error("Configuration file not found: %s", config_path)
        return 1

    try:
        monitor = load_monitor_from_file(str(config_path))
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load configuration: %s", exc)
        return 1

    logger.info(
        "Starting procwatch with %d process(es) defined.",
        len(monitor.processes),
    )

    try:
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Shutting down procwatch (KeyboardInterrupt).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
