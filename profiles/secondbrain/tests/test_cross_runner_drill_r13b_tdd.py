"""R13-B RED: isolated synthetic cross-runner export/import acceptance oracles."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brain_core.backup import BackupFailure
from ci_cross_runner_drill import DrillFailure, produce_fixture, consume_fixture


def test_cross_runner_fixture_bytes_and_complete_closure(tmp_path):
    transfer = tmp_path / "export from other runner"
    produced = produce_fixture(transfer)
    assert produced["status"] == "CI_FIXTURE_EXPORTED_SYNTHETIC_ONLY"
    assert (transfer / "snapshot" / ".complete").is_file()
    assert (transfer / "external-checkpoint.json").is_file()
    assert (transfer / "proof.json").is_file()
    assert not (transfer / "source").exists()
    assert not (transfer / "root").exists()
    assert "temp" not in json.loads((transfer / "proof.json").read_bytes())
    received = consume_fixture(transfer)
    assert received["status"] == "CI_CROSS_RUNNER_RESTORE_VERIFIED_NO_INDEPENDENT_CUSTODY"
    assert received["manifest_sha256"] == produced["manifest_sha256"]
    assert received["captures_verified"] == 3
    assert received["unique_objects"] == 2
    assert received["read_only"] is True
    assert received["source_available"] is False


def test_completed_copy_to_unrelated_path_without_original(tmp_path):
    folder = tmp_path / "artifact"
    produce_fixture(folder)
    remote = tmp_path / "downloaded elsewhere"
    import shutil
    shutil.copytree(folder, remote)
    assert consume_fixture(remote)["captures_verified"] == 3


@pytest.mark.parametrize("target", ["proof", "checkpoint", "snapshot", "marker", "missing", "extra"])
def test_corrupt_transfer_never_reports_verified(tmp_path, target):
    transfer = tmp_path / "artifact"
    produce_fixture(transfer)
    if target == "proof":
        proof = transfer / "proof.json"
        proof.write_bytes(proof.read_bytes() + b"junk")
    elif target == "checkpoint":
        (transfer / "external-checkpoint.json").write_bytes(b"{}")
    elif target == "snapshot":
        from brain_core.backup import _strict_json
        from pathlib import Path
        m = json.loads((transfer / "snapshot" / "manifest.json").read_bytes())
        (transfer / "snapshot" / "data" / m["files"][0]["path"]).write_bytes(b"tamper")
    elif target == "marker":
        (transfer / "snapshot" / ".complete").unlink()
    elif target == "missing":
        (transfer / "proof.json").unlink()
    else:
        (transfer / "unexpected private byte").write_bytes(b"should refuse")
    with pytest.raises((DrillFailure, BackupFailure)):
        consume_fixture(transfer)


def test_repeated_export_refuses_to_overwrite(tmp_path):
    transfer = tmp_path / "fixture"
    produce_fixture(transfer)
    with pytest.raises(DrillFailure, match="TRANSFER_CONFLICT"):
        produce_fixture(transfer)


def test_import_refuses_symlink_and_unlisted_file(tmp_path):
    transfer = tmp_path / "fixture"
    produce_fixture(transfer)
    path = transfer / "proof.json"
    moved = tmp_path / "outside"
    moved.write_bytes(path.read_bytes()); path.unlink()
    try: path.symlink_to(moved)
    except (OSError, NotImplementedError): pytest.skip("symlink unavailable")
    with pytest.raises(DrillFailure, match="UNSAFE_TRANSFER"):
        consume_fixture(transfer)
