"""R13-E RED: same-content file NAME substitutions between copy/digest checks.

These are deterministic static injection tests, NOT hostile atomic parent
directory TOCTOU proofs. No private evidence or real cloud drives are used.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))

from brain_core import backup as mod
from brain_core.backup import BackupFailure, create_backup, restore_backup, verify_backup
from brain_core.capture import capture_file
from brain_core.writer import configure_writer, publish_capture
from brain_core.custody import commit_capture
from brain_core.object import create_object


def source_root(tmp_path):
    root = tmp_path / "synthetic source root"
    root.mkdir()
    source = tmp_path / "synthetic.txt"
    source.write_bytes(b"same contents cannot prove same inode\0")
    authority = configure_writer(root, "ci-one-writer")
    cap = capture_file(root, source, "ci-device", "test")
    publish_capture(root, "ci-device", cap["capture_id"], "ci-one-writer", authority["writer_epoch"])
    commit_capture(root, "ci-device", cap["capture_id"], "ci-one-writer", authority["writer_epoch"])
    create_object(root, "ci-device", cap["capture_id"], "ci-one-writer", authority["writer_epoch"])
    return root


def replace_with_same_bytes(path: Path):
    before = path.stat()
    sibling = path.parent / (path.name + ".injected-replacement")
    sibling.write_bytes(path.read_bytes())
    os.replace(sibling, path)
    after = path.stat()
    assert path.read_bytes() and before.st_ino != after.st_ino
    assert before.st_size == after.st_size
    assert after.st_nlink == 1


def test_backup_rejects_same_bytes_leaf_replacement_during_copy(tmp_path, monkeypatch):
    root = source_root(tmp_path)
    original = mod._copy_source
    injection = {"count": 0}
    def drift(source, destination):
        outcome = original(source, destination)
        if source.name == "authority.json" and not injection["count"]:
            replace_with_same_bytes(source)
            injection["count"] += 1
        return outcome
    monkeypatch.setattr(mod, "_copy_source", drift)
    folder = tmp_path / "incomplete snapshot"
    with pytest.raises(BackupFailure, match="SOURCE_CHANGED"):
        create_backup(root, folder)
    assert injection["count"] == 1
    assert folder.is_dir()
    assert not (folder / ".complete").exists()


def test_restore_rejects_same_bytes_leaf_replacement_during_copy(tmp_path, monkeypatch):
    root = source_root(tmp_path)
    snapshot = tmp_path / "snapshot"
    create_backup(root, snapshot)
    original = mod._copy_source
    injection = {"count": 0}
    def drift(source, destination):
        result = original(source, destination)
        if source.name == "authority.json" and not injection["count"]:
            replace_with_same_bytes(source)
            injection["count"] += 1
        return result
    monkeypatch.setattr(mod, "_copy_source", drift)
    target = tmp_path / "incomplete restored"
    with pytest.raises(BackupFailure, match="INCOMPLETE_RESTORE"):
        restore_backup(snapshot, target)
    assert injection["count"] == 1
    assert target.is_dir()  # quarantine created first
    assert (target / "90_System" / "writer" / "recovery-hold.json").is_file()


def test_verify_rejects_same_bytes_snapshot_leaf_swap_after_digest(tmp_path, monkeypatch):
    root = source_root(tmp_path)
    snapshot = tmp_path / "snapshot"
    create_backup(root, snapshot)
    original = mod._digest_fd
    injection = {"count": 0}
    def digest_and_replace(file):
        value = original(file)
        if file.name == "authority.json" and not injection["count"]:
            replace_with_same_bytes(file)
            injection["count"] += 1
        return value
    monkeypatch.setattr(mod, "_digest_fd", digest_and_replace)
    with pytest.raises(BackupFailure, match="SNAPSHOT_TAMPERED"):
        verify_backup(snapshot)
    assert injection["count"] == 1


def test_restore_rejects_same_bytes_leaf_swap_during_preflight_digest(tmp_path, monkeypatch):
    root = source_root(tmp_path)
    snapshot = tmp_path / "snapshot"
    create_backup(root, snapshot)
    original = mod._digest_fd
    triggered = {"value": False}
    def swap(file):
        result = original(file)
        if file.name == "authority.json" and not triggered["value"]:
            replace_with_same_bytes(file)
            triggered["value"] = True
        return result
    monkeypatch.setattr(mod, "_digest_fd", swap)
    target = tmp_path / "never created"
    with pytest.raises(BackupFailure, match="SNAPSHOT_TAMPERED"):
        restore_backup(snapshot, target)
    assert triggered["value"]
    assert not target.exists()


def test_ordinary_source_and_valid_snapshot_still_verify_and_restore(tmp_path):
    root = source_root(tmp_path)
    snapshot = tmp_path / "snapshot"
    created = create_backup(root, snapshot)
    assert verify_backup(snapshot)["manifest_sha256"] == created["manifest_sha256"]
    target = tmp_path / "restored"
    assert restore_backup(snapshot, target)["manifest_sha256"] == created["manifest_sha256"]
