"""R13-H RED: detached R10 checkpoint is untrusted local filesystem input.

Synthetic tests only: Win32 stat-bit injection is NOT actual cloud hydration,
and independent file path is NOT proof of independently governed custody.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys

import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))
import brain_core.checkpoint as checkpoint_module
from brain_core.checkpoint import CheckpointFailure, verify_checkpoint
from ci_cross_runner_drill import produce_fixture
from synthetic_offline_drill import DrillFailure, run_drill

CLOUD_BITS = [0x00000400, 0x00001000, 0x00040000, 0x00400000]


class FlaggedStat:
    def __init__(self, original, flags):
        self.original = original
        self.st_file_attributes = flags

    def __getattr__(self, name):
        return getattr(self.original, name)


def setup_witness(tmp_path: Path):
    origin = tmp_path / "synthetic original"
    produce_fixture(origin)
    proof = json.loads((origin / "proof.json").read_bytes())
    witness_dir = tmp_path / "detached witness"
    witness_dir.mkdir()
    witness = witness_dir / "checkpoint.json"
    shutil.copy2(origin / "external-checkpoint.json", witness)
    roster = ["ci-device/" + cap for cap in proof["capture_ids"]]
    return origin / "snapshot", witness, proof["manifest_sha256"], roster


def inject_metadata(monkeypatch, file: Path, flags: int):
    original = Path.lstat
    wanted = os.fspath(file)
    def guarded(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        return FlaggedStat(info, flags) if os.fspath(path) == wanted else info
    monkeypatch.setattr(Path, "lstat", guarded)


@pytest.mark.parametrize("flags", CLOUD_BITS)
def test_detached_checkpoint_leaf_cloud_flags_refused_without_payload_read(tmp_path, monkeypatch, flags):
    snapshot, witness, digest, roster = setup_witness(tmp_path)
    inject_metadata(monkeypatch, witness, flags)
    original = Path.read_bytes
    def no_hydration(path):
        if path == witness:
            raise AssertionError("unsafe checkpoint was read/hydrated")
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", no_hydration)
    with pytest.raises(CheckpointFailure, match="UNSAFE_CHECKPOINT_PATH"):
        verify_checkpoint(snapshot / "data", witness)
    target = tmp_path / "must not be created"
    with pytest.raises(DrillFailure, match="CHECKPOINT_INVALID"):
        run_drill(snapshot, target, digest, witness, roster)
    assert not target.exists()


@pytest.mark.parametrize("flags", CLOUD_BITS)
def test_unsafe_checkpoint_parent_directory_is_refused_before_read(tmp_path, monkeypatch, flags):
    snapshot, witness, _digest, _roster = setup_witness(tmp_path)
    inject_metadata(monkeypatch, witness.parent, flags)
    with pytest.raises(CheckpointFailure, match="UNSAFE_CHECKPOINT_PATH"):
        verify_checkpoint(snapshot / "data", witness)


def test_checkpoint_leaf_hardlink_to_uncontrolled_other_name_is_refused(tmp_path):
    snapshot, witness, digest, roster = setup_witness(tmp_path)
    original = tmp_path / "same-inode-outside-witness"
    try:
        os.link(witness, original)
    except (OSError, NotImplementedError) as exc:
        pytest.skip("hardlink unavailable: " + str(exc))
    assert witness.stat().st_nlink >= 2
    with pytest.raises(CheckpointFailure, match="UNSAFE_CHECKPOINT_PATH"):
        verify_checkpoint(snapshot / "data", witness)
    target = tmp_path / "no-restore"
    with pytest.raises(DrillFailure, match="CHECKPOINT_INVALID"):
        run_drill(snapshot, target, digest, witness, roster)
    assert not target.exists()


def test_checkpoint_directory_junction_like_path_refused(tmp_path, monkeypatch):
    snapshot, witness, _digest, _roster = setup_witness(tmp_path)
    original = Path.is_junction if hasattr(Path, "is_junction") else None
    def junction(path):
        if path == witness.parent:
            return True
        return original(path) if original is not None else False
    monkeypatch.setattr(Path, "is_junction", junction, raising=False)
    with pytest.raises(CheckpointFailure, match="UNSAFE_CHECKPOINT_PATH"):
        verify_checkpoint(snapshot / "data", witness)


def test_byte_identical_checkpoint_path_replaced_after_first_parse_refused(tmp_path, monkeypatch):
    snapshot, witness, _digest, _roster = setup_witness(tmp_path)
    original = checkpoint_module._strict_json
    injected = {"changed": False}
    def replace_after_parse(path):
        parsed = original(path)
        if path == witness and not injected["changed"]:
            replacement = witness.parent / "replacement.json"
            replacement.write_bytes(witness.read_bytes())
            initial = witness.stat().st_ino
            os.replace(replacement, witness)
            assert witness.stat().st_ino != initial
            injected["changed"] = True
        return parsed
    monkeypatch.setattr(checkpoint_module, "_strict_json", replace_after_parse)
    with pytest.raises(CheckpointFailure, match="UNSAFE_CHECKPOINT_PATH"):
        verify_checkpoint(snapshot / "data", witness)
    assert injected["changed"]


def test_regular_canonical_synthetic_checkpoint_still_works(tmp_path):
    snapshot, witness, digest, roster = setup_witness(tmp_path)
    assert verify_checkpoint(snapshot / "data", witness)["status"] == (
        "CHECKPOINT_EXACT_MATCH_EXTERNAL_CUSTODY_UNVERIFIED")
    restored = tmp_path / "recovered"
    result = run_drill(snapshot, restored, digest, witness, roster)
    assert result["captures_verified"] == 3
    assert result["actual_rpo_rto"] == "NOT_MEASURED_OPERATOR_REQUIRED"
