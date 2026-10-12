"""R13-G operator-invoked *synthetic-only* offline restore preflight.

Operator supplies R12 manifest fingerprint, checkpoint and exact capture
roster OUT OF BAND. We verify matching bytes, not how independently they
were retained. This script cannot certify offsite custody, actual loss,
trusted timestamps, full RPO/RTO or cross-device Writer fencing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

from brain_core.backup import BackupFailure, verify_backup, restore_backup, CAP, DEVICE
from brain_core.capture import CaptureFailure, verify_capture
from brain_core.checkpoint import CheckpointFailure, verify_checkpoint
from brain_core.custody import CustodyFailure, verify_chain, verify_commit
from brain_core.object import ObjectFailure, verify_object_link
from brain_core.recovery import RecoveryFailure, recovery_status
from brain_core.verify import IntegrityFailure, _strict_json, _safe_regular_file
from brain_core.writer import WriterFailure, verify_publication

_CAPTURE_ROSTER = re.compile(rf"{DEVICE}/{CAP}\Z")


class DrillFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def run_drill(snapshot: str | Path, destination: str | Path,
              expected_manifest_sha256: str, checkpoint: str | Path,
              expected_captures: list[str]) -> dict[str, Any]:
    """Check operator inputs BEFORE creating a fresh read-only restore root.

    Source must be an R13-B synthetic snapshot; no live evidence accepted.
    The provided witness values are NOT automatically authenticated.
    """
    if (not isinstance(expected_captures, list) or
            not expected_captures or
            any(type(item) is not str or
                not _CAPTURE_ROSTER.fullmatch(item) for item in expected_captures) or
            len(expected_captures) != len(set(expected_captures))):
        raise DrillFailure("INVALID_CAPTURE_ROSTER")
    supplied = set(expected_captures)
    source = Path(snapshot).expanduser().absolute()
    target = Path(destination).expanduser().absolute()
    checkpoint_path = Path(checkpoint).expanduser().absolute()
    if target.exists() or target.is_symlink():
        raise DrillFailure("DESTINATION_CONFLICT")
    if checkpoint_path == source or checkpoint_path.is_relative_to(source):
        raise DrillFailure("CHECKPOINT_INVALID")
    try:
        verified = verify_backup(source, expected_manifest_sha256=expected_manifest_sha256)
    except BackupFailure as exc:
        raise DrillFailure(exc.code) from exc

    # All paths and the canonical body hash have just been checked by R12.
    # A second read never establishes a trusted writer/source by itself.
    try:
        manifest = _strict_json(source / "manifest.json")
        actual = set()
        for entry in manifest["files"]:
            parts = entry["path"].split("/")
            if (len(parts) == 5 and parts[:2] == ["00_Inbox", "Drop"] and
                    parts[4] == "capture.receipt.json"):
                actual.add(parts[2] + "/" + parts[3])
        if supplied != actual:
            raise DrillFailure("CAPTURE_ROSTER_MISMATCH")
        for value in sorted(actual):
            device, cap = value.split("/", 1)
            if device != "ci-device":
                raise DrillFailure("NON_SYNTHETIC_CAPTURE")
            file = source / "data" / "00_Inbox" / "Drop" / device / cap / "capture.receipt.json"
            _safe_regular_file(source, file, missing_code="INCOMPLETE_CAPTURE")
            receipt = _strict_json(file)
            if receipt.get("collector") != "ci-synthetic":
                raise DrillFailure("NON_SYNTHETIC_CAPTURE")
        witness = verify_checkpoint(source / "data", checkpoint_path)
        if witness["status"] != "CHECKPOINT_EXACT_MATCH_EXTERNAL_CUSTODY_UNVERIFIED":
            raise DrillFailure("CHECKPOINT_INVALID")
    except DrillFailure:
        raise
    except (CheckpointFailure, IntegrityFailure, OSError, ValueError, KeyError, TypeError) as exc:
        raise DrillFailure("CHECKPOINT_INVALID") from exc

    start = time.monotonic()
    try:
        result = restore_backup(source, target, expected_manifest_sha256=expected_manifest_sha256)
        if (result["status"] != "LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED" or
                recovery_status(target)["status"] != "RECOVERED_READ_ONLY"):
            raise DrillFailure("RESTORE_INVALID")
        chain = verify_chain(target)
        if chain["event_count"] != manifest["event_count"]:
            raise DrillFailure("RESTORE_INVALID")
        if (verify_checkpoint(target, checkpoint_path)["status"] !=
                "CHECKPOINT_EXACT_MATCH_EXTERNAL_CUSTODY_UNVERIFIED"):
            raise DrillFailure("RESTORE_INVALID")
        objects = set()
        for value in sorted(actual):
            device, cap_id = value.split("/", 1)
            cap = verify_capture(target, device, cap_id)
            pub = verify_publication(target, device, cap_id)
            commit = verify_commit(target, device, cap_id)
            link = verify_object_link(target, device, cap_id)
            if (cap["sha256"] != pub["sha256"] or
                    commit["capture_id"] != cap_id or
                    link["sha256"] != cap["sha256"]):
                raise DrillFailure("RESTORE_INVALID")
            objects.add(link["object_id"])
        if len(objects) != manifest["object_count"]:
            raise DrillFailure("RESTORE_INVALID")
        elapsed = time.monotonic() - start
    except DrillFailure:
        raise
    except (BackupFailure, CaptureFailure, CheckpointFailure, CustodyFailure,
            ObjectFailure, RecoveryFailure, IntegrityFailure, WriterFailure,
            OSError, ValueError, KeyError, TypeError) as exc:
        raise DrillFailure("RESTORE_INVALID") from exc
    return {
        "status": "SYNTHETIC_LOCAL_RESTORE_VERIFIED_OPERATOR_CUSTODY_UNVERIFIED",
        "manifest_sha256": verified["manifest_sha256"],
        "captures_verified": len(actual),
        "unique_objects": len(objects),
        "event_count": chain["event_count"],
        "read_only_advisory": True,
        "restore_execution_seconds": round(elapsed, 6),
        "actual_rpo_rto": "NOT_MEASURED_OPERATOR_REQUIRED",
        "scope": "synthetic_manual_witness_inputs_not_independent_custody_proof",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Synthetic-only R13 independent-operator rehearsal; NOT offsite proof")
    p.add_argument("--snapshot", required=True)
    p.add_argument("--to-root", required=True)
    p.add_argument("--expect-manifest-sha256", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--expect-capture", required=True, action="append")
    args = p.parse_args(argv)
    try:
        output = run_drill(args.snapshot, args.to_root, args.expect_manifest_sha256,
                           args.checkpoint, args.expect_capture)
    except DrillFailure as exc:
        print(json.dumps({"status": "FAIL", "error_code": exc.code}, sort_keys=True))
        return 3
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
