"""R11 local object record and capture-specific linkage; unsealed, unanchored.

The shared SHA-256 EvidenceObject describes BYTES. A separate per-capture link
preserves each Observation + Acquisition/Custody pair. Local JSON and clock
do not constitute forensic sealing, provenance authentication or trusted time.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

from .capture import CaptureFailure, _arguments, _fsync_dir
from .custody import CustodyFailure, _canon, _scan, verify_commit
from .verify import IntegrityFailure, _digest_fd, _safe_regular_file, _strict_json, verify_object
from .writer import (
    WriterFailure, _authority, _publish_bytes_once, _root, _vault_path,
    _writer_lock, verify_publication,
)


class ObjectFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _checked(root: str | Path, device: str, capture_id: str) -> Path:
    try:
        path, _ = _arguments(root, device, capture_id)
        return path
    except CaptureFailure as exc:
        raise ObjectFailure("INVALID_ARGUMENT" if exc.code == "INVALID_ARGUMENT" else exc.code) from exc


def _object_path(root: Path, oid: str) -> Path:
    return root / "10_Evidence" / "Records" / "objects" / (oid + ".json")


def _link_path(root: Path, device: str, capture_id: str) -> Path:
    return root / "10_Evidence" / "Records" / "objects" / "links" / device / (capture_id + ".json")


def _read_link(root: Path, path: Path) -> dict[str, Any]:
    try:
        _safe_regular_file(root, path, missing_code="INCOMPLETE_OBJECT_LINK")
        document = _strict_json(path)
        if path.read_bytes() != _canon(document):
            raise ObjectFailure("LINK_TAMPERED")
        return document
    except IntegrityFailure as exc:
        if exc.code == "UNSAFE_PATH":
            raise ObjectFailure("UNSAFE_PATH") from exc
        if exc.code == "INCOMPLETE_OBJECT_LINK":
            raise ObjectFailure("INCOMPLETE_OBJECT_LINK") from exc
        raise ObjectFailure("LINK_TAMPERED") from exc
    except (OSError, CustodyFailure) as exc:
        raise ObjectFailure("LINK_TAMPERED") from exc


def _dependencies(root: Path, device: str, cid: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Full, independent re-verification; no undocumented inferred provenance."""
    try:
        pub = verify_publication(root, device, cid)  # also verifies Capture and Vault
    except WriterFailure as exc:
        raise ObjectFailure("PUBLICATION_INVALID" if exc.code != "UNSAFE_PATH" else "UNSAFE_PATH") from exc
    try:
        custody = verify_commit(root, device, cid)  # checks full local chain and receipt
        chain = _scan(root)
    except CustodyFailure as exc:
        raise ObjectFailure("CUSTODY_INVALID" if exc.code != "UNSAFE_PATH" else "UNSAFE_PATH") from exc
    hits = [e for e in chain if (e["device_id"], e["capture_id"]) == (device, cid)]
    if (len(hits) != 2 or hits[1]["sequence"] != hits[0]["sequence"] + 1 or
            hits[0]["event_type"] != "ACQUISITION" or hits[1]["event_type"] != "CUSTODY"):
        raise ObjectFailure("CUSTODY_INVALID")
    acq, event = hits
    for part in (acq, event):
        for field in ("object_id", "sha256", "writer_id", "writer_epoch", "observation_sha256"):
            if part[field] != pub[field]:
                raise ObjectFailure("LINK_TAMPERED")
    if (custody["custody_hash"] != event["event_hash"] or
            custody["sequence"] != event["sequence"] or
            custody["observation_sha256"] != pub["observation_sha256"] or
            custody["writer_epoch"] != pub["writer_epoch"]):
        raise ObjectFailure("LINK_TAMPERED")
    # Commit receipt bytes were independently checked by verify_commit.
    commit_body = {key: val for key, val in custody.items() if key != "scope"}
    link = {
        "schema_version": 1, "kind": "LOCAL_EVIDENCE_OBJECT_LINK",
        "device_id": device, "capture_id": cid,
        "object_id": pub["object_id"], "sha256": pub["sha256"],
        "observation_id": pub["observation_id"],
        "observation_sha256": pub["observation_sha256"],
        "publication_receipt_sha256": pub["receipt_sha256"],
        "acquisition_sequence": acq["sequence"],
        "acquisition_hash": acq["event_hash"],
        "custody_sequence": event["sequence"],
        "custody_hash": event["event_hash"],
        "commit_receipt_sha256": hashlib.sha256(_canon(commit_body)).hexdigest(),
        "writer_id": pub["writer_id"], "writer_epoch": pub["writer_epoch"],
    }
    return pub, custody, link


def _record(root: Path, pub: dict[str, Any]) -> dict[str, Any]:
    vault = _vault_path(root, pub["sha256"])
    try:
        _safe_regular_file(root, vault, missing_code="NOT_HYDRATED")
        digest, sha512, count = _digest_fd(vault)
    except IntegrityFailure as exc:
        raise ObjectFailure(exc.code) from exc
    if digest != pub["sha256"] or count != pub["size_bytes"]:
        raise ObjectFailure("INTEGRITY_MISMATCH")
    return {
        "schema_version": 2, "object_id": pub["object_id"],
        "sha256": digest, "sha512": sha512, "size_bytes": count,
        "media_type": "application/octet-stream",
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "record_scope": "LOCAL_UNSEALED_UNANCHORED",
        "vault_relpath": pub["vault_relpath"], "source_fidelity": "unknown",
    }


