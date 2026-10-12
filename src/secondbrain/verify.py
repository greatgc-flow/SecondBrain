"""Verification engine for SecondBrain repository: strict, read-only integrity checks."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

from secondbrain.capture import compute_sha256
from secondbrain.errors import UsageIOError
from secondbrain.publish import is_tool_temp_file
from secondbrain.receipt import (
    HEX64_PATTERN,
    is_reparse_point,
    load_and_validate_receipt,
)
from secondbrain.root import validate_root

HEX2_PATTERN = re.compile(r"^[0-9a-f]{2}$")


def is_writer_locked(root: Path) -> bool:
    """Check if writer lock is currently held by an active process.

    Probes byte zero WITHOUT creating writer.lock if it does not exist.
    """
    lock_path = root / "writer.lock"
    if not lock_path.is_file() or is_reparse_point(lock_path):
        return False
    try:
        with open(lock_path, "r+b") as fp:
            fp.seek(0)
            if sys.platform == "win32":
                import msvcrt

                try:
                    msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
                    fp.seek(0)
                    msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)
                    return False
                except (OSError, IOError):
                    return True
            else:
                import fcntl

                try:
                    fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
                    return False
                except (OSError, IOError):
                    return True
    except FileNotFoundError:
        return False
    except (PermissionError, OSError):
        # On Windows, if open fails due to a sharing violation, writer holds it
        return True


def scan_objects(root: Path) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    """Stream objects directory traversal enforcing exact depth 2 layout and lowercase hex.

    Returns:
        (objects_map, problem_and_activity_items)
    """
    objects_dir = root / "objects"
    objects_map: dict[str, Path] = {}
    items: list[dict[str, Any]] = []

    if not objects_dir.is_dir():
        return objects_map, items

    if is_reparse_point(objects_dir):
        items.append(
            {
                "code": "corrupt_object",
                "path": str(objects_dir),
                "id": "objects",
                "error": f"Objects directory is a symlink or reparse point: {objects_dir}",
                "message": f"Objects directory is a symlink or reparse point: {objects_dir}",
            }
        )
        return objects_map, items

    writer_active = is_writer_locked(root)

    try:
        with os.scandir(objects_dir) as prefix_it:
            for prefix_entry in prefix_it:
                prefix_path = Path(prefix_entry.path)

                # Tool temp files in objects/
                if is_tool_temp_file(prefix_path):
                    if writer_active or is_writer_locked(root):
                        items.append(
                            {
                                "code": "temp_file_in_flight",
                                "severity": "possible_concurrent_activity",
                                "path": str(prefix_path),
                                "id": prefix_entry.name,
                                "message": f"Live publication temp file: {prefix_entry.name}",
                            }
                        )
                    else:
                        items.append(
                            {
                                "code": "temp_file",
                                "path": str(prefix_path),
                                "id": prefix_entry.name,
                                "error": f"Leftover tool temp file: {prefix_entry.name}",
                                "message": f"Leftover tool temp file: {prefix_entry.name}",
                            }
                        )
                    continue

                if is_reparse_point(prefix_path):
                    items.append(
                        {
                            "code": "corrupt_object",
                            "path": str(prefix_path),
                            "id": prefix_entry.name,
                            "error": f"Prefix directory is a symlink or reparse point: {prefix_entry.name}",
                            "message": f"Prefix directory is a symlink or reparse point: {prefix_entry.name}",
                        }
                    )
                    continue

                # Top-level files under objects/ that are not tool temp files
                if prefix_entry.is_file(follow_symlinks=False):
                    items.append(
                        {
                            "code": "corrupt_object",
                            "path": str(prefix_path),
                            "id": prefix_entry.name,
                            "error": f"Unexpected file in objects root: {prefix_entry.name}",
                            "message": f"Unexpected file in objects root: {prefix_entry.name}",
                        }
                    )
                    continue

                if not prefix_entry.is_dir(follow_symlinks=False):
                    continue

                prefix_name = prefix_entry.name
                if not HEX2_PATTERN.match(prefix_name):
                    items.append(
                        {
                            "code": "corrupt_object",
                            "path": str(prefix_path),
                            "id": prefix_name,
                            "error": f"Invalid prefix directory name: '{prefix_name}'. Expected 2 lowercase hex characters.",
                            "message": f"Invalid prefix directory name: '{prefix_name}'",
                        }
                    )
                    continue

                # Stream files in the prefix directory
                try:
                    with os.scandir(prefix_entry.path) as obj_it:
                        for obj_entry in obj_it:
                            obj_path = Path(obj_entry.path)

                            if is_tool_temp_file(obj_path):
                                if writer_active or is_writer_locked(root):
                                    items.append(
                                        {
                                            "code": "temp_file_in_flight",
                                            "severity": "possible_concurrent_activity",
                                            "path": str(obj_path),
                                            "id": obj_entry.name,
                                            "message": f"Live publication temp file: {obj_entry.name}",
                                        }
                                    )
                                else:
                                    items.append(
                                        {
                                            "code": "temp_file",
                                            "path": str(obj_path),
                                            "id": obj_entry.name,
                                            "error": f"Leftover tool temp file: {obj_entry.name}",
                                            "message": f"Leftover tool temp file: {obj_entry.name}",
                                        }
                                    )
                                continue

                            if is_reparse_point(obj_path):
                                items.append(
                                    {
                                        "code": "corrupt_object",
                                        "path": str(obj_path),
                                        "id": obj_entry.name,
                                        "error": f"Object file is a symlink or reparse point: {obj_entry.name}",
                                        "message": f"Object file is a symlink or reparse point: {obj_entry.name}",
                                    }
                                )
                                continue

                            if obj_entry.is_dir(follow_symlinks=False):
                                items.append(
                                    {
                                        "code": "corrupt_object",
                                        "path": str(obj_path),
                                        "id": obj_entry.name,
                                        "error": f"Nested directory inside prefix dir: {obj_entry.name}",
                                        "message": f"Nested directory inside prefix dir: {obj_entry.name}",
                                    }
                                )
                                continue

                            obj_name = obj_entry.name
                            if not HEX64_PATTERN.match(obj_name):
                                items.append(
                                    {
                                        "code": "corrupt_object",
                                        "path": str(obj_path),
                                        "id": obj_name,
                                        "error": f"Invalid object filename: '{obj_name}'. Must be 64 lowercase hex chars.",
                                        "message": f"Invalid object filename: '{obj_name}'",
                                    }
                                )
                                continue

                            if obj_name[:2] != prefix_name:
                                items.append(
                                    {
                                        "code": "corrupt_object",
                                        "path": str(obj_path),
                                        "id": obj_name,
                                        "error": f"Object {obj_name} in mismatched prefix dir '{prefix_name}'",
                                        "message": f"Object {obj_name} in mismatched prefix dir '{prefix_name}'",
                                    }
                                )
                                continue

                            try:
                                actual_sha = compute_sha256(obj_path)
                            except (PermissionError, OSError) as exc:
                                items.append(
                                    {
                                        "code": "io_error",
                                        "path": str(obj_path),
                                        "id": obj_name,
                                        "error": f"Cannot read object {obj_name}: {exc}",
                                        "message": f"Cannot read object {obj_name}: {exc}",
                                    }
                                )
                                continue
                            except Exception as exc:
                                items.append(
                                    {
                                        "code": "corrupt_object",
                                        "path": str(obj_path),
                                        "id": obj_name,
                                        "error": f"Hash computation error on {obj_name}: {exc}",
                                        "message": f"Hash computation error on {obj_name}: {exc}",
                                    }
                                )
                                continue

                            if actual_sha != obj_name:
                                items.append(
                                    {
                                        "code": "corrupt_object",
                                        "path": str(obj_path),
                                        "id": obj_name,
                                        "error": f"Object hash mismatch: expected {obj_name}, got {actual_sha}",
                                        "message": f"Object hash mismatch: expected {obj_name}, got {actual_sha}",
                                    }
                                )
                            else:
                                objects_map[obj_name] = obj_path

                except (PermissionError, OSError) as exc:
                    items.append(
                        {
                            "code": "io_error",
                            "path": str(prefix_path),
                            "id": prefix_name,
                            "error": f"Cannot read prefix directory {prefix_name}: {exc}",
                            "message": f"Cannot read prefix directory {prefix_name}: {exc}",
                        }
                    )
    except (PermissionError, OSError) as exc:
        raise UsageIOError(f"Cannot read objects directory: {exc}") from exc

    return objects_map, items


def scan_receipts(root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Stream receipts/v1 directory traversal validating strict schema and lowercase names."""
    receipts_dir = root / "receipts" / "v1"
    receipts_map: dict[str, dict[str, Any]] = {}
    items: list[dict[str, Any]] = []

    if not receipts_dir.is_dir():
        return receipts_map, items

    if is_reparse_point(receipts_dir):
        items.append(
            {
                "code": "invalid_receipt",
                "path": str(receipts_dir),
                "id": "v1",
                "error": f"Receipts directory is a symlink or reparse point: {receipts_dir}",
                "message": f"Receipts directory is a symlink or reparse point: {receipts_dir}",
            }
        )
        return receipts_map, items

    writer_active = is_writer_locked(root)

    try:
        with os.scandir(receipts_dir) as it:
            for entry in it:
                rec_path = Path(entry.path)

                if is_tool_temp_file(rec_path):
                    if writer_active or is_writer_locked(root):
                        items.append(
                            {
                                "code": "temp_file_in_flight",
                                "severity": "possible_concurrent_activity",
                                "path": str(rec_path),
                                "id": entry.name,
                                "message": f"Live publication temp file: {entry.name}",
                            }
                        )
                    else:
                        items.append(
                            {
                                "code": "temp_file",
                                "path": str(rec_path),
                                "id": entry.name,
                                "error": f"Leftover tool temp file: {entry.name}",
                                "message": f"Leftover tool temp file: {entry.name}",
                            }
                        )
                    continue

                if is_reparse_point(rec_path):
                    items.append(
                        {
                            "code": "invalid_receipt",
                            "path": str(rec_path),
                            "id": entry.name,
                            "error": f"Receipt file is a symlink or reparse point: {entry.name}",
                            "message": f"Receipt file is a symlink or reparse point: {entry.name}",
                        }
                    )
                    continue

                if entry.is_dir(follow_symlinks=False):
                    items.append(
                        {
                            "code": "invalid_receipt",
                            "path": str(rec_path),
                            "id": entry.name,
                            "error": f"Unexpected subdirectory in receipts/v1: {entry.name}",
                            "message": f"Unexpected subdirectory in receipts/v1: {entry.name}",
                        }
                    )
                    continue

                if not entry.name.endswith(".json"):
                    items.append(
                        {
                            "code": "invalid_receipt",
                            "path": str(rec_path),
                            "id": entry.name,
                            "error": f"Non-JSON file in receipts/v1: {entry.name}",
                            "message": f"Non-JSON file in receipts/v1: {entry.name}",
                        }
                    )
                    continue

                try:
                    data = load_and_validate_receipt(rec_path)
                    rec_id = data["id"]
                    if rec_id in receipts_map:
                        items.append(
                            {
                                "code": "invalid_receipt",
                                "path": str(rec_path),
                                "id": rec_id,
                                "error": f"Duplicate receipt ID '{rec_id}' in {entry.name}",
                                "message": f"Duplicate receipt ID '{rec_id}' in {entry.name}",
                            }
                        )
                    else:
                        receipts_map[rec_id] = data

                except UsageIOError as exc:
                    items.append(
                        {
                            "code": "io_error",
                            "path": str(rec_path),
                            "id": entry.name[:-5],
                            "error": str(exc),
                            "message": str(exc),
                        }
                    )
                except Exception as exc:
                    items.append(
                        {
                            "code": "invalid_receipt",
                            "path": str(rec_path),
                            "id": entry.name[:-5],
                            "error": str(exc),
                            "message": str(exc),
                        }
                    )

    except (PermissionError, OSError) as exc:
        raise UsageIOError(f"Cannot read receipts directory: {exc}") from exc

    return receipts_map, items


