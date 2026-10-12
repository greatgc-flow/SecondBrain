"""R12 RED first: synthetic whole-root closure, offline snapshot and restore."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE))

from brain_core.capture import capture_file
from brain_core.writer import configure_writer, publish_capture
from brain_core.custody import commit_capture, verify_chain
from brain_core.object import create_object, verify_object_link
from brain_core.backup import BackupFailure, create_backup, verify_backup, restore_backup


def fixture(tmp_path, n=2, data=b"synthetic evidence, never private\x00"):
    root = tmp_path / "한글 공백 로컬 원본"
    root.mkdir()
    src = tmp_path / "테스트 file.txt"
    src.write_bytes(data)
    writer = configure_writer(root, "only-writer")
    caps = []
    for _ in range(n):
        cap = capture_file(root, src, "pc1", "synthetic")
        publish_capture(root, "pc1", cap["capture_id"], "only-writer", writer["writer_epoch"])
        commit_capture(root, "pc1", cap["capture_id"], "only-writer", writer["writer_epoch"])
        create_object(root, "pc1", cap["capture_id"], "only-writer", writer["writer_epoch"])
        caps.append(cap)
    return root, src, caps


def test_complete_snapshot_is_byte_exact_and_restores_full_closure(tmp_path):
    root, src, caps = fixture(tmp_path)
    before = src.read_bytes()
    folder = tmp_path / "별도 보관 snapshot"
    snap = create_backup(root, folder)
    assert snap["status"] == "LOCAL_SNAPSHOT_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED"
    assert snap["capture_count"] == 2 and snap["event_count"] == 4
    assert (folder / "manifest.json").is_file()
    assert (folder / ".complete").is_file()
    assert verify_backup(folder)["manifest_sha256"] == snap["manifest_sha256"]
    m = json.loads((folder / "manifest.json").read_bytes())
    assert all(not p["path"].startswith("/") and ".." not in p["path"].split("/") for p in m["files"])
    assert str(root).encode() not in (folder / "manifest.json").read_bytes()
    dest = tmp_path / "복구 루트 New"
    done = restore_backup(folder, dest)
    assert done["status"] == "LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED"
    assert verify_chain(dest)["event_count"] == 4
    for cap in caps:
        assert verify_object_link(dest, "pc1", cap["capture_id"])["status"] == "LOCAL_OBJECT_LINK_VERIFIED_UNANCHORED"
    assert src.read_bytes() == before
    assert restore_backup(folder, dest)["status"] == "RESTORE_ALREADY_VALID_LOCAL"


def test_same_payload_dedup_and_single_capture(tmp_path):
    root, src, caps = fixture(tmp_path, n=1, data=b"")
    snap = create_backup(root, tmp_path / "external snapshot")
    assert snap["capture_count"] == 1
    assert snap["object_count"] == 1
    assert restore_backup(tmp_path / "external snapshot", tmp_path / "new root")["file_count"] == snap["file_count"]


def test_requires_full_r11_closure_no_orphan_capture(tmp_path):
    root, src, caps = fixture(tmp_path, n=1)
    capture_file(root, src, "pc1", "synthetic")  # READY only, never committed/linked
    with pytest.raises(BackupFailure, match="SNAPSHOT_NOT_CLOSED"):
        create_backup(root, tmp_path / "backup")
    assert not (tmp_path / "backup" / ".complete").exists()


def test_corrupted_source_blocks_snapshot_before_destination(tmp_path):
    root, _, caps = fixture(tmp_path, n=1)
    path = root / "10_Evidence/Records/custody/events/00000000000000000001.json"
    path.write_bytes(b"tampered")
    with pytest.raises(BackupFailure, match="SOURCE_INVALID"):
        create_backup(root, tmp_path / "backup")
    assert not (tmp_path / "backup").exists()


def test_snapshot_cannot_reside_in_source_or_contain_source(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    with pytest.raises(BackupFailure, match="UNSAFE_DESTINATION"):
        create_backup(root, root / "backup")
    with pytest.raises(BackupFailure, match="UNSAFE_DESTINATION"):
        create_backup(root, tmp_path)  # backup directory would contain source
    assert not (root / "backup").exists()


@pytest.mark.parametrize("mutation", ["data", "missing", "manifest", "extra", "marker", "duplicate"])
def test_snapshot_verifier_fails_closed_and_restore_refuses_tampering(tmp_path, mutation):
    root, _, _ = fixture(tmp_path, n=1)
    folder = tmp_path / "backup"
    create_backup(root, folder)
    manifest = folder / "manifest.json"
    data = json.loads(manifest.read_bytes())
    target = folder / "data" / data["files"][0]["path"]
    if mutation == "data":
        target.write_bytes(b"corrupt")
    elif mutation == "missing":
        target.unlink()
    elif mutation == "manifest":
        data["files"][0]["sha256"] = "0" * 64
        manifest.write_text(json.dumps(data), encoding="utf-8")
    elif mutation == "extra":
        (folder / "data" / "unlisted").write_bytes(b"bad")
    elif mutation == "marker":
        (folder / ".complete").unlink()
    elif mutation == "duplicate":
        blob = manifest.read_bytes()
        manifest.write_bytes(blob[:-1] + b',"schema_version":1}')
    with pytest.raises(BackupFailure):
        verify_backup(folder)
    with pytest.raises(BackupFailure):
        restore_backup(folder, tmp_path / "recovery")
    assert not (tmp_path / "recovery").exists()


@pytest.mark.parametrize("location", ["source", "backup"])
def test_symlinks_are_rejected(tmp_path, location):
    root, _, _ = fixture(tmp_path, n=1)
    if location == "source":
        file = root / "10_Evidence/Records/objects"
        out = tmp_path / "moved"; file.rename(out)
        try: file.symlink_to(out, target_is_directory=True)
        except (OSError, NotImplementedError): pytest.skip("symlink unavailable")
        with pytest.raises(BackupFailure):
            create_backup(root, tmp_path / "snapshot")
    else:
        folder = tmp_path / "snapshot"
        create_backup(root, folder)
        data = json.loads((folder / "manifest.json").read_bytes())
        file = folder / "data" / data["files"][0]["path"]
        out = tmp_path / "outside"
        out.write_bytes(file.read_bytes())
        file.unlink()
        try: file.symlink_to(out)
        except (OSError, NotImplementedError): pytest.skip("symlink unavailable")
        with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
            verify_backup(folder)


def test_destination_existing_different_never_overwritten(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    folder = tmp_path / "snapshot"
    create_backup(root, folder)
    dest = tmp_path / "existing"
    dest.mkdir()
    note = dest / "important"; note.write_bytes(b"keep")
    with pytest.raises(BackupFailure, match="DESTINATION_CONFLICT"):
        restore_backup(folder, dest)
    assert note.read_bytes() == b"keep"


def test_fail_during_copy_never_creates_completion_marker(tmp_path, monkeypatch):
    from brain_core import backup as mod
    root, _, _ = fixture(tmp_path, n=1)
    real = mod._copy_file
    def interrupted(*args, **kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(mod, "_copy_file", interrupted)
    with pytest.raises(BackupFailure, match="INCOMPLETE_SNAPSHOT"):
        create_backup(root, tmp_path / "snapshot")
    assert not (tmp_path / "snapshot" / ".complete").exists()
    monkeypatch.setattr(mod, "_copy_file", real)


def test_fail_during_restore_never_reports_completion_and_retry_only_after_cleanup(tmp_path, monkeypatch):
    from brain_core import backup as mod
    root, _, _ = fixture(tmp_path, n=1)
    folder = tmp_path / "snapshot"; create_backup(root, folder)
    original = mod._copy_file
    def interrupted(*args, **kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(mod, "_copy_file", interrupted)
    target = tmp_path / "restored"
    with pytest.raises(BackupFailure, match="INCOMPLETE_RESTORE"):
        restore_backup(folder, target)
    monkeypatch.setattr(mod, "_copy_file", original)
    with pytest.raises(BackupFailure, match="DESTINATION_CONFLICT"):
        restore_backup(folder, target)
    assert not (target / ".restore.complete").exists()


def test_restore_destination_parent_symlink_denied(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    folder = tmp_path / "snapshot"; create_backup(root, folder)
    actual = tmp_path / "actual"; actual.mkdir()
    indirect = tmp_path / "via-link"
    try: indirect.symlink_to(actual, target_is_directory=True)
    except (OSError, NotImplementedError): pytest.skip("symlink unavailable")
    with pytest.raises(BackupFailure, match="UNSAFE_DESTINATION"):
        restore_backup(folder, indirect / "recovery")
    assert not (actual / "recovery").exists()


def test_root_relocation_does_not_invalidate_backup_snapshot(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    folder = tmp_path / "snapshot"; snap = create_backup(root, folder)
    moved = tmp_path / "이름 변경 Root"
    root.rename(moved)
    assert verify_backup(folder)["manifest_sha256"] == snap["manifest_sha256"]


def test_cli_backup_create_verify_restore_exit_codes(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    folder = tmp_path / "snapshot"; dest = tmp_path / "restore Korean"
    base = [sys.executable, str(SOURCE / "brain.py"), "backup"]
    def run(args, expected=0):
        process = subprocess.run(base+args, text=True, capture_output=True)
        assert process.returncode == expected, process.stderr
        return json.loads(process.stdout)
    assert run(["create", "--root", str(root), "--to", str(folder), "--json"])["capture_count"] == 1
    assert run(["verify", str(folder), "--json"])["status"].startswith("LOCAL_SNAPSHOT_")
    assert run(["restore", str(folder), "--to-root", str(dest), "--json"])["status"].startswith("LOCAL_RESTORE_")
    assert run(["restore", str(folder), "--to-root", str(dest), "--json"])["status"] == "RESTORE_ALREADY_VALID_LOCAL"
    (folder / ".complete").unlink()
    assert run(["verify", str(folder), "--json"], expected=3)["error_code"] == "INCOMPLETE_SNAPSHOT"


def test_no_network_or_provider_api(tmp_path, monkeypatch):
    import socket
    root, _, _ = fixture(tmp_path, n=1)
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    folder = tmp_path / "snapshot"
    create_backup(root, folder)
    verify_backup(folder)
    restore_backup(folder, tmp_path / "restored")


def test_unknown_empty_directory_rejected_before_snapshot(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    (root / "10_Evidence/Records/unlisted-empty").mkdir()
    with pytest.raises(BackupFailure, match="SNAPSHOT_NOT_CLOSED"):
        create_backup(root, tmp_path / "snapshot")


def test_unlisted_empty_directory_in_snapshot_or_restore_is_conflict(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    folder = tmp_path / "snapshot"; create_backup(root, folder)
    (folder / "data" / "hidden-empty").mkdir()
    with pytest.raises(BackupFailure, match="SNAPSHOT_TAMPERED"):
        verify_backup(folder)
    (folder / "data" / "hidden-empty").rmdir()
    dest = tmp_path / "restored"
    restore_backup(folder, dest)
    (dest / "unlisted-dir").mkdir()
    with pytest.raises(BackupFailure, match="DESTINATION_CONFLICT"):
        restore_backup(folder, dest)


def test_local_writer_busy_never_starts_snapshot(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    lock = root / "90_System/writer/.active"
    lock.write_bytes(b"another writer")
    with pytest.raises(BackupFailure, match="SOURCE_BUSY"):
        create_backup(root, tmp_path / "snapshot")
    assert not (tmp_path / "snapshot").exists()


def test_completion_marker_write_interrupted_fails_closed(tmp_path, monkeypatch):
    from brain_core import backup as mod
    root, _, _ = fixture(tmp_path, n=1)
    real = mod._write_exclusive
    def fail_on_marker(path, data):
        if path.name == ".complete":
            raise OSError("simulated marker fsync failure")
        return real(path, data)
    monkeypatch.setattr(mod, "_write_exclusive", fail_on_marker)
    with pytest.raises(BackupFailure, match="INCOMPLETE_SNAPSHOT"):
        create_backup(root, tmp_path / "snapshot")
    assert not (tmp_path / "snapshot" / ".complete").exists()
    monkeypatch.setattr(mod, "_write_exclusive", real)
    with pytest.raises(BackupFailure, match="INCOMPLETE_SNAPSHOT"):
        verify_backup(tmp_path / "snapshot")
