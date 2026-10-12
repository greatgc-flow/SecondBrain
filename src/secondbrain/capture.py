"""Capture engine for SecondBrain."""

from __future__ import annotations

import hashlib
import json
import os
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.errors import IntegrityError, UsageIOError
from secondbrain import publish
from secondbrain.publish import (
    atomic_publish_bytes,
    retry_sharing_violation,
    retry_open_read,
)


def utc_now() -> datetime:
    """Return current UTC datetime (mockable for deterministic tests)."""
    return datetime.now(timezone.utc)


def compute_sha256(path: Path, chunk_size: int = 65536) -> str:
    """Compute lowercase SHA-256 hex digest of a file using retry on sharing violations."""
    hasher = hashlib.sha256()
    with retry_sharing_violation(lambda: retry_open_read(path, max_retries=1)) as fp:
        while chunk := fp.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def check_overlap(source: Path, root: Path) -> None:
    """Reject a source that overlaps the root (source inside root or root inside source)."""
    src_norm = Path(os.path.normcase(str(source.resolve())))
    root_norm = Path(os.path.normcase(str(root.resolve())))
    if src_norm == root_norm:
        raise UsageIOError(f"Source and root overlap: '{source}' and '{root}'")
    if root_norm in src_norm.parents:
        raise UsageIOError(f"Source '{source}' is inside root '{root}'")
    if src_norm in root_norm.parents:
        raise UsageIOError(f"Root '{root}' is inside source '{source}'")


def generate_receipt_id(sha256: str, receipts_dir: Path, dt: datetime | None = None) -> str:
    """Generate a collision-safe acquisition receipt ID in UTC (fully lowercase)."""
    when = dt or utc_now()
    timestamp_str = when.strftime("%Y%m%dt%H%M%Sz").lower()
    prefix_hex = sha256[:8].lower()
    base_id = f"cap-{timestamp_str}-{prefix_hex}"

    candidate_id = base_id
    candidate_path = receipts_dir / f"{candidate_id}.json"
    collision_index = 2
    while candidate_path.exists():
        candidate_id = f"{base_id}-{collision_index}"
        candidate_path = receipts_dir / f"{candidate_id}.json"
        collision_index += 1

    return candidate_id


