"""R13-F RED: Windows cloud placeholder/offline/reparse metadata must fail closed.

These tests inject real Win32 attribute bit values into synthetic os.stat
responses on both CI operating systems; they do NOT impersonate a genuine
hydration, OneDrive or Google Drive integration test.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))

from brain_core.backup import BackupFailure, create_backup, restore_backup, verify_backup
from brain_core.capture import CaptureFailure, capture_file
from brain_core.verify import IntegrityFailure, _digest_fd
from brain_core.recovery import RecoveryFailure, recovery_status
from ci_cross_runner_drill import produce_fixture

BITS = {
    "reparse": 0x00000400,
    "offline": 0x00001000,
    "recall_on_open": 0x00040000,
    "recall_on_data_access": 0x00400000,
}


class StatWithAttribute:
    def __init__(self, original, flags):
        self._original = original
        self.st_file_attributes = flags

    def __getattr__(self, name):
        return getattr(self._original, name)


def inject_lstat(monkeypatch, target: Path, flags: int):
    original = Path.lstat
    wanted = os.fspath(target)
    def flagged(self, *args, **kwargs):
        real = original(self, *args, **kwargs)
        if os.fspath(self) == wanted:
            return StatWithAttribute(real, flags)
        return real
    monkeypatch.setattr(Path, "lstat", flagged)


def fixture_snapshot(tmp_path):
    transfer = tmp_path / "synthetic-transfer"
    produce_fixture(transfer)
    return transfer / "snapshot"


@pytest.mark.parametrize("attribute", list(BITS))
def test_source_offline_or_placeholder_is_refused_before_any_capture(tmp_path, monkeypatch, attribute):
    root = tmp_path / "root"
    root.mkdir()
    file = tmp_path / "source"
    file.write_bytes(b"synthetic-only")
    inject_lstat(monkeypatch, file, BITS[attribute])
    with pytest.raises(CaptureFailure, match="UNSAFE_SOURCE"):
        capture_file(root, file, "ci-device", "test")
    assert not (root / "00_Inbox").exists()


@pytest.mark.parametrize("attribute", list(BITS))
def test_cloud_flagged_snapshot_manifest_is_not_read_before_refusal(tmp_path, monkeypatch, attribute):
    snapshot = fixture_snapshot(tmp_path)
    manifest = snapshot / "manifest.json"
    original = Path.read_bytes
    def refuse_manifest_read(self):
        if self == manifest:
            raise AssertionError("an unsafe cloud placeholder manifest was hydrated/read")
        return original(self)
    monkeypatch.setattr(Path, "read_bytes", refuse_manifest_read)
    inject_lstat(monkeypatch, manifest, BITS[attribute])
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        verify_backup(snapshot)
    target = tmp_path / "not-created"
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        restore_backup(snapshot, target)
    assert not target.exists()


@pytest.mark.parametrize("attribute", list(BITS))
def test_flagged_source_root_blocks_backup_before_destination(tmp_path, monkeypatch, attribute):
    # A complete source root is required, but the root itself can be offline.
    transfer = tmp_path / "transfer"
    produce_fixture(transfer)
    snapshot = transfer / "snapshot"
    # Snapshot verify must not silently accept a placeholder *root*.
    inject_lstat(monkeypatch, snapshot, BITS[attribute])
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        verify_backup(snapshot)


@pytest.mark.parametrize("attribute", list(BITS))
def test_flagged_data_directory_blocks_snapshot_verification(tmp_path, monkeypatch, attribute):
    snapshot = fixture_snapshot(tmp_path)
    data_dir = snapshot / "data"
    inject_lstat(monkeypatch, data_dir, BITS[attribute])
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        verify_backup(snapshot)


@pytest.mark.parametrize("attribute", list(BITS))
def test_unsafe_recovery_hold_marker_is_not_trusted(tmp_path, monkeypatch, attribute):
    snapshot = fixture_snapshot(tmp_path)
    target = tmp_path / "restored"
    restore_backup(snapshot, target)
    marker = target / "90_System/writer/recovery-hold.json"
    inject_lstat(monkeypatch, marker, BITS[attribute])
    with pytest.raises(RecoveryFailure, match="UNSAFE_PATH"):
        recovery_status(target)


@pytest.mark.parametrize("attribute", list(BITS))
def test_open_fd_metadata_flags_are_rejected_before_digest_read(tmp_path, monkeypatch, attribute):
    file = tmp_path / "source"
    file.write_bytes(b"synthetic-only")
    original = os.fstat
    wanted = file.stat().st_ino
    def flagged(fd):
        result = original(fd)
        if result.st_ino == wanted:
            return StatWithAttribute(result, BITS[attribute])
        return result
    monkeypatch.setattr(os, "fstat", flagged)
    with pytest.raises(IntegrityFailure, match="UNSAFE_PATH"):
        _digest_fd(file)



@pytest.mark.parametrize("attribute", list(BITS))
def test_leaf_digest_rejects_known_placeholder_before_even_os_open(tmp_path, monkeypatch, attribute):
    file = tmp_path / "source"
    file.write_bytes(b"no hydration allowed")
    original_open = os.open
    def fail_if_hydrating(path, *args, **kwargs):
        if os.fspath(path) == os.fspath(file):
            raise AssertionError("os.open must not be called on flagged placeholder")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, "open", fail_if_hydrating)
    inject_lstat(monkeypatch, file, BITS[attribute])
    with pytest.raises(IntegrityFailure, match="UNSAFE_PATH"):
        _digest_fd(file)

def test_conventional_local_files_still_work_on_both_os(tmp_path):
    snapshot = fixture_snapshot(tmp_path)
    assert verify_backup(snapshot)["capture_count"] == 3
    target = tmp_path / "restored"
    assert restore_backup(snapshot, target)["object_count"] == 2
    assert recovery_status(target)["status"] == "RECOVERED_READ_ONLY"
