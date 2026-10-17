"""Restore engine for SecondBrain: restore from dated manifests with integrity checks."""

from __future__ import annotations

import json
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Any

from secondbrain.backup import (
    check_isolation,
    is_nlink_zero,
    validate_relative_path,
)
from secondbrain.capture import compute_sha256
from secondbrain.errors import IntegrityError, UsageIOError
from secondbrain.publish import (
    compute_file_sha256,
    is_tool_temp_file,
    stage_and_verify_copy,
)
from secondbrain.receipt import (
    HEX64_PATTERN,
    load_and_validate_receipt,
    validate_receipt_path,
)
from secondbrain.verify import verify_repository

MANIFEST_NAME_PATTERN = re.compile(r"^(\d{8}T\d{6}Z)(?:-(\d+))?\.json$")


def parse_manifest_name(filename: str) -> tuple[str, int] | None:
    """Parse manifest filename into (timestamp_str, collision_counter) for numerical ordering."""
    m = MANIFEST_NAME_PATTERN.match(filename)
    if not m:
        return None
    ts_str = m.group(1)
    counter = int(m.group(2)) if m.group(2) else 1
    return (ts_str, counter)


TOOL_RESERVED_NAMES = {".sb", ".sb-restore.marker", "backup.lock", "writer.lock"}


def is_tool_reserved_entry_path(path_val: str) -> bool:
    """Check if entry path or any of its components is a tool-reserved name."""
    p = Path(path_val)
    if is_tool_temp_file(p):
        return True
    for part in p.parts:
        if part in TOOL_RESERVED_NAMES:
            return True
        if part.startswith((".sb-", ".sb_")):
            return True
    return False


def validate_manifest_schema(data: Any, manifest_path: Path) -> None:
    """Validate strict MANIFEST v1 schema: {schema_version, created_utc, tool_version, entries:[...]}."""
    if not isinstance(data, dict):
        raise IntegrityError(f"Malformed manifest root in '{manifest_path}': must be a JSON object")

    if data.get("schema_version") != 1:
        raise IntegrityError(f"Unsupported or missing schema_version in '{manifest_path}': expected 1")

    if not data.get("created_utc") or not isinstance(data.get("created_utc"), str):
        raise IntegrityError(f"Missing or invalid created_utc in '{manifest_path}'")

    if not data.get("tool_version") or not isinstance(data.get("tool_version"), str):
        raise IntegrityError(f"Missing or invalid tool_version in '{manifest_path}'")

    entries = data.get("entries")
    if not isinstance(entries, list) or len(entries) == 0:
        raise IntegrityError(f"Empty or missing roster in manifest '{manifest_path}': not a valid manifest")

    config_count = 0
    seen_paths: set[str] = set()

    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise IntegrityError(f"Malformed entry #{idx} in '{manifest_path}': must be a dict")

        kind = entry.get("kind")
        if kind not in ("object", "receipt", "config"):
            raise IntegrityError(f"Invalid entry kind '{kind}' in #{idx} of '{manifest_path}'")

        path_val = entry.get("path")
        if not path_val or not isinstance(path_val, str):
            raise IntegrityError(f"Invalid entry path '{path_val}' in #{idx} of '{manifest_path}'")
        validate_relative_path(path_val)

        norm_path = path_val.replace("\\", "/")

        if is_tool_reserved_entry_path(norm_path):
            raise IntegrityError(
                f"Entry #{idx} in '{manifest_path}' uses tool-reserved name: '{norm_path}'"
            )

        if norm_path in seen_paths:
            raise IntegrityError(
                f"Duplicate entry path '{norm_path}' in #{idx} of '{manifest_path}'"
            )
        seen_paths.add(norm_path)

        sha = entry.get("sha256")
        if not sha or not isinstance(sha, str) or not HEX64_PATTERN.match(sha.lower()):
            raise IntegrityError(f"Invalid entry sha256 '{sha}' in #{idx} of '{manifest_path}'")
        sha_lower = sha.lower()

        size = entry.get("size")
        if not isinstance(size, int) or size < 0:
            raise IntegrityError(f"Invalid entry size '{size}' in #{idx} of '{manifest_path}'")

        if kind == "config":
            config_count += 1
            valid_cfg = (
                norm_path == f"configs/{sha_lower}.json"
                or norm_path == "config.json"
                or (norm_path.startswith("configs/") and norm_path.endswith(".json"))
            )
            if not valid_cfg:
                raise IntegrityError(
                    f"Invalid config path '{norm_path}' in manifest '{manifest_path}'"
                )

        elif kind == "object":
            expected_prefix = sha_lower[:2]
            expected_path = f"objects/{expected_prefix}/{sha_lower}"
            if norm_path != expected_path:
                raise IntegrityError(
                    f"Invalid object path '{norm_path}' in #{idx} of '{manifest_path}': expected '{expected_path}'"
                )

        elif kind == "receipt":
            validate_receipt_path(norm_path)

    if config_count != 1:
        raise IntegrityError(
            f"Manifest '{manifest_path}' must contain exactly one config entry, found {config_count}"
        )


