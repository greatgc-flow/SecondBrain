"""Command-line interface for SecondBrain."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from secondbrain import __version__

SUBCOMMANDS: tuple[str, ...] = (
    "capture",
    "find",
    "open",
    "verify",
    "backup",
    "restore",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for sb."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root",
        type=str,
        default=None,
        help="Root directory for the SecondBrain repository/store",
    )
    common.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON instead of human-readable text",
    )

    parser = argparse.ArgumentParser(
        prog="sb",
        description="SecondBrain - Personal knowledge and evidence preservation CLI",
        parents=[common],
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="subcommands",
        description="Available subcommands",
    )

    for name in SUBCOMMANDS:
        subparsers.add_parser(
            name,
            help=f"{name} command (stub)",
            parents=[common],
        )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(2)

    if args.command in SUBCOMMANDS:
        print("not implemented")
        sys.exit(2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
