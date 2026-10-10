"""R13-G RED: synthetic field-drill verifies detached caller inputs before restore.

A separately supplied string is NOT proof of independent human custody.
Only generated synthetic R13-B captures may pass this offline tool.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))
from ci_cross_runner_drill import produce_fixture
from brain_core.recovery import recovery_status
from synthetic_offline_drill import DrillFailure, run_drill


def recovered_fixture(tmp_path):
    """Copy synthetic fixture to unrelated directories; remove origin."""
    origin = tmp_path / "origin"
    produce_fixture(origin)
    proof = json.loads((origin / "proof.json").read_bytes())
    remote = tmp_path / "retrieved synthetic snapshot"
    shutil.copytree(origin / "snapshot", remote)
    witness = tmp_path / "separate simulated witness"
    witness.mkdir()
    checkpoint = witness / "checkpoint.json"
    shutil.copy2(origin / "external-checkpoint.json", checkpoint)
    shutil.rmtree(origin)
    assert not origin.exists()
    roster = ["ci-device/" + cid for cid in proof["capture_ids"]]
    return remote, checkpoint, proof["manifest_sha256"], roster


def test_external_supplied_witness_preflight_and_fresh_quarantine_restore(tmp_path):
    snapshot, checkpoint, digest, roster = recovered_fixture(tmp_path)
    restored = tmp_path / "new quarantined root"
    r = run_drill(snapshot, restored, digest, checkpoint, roster)
    assert r["status"] == "SYNTHETIC_LOCAL_RESTORE_VERIFIED_OPERATOR_CUSTODY_UNVERIFIED"
    assert r["manifest_sha256"] == digest
    assert r["captures_verified"] == 3
    assert r["unique_objects"] == 2
    assert r["event_count"] == 6
    assert r["scope"] == "synthetic_manual_witness_inputs_not_independent_custody_proof"
    assert r["read_only_advisory"] is True
    assert isinstance(r["restore_execution_seconds"], float)
    assert r["restore_execution_seconds"] >= 0
    assert r["actual_rpo_rto"] == "NOT_MEASURED_OPERATOR_REQUIRED"
    assert recovery_status(restored)["status"] == "RECOVERED_READ_ONLY"
    with pytest.raises(DrillFailure, match="DESTINATION_CONFLICT"):
        run_drill(snapshot, restored, digest, checkpoint, roster)


@pytest.mark.parametrize("bad", ["0"*64, "G"*64, " ", "", "A"*64])
def test_wrong_or_invalid_pin_fails_without_creating_root(tmp_path, bad):
    snapshot, checkpoint, _digest, roster = recovered_fixture(tmp_path)
    target = tmp_path / "must remain absent"
    with pytest.raises(DrillFailure, match="(INVALID_EXPECTED_MANIFEST_SHA256|MANIFEST_DIGEST_MISMATCH)"):
        run_drill(snapshot, target, bad, checkpoint, roster)
    assert not target.exists()


def test_valid_but_rolled_back_snapshot_cannot_use_newer_witness(tmp_path):
    origin = tmp_path / "first"
    produce_fixture(origin)
    expected = recovered_fixture(tmp_path / "unrelated") if False else None
    other = tmp_path / "other"
    produce_fixture(other)
    proof = json.loads((other / "proof.json").read_bytes())
    roster = ["ci-device/" + x for x in proof["capture_ids"]]
    assert proof["manifest_sha256"] != json.loads((origin / "proof.json").read_bytes())["manifest_sha256"]
    target = tmp_path / "rollback target"
    with pytest.raises(DrillFailure, match="MANIFEST_DIGEST_MISMATCH"):
        run_drill(origin / "snapshot", target, proof["manifest_sha256"],
                  other / "external-checkpoint.json", roster)
    assert not target.exists()


@pytest.mark.parametrize("roster_change", ["missing", "extra", "duplicate", "malformed"])
def test_wrong_capture_roster_refused_during_preflight(tmp_path, roster_change):
    snapshot, checkpoint, digest, roster = recovered_fixture(tmp_path)
    if roster_change == "missing":
        roster = roster[:-1]
    elif roster_change == "extra":
        roster = roster + ["ci-device/CAP-00000000-0000-7000-8000-000000000000"]
    elif roster_change == "duplicate":
        roster = roster + [roster[0]]
    else:
        roster = ["ci-device/NOT_AN_ID"]
    target = tmp_path / "should-not-exist"
    with pytest.raises(DrillFailure, match="(CAPTURE_ROSTER_MISMATCH|INVALID_CAPTURE_ROSTER)"):
        run_drill(snapshot, target, digest, checkpoint, roster)
    assert not target.exists()


@pytest.mark.parametrize("bad", ["missing", "tampered"])
def test_detached_checkpoint_must_match_before_any_restore(tmp_path, bad):
    snapshot, checkpoint, digest, roster = recovered_fixture(tmp_path)
    if bad == "missing":
        checkpoint.unlink()
    else:
        checkpoint.write_bytes(b"{}")
    target = tmp_path / "should-not-exist"
    with pytest.raises(DrillFailure, match="CHECKPOINT_INVALID"):
        run_drill(snapshot, target, digest, checkpoint, roster)
    assert not target.exists()


def test_cli_untrusted_pin_failure_has_json_and_exit3(tmp_path):
    snapshot, checkpoint, _digest, roster = recovered_fixture(tmp_path)
    target = tmp_path / "not-there"
    argv = [sys.executable, str(PROFILE / "synthetic_offline_drill.py"),
            "--snapshot", str(snapshot), "--to-root", str(target),
            "--expect-manifest-sha256", "0"*64, "--checkpoint", str(checkpoint)]
    for cap in roster:
        argv.extend(("--expect-capture", cap))
    result = subprocess.run(argv, capture_output=True, text=True)
    assert result.returncode == 3, result.stderr
    assert json.loads(result.stdout)["error_code"] == "MANIFEST_DIGEST_MISMATCH"
    assert not target.exists()
