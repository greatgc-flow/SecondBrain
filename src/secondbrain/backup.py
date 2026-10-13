"""Backup engine for SecondBrain: append-only mirror with strict MANIFEST v1 and isolated writes."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain import __version__
from secondbrain.capture import compute_sha256
from secondbrain.errors import IntegrityError, LockError, UsageIOError
from secondbrain.lock import WriterLock
from secondbrain.publish import (
    compute_file_sha256,
    is_tool_temp_file,
    make_temp_path,
    publish_no_clobber,
    retry_sharing_violation,
    stage_and_verify_bytes,
    stage_and_verify_copy,
)
from secondbrain.receipt import (
    HEX64_PATTERN,
    is_reparse_point,
    load_and_validate_receipt,
    receipt_rel_path,
    validate_receipt_path,
)
from secondbrain.root import (
    check_uncertain_sync,
    is_cloud_synced_path,
    load_config,
    validate_root,
)

RESERVED_WINDOWS_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
})


def validate_relative_path(path_str: str) -> Path:
    """Validate relative path: no .., absolute, drive letters, NTFS streams, reserved names.

    Raises IntegrityError on invalid path.
    """
    if not path_str or not isinstance(path_str, str):
        raise IntegrityError(f"Malformed path: must be a non-empty string, got {path_str!r}")

    if "\0" in path_str:
        raise IntegrityError(f"Invalid path containing null bytes: {path_str!r}")

    if re.match(r"^[a-zA-Z]:", path_str):
        raise IntegrityError(f"Path must not contain drive letters: {path_str!r}")

    p = Path(path_str)
    if p.is_absolute() or path_str.startswith(("/", "\\")):
        raise IntegrityError(f"Path must be relative, got absolute path: {path_str!r}")

    for part in p.parts:
        if part in (".", ".."):
            raise IntegrityError(f"Path traversal ('{part}') is prohibited: {path_str!r}")
        if ":" in part:
            raise IntegrityError(f"NTFS alternate data streams (':') are prohibited: {path_str!r}")

        base = part.split(".")[0].upper()
        if base in RESERVED_WINDOWS_NAMES:
            raise IntegrityError(f"Windows reserved name '{part}' is prohibited: {path_str!r}")

    return p


def _get_path_identity(p: Path) -> tuple[int, int] | None:
    try:
        st = os.stat(str(p))
        dev = getattr(st, "st_dev", 0)
        ino = getattr(st, "st_ino", 0)
        if ino != 0 or dev != 0:
            return (dev, ino)
    except OSError:
        pass
    return None


def _get_existing_ancestors(p: Path) -> list[Path]:
    try:
        resolved = Path(os.path.realpath(str(p)))
    except Exception:
        resolved = p.resolve()
    res = []
    curr = resolved
    while True:
        if curr.exists():
            res.append(curr)
        parent = curr.parent
        if parent == curr:
            break
        curr = parent
    return res


def check_isolation(path_a: Path, path_b: Path) -> None:
    """Refuse any write path that resolves into active data root in both overlap directions.

    Inspects real paths, case, short names, junctions/symlinks, and device/inode identities.
    """
    try:
        a_real = Path(os.path.normcase(os.path.realpath(str(path_a))))
    except Exception:
        a_real = Path(os.path.normcase(str(path_a.resolve())))

    try:
        b_real = Path(os.path.normcase(os.path.realpath(str(path_b))))
    except Exception:
        b_real = Path(os.path.normcase(str(path_b.resolve())))

    if a_real == b_real:
        raise UsageIOError(f"Root overlap refused: '{path_a}' and '{path_b}' resolve to the same location")
    if b_real in a_real.parents:
        raise UsageIOError(f"Root overlap refused: '{path_a}' is inside '{path_b}'")
    if a_real in b_real.parents:
        raise UsageIOError(f"Root overlap refused: '{path_b}' is inside '{path_a}'")

    # Ancestor device/inode inspection
    a_ident = _get_path_identity(path_a) if path_a.exists() else None
    b_ident = _get_path_identity(path_b) if path_b.exists() else None

    if a_ident is not None and b_ident is not None and a_ident == b_ident:
        raise UsageIOError(f"Root identity collision refused: '{path_a}' and '{path_b}' resolve to the same filesystem entity")

    if b_ident is not None:
        for anc in _get_existing_ancestors(path_a):
            if _get_path_identity(anc) == b_ident:
                raise UsageIOError(f"Ancestor identity collision refused: '{path_a}' is inside '{path_b}'")

    if a_ident is not None:
        for anc in _get_existing_ancestors(path_b):
            if _get_path_identity(anc) == a_ident:
                raise UsageIOError(f"Ancestor identity collision refused: '{path_b}' is inside '{path_a}'")


def is_nlink_zero(path: Path) -> bool:
    """Check if st_nlink is 0 on path (virtual drive / Google Drive FS)."""
    try:
        st = os.stat(str(path))
        return getattr(st, "st_nlink", 1) == 0
    except OSError:
        return False


def check_backup_cloud_synced(backup_root: Path) -> None:
    """Warn when backup root looks cloud-synced (intended use per ADR 0003)."""
    is_synced, sync_reason = is_cloud_synced_path(backup_root)
    uncertain = check_uncertain_sync(backup_root)
    reason = sync_reason or uncertain
    if is_synced or uncertain:
        msg = (
            f"Warning (ADR 0003): Backup root '{backup_root}' appears to be cloud-synced ({reason}). "
            "This is the intended use; local backup success means verified local writes, not confirmed cloud sync."
        )
        print(msg, file=sys.stderr)
        warnings.warn(msg, UserWarning, stacklevel=2)


def check_backup_nlink(backup_root: Path) -> None:
    """Warn when st_nlink is 0 on virtual drive (Google Drive FS)."""
    if is_nlink_zero(backup_root):
        msg = f"Warning: st_nlink is 0 on backup root '{backup_root}' (virtual drive / Google Drive FS). Continuing."
        print(msg, file=sys.stderr)
        warnings.warn(msg, UserWarning, stacklevel=2)


import stat


def reject_reparse_ancestors(target_path: Path, root: Path, role: str = "path") -> None:
    """Walk each component from root down to target_path and reject if any component is a symlink or reparse point."""
    if target_path.is_absolute():
        try:
            rel = target_path.relative_to(root)
        except ValueError:
            return
        parts = rel.parts
    else:
        parts = target_path.parts

    curr = root
    for part in parts:
        curr = curr / part
        if os.path.lexists(str(curr)):
            if curr.is_symlink() or os.path.islink(str(curr)) or is_reparse_point(curr):
                raise IntegrityError(
                    f"Symlink or reparse point rejected for {role}: '{curr}'"
                )
        else:
            break


def validate_payload_file(p: Path, role: str = "payload", root: Path | None = None) -> None:
    """Ensure a payload file (source or backup) is a regular file with nlink==1 and not a link/reparse point."""
    if not os.path.lexists(str(p)):
        return
    if root is not None:
        reject_reparse_ancestors(p, root, role=role)
    if p.is_symlink() or os.path.islink(str(p)) or is_reparse_point(p):
        raise IntegrityError(f"Symlink or reparse point rejected for {role} file: '{p}'")
    try:
        st = os.lstat(str(p))
    except OSError as exc:
        raise UsageIOError(f"Cannot stat {role} file '{p}': {exc}") from exc

    if not stat.S_ISREG(st.st_mode):
        raise IntegrityError(f"Non-regular file rejected for {role} file: '{p}'")

    if not is_nlink_zero(p) and getattr(st, "st_nlink", 1) != 1:
        raise IntegrityError(
            f"Hardlink alias rejected for {role} file: '{p}' has nlink={st.st_nlink} != 1"
        )


def check_payload_isolation(
    dst_file: Path,
    src_file: Path | None = None,
    source_file_ids: set[tuple[int, int]] | None = None,
    backup_root: Path | None = None,
    data_root: Path | None = None,
) -> None:
    """Ensure backup payload file is strictly independent.

    Rejects symlinks/reparse points and hardlink aliases for both dst and src.
    Only regular files with nlink==1 are accepted.
    """
    if os.path.lexists(str(dst_file)):
        if backup_root is not None:
            reject_reparse_ancestors(dst_file, backup_root, role="backup payload")
        validate_payload_file(dst_file, role="backup payload", root=backup_root)

        dst_ident = _get_path_identity(dst_file)
        if dst_ident is not None and source_file_ids is not None:
            if dst_ident in source_file_ids:
                raise IntegrityError(
                    f"Hardlink alias rejected in backup payload: '{dst_file}' shares file identity with source"
                )

        if src_file is not None and os.path.lexists(str(src_file)):
            try:
                if os.path.samefile(str(dst_file), str(src_file)):
                    raise IntegrityError(
                        f"Hardlink alias rejected in backup payload: '{dst_file}' shares file identity with source '{src_file}'"
                    )
            except OSError:
                pass

    if src_file is not None and os.path.lexists(str(src_file)):
        if data_root is not None:
            reject_reparse_ancestors(src_file, data_root, role="source payload")
        validate_payload_file(src_file, role="source payload", root=data_root)


def validate_source_store_layout(root: Path) -> None:
    """Validate source store layout before backup.

    Raises UsageIOError (exit 2) if root is nonexistent, not a directory,
    or missing required SecondBrain layout (objects, receipts/v1).
    """
    if not root.exists() or not root.is_dir() or is_reparse_point(root):
        raise UsageIOError(f"Source repository does not exist or is not a directory: '{root}'")

    validate_root(root)

    objects_dir = root / "objects"
    receipts_dir = root / "receipts"
    receipts_v1_dir = receipts_dir / "v1"

    if not objects_dir.is_dir() or is_reparse_point(objects_dir):
        raise UsageIOError(f"Not a SecondBrain store: missing or non-directory 'objects' in '{root}'")
    if not receipts_dir.is_dir() or is_reparse_point(receipts_dir):
        raise UsageIOError(f"Not a SecondBrain store: missing or non-directory 'receipts' in '{root}'")
    if not receipts_v1_dir.is_dir() or is_reparse_point(receipts_v1_dir):
        raise UsageIOError(f"Not a SecondBrain store: missing or non-directory 'receipts/v1' in '{root}'")

    for d in (objects_dir, receipts_dir, receipts_v1_dir):
        curr = root
        for part in d.relative_to(root).parts:
            curr = curr / part
            if curr.is_symlink() or os.path.islink(str(curr)) or is_reparse_point(curr):
                raise UsageIOError(f"Not a SecondBrain store: symlink or reparse point '{curr}' in '{root}'")


class BackupLock:
    """Exclusive lock for serializing backup snapshot & manifest publication. Stale-lock safe."""

    def __init__(self, backup_root: Path, timeout: float = 30.0, data_root: Path | None = None) -> None:
        self.backup_root = backup_root
        self.lock_path = backup_root / ".sb" / "backup.lock"
        self.timeout = timeout
        self.data_root = data_root
        self._fp: Any = None

    def acquire(self) -> None:
        reject_reparse_ancestors(self.lock_path, self.backup_root, role="backup lock")
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        start_time = time.time()
        while True:
            try:
                if self.lock_path.is_symlink() or is_reparse_point(self.lock_path):
                    raise LockError(f"Backup lock path is a symlink or reparse point: {self.lock_path}")

                if self.lock_path.exists():
                    st = self.lock_path.stat()
                    if st.st_nlink > 1:
                        raise LockError(
                            f"Backup lock path has multiple hardlinks (nlink={st.st_nlink}): {self.lock_path}"
                        )
                    if self.data_root is not None:
                        try:
                            if os.path.samefile(self.lock_path, self.data_root):
                                raise LockError(f"Backup lock path is same file as data root: {self.lock_path}")
                        except OSError:
                            pass
                        for r_dir, _, r_files in os.walk(self.data_root):
                            for r_f in r_files:
                                r_path = Path(r_dir) / r_f
                                try:
                                    if os.path.samefile(self.lock_path, r_path):
                                        raise LockError(
                                            f"Backup lock path is same file as data root file '{r_path}'"
                                        )
                                except OSError:
                                    pass

                    # Open pre-existing file without writing content ("no content writes into pre-existing files")
                    self._fp = open(self.lock_path, "r+b")
                    fstat = os.fstat(self._fp.fileno())
                    if fstat.st_nlink > 1:
                        self._fp.close()
                        self._fp = None
                        raise LockError(
                            f"Backup lock path has multiple hardlinks (nlink={fstat.st_nlink}): {self.lock_path}"
                        )
                else:
                    # Create atomically with O_CREAT | O_EXCL
                    flags = os.O_CREAT | os.O_EXCL | os.O_RDWR
                    try:
                        fd = os.open(str(self.lock_path), flags)
                        self._fp = os.fdopen(fd, "w+b")
                        self._fp.write(b"L")
                        self._fp.flush()
                    except FileExistsError:
                        time.sleep(0.01)
                        continue

                self._fp.seek(0)
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(self._fp.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except LockError:
                if self._fp is not None:
                    try:
                        self._fp.close()
                    except Exception:
                        pass
                    self._fp = None
                raise
            except (OSError, IOError) as exc:
                if self._fp is not None:
                    try:
                        self._fp.close()
                    except Exception:
                        pass
                    self._fp = None
                if time.time() - start_time >= self.timeout:
                    raise LockError(f"Timed out acquiring backup publication lock on {self.lock_path}") from exc
                time.sleep(0.05)

    def release(self) -> None:
        if self._fp is not None:
            try:
                self._fp.seek(0)
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(self._fp.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._fp.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            finally:
                try:
                    self._fp.close()
                except Exception:
                    pass
                self._fp = None

    def __enter__(self) -> BackupLock:
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()


def backup_repository(
    data_root: Path,
    backup_root: Path | None = None,
    store_backup_root: bool = False,
    tool_version: str = __version__,
) -> dict[str, Any]:
    """Mirror repository objects, receipts, and config to backup_root with strict MANIFEST v1 written last."""
    resolved_data_root = data_root.resolve()
    validate_source_store_layout(resolved_data_root)

    # 1. Resolve backup_root from parameter or config
    if backup_root is None:
        cfg = load_config(resolved_data_root)
        cfg_root = cfg.get("backup_root")
        if not cfg_root:
            raise UsageIOError(
                "No backup root specified and none configured in config.json. Use sb backup --backup-root PATH."
            )
        resolved_backup_root = Path(cfg_root).resolve()
    else:
        resolved_backup_root = backup_root.resolve()

    # 2. Refuse overlap between data root and backup root (in both overlap directions)
    check_isolation(resolved_backup_root, resolved_data_root)

    # 3. Check cloud-synced path and virtual drive warnings
    check_backup_cloud_synced(resolved_backup_root)

    try:
        resolved_backup_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise UsageIOError(f"Cannot create or access backup root '{resolved_backup_root}': {exc}") from exc

    check_backup_nlink(resolved_backup_root)

    # Hold BackupLock for the entire snapshot: roster build through manifest publish
    with BackupLock(resolved_backup_root, data_root=resolved_data_root):
        roster_now = datetime.now(timezone.utc)
        ts_str = roster_now.strftime("%Y%m%dT%H%M%SZ")

        # 4. Snapshot data_root state under brief WriterLock WITHOUT mutating data root!
        start_lock = time.time()
        while True:
            try:
                with WriterLock(resolved_data_root):
                    config = load_config(resolved_data_root)

                    # Reject any unexpected entry in receipts/ (same rule as verify)
                    src_receipts_dir = resolved_data_root / "receipts"
                    if src_receipts_dir.is_dir():
                        reject_reparse_ancestors(src_receipts_dir, resolved_data_root, role="source receipts dir")
                        if is_reparse_point(src_receipts_dir):
                            raise IntegrityError(f"Receipts directory is a symlink or reparse point: {src_receipts_dir}")
                        try:
                            for entry in os.scandir(src_receipts_dir):
                                if is_tool_temp_file(Path(entry.path)):
                                    continue
                                if entry.name != "v1":
                                    raise IntegrityError(
                                        f"Invalid item in receipts directory outside receipts/v1: {entry.name}"
                                    )
                        except OSError as exc:
                            raise UsageIOError(f"Failed to scan receipts directory during backup snapshot: {exc}") from exc

                    receipts_dir = resolved_data_root / "receipts" / "v1"
                    snapshot_receipts: list[dict[str, Any]] = []
                    if receipts_dir.is_dir():
                        reject_reparse_ancestors(receipts_dir, resolved_data_root, role="source receipts/v1 dir")
                        if is_reparse_point(receipts_dir):
                            raise IntegrityError(f"Receipts/v1 directory is a symlink or reparse point: {receipts_dir}")
                        try:
                            for entry in sorted(os.scandir(receipts_dir), key=lambda e: e.name):
                                rec_path = Path(entry.path)
                                if is_tool_temp_file(rec_path):
                                    continue
                                reject_reparse_ancestors(rec_path, resolved_data_root, role="source receipt")
                                if is_reparse_point(rec_path):
                                    raise IntegrityError(f"Receipt file is a symlink or reparse point: {entry.name}")
                                if entry.is_dir(follow_symlinks=False):
                                    raise IntegrityError(f"Unexpected subdirectory in receipts/v1: {entry.name}")
                                if not entry.name.endswith(".json"):
                                    raise IntegrityError(f"Non-JSON file in receipts/v1: {entry.name}")
                                rec = load_and_validate_receipt(rec_path)
                                snapshot_receipts.append(rec)
                        except OSError as exc:
                            raise UsageIOError(f"Failed to read receipts during backup snapshot: {exc}") from exc

                    # Verify no duplicate receipts
                    seen_rec_ids: set[str] = set()
                    for rec in snapshot_receipts:
                        if rec["id"] in seen_rec_ids:
                            raise IntegrityError(f"Duplicate receipt ID '{rec['id']}'")
                        seen_rec_ids.add(rec["id"])

                    # Reject any unexpected entry in objects/ (same rule as verify)
                    all_object_shas: set[str] = {rec["sha256"] for rec in snapshot_receipts}
                    src_objects_dir = resolved_data_root / "objects"
                    hex2_pattern = re.compile(r"^[0-9a-f]{2}$")
                    if src_objects_dir.is_dir():
                        reject_reparse_ancestors(src_objects_dir, resolved_data_root, role="source objects dir")
                        if is_reparse_point(src_objects_dir):
                            raise IntegrityError(f"Objects directory is a symlink or reparse point: {src_objects_dir}")
                        for prefix_entry in sorted(os.scandir(src_objects_dir), key=lambda e: e.name):
                            prefix_path = Path(prefix_entry.path)
                            if is_tool_temp_file(prefix_path):
                                continue
                            reject_reparse_ancestors(prefix_path, resolved_data_root, role="source prefix directory")
                            if is_reparse_point(prefix_path):
                                raise IntegrityError(f"Prefix directory is a symlink or reparse point: {prefix_entry.name}")
                            if prefix_entry.is_file(follow_symlinks=False):
                                raise IntegrityError(f"Unexpected file in objects root: {prefix_entry.name}")
                            if not prefix_entry.is_dir(follow_symlinks=False):
                                raise IntegrityError(f"Unexpected entry in objects root: {prefix_entry.name}")
                            prefix_name = prefix_entry.name
                            if not hex2_pattern.match(prefix_name):
                                raise IntegrityError(
                                    f"Invalid prefix directory name: '{prefix_name}'. Expected 2 lowercase hex characters."
                                )
                            for obj_entry in sorted(os.scandir(prefix_entry.path), key=lambda e: e.name):
                                obj_path = Path(obj_entry.path)
                                if is_tool_temp_file(obj_path):
                                    continue
                                reject_reparse_ancestors(obj_path, resolved_data_root, role="source object")
                                if is_reparse_point(obj_path):
                                    raise IntegrityError(f"Object file is a symlink or reparse point: {obj_entry.name}")
                                if obj_entry.is_dir(follow_symlinks=False):
                                    raise IntegrityError(f"Nested directory inside prefix dir: {obj_entry.name}")
                                obj_name = obj_entry.name
                                if not HEX64_PATTERN.match(obj_name) or obj_name != obj_name.lower():
                                    raise IntegrityError(
                                        f"Invalid object filename: '{obj_name}'. Must be 64 lowercase hex chars."
                                    )
                                if obj_name[:2] != prefix_name:
                                    raise IntegrityError(
                                        f"Object {obj_name} in mismatched prefix dir '{prefix_name}'"
                                    )
                                all_object_shas.add(obj_name)

                    # Collect source file identities to detect hardlink aliases, and validate source payload files
                    source_file_ids: set[tuple[int, int]] = set()
                    src_cfg_path = resolved_data_root / "config.json"
                    if os.path.lexists(str(src_cfg_path)):
                        reject_reparse_ancestors(src_cfg_path, resolved_data_root, role="source config")
                        validate_payload_file(src_cfg_path, role="source config", root=resolved_data_root)
                        cfg_ident = _get_path_identity(src_cfg_path)
                        if cfg_ident is not None:
                            source_file_ids.add(cfg_ident)

                    for sha in all_object_shas:
                        obj_p = resolved_data_root / "objects" / sha[:2] / sha
                        reject_reparse_ancestors(obj_p, resolved_data_root, role="source object")
                        validate_payload_file(obj_p, role="source object", root=resolved_data_root)
                        o_ident = _get_path_identity(obj_p)
                        if o_ident is not None:
                            source_file_ids.add(o_ident)

                    for rec in snapshot_receipts:
                        rec_p = resolved_data_root / "receipts" / "v1" / f"{rec['id']}.json"
                        reject_reparse_ancestors(rec_p, resolved_data_root, role="source receipt")
                        validate_payload_file(rec_p, role="source receipt", root=resolved_data_root)
                        r_ident = _get_path_identity(rec_p)
                        if r_ident is not None:
                            source_file_ids.add(r_ident)
                break
            except LockError as exc:
                if "Another process holds" not in str(exc) or time.time() - start_lock >= 10.0:
                    raise
                time.sleep(0.05)

        # 5. Mirror missing objects outside WriterLock, including orphan source objects
        needed_objects: dict[str, int] = {}
        copied_objects = 0
        reused_objects = 0

        backup_objects_dir = resolved_backup_root / "objects"
        check_isolation(backup_objects_dir, resolved_data_root)
        reject_reparse_ancestors(backup_objects_dir, resolved_backup_root, role="backup objects dir")
        backup_objects_dir.mkdir(parents=True, exist_ok=True)

        for sha256 in sorted(all_object_shas):
            src_obj = resolved_data_root / "objects" / sha256[:2] / sha256
            dst_obj = backup_objects_dir / sha256[:2] / sha256
            check_isolation(dst_obj, resolved_data_root)
            reject_reparse_ancestors(dst_obj, resolved_backup_root, role="backup object")
            reject_reparse_ancestors(src_obj, resolved_data_root, role="source object")

            validate_payload_file(src_obj, role="source object", root=resolved_data_root)
            if not src_obj.is_file(follow_symlinks=False):
                raise IntegrityError(f"Referenced object does not exist or is not a regular file: {src_obj}")

            # Ensure source object in data root is not corrupted
            src_sha = compute_file_sha256(src_obj)
            if src_sha != sha256:
                raise IntegrityError(
                    f"Corrupted object in data root: {src_obj} expected {sha256} got {src_sha}"
                )

            if os.path.lexists(str(dst_obj)):
                check_payload_isolation(
                    dst_obj, src_obj, source_file_ids,
                    backup_root=resolved_backup_root, data_root=resolved_data_root,
                )
                # Existing objects already in backup root are VERIFIED before being trusted
                dst_sha = compute_file_sha256(dst_obj)
                if dst_sha != sha256:
                    raise IntegrityError(
                        f"Corrupted existing object in backup root: {dst_obj} expected {sha256} got {dst_sha}"
                    )
                reused_objects += 1
                needed_objects[sha256] = dst_obj.stat().st_size
            else:
                size = stage_and_verify_copy(src_obj, dst_obj, expected_sha=sha256)
                check_payload_isolation(
                    dst_obj, src_obj, source_file_ids,
                    backup_root=resolved_backup_root, data_root=resolved_data_root,
                )
                copied_objects += 1
                needed_objects[sha256] = size

        # 6. Mirror receipts
        backup_receipts_dir = resolved_backup_root / "receipts" / "v1"
        check_isolation(backup_receipts_dir, resolved_data_root)
        reject_reparse_ancestors(backup_receipts_dir, resolved_backup_root, role="backup receipts dir")
        backup_receipts_dir.mkdir(parents=True, exist_ok=True)
        copied_receipts = 0
        reused_receipts = 0
        receipt_entries_info: list[dict[str, Any]] = []

        for rec in snapshot_receipts:
            rec_id = rec["id"]
            rel_rec_path = validate_receipt_path(receipt_rel_path(rec_id))
            validate_relative_path(rel_rec_path)

            src_rec = resolved_data_root / rel_rec_path
            dst_rec = backup_receipts_dir / f"{rec_id}.json"
            check_isolation(dst_rec, resolved_data_root)
            reject_reparse_ancestors(dst_rec, resolved_backup_root, role="backup receipt")
            reject_reparse_ancestors(src_rec, resolved_data_root, role="source receipt")

            validate_payload_file(src_rec, role="source receipt", root=resolved_data_root)
            if not src_rec.is_file(follow_symlinks=False):
                raise IntegrityError(f"Receipt file does not exist or is not a regular file: {src_rec}")
            src_rec_sha = compute_file_sha256(src_rec)
            src_rec_size = src_rec.stat().st_size

            if os.path.lexists(str(dst_rec)):
                check_payload_isolation(
                    dst_rec, src_rec, source_file_ids,
                    backup_root=resolved_backup_root, data_root=resolved_data_root,
                )
                dst_rec_sha = compute_file_sha256(dst_rec)
                if dst_rec_sha != src_rec_sha:
                    raise IntegrityError(
                        f"Differing existing receipt in backup root: {dst_rec} expected {src_rec_sha} got {dst_rec_sha}"
                    )
                reused_receipts += 1
            else:
                stage_and_verify_copy(src_rec, dst_rec, expected_sha=src_rec_sha, expected_size=src_rec_size)
                check_payload_isolation(
                    dst_rec, src_rec, source_file_ids,
                    backup_root=resolved_backup_root, data_root=resolved_data_root,
                )
                copied_receipts += 1

            receipt_entries_info.append({
                "kind": "receipt",
                "path": rel_rec_path,
                "sha256": src_rec_sha,
                "size": src_rec_size,
            })

        # 7. Mirror data config: versioned per snapshot (hash-named) instead of fixed name
        src_cfg = resolved_data_root / "config.json"
        manifest_entries: list[dict[str, Any]] = []

        backup_configs_dir = resolved_backup_root / "configs"
        check_isolation(backup_configs_dir, resolved_data_root)
        reject_reparse_ancestors(backup_configs_dir, resolved_backup_root, role="backup configs dir")
        backup_configs_dir.mkdir(parents=True, exist_ok=True)

        if os.path.lexists(str(src_cfg)):
            reject_reparse_ancestors(src_cfg, resolved_data_root, role="source config")
            validate_payload_file(src_cfg, role="source config", root=resolved_data_root)
            if not src_cfg.is_file(follow_symlinks=False):
                raise IntegrityError(f"Config file is not a regular file: {src_cfg}")
            cfg_sha = compute_file_sha256(src_cfg)
            cfg_size = src_cfg.stat().st_size
            dst_cfg = backup_configs_dir / f"{cfg_sha}.json"
            check_isolation(dst_cfg, resolved_data_root)
            reject_reparse_ancestors(dst_cfg, resolved_backup_root, role="backup config")

            if os.path.lexists(str(dst_cfg)):
                check_payload_isolation(
                    dst_cfg, src_cfg, source_file_ids,
                    backup_root=resolved_backup_root, data_root=resolved_data_root,
                )
                dst_cfg_sha = compute_file_sha256(dst_cfg)
                if dst_cfg_sha != cfg_sha:
                    raise IntegrityError(
                        f"Differing existing config in backup root: {dst_cfg} expected {cfg_sha} got {dst_cfg_sha}"
                    )
            else:
                stage_and_verify_copy(src_cfg, dst_cfg, expected_sha=cfg_sha, expected_size=cfg_size)
                check_payload_isolation(
                    dst_cfg, src_cfg, source_file_ids,
                    backup_root=resolved_backup_root, data_root=resolved_data_root,
                )
        else:
            default_cfg_bytes = (json.dumps({"backup_root": None}, indent=2) + "\n").encode("utf-8")
            cfg_sha = hashlib.sha256(default_cfg_bytes).hexdigest().lower()
            cfg_size = len(default_cfg_bytes)
            dst_cfg = backup_configs_dir / f"{cfg_sha}.json"
            check_isolation(dst_cfg, resolved_data_root)
            reject_reparse_ancestors(dst_cfg, resolved_backup_root, role="backup config")

            if os.path.lexists(str(dst_cfg)):
                check_payload_isolation(
                    dst_cfg, None, source_file_ids,
                    backup_root=resolved_backup_root, data_root=resolved_data_root,
                )
                dst_cfg_sha = compute_file_sha256(dst_cfg)
                if dst_cfg_sha != cfg_sha:
                    raise IntegrityError(
                        f"Differing existing config in backup root: {dst_cfg} expected {cfg_sha} got {dst_cfg_sha}"
                    )
            else:
                stage_and_verify_bytes(default_cfg_bytes, dst_cfg, expected_sha=cfg_sha)
                check_payload_isolation(
                    dst_cfg, None, source_file_ids,
                    backup_root=resolved_backup_root, data_root=resolved_data_root,
                )

        manifest_entries.append({
            "kind": "config",
            "path": f"configs/{cfg_sha}.json",
            "sha256": cfg_sha,
            "size": cfg_size,
        })

        # Add receipts and objects to manifest entries
        manifest_entries.extend(receipt_entries_info)
        for sha in sorted(needed_objects.keys()):
            obj_rel_path = f"objects/{sha[:2]}/{sha}"
            validate_relative_path(obj_rel_path)
            manifest_entries.append({
                "kind": "object",
                "path": obj_rel_path,
                "sha256": sha,
                "size": needed_objects[sha],
            })

        # 8. Write dated MANIFEST v1 LAST, atomically, no-clobber, under BackupLock
        manifests_dir = resolved_backup_root / "manifests"
        check_isolation(manifests_dir, resolved_data_root)
        reject_reparse_ancestors(manifests_dir, resolved_backup_root, role="backup manifests dir")
        manifests_dir.mkdir(parents=True, exist_ok=True)

        manifest_data = {
            "schema_version": 1,
            "created_utc": roster_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tool_version": tool_version,
            "entries": manifest_entries,
        }
        manifest_bytes = (json.dumps(manifest_data, indent=2) + "\n").encode("utf-8")
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest().lower()

        # Look for collision counter in the same second without sleeping
        base_name = f"{ts_str}.json"
        base_path = manifests_dir / base_name

        if not base_path.exists():
            chosen_name = base_name
        else:
            counter = 2
            while (manifests_dir / f"{ts_str}-{counter}.json").exists():
                counter += 1
            chosen_name = f"{ts_str}-{counter}.json"

        manifest_path = manifests_dir / chosen_name
        check_isolation(manifest_path, resolved_data_root)
        reject_reparse_ancestors(manifest_path, resolved_backup_root, role="backup manifest")
        stage_and_verify_bytes(manifest_bytes, manifest_path, expected_sha=manifest_sha)

    summary = {
        "backup_root": str(resolved_backup_root),
        "manifest": chosen_name,
        "manifest_path": str(manifest_path),
        "copied_objects": copied_objects,
        "reused_objects": reused_objects,
        "copied_receipts": copied_receipts,
        "reused_receipts": reused_receipts,
        "total_objects": len(needed_objects),
        "total_receipts": len(snapshot_receipts),
    }

    return {
        "status": "ok",
        "backup_root": str(resolved_backup_root),
        "manifest": chosen_name,
        "manifest_path": str(manifest_path),
        "copied_objects": copied_objects,
        "reused_objects": reused_objects,
        "copied_receipts": copied_receipts,
        "reused_receipts": reused_receipts,
        "total_objects": len(needed_objects),
        "total_receipts": len(snapshot_receipts),
        "results": [summary],
        "errors": [],
    }