def _validate_record(root: Path, path: Path, expected: dict[str, Any]) -> None:
    try:
        verified = verify_object(root, expected["object_id"])
        _safe_regular_file(root, path, missing_code="INCOMPLETE_COMMIT")
        existing = _strict_json(path)
        canonical = path.read_bytes() == _canon(existing)
        if (not canonical or existing.get("record_scope") != "LOCAL_UNSEALED_UNANCHORED" or
                "recorded_at" not in existing or "sealed_at" in existing or
                any(existing.get(k) != val for k, val in expected.items() if k != "recorded_at") or
                verified["sha256"] != expected["sha256"]):
            raise ObjectFailure("OBJECT_RECORD_CONFLICT")
    except IntegrityFailure as exc:
        if exc.code == "UNSAFE_PATH":
            raise ObjectFailure("UNSAFE_PATH") from exc
        if exc.code in ("INTEGRITY_MISMATCH", "NOT_HYDRATED"):
            raise ObjectFailure(exc.code) from exc
        raise ObjectFailure("OBJECT_RECORD_CONFLICT") from exc
    except CustodyFailure as exc:
        raise ObjectFailure(exc.code) from exc
    except OSError as exc:
        raise ObjectFailure("OBJECT_RECORD_CONFLICT") from exc


def _publish_record(root: Path, path: Path, data: bytes) -> None:
    """Reuse R8 immutable create-if-absent helper and synchronize the directory."""
    _publish_bytes_once(root, path, data)
    _fsync_dir(path.parent)


def verify_object_link(root: str | Path, device_id: str, capture_id: str) -> dict[str, Any]:
    """Read-only check of local byte record, Capture, Observation and two custody events."""
    checked = _checked(root, device_id, capture_id)
    _, _, expected = _dependencies(checked, device_id, capture_id)
    try:
        obj = verify_object(checked, expected["object_id"])
        record = _strict_json(_object_path(checked, expected["object_id"]))
        if record.get("record_scope") != "LOCAL_UNSEALED_UNANCHORED" or "sealed_at" in record:
            raise ObjectFailure("OBJECT_RECORD_CONFLICT")
        record_bytes = _object_path(checked, expected["object_id"]).read_bytes()
        if record_bytes != _canon(record):
            raise ObjectFailure("OBJECT_RECORD_CONFLICT")
        expected["object_record_sha256"] = hashlib.sha256(record_bytes).hexdigest()
    except IntegrityFailure as exc:
        code = "INCOMPLETE_OBJECT_LINK" if exc.code == "INCOMPLETE_COMMIT" else exc.code
        raise ObjectFailure(code) from exc
    except CustodyFailure as exc:
        raise ObjectFailure(exc.code) from exc
    actual = _read_link(checked, _link_path(checked, device_id, capture_id))
    if actual.get("object_record_sha256") != expected["object_record_sha256"]:
        raise ObjectFailure("OBJECT_RECORD_CONFLICT")
    if actual != expected:
        raise ObjectFailure("LINK_TAMPERED")
    return {
        "status": "LOCAL_OBJECT_LINK_VERIFIED_UNANCHORED",
        "object_id": expected["object_id"], "device_id": device_id,
        "capture_id": capture_id, "sha256": obj["sha256"],
        "custody_hash": expected["custody_hash"],
        "scope": "local_only_no_external_attestation_or_legal_seal",
    }


def create_object(root: str | Path, device_id: str, capture_id: str,
                  writer_id: str, writer_epoch: str) -> dict[str, Any]:
    """Write immutable shared metadata first, then the capture-specific lineage LAST.

    Retrying is safe: matching records are reverified; conflicting ones never
    overwritten. Interrupted writes may leave an unlinked object metadata record.
    """
    checked = _checked(root, device_id, capture_id)
    if not writer_id or not writer_epoch:
        raise ObjectFailure("WRITER_NOT_AUTHORIZED")
    try:
        writer = _authority(checked)
    except WriterFailure as exc:
        raise ObjectFailure("WRITER_NOT_AUTHORIZED") from exc
    if (writer_id, writer_epoch) != (writer["writer_id"], writer["writer_epoch"]):
        raise ObjectFailure("WRITER_NOT_AUTHORIZED")
    try:
        with _writer_lock(checked):
            if _authority(checked) != writer:
                raise ObjectFailure("WRITER_NOT_AUTHORIZED")
            pub, _, link = _dependencies(checked, device_id, capture_id)
            if (pub["writer_id"], pub["writer_epoch"]) != (writer_id, writer_epoch):
                raise ObjectFailure("WRITER_NOT_AUTHORIZED")
            expected = _record(checked, pub)
            obj_path = _object_path(checked, pub["object_id"])
            if obj_path.exists() or obj_path.is_symlink():
                _validate_record(checked, obj_path, expected)
                _fsync_dir(obj_path.parent)
            else:
                _publish_record(checked, obj_path, _canon(expected))
                _validate_record(checked, obj_path, expected)
            link["object_record_sha256"] = hashlib.sha256(obj_path.read_bytes()).hexdigest()
            link_path = _link_path(checked, device_id, capture_id)
            if link_path.exists() or link_path.is_symlink():
                if _read_link(checked, link_path) != link:
                    raise ObjectFailure("LINK_TAMPERED")
                _fsync_dir(link_path.parent)
            else:
                _publish_record(checked, link_path, _canon(link))
            return verify_object_link(checked, device_id, capture_id)
    except ObjectFailure:
        raise
    except WriterFailure as exc:
        raise ObjectFailure(exc.code) from exc
    except (OSError, CustodyFailure) as exc:
        raise ObjectFailure("INCOMPLETE_OBJECT") from exc