def capture_file(source_path: Path, root: Path, tool_version: str) -> dict[str, Any]:
    """Capture a single file into content-addressed objects and versioned receipts.

    Single pass copy to staged temp file while hashing bytes actually copied.
    Verifies source did not change during copy (fails with IntegrityError, exit 1, publishes nothing).
    Verifies existing objects (re-publishing if corrupt).
    """
    if not source_path.is_file():
        raise UsageIOError(f"Source file not found or not a regular file: {source_path}")

    check_overlap(source_path, root)

    # Prepare objects directory
    objects_root = root / "objects"
    objects_root.mkdir(parents=True, exist_ok=True)

    # Staged temp file on target volume
    import uuid

    staged_tmp = objects_root / f".sb-tmp-stage-{os.getpid()}-{uuid.uuid4().hex[:8]}.tmp"

    # Single-pass copy and hash bytes actually copied
    hasher = hashlib.sha256()
    bytes_copied = 0
    try:
        stat_before = source_path.stat()
        with retry_sharing_violation(
            lambda: retry_open_read(source_path, max_retries=1)
        ) as in_fp, open(staged_tmp, "wb") as out_fp:
            while chunk := in_fp.read(65536):
                hasher.update(chunk)
                out_fp.write(chunk)
                bytes_copied += len(chunk)
            out_fp.flush()
            os.fsync(out_fp.fileno())

        stat_after = source_path.stat()
        sha256 = hasher.hexdigest().lower()

        # Verify source did not change during copy
        source_changed = False
        if (
            stat_before.st_size != bytes_copied
            or stat_after.st_size != bytes_copied
            or stat_before.st_mtime_ns != stat_after.st_mtime_ns
        ):
            source_changed = True
        else:
            if compute_sha256(source_path) != sha256:
                source_changed = True

        if source_changed:
            raise IntegrityError(
                f"Source file changed during copy: {source_path}. Publishing aborted."
            )

        # Hook for process-death test at staging stage
        if os.environ.get("_SB_TEST_TERMINATE_STAGE") == "after_staging":
            os._exit(42)

        prefix = sha256[:2]
        object_dir = root / "objects" / prefix
        object_dir.mkdir(parents=True, exist_ok=True)
        object_path = object_dir / sha256

        # If object already exists, verify its hash (and re-publish if corrupt)
        if object_path.is_file():
            is_valid = False
            try:
                if compute_sha256(object_path) == sha256:
                    is_valid = True
            except Exception:
                is_valid = False

            if is_valid:
                obj_status = "reused"
                if staged_tmp.exists():
                    staged_tmp.unlink()
            else:
                # Corrupt existing object: re-publish valid bytes from staged temp file
                publish.atomic_replace(staged_tmp, object_path)
                obj_status = "new"
        else:
            publish.atomic_replace(staged_tmp, object_path)
            obj_status = "new"

        # Hook for process-death test at object stage
        if os.environ.get("_SB_TEST_TERMINATE_STAGE") == "after_object":
            os._exit(43)

        # Build acquisition receipt
        receipts_dir = root / "receipts" / "v1"
        receipts_dir.mkdir(parents=True, exist_ok=True)
        receipt_id = generate_receipt_id(sha256, receipts_dir)

        nfc_name = unicodedata.normalize("NFC", source_path.name)
        raw_name = source_path.name
        collected_at = datetime.now().astimezone().isoformat(timespec="seconds")

        receipt_data = {
            "id": receipt_id,
            "sha256": sha256,
            "original_name": nfc_name,
            "original_name_raw": raw_name,
            "source_path": str(source_path.resolve()),
            "collected_at": collected_at,
            "tool_version": tool_version,
        }

        receipt_bytes = (json.dumps(receipt_data, indent=2) + "\n").encode("utf-8")
        receipt_path = receipts_dir / f"{receipt_id.lower()}.json"
        atomic_publish_bytes(receipt_path, receipt_bytes)

        return {
            "id": receipt_id,
            "name": nfc_name,
            "sha256": sha256,
            "source_path": receipt_data["source_path"],
            "object": obj_status,
        }

    except Exception:
        if staged_tmp.exists():
            try:
                staged_tmp.unlink()
            except OSError:
                pass
        raise


def capture_folder(folder_path: Path, root: Path, tool_version: str) -> dict[str, Any]:
    """Recursively walk a folder and capture regular files with per-file status."""
    if not folder_path.is_dir():
        raise UsageIOError(f"Source directory not found: {folder_path}")

    check_overlap(folder_path, root)

    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    captured_count = 0
    reused_count = 0
    failed_count = 0

    all_files: list[Path] = []
    try:
        for item in sorted(folder_path.rglob("*")):
            try:
                if item.is_file():
                    all_files.append(item)
            except (PermissionError, OSError) as exc:
                failed_count += 1
                errors.append({"path": str(item), "error": str(exc), "category": "usage_io"})
    except (PermissionError, OSError) as exc:
        raise UsageIOError(f"Cannot read directory contents: {folder_path} ({exc})") from exc

    for file_path in all_files:
        try:
            res = capture_file(file_path, root, tool_version)
            results.append(res)
            captured_count += 1
            if res["object"] == "reused":
                reused_count += 1
        except IntegrityError as exc:
            failed_count += 1
            errors.append({"path": str(file_path), "error": str(exc), "category": "integrity"})
        except (UsageIOError, OSError) as exc:
            failed_count += 1
            errors.append({"path": str(file_path), "error": str(exc), "category": "usage_io"})

    return {
        "captured": captured_count,
        "reused_objects": reused_count,
        "failed": failed_count,
        "results": results,
        "errors": errors,
    }
