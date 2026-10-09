"""R13 RED: fail-closed restored-root writer quarantine, synthetic only."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))

from brain_core.capture import CaptureFailure, capture_file, verify_capture
from brain_core.writer import WriterFailure, configure_writer, publish_capture, verify_publication
from brain_core.custody import CustodyFailure, commit_capture, verify_commit, verify_chain
from brain_core.object import ObjectFailure, create_object, verify_object_link
from brain_core.backup import BackupFailure, create_backup, restore_backup, verify_backup
from brain_core.recovery import RecoveryFailure, recovery_status

def setup_pair(tmp_path):
    root = tmp_path / "원본 한글 brain"
    root.mkdir()
    source = tmp_path / "synthetic content.txt"
    source.write_bytes(b"R13 synthetic bytes no private data\x00")
    cap = capture_file(root, source, "pc_1", "synthetic")
    auth = configure_writer(root, "single-writer")
    publish_capture(root, "pc_1", cap["capture_id"], "single-writer", auth["writer_epoch"])
    commit_capture(root, "pc_1", cap["capture_id"], "single-writer", auth["writer_epoch"])
    create_object(root, "pc_1", cap["capture_id"], "single-writer", auth["writer_epoch"])
    return root, source, cap, auth

def restore_pair(tmp_path):
    root, source, cap, auth = setup_pair(tmp_path)
    snapshot = tmp_path / "독립 위치 아님 local-copy"
    original = create_backup(root, snapshot)
    target = tmp_path / "복원된 brain root"
    restored = restore_backup(snapshot, target)
    return root, snapshot, target, source, cap, auth, original, restored

def test_restored_root_is_quarantined_and_linked_to_manifest(tmp_path):
    root, snap, new, source, cap, auth, result, restored = restore_pair(tmp_path)
    marker = new / "90_System/writer/recovery-hold.json"
    assert marker.is_file()
    record = json.loads(marker.read_bytes())
    assert record == {"schema_version": 1, "kind": "LOCAL_RECOVERY_HOLD",
                      "status": "RECOVERED_READ_ONLY",
                      "manifest_sha256": result["manifest_sha256"]}
    assert recovery_status(new)["status"] == "RECOVERED_READ_ONLY"
    assert recovery_status(new)["writer_active"] is False
    assert recovery_status(root)["status"] == "LOCAL_WRITER_POLICY_ONLY"
    assert recovery_status(root)["writer_active"] is None
    assert restored["status"] == "LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED"
    assert restore_backup(snap, new)["status"] == "RESTORE_ALREADY_VALID_LOCAL"
    assert verify_backup(snap)["manifest_sha256"] == result["manifest_sha256"]
    assert verify_object_link(new, "pc_1", cap["capture_id"])["status"] == "LOCAL_OBJECT_LINK_VERIFIED_UNANCHORED"
    assert verify_capture(new, "pc_1", cap["capture_id"])["status"] == "READY"
    assert verify_publication(new, "pc_1", cap["capture_id"])["status"] == "VAULT_VERIFIED_UNCOMMITTED"
    assert verify_commit(new, "pc_1", cap["capture_id"])["status"] == "LOCAL_CHAIN_COMMITTED_UNANCHORED"
    assert verify_chain(new)["event_count"] == 2
    assert source.read_bytes() == b"R13 synthetic bytes no private data\x00"

def test_hold_blocks_all_write_entrypoints_but_not_source(tmp_path):
    root, snap, new, source, cap, auth, *_ = restore_pair(tmp_path)
    with pytest.raises(CaptureFailure, match="RECOVERY_HOLD"):
        capture_file(new, source, "pc_1", "new-collector")
    with pytest.raises(WriterFailure, match="RECOVERY_HOLD"):
        configure_writer(new, "another-writer")
    with pytest.raises(WriterFailure, match="RECOVERY_HOLD"):
        publish_capture(new, "pc_1", cap["capture_id"], "single-writer", auth["writer_epoch"])
    with pytest.raises(CustodyFailure, match="RECOVERY_HOLD"):
        commit_capture(new, "pc_1", cap["capture_id"], "single-writer", auth["writer_epoch"])
    with pytest.raises(ObjectFailure, match="RECOVERY_HOLD"):
        create_object(new, "pc_1", cap["capture_id"], "single-writer", auth["writer_epoch"])
    with pytest.raises(BackupFailure, match="RECOVERY_HOLD"):
        create_backup(new, tmp_path / "should-not-duplicate")
    # The source retains its previously authorized local capability.
    assert recovery_status(root)["status"] == "LOCAL_WRITER_POLICY_ONLY"

def test_manifest_hold_missing_or_corrupt_fails_restore_retry(tmp_path):
    root, snap, new, source, cap, auth, *_ = restore_pair(tmp_path)
    marker = new / "90_System/writer/recovery-hold.json"
    marker.unlink()
    with pytest.raises(BackupFailure, match="DESTINATION_CONFLICT"):
        restore_backup(snap, new)
    with pytest.raises(RecoveryFailure, match="RECOVERY_HOLD_MISSING"):
        recovery_status(new)
    marker.write_bytes(b'{"status":"RECOVERED_READ_ONLY"}')
    with pytest.raises(BackupFailure, match="DESTINATION_CONFLICT"):
        restore_backup(snap, new)
    with pytest.raises(RecoveryFailure, match="RECOVERY_HOLD_INVALID"):
        recovery_status(new)
    with pytest.raises(CaptureFailure, match="RECOVERY_HOLD"):
        capture_file(new, source, "pc_1", "synthetic")

def test_tampered_hold_manifest_cannot_become_valid(tmp_path):
    root, snap, new, *_ = restore_pair(tmp_path)
    marker = new / "90_System/writer/recovery-hold.json"
    record = json.loads(marker.read_bytes())
    record["manifest_sha256"] = "f"*64
    marker.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    with pytest.raises(BackupFailure, match="DESTINATION_CONFLICT"):
        restore_backup(snap, new)
    with pytest.raises(RecoveryFailure, match="RECOVERY_HOLD_INVALID"):
        recovery_status(new)

def test_restore_copies_only_after_hold_written(tmp_path, monkeypatch):
    from brain_core import backup as mod
    root, source, cap, auth = setup_pair(tmp_path)
    folder = tmp_path / "snapshot"
    create_backup(root, folder)
    original = mod._copy_file
    target = tmp_path / "restored"
    calls = []
    def check(*args, **kwargs):
        calls.append(True)
        assert (target / "90_System/writer/recovery-hold.json").is_file()
        return original(*args, **kwargs)
    monkeypatch.setattr(mod, "_copy_file", check)
    restore_backup(folder, target)
    assert calls

def test_failure_creating_hold_cannot_copy_authority(tmp_path, monkeypatch):
    from brain_core import backup as mod
    root, source, cap, auth = setup_pair(tmp_path)
    folder = tmp_path / "snapshot"; create_backup(root, folder)
    original = mod._write_exclusive
    def fail_hold(path, data):
        if path.name == "recovery-hold.json":
            raise OSError("injected failure")
        return original(path, data)
    monkeypatch.setattr(mod, "_write_exclusive", fail_hold)
    target = tmp_path / "restore fail"
    with pytest.raises(BackupFailure, match="INCOMPLETE_RESTORE"):
        restore_backup(folder, target)
    assert not (target / "90_System/writer/authority.json").exists()

def test_offline_snapshot_usable_without_original_root(tmp_path):
    root, snap, dest, *_ = restore_pair(tmp_path)
    renamed = tmp_path / "source disconnected"
    root.rename(renamed)
    assert recovery_status(dest)["status"] == "RECOVERED_READ_ONLY"
    assert verify_backup(snap)["status"] == "LOCAL_SNAPSHOT_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED"
    assert restore_backup(snap, dest)["status"] == "RESTORE_ALREADY_VALID_LOCAL"

def test_cli_recovery_status_and_capture_refusal(tmp_path):
    root, snap, new, source, cap, auth, *_ = restore_pair(tmp_path)
    base = [sys.executable, str(PROFILE / "brain.py")]
    result = subprocess.run(base+["recovery","status","--root",str(new),"--json"],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "RECOVERED_READ_ONLY"
    c = subprocess.run(base+["capture","file",str(source),"--root",str(new),
        "--device-id","pc_1","--collector","syn","--json"], capture_output=True,text=True)
    assert c.returncode == 3
    assert json.loads(c.stdout)["error_code"] == "RECOVERY_HOLD"
    wrong = subprocess.run(base+["recovery","status","--root",str(tmp_path/"missing"),"--json"],
        capture_output=True,text=True)
    assert wrong.returncode == 3
    assert json.loads(wrong.stdout)["error_code"] == "INVALID_ROOT"

def test_forged_link_or_directory_cannot_be_read_as_authorization(tmp_path):
    root, snap, new, source, cap, auth, *_ = restore_pair(tmp_path)
    path = new / "90_System/writer/recovery-hold.json"
    out = tmp_path / "saved-hold"
    out.write_bytes(path.read_bytes())
    path.unlink()
    try: path.symlink_to(out)
    except (OSError, NotImplementedError): pytest.skip("symlink unavailable")
    with pytest.raises(RecoveryFailure, match="UNSAFE_PATH"):
        recovery_status(new)
    with pytest.raises(CaptureFailure, match="RECOVERY_HOLD"):
        capture_file(new, source, "pc_1", "synthetic")


@pytest.mark.skipif(sys.platform != "win32", reason="real Windows NTFS junction case")
def test_real_windows_junction_restore_destination_is_rejected(tmp_path):
    root, source, cap, auth = setup_pair(tmp_path)
    backup = tmp_path / "backup"
    create_backup(root, backup)
    actual = tmp_path / "real"; actual.mkdir()
    alias = tmp_path / "junction-alias"
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(actual)],
                            capture_output=True)
    if result.returncode:
        pytest.skip("junction creation unsupported on runner")
    assert alias.is_junction()
    with pytest.raises(BackupFailure, match="UNSAFE_DESTINATION"):
        restore_backup(backup, alias / "root")
    assert not (actual / "root").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="real Windows NTFS junction case")
def test_real_windows_junction_inside_source_rejected(tmp_path):
    root, source, cap, auth = setup_pair(tmp_path)
    objects = root / "10_Evidence/Records/objects"
    outside = tmp_path / "moved-objects"
    objects.rename(outside)
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(objects), str(outside)],
                            capture_output=True)
    if result.returncode:
        pytest.skip("junction creation unsupported on runner")
    assert objects.is_junction()
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        create_backup(root, tmp_path / "backup")
