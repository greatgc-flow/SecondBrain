"""R13-C RED: optional detached expected-manifest fingerprint must fail closed.

The expected 64-digit digest is *operator-supplied*. A value stored inside
the same backup is NOT an authenticated independent witness.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))

from ci_cross_runner_drill import produce_fixture
from brain_core.backup import BackupFailure, restore_backup, verify_backup


def snapshot(tmp_path):
    parent = tmp_path / "synthetic transfer"
    result = produce_fixture(parent)
    return parent / "snapshot", result["manifest_sha256"]


def test_matching_detached_fingerprint_verifies_then_restores(tmp_path):
    folder, fingerprint = snapshot(tmp_path)
    verified = verify_backup(folder, expected_manifest_sha256=fingerprint)
    assert verified["manifest_sha256"] == fingerprint
    target = tmp_path / "new restore root"
    restored = restore_backup(folder, target, expected_manifest_sha256=fingerprint)
    assert restored["status"] == "LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED"
    assert (target / "90_System/writer/recovery-hold.json").is_file()
    assert restore_backup(folder, target, expected_manifest_sha256=fingerprint)["status"] == "RESTORE_ALREADY_VALID_LOCAL"


def test_wrong_fingerprint_aborts_before_new_destination(tmp_path):
    folder, fingerprint = snapshot(tmp_path)
    wrong = "0" * 64 if fingerprint != "0"*64 else "1"*64
    with pytest.raises(BackupFailure, match="MANIFEST_DIGEST_MISMATCH"):
        verify_backup(folder, expected_manifest_sha256=wrong)
    target = tmp_path / "never created"
    with pytest.raises(BackupFailure, match="MANIFEST_DIGEST_MISMATCH"):
        restore_backup(folder, target, expected_manifest_sha256=wrong)
    assert not target.exists()


def test_other_locally_valid_snapshot_cannot_substitute_for_detached_pin(tmp_path):
    first, fingerprint = snapshot(tmp_path / "first")
    second, newer = snapshot(tmp_path / "second")
    assert fingerprint != newer
    assert verify_backup(second)["manifest_sha256"] == newer
    with pytest.raises(BackupFailure, match="MANIFEST_DIGEST_MISMATCH"):
        restore_backup(second, tmp_path / "disallowed", expected_manifest_sha256=fingerprint)
    assert not (tmp_path / "disallowed").exists()


@pytest.mark.parametrize("bad", ["", "abc", "F"*64, "0"*63, "0"*65,
                                  "../" + "a"*61, 0, False, 123, b"0"*64])
def test_invalid_expected_fingerprint_rejected_without_restore(tmp_path, bad):
    folder, fingerprint = snapshot(tmp_path)
    with pytest.raises(BackupFailure, match="INVALID_EXPECTED_MANIFEST_SHA256"):
        verify_backup(folder, expected_manifest_sha256=bad)
    dest = tmp_path / "no-target"
    with pytest.raises(BackupFailure, match="INVALID_EXPECTED_MANIFEST_SHA256"):
        restore_backup(folder, dest, expected_manifest_sha256=bad)
    assert not dest.exists()


def test_cli_match_and_mismatch_verify_restore_json_exit_codes(tmp_path):
    folder, fingerprint = snapshot(tmp_path)
    cli = [sys.executable, str(PROFILE / "brain.py"), "backup"]
    def run(args):
        return subprocess.run(cli + args, capture_output=True, text=True)
    good = run(["verify", str(folder), "--expect-manifest-sha256", fingerprint, "--json"])
    assert good.returncode == 0, good.stderr
    assert json.loads(good.stdout)["manifest_sha256"] == fingerprint
    wrong = "a"*64 if fingerprint != "a"*64 else "b"*64
    failed = run(["restore", str(folder), "--to-root", str(tmp_path / "not-created"),
                  "--expect-manifest-sha256", wrong, "--json"])
    assert failed.returncode == 3
    assert json.loads(failed.stdout)["error_code"] == "MANIFEST_DIGEST_MISMATCH"
    assert not (tmp_path / "not-created").exists()
    restored = run(["restore", str(folder), "--to-root", str(tmp_path / "restored"),
                    "--expect-manifest-sha256", fingerprint, "--json"])
    assert restored.returncode == 0, restored.stderr
    assert json.loads(restored.stdout)["status"] == "LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED"


def test_backwards_compatible_verify_and_restore_without_pin(tmp_path):
    folder, fingerprint = snapshot(tmp_path)
    assert verify_backup(folder)["manifest_sha256"] == fingerprint
    target = tmp_path / "restore"
    assert restore_backup(folder, target)["manifest_sha256"] == fingerprint


def test_bad_pin_on_valid_existing_restore_is_not_idempotent_success(tmp_path):
    folder, fingerprint = snapshot(tmp_path)
    target = tmp_path / "restored"
    restore_backup(folder, target, expected_manifest_sha256=fingerprint)
    wrong = "d"*64 if fingerprint != "d"*64 else "e"*64
    with pytest.raises(BackupFailure, match="MANIFEST_DIGEST_MISMATCH"):
        restore_backup(folder, target, expected_manifest_sha256=wrong)
