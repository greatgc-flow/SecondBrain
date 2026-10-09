"""Capture-only, append-only local landing zone. NOT a sealed evidence vault.

Data layout: 00_Inbox/Drop/<device>/<capture>/payload,
            capture.receipt.json, .ready (published LAST).

No OneDrive/Drive API, no source deletion, no canonical object/custody writes.
The marker is a local consistency signal, NOT external authentication.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import time
import uuid
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .verify import IntegrityFailure, _strict_json, _safe_regular_file

_DEVICE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
_CAPTURE = re.compile(r"CAP-[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
_CHUNK = 1024 * 1024


class CaptureFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _uuid7() -> str:
    # RFC 9562 layout: 48-bit unix milliseconds | v7 | 12 rand | variant | 62 rand
    ms = int(time.time() * 1000)
    if not (0 <= ms < 2**48):
        raise CaptureFailure("INVALID_ARGUMENT")
    raw = (ms << 80) | (0x7 << 76) | (secrets.randbits(12) << 64) | (0b10 << 62) | secrets.randbits(62)
    return str(uuid.UUID(int=raw))


def _arguments(root: str | Path, device_id: str, capture_id: str | None) -> tuple[Path, str]:
    if not isinstance(device_id, str) or not _DEVICE.fullmatch(device_id):
        raise CaptureFailure("INVALID_ARGUMENT")
    cid = capture_id if capture_id is not None else "CAP-" + _uuid7()
    if not isinstance(cid, str) or not _CAPTURE.fullmatch(cid):
        raise CaptureFailure("INVALID_ARGUMENT")
    p = Path(root).expanduser().absolute()
    if not p.is_dir() or p.is_symlink():
        raise CaptureFailure("INVALID_ROOT")
    return p, cid


def _ensure_parent(root: Path, directory: Path) -> None:
    try:
        rel = directory.relative_to(root)
        curr = root
        for part in rel.parts:
            curr = curr / part
            try:
                curr.mkdir()
            except FileExistsError:
                pass
            mode = curr.lstat().st_mode
            if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
                raise CaptureFailure("UNSAFE_PATH")
    except OSError as exc:
        raise CaptureFailure("UNSAFE_PATH") from exc


def _source_fd(source: Path) -> int:
    try:
        source = source.absolute()
        path = Path(source.anchor)
        for part in source.parts[1:]:
            path = path / part
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise CaptureFailure("UNSAFE_SOURCE")
            if path == source:
                if not stat.S_ISREG(mode):
                    raise CaptureFailure("UNSAFE_SOURCE")
            elif not stat.S_ISDIR(mode):
                raise CaptureFailure("UNSAFE_SOURCE")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(source, flags)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise CaptureFailure("UNSAFE_SOURCE")
        return fd
    except (OSError, ValueError) as exc:
        raise CaptureFailure("UNSAFE_SOURCE") from exc


def _identity(s: os.stat_result) -> tuple[int, ...]:
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def _hash_source(source: Path) -> tuple[str, str, int]:
    fd = _source_fd(source)
    with os.fdopen(fd, "rb") as f:
        before = _identity(os.fstat(f.fileno()))
        a, b, count = hashlib.sha256(), hashlib.sha512(), 0
        while block := f.read(_CHUNK):
            a.update(block); b.update(block); count += len(block)
        if before != _identity(os.fstat(f.fileno())) or count != before[2]:
            raise CaptureFailure("SOURCE_CHANGED")
    return a.hexdigest(), b.hexdigest(), count


def _copy_source(source: Path, dest: Path) -> tuple[str, str, int]:
    fd = _source_fd(source)
    try:
        with os.fdopen(fd, "rb") as src:
            before = _identity(os.fstat(src.fileno()))
            a, b, count = hashlib.sha256(), hashlib.sha512(), 0
            with dest.open("xb") as dst:
                while block := src.read(_CHUNK):
                    dst.write(block); a.update(block); b.update(block); count += len(block)
                dst.flush(); os.fsync(dst.fileno())
            if before != _identity(os.fstat(src.fileno())) or count != before[2]:
                raise CaptureFailure("SOURCE_CHANGED")
            src.seek(0)
            check = hashlib.sha256()
            while block := src.read(_CHUNK):
                check.update(block)
            if check.hexdigest() != a.hexdigest() or before != _identity(os.fstat(src.fileno())):
                raise CaptureFailure("SOURCE_CHANGED")
        return a.hexdigest(), b.hexdigest(), count
    except FileExistsError as exc:
        raise CaptureFailure("INCOMPLETE_CAPTURE") from exc


def _write_exclusive(path: Path, blob: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(blob); f.flush(); os.fsync(f.fileno())


def _fsync_dir(path: Path) -> None:
    # Best-effort on Windows; durable rename still requires OS/filesystem behavior.
    if os.name != "nt":
        fd = os.open(path, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)


def _encode(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _load(path: Path) -> dict[str, Any]:
    try: return _strict_json(path)
    except IntegrityFailure as exc:
        raise CaptureFailure("INCOMPLETE_CAPTURE" if exc.code != "JSON_DUPLICATE_KEY" else "RECEIPT_TAMPERED") from exc


def verify_capture(root: str | Path, device_id: str, capture_id: str) -> dict[str, Any]:
    root, cid = _arguments(root, device_id, capture_id)
    directory = root / "00_Inbox" / "Drop" / device_id / cid
    marker, rp, payload = directory / ".ready", directory / "capture.receipt.json", directory / "payload"
    for path in (marker, rp, payload):
        try: _safe_regular_file(root, path, missing_code="INCOMPLETE_CAPTURE")
        except IntegrityFailure as exc:
            if exc.code == "UNSAFE_PATH": raise CaptureFailure("UNSAFE_PATH") from exc
            raise CaptureFailure("INCOMPLETE_CAPTURE") from exc
    mark = _load(marker)
    receipt_raw = rp.read_bytes()
    receipt = _load(rp)
    if not isinstance(mark, dict) or set(mark) != {"schema_version", "capture_id", "receipt_sha256", "payload_sha256"}:
        raise CaptureFailure("INCOMPLETE_CAPTURE")
    if mark["schema_version"] != 1 or mark["capture_id"] != cid or mark["receipt_sha256"] != hashlib.sha256(receipt_raw).hexdigest():
        raise CaptureFailure("RECEIPT_TAMPERED")
    schema_path = Path(__file__).resolve().parents[1] / "schemas/v2/capture-receipt.schema.json"
    schema = _load(schema_path)
    if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(receipt)):
        raise CaptureFailure("SCHEMA_INVALID")
    if receipt["capture_id"] != cid or receipt["device_id"] != device_id:
        raise CaptureFailure("RECEIPT_TAMPERED")
    a, b, size = hashlib.sha256(), hashlib.sha512(), 0
    # Source checkout prototype: lstat path checks, O_NOFOLLOW leaf, stat stability.
    flags = os.O_RDONLY | getattr(os,"O_BINARY",0) | getattr(os,"O_NOFOLLOW",0)
    try:
        with os.fdopen(os.open(payload, flags),"rb") as f:
            before = _identity(os.fstat(f.fileno()))
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                raise CaptureFailure("UNSAFE_PATH")
            while block := f.read(_CHUNK):
                a.update(block); b.update(block); size += len(block)
            if before != _identity(os.fstat(f.fileno())):
                raise CaptureFailure("SOURCE_CHANGED")
    except OSError as exc:
        raise CaptureFailure("INCOMPLETE_CAPTURE") from exc
    if (a.hexdigest() != receipt["sha256"] or b.hexdigest() != receipt.get("sha512")
        or size != receipt["size_bytes"] or mark["payload_sha256"] != a.hexdigest()):
        raise CaptureFailure("INTEGRITY_MISMATCH")
    return {"status": "READY", "scope": "capture_only_uncommitted", "capture_id": cid,
            "device_id": device_id, "sha256": a.hexdigest(), "size_bytes": size}


def capture_file(root: str | Path, source: str | Path, device_id: str, collector: str,
                 *, capture_id: str | None = None, source_type: str = "filesystem") -> dict[str, Any]:
    """Copy-only capture; no canonical Vault/Records writes or custody claims.

    Incomplete directories are retained for review; no automatic overwrite/cleanup.
    """
    root, cid = _arguments(root, device_id, capture_id)
    from .recovery import recovery_hold_present
    if recovery_hold_present(root):
        raise CaptureFailure('RECOVERY_HOLD')
    if not collector or not isinstance(collector, str) or not source_type or not isinstance(source_type,str):
        raise CaptureFailure("INVALID_ARGUMENT")
    source = Path(source).expanduser().absolute()
    dest = root / "00_Inbox" / "Drop" / device_id / cid
    if dest.exists() or dest.is_symlink():
        if not (dest / ".ready").is_file():
            raise CaptureFailure("INCOMPLETE_CAPTURE")
        existing = verify_capture(root, device_id, cid)
        digest, _, length = _hash_source(source)
        if digest != existing["sha256"] or length != existing["size_bytes"]:
            raise CaptureFailure("CAPTURE_CONFLICT")
        return {**existing, "already_exists": True}
    # Refuse unsafe source before creating directory.
    fd = _source_fd(source); os.close(fd)
    _ensure_parent(root, dest.parent)
    try: dest.mkdir(mode=0o700)
    except FileExistsError as exc: raise CaptureFailure("CAPTURE_CONFLICT") from exc
    try:
        sha256, sha512, size = _copy_source(source, dest / "payload")
        receipt = {"schema_version": 2, "capture_id": cid, "device_id": device_id,
            "captured_at": _utc(), "ingest_channel": "filesystem-drop",
            "source_type": source_type, "size_bytes": size, "sha256": sha256,
            "sha512": sha512, "status": "READY", "source_path": str(source),
            "original_filename": source.name, "collector": collector}
        blob = _encode(receipt)
        _write_exclusive(dest / "capture.receipt.json", blob)
        _fsync_dir(dest)
        _write_exclusive(dest / ".ready", _encode({"schema_version": 1, "capture_id": cid,
            "receipt_sha256": hashlib.sha256(blob).hexdigest(), "payload_sha256": sha256}))
        _fsync_dir(dest)
    except (OSError, CaptureFailure) as exc:
        # Leaves inspectable incomplete landing zone; source remains untouched.
        if isinstance(exc,CaptureFailure):raise
        raise CaptureFailure("INCOMPLETE_CAPTURE") from exc
    result = verify_capture(root, device_id, cid)
    return {**result, "already_exists": False}