def check_manifest_complete(backup_root: Path, manifest_data: dict[str, Any]) -> tuple[bool, str]:
    """Check if every listed authoritative file exists in the backup root with the right size and sha256."""
    entries = manifest_data.get("entries", [])
    for entry in entries:
        rel_path = entry["path"]
        target = backup_root / rel_path
        if not target.is_file():
            return False, f"Missing listed file: {rel_path}"

        expected_size = entry["size"]
        try:
            actual_size = target.stat().st_size
        except OSError as exc:
            return False, f"Cannot stat {rel_path}: {exc}"

        if actual_size != expected_size:
            return False, f"Size mismatch on {rel_path}: expected {expected_size}, got {actual_size}"

        expected_sha = entry["sha256"].lower()
        actual_sha = compute_file_sha256(target)
        if actual_sha != expected_sha:
            return False, f"SHA256 mismatch on {rel_path}: expected {expected_sha}, got {actual_sha}"

    return True, "OK"


def reserve_target_dir(target_dir: Path) -> Path:
    """Exclusively reserve the empty target directory by creating a marker file with O_CREAT | O_EXCL BEFORE emptiness check."""
    target_dir.mkdir(parents=True, exist_ok=True)
    marker_path = target_dir / ".sb-restore.marker"

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(marker_path), flags)
        os.close(fd)
    except FileExistsError as exc:
        raise UsageIOError(f"Target directory '{target_dir}' is already reserved by another restore operation") from exc
    except OSError as exc:
        raise UsageIOError(f"Cannot reserve target directory '{target_dir}': {exc}") from exc

    # After exclusive reservation, check if target_dir has any other files
    try:
        entries = [p for p in target_dir.iterdir() if p != marker_path]
        if entries:
            try:
                marker_path.unlink()
            except OSError:
                pass
            raise UsageIOError(f"Target directory '{target_dir}' is not empty")
    except UsageIOError:
        raise
    except OSError as exc:
        try:
            marker_path.unlink()
        except OSError:
            pass
        raise UsageIOError(f"Cannot inspect target directory '{target_dir}': {exc}") from exc

    return marker_path


