"""Verification engine for SecondBrain repository."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from secondbrain.capture import compute_sha256
from secondbrain.errors import UsageIOError
from secondbrain.publish import is_tool_temp_file
from secondbrain.root import validate_root

HEX64_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def is_writer_locked(root: Path) -> bool:
    """Check if writer lock is currently held by an active process."""
    lock_path = root / "writer.lock"
    if not lock_path.is_file():
        return False
    try:
        with open(lock_path, "a+b") as fp:
            if sys.platform == "win32":
                import msvcrt

                try:
                    msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
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
    except (OSError, IOError):
        return True


def scan_objects(root: Path) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    """Scan objects directory, re-hashing each object and reporting corrupt ones."""
    objects_dir = root / "objects"
    objects_map: dict[str, Path] = {}
    problems: list[dict[str, Any]] = []

    if not objects_dir.is_dir():
        return objects_map, problems

    try:
        for path in sorted(objects_dir.rglob("*")):
            try:
                if not path.is_file():
                    continue
                if is_tool_temp_file(path):
                    continue

                name = path.name.lower()
                if not HEX64_PATTERN.match(name):
                    problems.append(
                        {
                            "code": "corrupt_object",
                            "path": str(path),
                            "id": path.name,
                            "error": f"Invalid object filename: {path.name}",
                            "message": f"Invalid object filename: {path.name}",
                        }
                    )
                    continue

                if path.parent.name.lower() != name[:2]:
                    problems.append(
                        {
                            "code": "corrupt_object",
                            "path": str(path),
                            "id": name,
                            "error": f"Object {name} located in mismatched prefix dir '{path.parent.name}'",
                            "message": f"Object {name} located in mismatched prefix dir '{path.parent.name}'",
                        }
                    )
                    continue

                try:
                    actual_sha = compute_sha256(path)
                except Exception as exc:
                    problems.append(
                        {
                            "code": "corrupt_object",
                            "path": str(path),
                            "id": name,
                            "error": f"Cannot read object {name}: {exc}",
                            "message": f"Cannot read object {name}: {exc}",
                        }
                    )
                    continue

                if actual_sha != name:
                    problems.append(
                        {
                            "code": "corrupt_object",
                            "path": str(path),
                            "id": name,
                            "error": f"Object hash mismatch: expected {name}, got {actual_sha}",
                            "message": f"Object hash mismatch: expected {name}, got {actual_sha}",
                        }
                    )
                else:
                    objects_map[name] = path

            except (PermissionError, OSError) as exc:
                problems.append(
                    {
                        "code": "corrupt_object",
                        "path": str(path),
                        "id": path.name,
                        "error": str(exc),
                        "message": str(exc),
                    }
                )
    except (PermissionError, OSError) as exc:
        raise UsageIOError(f"Cannot read objects directory: {exc}") from exc

    return objects_map, problems


def scan_receipts(root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Scan receipts/v1 directory, validating JSON schema and reporting invalid ones."""
    receipts_dir = root / "receipts" / "v1"
    receipts_map: dict[str, dict[str, Any]] = {}
    problems: list[dict[str, Any]] = []

    if not receipts_dir.is_dir():
        return receipts_map, problems

    try:
        for path in sorted(receipts_dir.glob("*.json")):
            try:
                if is_tool_temp_file(path):
                    continue

                try:
                    raw_content = path.read_text(encoding="utf-8")
                    if not raw_content.strip():
                        raise ValueError("Receipt file is empty")
                    data = json.loads(raw_content)
                    if not isinstance(data, dict):
                        raise ValueError("Receipt root must be a JSON object")

                    required_fields = (
                        "id",
                        "sha256",
                        "original_name",
                        "source_path",
                        "collected_at",
                        "tool_version",
                    )
                    for field in required_fields:
                        if field not in data:
                            raise ValueError(f"Missing required field: {field}")
                        if not isinstance(data[field], str):
                            raise ValueError(f"Field '{field}' must be a string")

                    sha = data["sha256"].lower()
                    if not HEX64_PATTERN.match(sha):
                        raise ValueError(f"Invalid sha256 hash in receipt: {data['sha256']}")

                    receipt_id = data["id"].lower()
                    receipts_map[receipt_id] = data

                except Exception as exc:
                    problems.append(
                        {
                            "code": "invalid_receipt",
                            "path": str(path),
                            "id": path.stem,
                            "error": f"Invalid receipt JSON at {path.name}: {exc}",
                            "message": f"Invalid receipt JSON at {path.name}: {exc}",
                        }
                    )

            except (PermissionError, OSError) as exc:
                problems.append(
                    {
                        "code": "invalid_receipt",
                        "path": str(path),
                        "id": path.stem,
                        "error": str(exc),
                        "message": str(exc),
                    }
                )
    except (PermissionError, OSError) as exc:
        raise UsageIOError(f"Cannot read receipts directory: {exc}") from exc

    return receipts_map, problems


