"""Command-line interface for SecondBrain."""

from __future__ import annotations

import argparse
import json
import sys
from functools import partial
from pathlib import Path
from typing import Any, Sequence

from secondbrain import __version__
from secondbrain.capture import capture_file, capture_folder
from secondbrain.errors import (
    IntegrityError,
    LockError,
    RootRefusedError,
    UsageIOError,
)
from secondbrain.lock import WriterLock
from secondbrain.open_cmd import open_item
from secondbrain.root import bootstrap_root, resolve_root, validate_root
from secondbrain.verify import verify_repository

SUBCOMMANDS: tuple[str, ...] = (
    "capture",
    "find",
    "open",
    "verify",
    "backup",
    "restore",
)

STUB_COMMANDS: tuple[str, ...] = (
    "find",
    "backup",
    "restore",
)


class JsonArgumentParser(argparse.ArgumentParser):
    """Argument parser that formats errors as JSON when --json is provided."""

    _current_argv: Sequence[str] | None = None

    def __init__(self, *args: Any, json_mode: bool = False, **kwargs: Any) -> None:
        self.json_mode = json_mode
        super().__init__(*args, **kwargs)

    def parse_args(
        self,
        args: Sequence[str] | None = None,
        namespace: argparse.Namespace | None = None,
    ) -> argparse.Namespace:
        self._current_argv = args if args is not None else sys.argv[1:]
        return super().parse_args(args, namespace)

    def error(self, message: str) -> None:
        argv_to_check = self._current_argv if self._current_argv is not None else sys.argv[1:]
        if self.json_mode or "--json" in argv_to_check:
            emit_error(
                is_json=True,
                error=message,
                path="",
                results=[],
                exit_code=2,
            )
        super().error(message)