def restore_repository(
    backup_root: Path,
    target_dir: Path,
    manifest_name: str | None = None,
) -> dict[str, Any]:
    """Restore repository from backup root into an empty target directory."""
    resolved_backup = backup_root.resolve()
    resolved_target = target_dir.resolve()

    # 1. Validate backup root
    if not resolved_backup.is_dir():
        raise UsageIOError(f"Backup root does not exist or is not a directory: '{resolved_backup}'")

    if is_nlink_zero(resolved_backup):
        msg = f"Warning: st_nlink is 0 on backup root '{resolved_backup}' (virtual drive / Google Drive FS). Continuing."
        print(msg, file=sys.stderr)
        warnings.warn(msg, UserWarning, stacklevel=2)

    # 2. Refuse overlap between target and backup root (both overlap directions)
    check_isolation(resolved_target, resolved_backup)

    # 3. Exclusively reserve the empty target directory
    marker_path = reserve_target_dir(resolved_target)

    try:
        # 4. Locate complete manifests (a restore never touches backup root)
        manifests_dir = resolved_backup / "manifests"
        if not manifests_dir.is_dir():
            raise UsageIOError(f"No manifests directory found in backup root: '{resolved_backup}'")

        candidate_files = [
            p for p in manifests_dir.glob("*.json")
            if p.is_file() and not is_tool_temp_file(p)
        ]
        if not candidate_files:
            raise UsageIOError(f"No complete manifests found in backup root: '{resolved_backup}'")

        skipped_manifests: list[dict[str, str]] = []
        chosen_manifest: Path | None = None
        chosen_manifest_data: dict[str, Any] | None = None

        if manifest_name:
            clean_name = manifest_name.strip()
            clean_json = clean_name if clean_name.endswith(".json") else f"{clean_name}.json"
            for p in candidate_files:
                if p.name == clean_name or p.name == clean_json or str(p) == manifest_name:
                    chosen_manifest = p
                    break
            if not chosen_manifest:
                raise UsageIOError(f"Manifest '{manifest_name}' not found in '{manifests_dir}'")

            try:
                content = chosen_manifest.read_text(encoding="utf-8")
                data = json.loads(content)
                validate_manifest_schema(data, chosen_manifest)
            except Exception as exc:
                raise IntegrityError(f"Corrupt or invalid specified manifest '{chosen_manifest}': {exc}") from exc

            is_complete, reason = check_manifest_complete(resolved_backup, data)
            if not is_complete:
                raise IntegrityError(f"Specified manifest '{chosen_manifest}' is not complete: {reason}")
            chosen_manifest_data = data
        else:
            # Order candidates by timestamp in the name and numeric collision counter (NEVER lexically)
            def _sort_key(p: Path) -> tuple[str, int]:
                parsed = parse_manifest_name(p.name)
                return parsed if parsed is not None else ("", -1)

            candidate_files.sort(key=_sort_key, reverse=True)

            for cand in candidate_files:
                try:
                    content = cand.read_text(encoding="utf-8")
                    data = json.loads(content)
                    validate_manifest_schema(data, cand)
                except Exception as exc:
                    skipped_manifests.append({"manifest": cand.name, "reason": str(exc)})
                    continue

                is_complete, reason = check_manifest_complete(resolved_backup, data)
                if not is_complete:
                    skipped_manifests.append({"manifest": cand.name, "reason": reason})
                    continue

                chosen_manifest = cand
                chosen_manifest_data = data
                break

            if chosen_manifest is None or chosen_manifest_data is None:
                raise IntegrityError(
                    f"No complete manifest found in backup root '{resolved_backup}'. "
                    f"Skipped candidate manifests: {skipped_manifests}"
                )

        if skipped_manifests:
            for s in skipped_manifests:
                print(f"Skipped incomplete manifest '{s['manifest']}': {s['reason']}", file=sys.stderr)

        # Ensure standard store directories exist (even for empty store)
        (resolved_target / "objects").mkdir(parents=True, exist_ok=True)
        (resolved_target / "receipts" / "v1").mkdir(parents=True, exist_ok=True)

        # 5. Restore files from manifest roster into target
        entries = chosen_manifest_data["entries"]
        objects_restored = 0
        receipts_restored = 0

        for entry in entries:
            rel_path_str = entry["path"]
            validate_relative_path(rel_path_str)

            src_file = resolved_backup / rel_path_str
            if entry["kind"] == "config":
                dst_file = resolved_target / "config.json"
            elif entry["kind"] == "receipt":
                validate_receipt_path(rel_path_str)
                dst_file = resolved_target / rel_path_str
            else:
                dst_file = resolved_target / rel_path_str
            check_isolation(dst_file, resolved_backup)

            exp_sha = entry["sha256"]
            exp_size = entry["size"]

            stage_and_verify_copy(src_file, dst_file, expected_sha=exp_sha, expected_size=exp_size)

            if entry["kind"] == "object":
                objects_restored += 1
            elif entry["kind"] == "receipt":
                # Validate receipt schema after copy
                load_and_validate_receipt(dst_file)
                receipts_restored += 1

        # 6. Rebuild index (if available) - report as warning with exit 0 only if data verified
        try:
            from secondbrain.search import ensure_index_current

            ensure_index_current(resolved_target, allow_restore_marker=True)
        except Exception as exc:
            msg = f"Warning: Index rebuild failed during restore: {exc}"
            print(msg, file=sys.stderr)
            warnings.warn(msg, UserWarning, stacklevel=2)

        # 7. Run full verify on restored repository
        verify_report = verify_repository(resolved_target, allow_restore_marker=True)
        if verify_report.get("io_errors"):
            raise UsageIOError(f"IO errors during verification of restored repository: {verify_report['io_errors']}")

        has_integrity_failure = (
            verify_report.get("missing", 0) > 0
            or verify_report.get("corrupt", 0) > 0
            or verify_report.get("invalid_receipts", 0) > 0
            or verify_report.get("temp_files", 0) > 0
        )
        if has_integrity_failure:
            raise IntegrityError(f"Restored repository failed verification: {verify_report}")

        if verify_report.get("orphan", 0) > 0:
            msg = f"Warning: Restored repository contains {verify_report['orphan']} unreferenced (orphan) object(s)."
            print(msg, file=sys.stderr)
            warnings.warn(msg, UserWarning, stacklevel=2)

        # 8. Clean up restore reservation marker only after all steps succeed
        if marker_path.exists():
            try:
                marker_path.unlink()
            except OSError:
                pass
    except BaseException:
        # Keep restore reservation marker on failure
        raise

    summary = {
        "verification": "PASS",
        "restored_root": str(resolved_target),
        "backup_root": str(resolved_backup),
        "manifest": chosen_manifest.name,
        "receipts": receipts_restored,
        "objects": objects_restored,
        "skipped_manifests": skipped_manifests,
    }

    return {
        "status": "ok",
        "verification": "PASS",
        "restored_root": str(resolved_target),
        "backup_root": str(resolved_backup),
        "manifest": chosen_manifest.name,
        "receipts": receipts_restored,
        "objects": objects_restored,
        "skipped_manifests": skipped_manifests,
        "verify_report": verify_report,
        "results": [summary],
        "errors": [],
    }