def scan_temp_files(root: Path) -> list[dict[str, Any]]:
    """Find leftover tool temp files, accounting for active concurrent writers."""
    problems: list[dict[str, Any]] = []
    if not root.exists():
        return problems

    try:
        for path in sorted(root.rglob("*.tmp")):
            try:
                if not path.is_file() or not is_tool_temp_file(path):
                    continue

                # If writer lock is held, wait briefly to see if temp file is in-flight
                if is_writer_locked(root):
                    time.sleep(0.05)
                    if not path.exists():
                        continue

                problems.append(
                    {
                        "code": "temp_file",
                        "path": str(path),
                        "id": path.name,
                        "error": f"Leftover tool temp file: {path.name}",
                        "message": f"Leftover tool temp file: {path.name}",
                    }
                )
            except OSError:
                pass
    except (PermissionError, OSError) as exc:
        raise UsageIOError(f"Cannot scan repository for temporary files: {exc}") from exc

    return problems


def verify_repository(root: Path) -> dict[str, Any]:
    """Verify repository integrity: objects, receipts, temp files. Read-only."""
    if not root.exists() or not root.is_dir():
        raise UsageIOError(f"Root directory does not exist or is not a directory: {root}")

    validate_root(root)

    problems: list[dict[str, Any]] = []

    # 1. Scan objects (re-hashing all objects)
    objects_map, object_problems = scan_objects(root)
    problems.extend(object_problems)

    # 2. Scan receipts (checking schema and parsing)
    receipts_map, receipt_problems = scan_receipts(root)
    problems.extend(receipt_problems)

    # 3. Scan leftover tool temp files
    temp_problems = scan_temp_files(root)
    problems.extend(temp_problems)

    # 4. Check missing objects referenced by receipts
    for rec_id, rec_data in list(receipts_map.items()):
        sha = rec_data["sha256"].lower()
        if sha not in objects_map:
            expected_obj_path = root / "objects" / sha[:2] / sha
            # Tolerate concurrent capture: check if object exists on disk
            if expected_obj_path.is_file():
                try:
                    if compute_sha256(expected_obj_path) == sha:
                        objects_map[sha] = expected_obj_path
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

    # 5. Check orphan objects (objects not referenced by any valid receipt)
    referenced_shas = {r["sha256"].lower() for r in receipts_map.values()}
    for obj_sha, obj_path in list(objects_map.items()):
        if obj_sha not in referenced_shas:
            # Tolerate concurrent capture: re-scan receipts in case a receipt was just written
            new_receipts, _ = scan_receipts(root)
            receipts_map.update(new_receipts)
            referenced_shas = {r["sha256"].lower() for r in receipts_map.values()}

            if obj_sha not in referenced_shas:
                problems.append(
                    {
                        "code": "orphan_object",
                        "path": str(obj_path),
                        "id": obj_sha,
                        "error": f"Object {obj_sha} has no receipt referencing it",
                        "message": f"Object {obj_sha} has no receipt referencing it",
                    }
                )

    # Compile counts
    missing_count = sum(1 for p in problems if p["code"] == "missing_object")
    corrupt_count = sum(1 for p in problems if p["code"] == "corrupt_object")
    orphan_count = sum(1 for p in problems if p["code"] == "orphan_object")
    invalid_receipts_count = sum(1 for p in problems if p["code"] == "invalid_receipt")
    temp_files_count = sum(1 for p in problems if p["code"] == "temp_file")

    is_clean = len(problems) == 0

    return {
        "status": "ok" if is_clean else "error",
        "receipts": len(receipts_map),
        "objects": len(objects_map),
        "missing": missing_count,
        "corrupt": corrupt_count,
        "orphan": orphan_count,
        "invalid_receipts": invalid_receipts_count,
        "temp_files": temp_files_count,
        "problems": problems,
        "errors": problems,
    }