def scan_root_temp_files(root: Path) -> list[dict[str, Any]]:
    """Find leftover tool temp files at the root level, accounting for active concurrent writers."""
    items: list[dict[str, Any]] = []
    writer_active = is_writer_locked(root)

    try:
        with os.scandir(root) as it:
            for entry in it:
                path = Path(entry.path)
                if entry.is_file(follow_symlinks=False) and is_tool_temp_file(path):
                    if writer_active or is_writer_locked(root):
                        items.append(
                            {
                                "code": "temp_file_in_flight",
                                "severity": "possible_concurrent_activity",
                                "path": str(path),
                                "id": entry.name,
                                "message": f"Live publication temp file: {entry.name}",
                            }
                        )
                    else:
                        items.append(
                            {
                                "code": "temp_file",
                                "path": str(path),
                                "id": entry.name,
                                "error": f"Leftover tool temp file: {entry.name}",
                                "message": f"Leftover tool temp file: {entry.name}",
                            }
                        )
    except (PermissionError, OSError) as exc:
        raise UsageIOError(f"Cannot scan repository root for temporary files: {exc}") from exc

    return items


def verify_repository(root: Path) -> dict[str, Any]:
    """Verify repository integrity: objects, receipts, temp files. Read-only.

    Differentiates integrity problems (exit 1) from IO errors / locked files (exit 2).
    Reports concurrent publication in progress as 'concurrent_activity' info.
    """
    if not root.exists() or not root.is_dir():
        raise UsageIOError(f"Root directory does not exist or is not a directory: {root}")

    validate_root(root)

    objects_dir = root / "objects"
    receipts_dir = root / "receipts"
    receipts_v1_dir = receipts_dir / "v1"
    if not objects_dir.is_dir() or is_reparse_point(objects_dir):
        raise UsageIOError(f"not a SecondBrain store: missing or non-directory 'objects' in {root}")
    if not receipts_dir.is_dir() or is_reparse_point(receipts_dir):
        raise UsageIOError(f"not a SecondBrain store: missing or non-directory 'receipts' in {root}")
    if not receipts_v1_dir.is_dir() or is_reparse_point(receipts_v1_dir):
        raise UsageIOError(f"not a SecondBrain store: missing or non-directory 'receipts/v1' in {root}")

    writer_observed = is_writer_locked(root)

    problems: list[dict[str, Any]] = []
    io_problems: list[dict[str, Any]] = []
    concurrent_activity: list[dict[str, Any]] = []

    # 1. Stream scan objects
    objects_map, obj_items = scan_objects(root)
    writer_observed = writer_observed or is_writer_locked(root)
    for item in obj_items:
        if item["code"] == "io_error":
            io_problems.append(item)
        elif item["code"] in ("temp_file_in_flight", "awaiting_receipt"):
            concurrent_activity.append(item)
        else:
            problems.append(item)

    # 2. Stream scan receipts
    receipts_map, rec_items = scan_receipts(root)
    writer_observed = writer_observed or is_writer_locked(root)
    for item in rec_items:
        if item["code"] == "io_error":
            io_problems.append(item)
        elif item["code"] in ("temp_file_in_flight", "awaiting_receipt"):
            concurrent_activity.append(item)
        else:
            problems.append(item)

    # 3. Scan root temp files
    root_tmp_items = scan_root_temp_files(root)
    writer_observed = writer_observed or is_writer_locked(root)
    for item in root_tmp_items:
        if item["code"] in ("temp_file_in_flight", "awaiting_receipt"):
            concurrent_activity.append(item)
        else:
            problems.append(item)

    if any(item.get("code") == "temp_file_in_flight" for item in concurrent_activity):
        writer_observed = True

    # 4. Check missing objects referenced by receipts
    for rec_id, rec_data in list(receipts_map.items()):
        sha = rec_data["sha256"]
        if sha not in objects_map:
            expected_obj_path = root / "objects" / sha[:2] / sha
            if expected_obj_path.is_file() and not is_reparse_point(expected_obj_path):
                try:
                    if compute_sha256(expected_obj_path) == sha:
                        objects_map[sha] = expected_obj_path
                        continue
                except (PermissionError, OSError) as exc:
                    io_problems.append(
                        {
                            "code": "io_error",
                            "path": str(expected_obj_path),
                            "id": sha,
                            "error": str(exc),
                            "message": f"Cannot read object {sha}: {exc}",
                        }
                    )
                    continue
                except Exception:
                    pass

            problems.append(
                {
                    "code": "missing_object",
                    "path": str(expected_obj_path),
                    "id": rec_data["id"],
                    "error": f"Object {sha} referenced by receipt {rec_data['id']} is missing",
                    "message": f"Object {sha} referenced by receipt {rec_data['id']} is missing",
                }
            )

    # 5. Check orphan objects: re-scan receipts once more after the object scan
    # so a publication that completes between scans is not reported as an orphan.
    referenced_shas = {r["sha256"] for r in receipts_map.values()}
    unreferenced_shas = [sha for sha in objects_map if sha not in referenced_shas]

    scan_not_stable = False
    if unreferenced_shas:
        receipts_count_before = len(receipts_map)
        receipts_dir = root / "receipts" / "v1"
        if receipts_dir.is_dir():
            try:
                with os.scandir(receipts_dir) as it:
                    for entry in it:
                        if entry.name.endswith(".json") and not entry.is_dir(follow_symlinks=False):
                            stem = entry.name[:-5]
                            if stem not in receipts_map:
                                try:
                                    data = load_and_validate_receipt(Path(entry.path))
                                    rec_id = data["id"]
                                    if rec_id not in receipts_map:
                                        receipts_map[rec_id] = data
                                    referenced_shas.add(data["sha256"])
                                except Exception:
                                    pass
            except OSError:
                pass

        if len(receipts_map) > receipts_count_before:
            scan_not_stable = True

        # Recompute unreferenced SHAs after reconciliation pass
        unreferenced_shas = [sha for sha in objects_map if sha not in referenced_shas]

        if is_writer_locked(root):
            writer_observed = True

        # Now classify remaining unreferenced objects
        for obj_sha in unreferenced_shas:
            obj_path = objects_map[obj_sha]
            if writer_observed or scan_not_stable:
                concurrent_activity.append(
                    {
                        "code": "awaiting_receipt",
                        "severity": "possible_concurrent_activity",
                        "path": str(obj_path),
                        "id": obj_sha,
                        "message": f"Object {obj_sha} awaiting receipt (possible concurrent activity)",
                    }
                )
            else:
                problems.append(
                    {
                        "code": "orphan_object",
                        "path": str(obj_path),
                        "id": obj_sha,
                        "error": f"Object {obj_sha} has no receipt referencing it",
                        "message": f"Object {obj_sha} has no receipt referencing it",
                    }
                )

    missing_count = sum(1 for p in problems if p["code"] == "missing_object")
    corrupt_count = sum(1 for p in problems if p["code"] == "corrupt_object")
    orphan_count = sum(1 for p in problems if p["code"] == "orphan_object")
    invalid_receipts_count = sum(1 for p in problems if p["code"] == "invalid_receipt")
    temp_files_count = sum(1 for p in problems if p["code"] == "temp_file")

    is_clean = len(problems) == 0 and len(io_problems) == 0
    if is_clean:
        status = "ok"
    elif io_problems and not problems:
        status = "io_error"
    else:
        status = "error"

    summary_result = {
        "status": status,
        "receipts": len(receipts_map),
        "objects": len(objects_map),
        "missing": missing_count,
        "corrupt": corrupt_count,
        "orphan": orphan_count,
        "invalid_receipts": invalid_receipts_count,
        "temp_files": temp_files_count,
        "concurrent_activity": len(concurrent_activity),
        "io_errors": len(io_problems),
    }

    return {
        "status": status,
        "receipts": len(receipts_map),
        "objects": len(objects_map),
        "missing": missing_count,
        "corrupt": corrupt_count,
        "orphan": orphan_count,
        "invalid_receipts": invalid_receipts_count,
        "temp_files": temp_files_count,
        "concurrent_activity": concurrent_activity,
        "problems": problems,
        "errors": problems + io_problems,
        "io_errors": io_problems,
        "results": [summary_result],
    }
