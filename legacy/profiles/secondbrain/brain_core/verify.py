"""S1 read-only object verifier; no credentials, cloud, AI or mutating features.

Contracts are sourced from ../schemas/v2; this source-checkout prototype is
NOT a tested wheel installation or a forensic-acquisition system.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
OBJECT_ID = re.compile(r"obj-sha256-([0-9a-f]{64})\Z")

# WinNT.h: reparse point, offline, recall-on-open, recall-on-data-access.
# Python exposes st_file_attributes on Windows; the latter two flags may
# not be present in every metadata API. No flag != guaranteed hydration.
_WINDOWS_UNSAFE_ATTRS = 0x00000400 | 0x00001000 | 0x00040000 | 0x00400000


def _unsafe_windows_attributes(result: os.stat_result) -> bool:
    return bool(getattr(result, "st_file_attributes", 0) & _WINDOWS_UNSAFE_ATTRS)


class IntegrityFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _strict_json(path: Path) -> dict[str, Any]:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out = {}
        for key, val in pairs:
            if key in out:
                raise IntegrityFailure("JSON_DUPLICATE_KEY")
            out[key] = val
        return out

    def bad_number(_value: str):
        raise IntegrityFailure("SCHEMA_INVALID")

    try:
        raw = path.read_bytes()
        obj = json.loads(raw.decode("utf-8", errors="strict"),
                         object_pairs_hook=pairs_hook, parse_constant=bad_number)
    except IntegrityFailure:
        raise
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise IntegrityFailure("SCHEMA_INVALID") from exc
    except OSError as exc:
        raise IntegrityFailure("INCOMPLETE_COMMIT") from exc
    if not isinstance(obj, dict):
        raise IntegrityFailure("SCHEMA_INVALID")
    return obj


def _safe_regular_file(root: Path, file: Path, *, missing_code: str) -> None:
    """Reject links and other special files on inspected relative path.

    Local lstat is not a substitute for OS-level secure openat in a hostile
    concurrently mutating filesystem. See limitations in docs.
    """
    try:
        rel = file.relative_to(root)
        cur = root
        for part in rel.parts:
            cur = cur / part
            current_stat = cur.lstat()
            mode = current_stat.st_mode
            if _unsafe_windows_attributes(current_stat):
                raise IntegrityFailure("UNSAFE_PATH")
            if stat.S_ISLNK(mode) or (hasattr(cur, 'is_junction') and cur.is_junction()):
                raise IntegrityFailure("UNSAFE_PATH")
            if cur == file:
                if not stat.S_ISREG(mode) or current_stat.st_nlink != 1:
                    # A hardlink can alias data outside the validated tree.
                    raise IntegrityFailure("UNSAFE_PATH")
            elif not stat.S_ISDIR(mode):
                raise IntegrityFailure("UNSAFE_PATH")
    except FileNotFoundError as exc:
        raise IntegrityFailure(missing_code) from exc
    except (OSError, ValueError) as exc:
        raise IntegrityFailure("UNSAFE_PATH") from exc


def _digest_fd(file: Path) -> tuple[str, str, int]:
    sha256, sha512 = hashlib.sha256(), hashlib.sha512()
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        leaf = file.lstat()  # metadata-only: refuse cloud recall BEFORE open()
        if (_unsafe_windows_attributes(leaf) or
                not stat.S_ISREG(leaf.st_mode) or leaf.st_nlink != 1):
            raise IntegrityFailure("UNSAFE_PATH")
        fd = os.open(file, flags)
        with os.fdopen(fd, "rb") as stream:
            first = os.fstat(stream.fileno())
            if (_unsafe_windows_attributes(first) or
                    not stat.S_ISREG(first.st_mode) or first.st_nlink != 1):
                raise IntegrityFailure("UNSAFE_PATH")
            if (first.st_dev, first.st_ino) != (leaf.st_dev, leaf.st_ino):
                raise IntegrityFailure("SOURCE_CHANGED")
            total = 0
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                sha256.update(block)
                sha512.update(block)
                total += len(block)
            last = os.fstat(stream.fileno())
        identity_first = (first.st_dev, first.st_ino, first.st_size, first.st_mtime_ns, first.st_ctime_ns)
        identity_last = (last.st_dev, last.st_ino, last.st_size, last.st_mtime_ns, last.st_ctime_ns)
        if identity_first != identity_last or last.st_nlink != 1 or _unsafe_windows_attributes(last):
            raise IntegrityFailure("SOURCE_CHANGED")
        return sha256.hexdigest(), sha512.hexdigest(), total
    except IntegrityFailure:
        raise
    except OSError as exc:
        raise IntegrityFailure("NOT_HYDRATED") from exc


def verify_object(root: str | Path, object_id: str) -> dict[str, str | int]:
    """Verify stored object metadata and payload bytes; do not change anything.

    PASS means only the current local bytes match canonical record digests.
    It does not assert original acquisition, custody authenticity or ERL.
    """
    match = OBJECT_ID.fullmatch(object_id)
    if not match:
        raise IntegrityFailure("SCHEMA_INVALID")
    digest = match.group(1)
    root = Path(root).expanduser().absolute()
    if not root.is_dir() or root.is_symlink() or _unsafe_windows_attributes(root.lstat()):
        raise IntegrityFailure("UNSAFE_PATH")
    rp = root / "10_Evidence" / "Records" / "objects" / f"{object_id}.json"
    _safe_regular_file(root, rp, missing_code="INCOMPLETE_COMMIT")
    record = _strict_json(rp)
    schema_file = Path(__file__).resolve().parents[1] / "schemas" / "v2" / "evidence-object.schema.json"
    schema = _strict_json(schema_file)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record))
    if errors:
        raise IntegrityFailure("SCHEMA_INVALID")
    if record["object_id"] != object_id or record["sha256"] != digest:
        raise IntegrityFailure("INTEGRITY_MISMATCH")
    expected_rel = f"10_Evidence/Vault/objects/sha256/{digest[:2]}/{digest[2:4]}/{digest}/payload"
    if record["vault_relpath"] != expected_rel:
        raise IntegrityFailure("UNSAFE_PATH")
    payload = root.joinpath(*expected_rel.split("/"))
    _safe_regular_file(root, payload, missing_code="NOT_HYDRATED")
    actual256, actual512, size = _digest_fd(payload)
    if (actual256 != digest or actual512 != record["sha512"] or size != record["size_bytes"]):
        raise IntegrityFailure("INTEGRITY_MISMATCH")
    return {"status": "PASS", "object_id": object_id, "size_bytes": size,
            "sha256": actual256, "sha512": actual512,
            "scope": "local_object_bytes_only"}
