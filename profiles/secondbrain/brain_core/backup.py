"""R12 strictly local whole-closure snapshot/restore, not an offsite custody claim.

This intentionally supports only complete R7-R11 roots; no cloud APIs,
archive extraction, credential access, legal attestation or unsafe overwrite.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
from typing import Any

from .capture import CaptureFailure, _copy_source, _fsync_dir, _write_exclusive
from .custody import CustodyFailure, _canon, verify_chain
from .object import ObjectFailure, verify_object_link
from .verify import IntegrityFailure, _digest_fd, _safe_regular_file, _strict_json
from .writer import WriterFailure, _writer_lock

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
CAP = r"CAP-[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
DEVICE = r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}"
OID = r"obj-sha256-[0-9a-f]{64}"
SHA = r"[0-9a-f]{64}"
EXPECTED = (
    re.compile(rf"00_Inbox/Drop/{DEVICE}/{CAP}/(?:payload|capture\.receipt\.json|\.ready)\Z"),
    re.compile(rf"10_Evidence/Records/pending/(?:observations|ingest)/{DEVICE}/{CAP}\.json\Z"),
    re.compile(r"10_Evidence/Records/custody/events/[0-9]{20}\.json\Z"),
    re.compile(rf"10_Evidence/Records/commits/{DEVICE}/{CAP}\.json\Z"),
    re.compile(rf"10_Evidence/Records/objects/{OID}\.json\Z"),
    re.compile(rf"10_Evidence/Records/objects/links/{DEVICE}/{CAP}\.json\Z"),
    re.compile(rf"10_Evidence/Vault/objects/sha256/[0-9a-f]{{2}}/[0-9a-f]{{2}}/{SHA}/payload\Z"),
    re.compile(r"90_System/writer/authority\.json\Z"),
)
LINK = re.compile(rf"10_Evidence/Records/objects/links/({DEVICE})/({CAP})\.json\Z")
CAP_DIR = re.compile(rf"00_Inbox/Drop/({DEVICE})/({CAP})\Z")
OBJ = re.compile(rf"10_Evidence/Records/objects/({OID})\.json\Z")


class BackupFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _no_symlink_ancestors(path: Path, code: str) -> None:
    for component in (path, *path.parents):
        try:
            if component.is_symlink():
                raise BackupFailure(code)
        except OSError as exc:
            raise BackupFailure(code) from exc


def _dir(path: str | Path, missing: str = "UNSAFE_PATH") -> Path:
    p = Path(path).expanduser().absolute()
    _no_symlink_ancestors(p, missing)
    if not p.is_dir():
        raise BackupFailure(missing)
    return p


def _destination(source: Path, destination: str | Path) -> Path:
    p = Path(destination).expanduser().absolute()
    _no_symlink_ancestors(p, "UNSAFE_DESTINATION")
    if p == source or p.is_relative_to(source) or source.is_relative_to(p):
        raise BackupFailure("UNSAFE_DESTINATION")
    if not p.parent.is_dir():
        raise BackupFailure("UNSAFE_DESTINATION")
    return p


def _walk_files(root: Path, *, skip_writer_lock: bool = False) -> tuple[list[str], list[str]]:
    """Reject symlinks, special files, unreadable paths and unsafe stage remnants."""
    files: list[str] = []
    dirs: list[str] = []
    def visit(folder: Path):
        try:
            children = sorted(folder.iterdir(), key=lambda p: p.name)
            for child in children:
                rel = child.relative_to(root).as_posix()
                if skip_writer_lock and rel == "90_System/writer/.active":
                    continue
                mode = child.lstat().st_mode
                if stat.S_ISDIR(mode):
                    if child.name.startswith(".stage-") or child.name == "__pycache__":
                        raise BackupFailure("SNAPSHOT_NOT_CLOSED")
                    dirs.append(rel)
                    visit(child)
                elif stat.S_ISREG(mode):
                    if child.name.startswith(".stage-") or child.name == ".active":
                        raise BackupFailure("SNAPSHOT_NOT_CLOSED")
                    files.append(rel)
                else:
                    raise BackupFailure("UNSAFE_PATH")
        except BackupFailure:
            raise
        except OSError as exc:
            raise BackupFailure("UNSAFE_PATH") from exc
    visit(root)
    return files, dirs


def _expected_dirs(files: list[str]) -> set[str]:
    result = set()
    for path in files:
        parts = path.split("/")
        result.update("/".join(parts[:n]) for n in range(1, len(parts)))
    return result


def _closure(root: Path, *, skip_writer_lock: bool = False) -> dict[str, Any]:
    files, dirs = _walk_files(root, skip_writer_lock=skip_writer_lock)
    if (not files or set(dirs) != _expected_dirs(files) or
            any(not any(regex.fullmatch(p) for regex in EXPECTED) for p in files)):
        raise BackupFailure("SNAPSHOT_NOT_CLOSED")
    links = set()
    objects = set()
    for p in files:
        if m := LINK.fullmatch(p):
            links.add((m.group(1), m.group(2)))
        if m := OBJ.fullmatch(p):
            objects.add(m.group(1))
    captures = {m.groups() for d in dirs if (m := CAP_DIR.fullmatch(d))}
    if not links or links != captures:
        raise BackupFailure("SNAPSHOT_NOT_CLOSED")
    # A locally valid hash chain alone does not authenticate its history.
    try:
        chain = verify_chain(root)
        if chain["event_count"] != 2 * len(links):
            raise BackupFailure("SNAPSHOT_NOT_CLOSED")
        expected_objects = set()
        for device, cid in sorted(links):
            linked = verify_object_link(root, device, cid)
            expected_objects.add(linked["object_id"])
    except (ObjectFailure, CustodyFailure, IntegrityFailure, WriterFailure) as exc:
        raise BackupFailure("SOURCE_INVALID") from exc
    if expected_objects != objects:
        raise BackupFailure("SNAPSHOT_NOT_CLOSED")
    # Every metadata type and Vault payload must correspond to a linked capture.
    paths = set(files)
    for device, cid in links:
        for rel in (
            f"00_Inbox/Drop/{device}/{cid}/payload",
            f"00_Inbox/Drop/{device}/{cid}/capture.receipt.json",
            f"00_Inbox/Drop/{device}/{cid}/.ready",
            f"10_Evidence/Records/pending/observations/{device}/{cid}.json",
            f"10_Evidence/Records/pending/ingest/{device}/{cid}.json",
            f"10_Evidence/Records/commits/{device}/{cid}.json",
        ):
            if rel not in paths:
                raise BackupFailure("SNAPSHOT_NOT_CLOSED")
    expected_vault = {
        f"10_Evidence/Vault/objects/sha256/{oid[-64:-62]}/{oid[-62:-60]}/{oid[-64:]}/payload"
        for oid in objects
    }
    actual_vault = {p for p in files if p.startswith("10_Evidence/Vault/")}
    if expected_vault != actual_vault:
        raise BackupFailure("SNAPSHOT_NOT_CLOSED")
    actual_obs = {p for p in files if p.startswith("10_Evidence/Records/pending/observations/")}
    actual_ingest = {p for p in files if p.startswith("10_Evidence/Records/pending/ingest/")}
    actual_commits = {p for p in files if p.startswith("10_Evidence/Records/commits/")}
    for kind, actual in (
        ("observations", actual_obs), ("ingest", actual_ingest), ("commits", actual_commits)
    ):
        expected = {
            (f"10_Evidence/Records/pending/{kind}/{d}/{c}.json" if kind != "commits"
             else f"10_Evidence/Records/commits/{d}/{c}.json")
            for d, c in links
        }
        if expected != actual:
            raise BackupFailure("SNAPSHOT_NOT_CLOSED")
    if "90_System/writer/authority.json" not in paths:
        raise BackupFailure("SNAPSHOT_NOT_CLOSED")
    return {
        "files": files, "capture_count": len(links),
        "object_count": len(objects), "event_count": chain["event_count"],
        "tip_hash": chain["tip_hash"]
    }


def _copy_file(source: Path, dest: Path) -> tuple[str, int]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    sha256, _, count = _copy_source(source, dest)
    _fsync_dir(dest.parent)
    return sha256, count


def _manifest_body(data: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1, "kind": "LOCAL_SECOND_BRAIN_R12_SNAPSHOT",
        "capture_count": data["capture_count"], "object_count": data["object_count"],
        "event_count": data["event_count"], "tip_hash": data["tip_hash"],
        "files": entries
    }


def _snapshot_result(manifest: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "status": status, "manifest_sha256": manifest["manifest_sha256"],
        "file_count": len(manifest["files"]),
        "capture_count": manifest["capture_count"],
        "object_count": manifest["object_count"],
        "event_count": manifest["event_count"],
        "scope": "local_file_consistency_only_external_custody_unverified"
    }


def _manifest_from_files(root: Path, source: Path, data: dict[str, Any]) -> dict[str, Any]:
    entries = []
    for rel in data["files"]:
        target = root.joinpath(*rel.split("/"))
        try:
            h, size = _copy_file(source.joinpath(*rel.split("/")), target)
        except (CaptureFailure, OSError) as exc:
            raise BackupFailure("INCOMPLETE_SNAPSHOT") from exc
        entries.append({"path": rel, "sha256": h, "size_bytes": size})
    body = _manifest_body(data, entries)
    return {**body, "manifest_sha256": hashlib.sha256(_canon(body)).hexdigest()}


def _validate_manifest(snapshot: Path) -> dict[str, Any]:
    path = snapshot / "manifest.json"
    try:
        _safe_regular_file(snapshot, path, missing_code="INCOMPLETE_SNAPSHOT")
        manifest = _strict_json(path)
        if path.read_bytes() != _canon(manifest):
            raise BackupFailure("SNAPSHOT_TAMPERED")
        if set(manifest) != {
            "schema_version", "kind", "capture_count", "object_count",
            "event_count", "tip_hash", "files", "manifest_sha256"
        } or manifest["schema_version"] != 1 or manifest["kind"] != "LOCAL_SECOND_BRAIN_R12_SNAPSHOT":
            raise BackupFailure("SNAPSHOT_TAMPERED")
        counts = ("capture_count", "object_count", "event_count")
        if any(type(manifest[k]) is not int or manifest[k] <= 0 for k in counts):
            raise BackupFailure("SNAPSHOT_TAMPERED")
        if (type(manifest["tip_hash"]) is not str or not HEX64.fullmatch(manifest["tip_hash"]) or
            type(manifest["manifest_sha256"]) is not str or not HEX64.fullmatch(manifest["manifest_sha256"])):
            raise BackupFailure("SNAPSHOT_TAMPERED")
        files = manifest["files"]
        if not isinstance(files, list) or not files:
            raise BackupFailure("SNAPSHOT_TAMPERED")
        names = []
        for item in files:
            if not isinstance(item, dict) or set(item) != {"path", "sha256", "size_bytes"}:
                raise BackupFailure("SNAPSHOT_TAMPERED")
            p, h, sz = item["path"], item["sha256"], item["size_bytes"]
            if (not isinstance(p, str) or not p or not any(rx.fullmatch(p) for rx in EXPECTED) or
                type(h) is not str or not HEX64.fullmatch(h) or
                type(sz) is not int or sz < 0):
                raise BackupFailure("SNAPSHOT_TAMPERED")
            names.append(p)
        if names != sorted(set(names)):
            raise BackupFailure("SNAPSHOT_TAMPERED")
        body = {key: val for key, val in manifest.items() if key != "manifest_sha256"}
        if hashlib.sha256(_canon(body)).hexdigest() != manifest["manifest_sha256"]:
            raise BackupFailure("SNAPSHOT_TAMPERED")
        marker = snapshot / ".complete"
        _safe_regular_file(snapshot, marker, missing_code="INCOMPLETE_SNAPSHOT")
        if marker.read_bytes() != (manifest["manifest_sha256"] + "\n").encode("ascii"):
            raise BackupFailure("SNAPSHOT_TAMPERED")
        listed, dirs = _walk_files(snapshot)
        wanted = {"manifest.json", ".complete"} | {"data/" + p for p in names}
        if set(listed) != wanted or set(dirs) != _expected_dirs(sorted(wanted)):
            raise BackupFailure("SNAPSHOT_TAMPERED")
        return manifest
    except BackupFailure:
        raise
    except IntegrityFailure as exc:
        if exc.code == "INCOMPLETE_SNAPSHOT":
            raise BackupFailure("INCOMPLETE_SNAPSHOT") from exc
        raise BackupFailure("UNSAFE_PATH" if exc.code == "UNSAFE_PATH" else "SNAPSHOT_TAMPERED") from exc
    except (CustodyFailure, OSError, KeyError, TypeError, ValueError) as exc:
        raise BackupFailure("SNAPSHOT_TAMPERED") from exc


def _compare_data(root: Path, manifest: dict[str, Any]) -> None:
    try:
        actual_files, dirs = _walk_files(root)
        if (actual_files != [e["path"] for e in manifest["files"]] or
                set(dirs) != _expected_dirs(actual_files)):
            raise BackupFailure("SNAPSHOT_TAMPERED")
        for e in manifest["files"]:
            file = root.joinpath(*e["path"].split("/"))
            _safe_regular_file(root, file, missing_code="SNAPSHOT_TAMPERED")
            sha, _, size = _digest_fd(file)
            if (sha, size) != (e["sha256"], e["size_bytes"]):
                raise BackupFailure("SNAPSHOT_TAMPERED")
        closed = _closure(root)
        for field in ("capture_count", "object_count", "event_count", "tip_hash"):
            if closed[field] != manifest[field]:
                raise BackupFailure("SNAPSHOT_TAMPERED")
    except (IntegrityFailure, ObjectFailure, CustodyFailure, WriterFailure) as exc:
        raise BackupFailure("SNAPSHOT_TAMPERED") from exc


def create_backup(root: str | Path, destination: str | Path) -> dict[str, Any]:
    source = _dir(root)
    target = _destination(source, destination)
    if target.exists() or target.is_symlink():
        raise BackupFailure("DESTINATION_CONFLICT")
    try:
        with _writer_lock(source):
            data = _closure(source, skip_writer_lock=True)
            try:
                target.mkdir(mode=0o700)  # exclusive directory creation; never replace
            except FileExistsError as exc:
                raise BackupFailure("DESTINATION_CONFLICT") from exc
            except OSError as exc:
                raise BackupFailure("UNSAFE_DESTINATION") from exc
            manifest = _manifest_from_files(target / "data", source, data)
            try:
                _write_exclusive(target / "manifest.json", _canon(manifest))
                _fsync_dir(target)
                _compare_data(_dir(target / "data"), manifest)
                _write_exclusive(target / ".complete", (manifest["manifest_sha256"] + "\n").encode("ascii"))
                _fsync_dir(target)
            except (OSError, CustodyFailure) as exc:
                raise BackupFailure("INCOMPLETE_SNAPSHOT") from exc
            return _snapshot_result(manifest, "LOCAL_SNAPSHOT_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED")
    except WriterFailure as exc:
        raise BackupFailure("SOURCE_BUSY" if exc.code == "WRITER_BUSY" else "SOURCE_INVALID") from exc


def verify_backup(snapshot: str | Path) -> dict[str, Any]:
    folder = _dir(snapshot)
    _no_symlink_ancestors(folder, "UNSAFE_PATH")
    manifest = _validate_manifest(folder)
    # Do not read a user's original root; verify only the supplied copy.
    data = _dir(folder / "data")
    _compare_data(data, manifest)
    return _snapshot_result(manifest, "LOCAL_SNAPSHOT_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED")


def restore_backup(snapshot: str | Path, destination: str | Path) -> dict[str, Any]:
    folder = _dir(snapshot)
    verified = verify_backup(folder)
    manifest = _validate_manifest(folder)
    target = _destination(folder, destination)
    if target.exists() or target.is_symlink():
        try:
            if not target.is_dir() or target.is_symlink():
                raise BackupFailure("DESTINATION_CONFLICT")
            _compare_data(_dir(target), manifest)
            return {**verified, "status": "RESTORE_ALREADY_VALID_LOCAL"}
        except BackupFailure as exc:
            raise BackupFailure("DESTINATION_CONFLICT") from exc
    try:
        target.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise BackupFailure("DESTINATION_CONFLICT") from exc
    except OSError as exc:
        raise BackupFailure("UNSAFE_DESTINATION") from exc
    try:
        for entry in manifest["files"]:
            p = entry["path"]
            sha, size = _copy_file(folder / "data" / p, target / p)
            if (sha, size) != (entry["sha256"], entry["size_bytes"]):
                raise BackupFailure("INCOMPLETE_RESTORE")
        _compare_data(target, manifest)
        _fsync_dir(target)
    except (BackupFailure, CaptureFailure, OSError) as exc:
        raise BackupFailure("INCOMPLETE_RESTORE") from exc
    return {**verified, "status": "LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED"}