def build_parser(json_mode: bool = False) -> argparse.ArgumentParser:
    """Build the argument parser for sb."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root",
        type=str,
        default=argparse.SUPPRESS,
        help="Root directory for the SecondBrain repository/store",
    )
    common.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Output structured JSON instead of human-readable text",
    )

    parser = JsonArgumentParser(
        prog="sb",
        description="SecondBrain - Personal knowledge and evidence preservation CLI",
        parents=[common],
        json_mode=json_mode,
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
        parser_class=partial(JsonArgumentParser, json_mode=json_mode),
    )

    capture_parser = subparsers.add_parser(
        "capture",
        help="Preserve bytes and acquisition receipt",
        parents=[common],
    )
    capture_parser.add_argument(
        "target",
        type=str,
        help="File or folder to capture",
    )

    open_parser = subparsers.add_parser(
        "open",
        help="Verify and open, or only print the verified path",
        parents=[common],
    )
    open_parser.add_argument(
        "id",
        type=str,
        help="Receipt ID or SHA-256 prefix (>= 8 hex)",
    )
    open_parser.add_argument(
        "--print-path",
        action="store_true",
        default=False,
        help="Print verified working-copy path without launching viewer",
    )

    subparsers.add_parser(
        "verify",
        help="Check all receipts and objects",
        parents=[common],
    )

    for name in STUB_COMMANDS:
        subparsers.add_parser(
            name,
            help=f"{name} command (stub)",
            parents=[common],
        )

    return parser


def emit_error(
    is_json: bool,
    error: str,
    path: str = "",
    results: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
    exit_code: int = 2,
    prefix: str = "Error: ",
) -> None:
    """Emit centralized error output as JSON or text and exit."""
    if is_json:
        err_list = errors if errors is not None else [{"path": str(path), "error": error}]
        out: dict[str, Any] = {
            "status": "error",
            "error": error,
            "results": results if results is not None else [],
            "errors": err_list,
        }
        print(json.dumps(out, indent=2))
    else:
        print(f"{prefix}{error}" if prefix else error, file=sys.stderr)
    sys.exit(exit_code)


def emit_success(
    is_json: bool,
    results: list[dict[str, Any]],
    captured: int,
    reused_objects: int,
    human_msg: str,
) -> None:
    """Emit centralized success output as JSON or text and exit."""
    if is_json:
        out = {
            "status": "ok",
            "captured": captured,
            "reused_objects": reused_objects,
            "failed": 0,
            "results": results,
            "errors": [],
        }
        print(json.dumps(out, indent=2))
    else:
        print(human_msg)
    sys.exit(0)


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entrypoint."""
    is_json = "--json" in (argv if argv is not None else sys.argv[1:])
    parser = build_parser(json_mode=is_json)
    args = parser.parse_args(argv)

    if args.command is None:
        if is_json:
            emit_error(
                is_json=True,
                error="No subcommand specified",
                path="",
                results=[],
                exit_code=2,
            )
        else:
            parser.print_help()
            sys.exit(2)

    if args.command in STUB_COMMANDS:
        if is_json:
            emit_error(
                is_json=True,
                error="not implemented",
                path="",
                results=[],
                exit_code=2,
            )
        else:
            print("not implemented")
            sys.exit(2)

    if args.command == "capture":
        cli_root = getattr(args, "root", None)

        try:
            root = resolve_root(cli_root)
            validate_root(root)
        except RootRefusedError as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(cli_root or ""),
                results=[],
                exit_code=2,
                prefix="",
            )

        target = Path(args.target)
        if not target.exists():
            emit_error(
                is_json=is_json,
                error=f"Target not found: {target}",
                path=str(target),
                results=[],
                exit_code=2,
            )

        try:
            with WriterLock(root):
                bootstrap_root(root)

                if target.is_file():
                    res = capture_file(target, root, __version__)
                    emit_success(
                        is_json=is_json,
                        results=[res],
                        captured=1,
                        reused_objects=1 if res["object"] == "reused" else 0,
                        human_msg=f"captured id={res['id']} name={res['name']} object={res['object']}",
                    )

                elif target.is_dir():
                    res = capture_folder(target, root, __version__)
                    failed = res["failed"]
                    has_integrity = any(
                        e.get("category") == "integrity" for e in res["errors"]
                    )
                    if failed == 0:
                        emit_success(
                            is_json=is_json,
                            results=res["results"],
                            captured=res["captured"],
                            reused_objects=res["reused_objects"],
                            human_msg=f"captured={res['captured']} reused_objects={res['reused_objects']} failed=0",
                        )
                    else:
                        exit_code = 1 if has_integrity else 2
                        if is_json:
                            out = {
                                "status": "error",
                                "captured": res["captured"],
                                "reused_objects": res["reused_objects"],
                                "failed": failed,
                                "results": res["results"],
                                "errors": res["errors"],
                            }
                            print(json.dumps(out, indent=2))
                        else:
                            print(
                                f"captured={res['captured']} reused_objects={res['reused_objects']} failed={failed}"
                            )
                            for err in res["errors"]:
                                print(
                                    f"Error capturing {err['path']}: {err['error']}",
                                    file=sys.stderr,
                                )
                        sys.exit(exit_code)

                else:
                    emit_error(
                        is_json=is_json,
                        error=f"Target is neither a regular file nor a directory: {target}",
                        path=str(target),
                        results=[],
                        exit_code=2,
                    )

        except LockError as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(root),
                results=[],
                exit_code=2,
            )
        except IntegrityError as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(target),
                results=[],
                exit_code=1,
                prefix="Integrity Error: ",
            )
        except (UsageIOError, OSError, IOError) as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(target),
                results=[],
                exit_code=2,
            )

    elif args.command == "verify":
        cli_root = getattr(args, "root", None)
        try:
            root = resolve_root(cli_root)
            validate_root(root)
        except RootRefusedError as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(cli_root or ""),
                results=[],
                exit_code=2,
                prefix="",
            )
        except (UsageIOError, OSError, IOError) as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(cli_root or ""),
                results=[],
                exit_code=2,
            )

        try:
            report = verify_repository(root)
            if report["status"] == "ok":
                if is_json:
                    print(json.dumps(report, indent=2))
                else:
                    print(
                        f"OK receipts={report['receipts']} objects={report['objects']} "
                        f"missing=0 corrupt=0 orphan=0"
                    )
                sys.exit(0)
            else:
                if is_json:
                    print(json.dumps(report, indent=2))
                else:
                    print(
                        f"FAIL receipts={report['receipts']} objects={report['objects']} "
                        f"missing={report['missing']} corrupt={report['corrupt']} orphan={report['orphan']}"
                    )
                    for prob in report.get("problems", []):
                        print(f"  [{prob['code']}] {prob['path']}: {prob['error']}", file=sys.stderr)
                sys.exit(1)
        except IntegrityError as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(root),
                results=[],
                exit_code=1,
                prefix="Integrity Error: ",
            )
        except (UsageIOError, OSError, IOError) as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(root),
                results=[],
                exit_code=2,
            )

    elif args.command == "open":
        cli_root = getattr(args, "root", None)
        try:
            root = resolve_root(cli_root)
            validate_root(root)
        except RootRefusedError as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(cli_root or ""),
                results=[],
                exit_code=2,
                prefix="",
            )
        except (UsageIOError, OSError, IOError) as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path=str(cli_root or ""),
                results=[],
                exit_code=2,
            )

        try:
            res = open_item(args.id, root, print_path=args.print_path)
            if is_json:
                out = {
                    "status": "ok",
                    "id": res["id"],
                    "path": res["path"],
                    "sha256": res["sha256"],
                    "opened": res["opened"],
                    "results": [res],
                    "errors": [],
                }
                print(json.dumps(out, indent=2))
            else:
                if args.print_path:
                    print(res["path"])
                else:
                    print(f"verified {res['id']}; opened {res['path']}")
            sys.exit(0)
        except IntegrityError as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path="",
                results=[],
                exit_code=1,
                prefix="Integrity Error: ",
            )
        except (UsageIOError, OSError, IOError) as exc:
            emit_error(
                is_json=is_json,
                error=str(exc),
                path="",
                results=[],
                exit_code=2,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
