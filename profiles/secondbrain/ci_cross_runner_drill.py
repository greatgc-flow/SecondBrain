"""R13-B disposable synthetic transfer between distinct CI runners.

There is intentionally no real-evidence, cloud, signing, zip packaging or
independent-custody logic here. Used ONLY by the CI workflow and its tests.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from brain_core.capture import CaptureFailure, capture_file, verify_capture
from brain_core.writer import WriterFailure, configure_writer, publish_capture, verify_publication
from brain_core.custody import CustodyFailure, _canon, commit_capture, verify_commit, verify_chain
from brain_core.object import ObjectFailure, create_object, verify_object_link
from brain_core.backup import BackupFailure, create_backup, verify_backup, restore_backup
from brain_core.checkpoint import CheckpointFailure, create_checkpoint, verify_checkpoint
from brain_core.recovery import RecoveryFailure, recovery_status
from brain_core.verify import IntegrityFailure, _strict_json, _safe_regular_file


class DrillFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _transfer_files(folder: Path) -> tuple[Path, Path, Path]:
    folder = folder.expanduser().absolute()
    if not folder.is_dir() or folder.is_symlink():
        raise DrillFailure("UNSAFE_TRANSFER")
    for component in (folder, *folder.parents):
        if component.is_symlink() or (hasattr(component, "is_junction") and component.is_junction()):
            raise DrillFailure("UNSAFE_TRANSFER")
    try:
        items = sorted(folder.iterdir(), key=lambda x: x.name)
        if [p.name for p in items] != ["external-checkpoint.json", "proof.json", "snapshot"]:
            raise DrillFailure("UNSAFE_TRANSFER")
        for name in ("external-checkpoint.json", "proof.json"):
            _safe_regular_file(folder, folder / name, missing_code="UNSAFE_TRANSFER")
        if not (folder / "snapshot").is_dir() or (folder / "snapshot").is_symlink():
            raise DrillFailure("UNSAFE_TRANSFER")
    except (OSError, IntegrityFailure) as exc:
        raise DrillFailure("UNSAFE_TRANSFER") from exc
    return folder / "snapshot", folder / "proof.json", folder / "external-checkpoint.json"


def produce_fixture(transfer: str | Path) -> dict:
    """Create synthetic evidence in private temporary root, publish only a copy."""
    output = Path(transfer).expanduser().absolute()
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise DrillFailure("TRANSFER_CONFLICT")
    with tempfile.TemporaryDirectory(prefix="secondbrain-r13b-producer-") as name:
        work = Path(name)
        root = work / "한글 출처 root"
        root.mkdir()
        writer = configure_writer(root, "ci-producer-single-writer")
        ids, object_ids = [], []
        for i, payload in enumerate((b"shared synthetic\0", b"shared synthetic\0",
                                     b"different\x00synthetic\xff")):
            source = work / ("한글 공백 %s.txt" % i)
            source.write_bytes(payload)
            capture = capture_file(root, source, "ci-device", "ci-synthetic")
            cid = capture["capture_id"]
            publish_capture(root, "ci-device", cid, "ci-producer-single-writer", writer["writer_epoch"])
            commit_capture(root, "ci-device", cid, "ci-producer-single-writer", writer["writer_epoch"])
            link = create_object(root, "ci-device", cid, "ci-producer-single-writer", writer["writer_epoch"])
            ids.append(cid)
            object_ids.append(link["object_id"])
        checkpoint = _canon(create_checkpoint(root))
        # No ZIP, source tree, credentials or external account data in artifact.
        output.mkdir(mode=0o700)
        (output / "external-checkpoint.json").write_bytes(checkpoint)
        snapshot = create_backup(root, output / "snapshot")
        proof = {
            "schema_version": 1, "kind": "R13B_CI_SYNTHETIC_TRANSFER",
            "capture_ids": ids, "device_id": "ci-device",
            "object_ids": object_ids,
            "checkpoint_sha256": hashlib.sha256(checkpoint).hexdigest(),
            "manifest_sha256": snapshot["manifest_sha256"],
            "expected_capture_count": 3, "expected_object_count": 2,
            "expected_event_count": 6,
            "scope": "cross_runner_synthetic_only_not_offsite_independence",
        }
        (output / "proof.json").write_bytes(_canon(proof))
        shutil.rmtree(root)
        # Root and originals were never copied to transfer directory.
        return {
            "status": "CI_FIXTURE_EXPORTED_SYNTHETIC_ONLY",
            "manifest_sha256": snapshot["manifest_sha256"],
            "capture_count": len(ids),
            "unique_objects": len(set(object_ids)),
        }


def consume_fixture(transfer: str | Path) -> dict:
    """Retrieve portable snapshot without access to the producer's source root."""
    folder = Path(transfer).expanduser().absolute()
    snapshot, proof_path, checkpoint_path = _transfer_files(folder)
    try:
        proof = _strict_json(proof_path)
        if proof_path.read_bytes() != _canon(proof):
            raise DrillFailure("TRANSFER_TAMPERED")
        if set(proof) != {
            "schema_version", "kind", "capture_ids", "device_id", "object_ids",
            "checkpoint_sha256", "manifest_sha256", "expected_capture_count",
            "expected_object_count", "expected_event_count", "scope"
        } or proof["schema_version"] != 1 or proof["kind"] != "R13B_CI_SYNTHETIC_TRANSFER":
            raise DrillFailure("TRANSFER_TAMPERED")
        if (proof["scope"] != "cross_runner_synthetic_only_not_offsite_independence" or
            proof["device_id"] != "ci-device" or
            proof["expected_capture_count"] != 3 or
            proof["expected_object_count"] != 2 or
            proof["expected_event_count"] != 6 or
            not isinstance(proof["capture_ids"], list) or
            not isinstance(proof["object_ids"], list) or
            len(proof["capture_ids"]) != 3 or len(proof["object_ids"]) != 3 or
            len(set(proof["capture_ids"])) != 3 or
            len(set(proof["object_ids"])) != 2):
            raise DrillFailure("TRANSFER_TAMPERED")
        if (hashlib.sha256(checkpoint_path.read_bytes()).hexdigest() != proof["checkpoint_sha256"]):
            raise DrillFailure("TRANSFER_TAMPERED")
        checked = verify_backup(snapshot, expected_manifest_sha256=proof['manifest_sha256'])
        if (checked["manifest_sha256"] != proof["manifest_sha256"] or
            checked["capture_count"] != 3 or checked["object_count"] != 2 or
            checked["event_count"] != 6):
            raise DrillFailure("TRANSFER_TAMPERED")
        with tempfile.TemporaryDirectory(prefix="secondbrain-r13b-consumer-") as name:
            restore = Path(name) / "복구 한글 root"
            restored = restore_backup(snapshot, restore, expected_manifest_sha256=proof['manifest_sha256'])
            if (restored["status"] != "LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED" or
                recovery_status(restore)["status"] != "RECOVERED_READ_ONLY"):
                raise DrillFailure("RESTORE_INCOMPLETE")
            chain = verify_chain(restore)
            if chain["event_count"] != 6:
                raise DrillFailure("RESTORE_INCOMPLETE")
            if verify_checkpoint(restore, checkpoint_path)["status"] != "CHECKPOINT_EXACT_MATCH_EXTERNAL_CUSTODY_UNVERIFIED":
                raise DrillFailure("RESTORE_INCOMPLETE")
            actual_oids = []
            for cid, oid in zip(proof["capture_ids"], proof["object_ids"]):
                cap = verify_capture(restore, "ci-device", cid)
                pub = verify_publication(restore, "ci-device", cid)
                commit = verify_commit(restore, "ci-device", cid)
                linked = verify_object_link(restore, "ci-device", cid)
                if (cap["sha256"] != pub["sha256"] or
                    commit["capture_id"] != cid or
                    linked["object_id"] != oid):
                    raise DrillFailure("RESTORE_INCOMPLETE")
                actual_oids.append(oid)
            if len(set(actual_oids)) != 2:
                raise DrillFailure("RESTORE_INCOMPLETE")
            src = Path(name) / "illegal new write.txt"
            src.write_bytes(b"must deny")
            try:
                capture_file(restore, src, "ci-device", "synthetic")
            except CaptureFailure as exc:
                if exc.code != "RECOVERY_HOLD":
                    raise DrillFailure("RESTORE_INCOMPLETE") from exc
            else:
                raise DrillFailure("RESTORE_INCOMPLETE")
            if restore_backup(snapshot, restore, expected_manifest_sha256=proof['manifest_sha256'])["status"] != "RESTORE_ALREADY_VALID_LOCAL":
                raise DrillFailure("RESTORE_INCOMPLETE")
        return {
            "status": "CI_CROSS_RUNNER_RESTORE_VERIFIED_NO_INDEPENDENT_CUSTODY",
            "manifest_sha256": checked["manifest_sha256"],
            "captures_verified": 3, "unique_objects": 2,
            "read_only": True, "source_available": False,
            "scope": "separate_ci_job_no_long_term_offsite_or_trusted_custody",
        }
    except DrillFailure:
        raise
    except (IntegrityFailure, CaptureFailure, WriterFailure, CustodyFailure,
            ObjectFailure, BackupFailure, CheckpointFailure, RecoveryFailure,
            OSError, ValueError, KeyError, TypeError) as exc:
        raise DrillFailure("TRANSFER_TAMPERED_OR_RESTORE_INVALID") from exc


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("produce", "consume"):
        print("usage: ci_cross_runner_drill.py {produce|consume} DIR", file=sys.stderr)
        raise SystemExit(2)
    try:
        result = (produce_fixture(sys.argv[2]) if sys.argv[1] == "produce"
                  else consume_fixture(sys.argv[2]))
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    except DrillFailure as exc:
        print("FAIL " + exc.code, file=sys.stderr)
        raise SystemExit(3)
