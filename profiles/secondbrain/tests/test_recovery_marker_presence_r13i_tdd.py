"""R13-I RED: recovery quarantine marker discovery must fail closed.

Synthetic-only tests.  These are not a cross-device lease, independent storage
check or real Windows cloud-placeholder acceptance.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))

from brain_core.backup import restore_backup
from brain_core.capture import CaptureFailure, capture_file
from brain_core.recovery import (
    RecoveryFailure, HOLD_REL, SENTINEL_REL,
    recovery_hold_present, recovery_status,
)
from brain_core.writer import WriterFailure, configure_writer
from ci_cross_runner_drill import produce_fixture


def recovery_root(tmp_path):
    transfer = tmp_path / "transfer"
    produce_fixture(transfer)
    restored = tmp_path / "quarantined root"
    restore_backup(transfer / "snapshot", restored)
    return restored


def test_existing_markers_do_not_depend_on_exists_or_is_symlink(tmp_path, monkeypatch):
    root = recovery_root(tmp_path)
    markers = {root / HOLD_REL, root / SENTINEL_REL}
    original_exists, original_symlink = Path.exists, Path.is_symlink

    def false_negative_exists(self, *args, **kwargs):
        return False if self in markers else original_exists(self, *args, **kwargs)

    def false_negative_symlink(self):
        return False if self in markers else original_symlink(self)

    # Model a filesystem provider returning false negatives to higher-level
    # presence probes. lstat still sees the actual, ordinary marker.
    monkeypatch.setattr(Path, "exists", false_negative_exists)
    monkeypatch.setattr(Path, "is_symlink", false_negative_symlink)

    assert recovery_hold_present(root)
    assert recovery_status(root)["status"] == "RECOVERED_READ_ONLY"
    with pytest.raises(WriterFailure, match="RECOVERY_HOLD"):
        configure_writer(root, "unauthorized-restored-writer")


def test_inaccessible_marker_is_assumed_present_and_blocks_mutation(tmp_path, monkeypatch):
    root = recovery_root(tmp_path)
    marker = root / HOLD_REL
    original_lstat = Path.lstat

    def denied(self, *args, **kwargs):
        if self == marker:
            raise PermissionError("synthetic ACL denies metadata")
        return original_lstat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", denied)
    assert recovery_hold_present(root)
    with pytest.raises(RecoveryFailure, match="UNSAFE_PATH"):
        recovery_status(root)
    source = tmp_path / "purely synthetic.txt"
    source.write_bytes(b"test bytes")
    with pytest.raises(CaptureFailure, match="RECOVERY_HOLD"):
        capture_file(root, source, "ci-device", "synthetic")
    assert not (root / "00_Inbox" / "Drop" / "ci-device").exists()


class FlaggedStat:
    def __init__(self, base):
        self._base = base
        self.st_file_attributes = 0x00000400  # Win32 FILE_ATTRIBUTE_REPARSE_POINT

    def __getattr__(self, key):
        return getattr(self._base, key)


def test_unsafe_writer_directory_blocks_even_if_markers_are_missing(tmp_path, monkeypatch):
    root = tmp_path / "root"
    parent = root / "90_System" / "writer"
    parent.mkdir(parents=True)
    original_lstat = Path.lstat

    def flagged(self, *args, **kwargs):
        result = original_lstat(self, *args, **kwargs)
        return FlaggedStat(result) if self == parent else result

    monkeypatch.setattr(Path, "lstat", flagged)
    # Never conclude 'no recovery hold' through a known unsafe reparse parent.
    assert recovery_hold_present(root)
    with pytest.raises(WriterFailure, match="RECOVERY_HOLD"):
        configure_writer(root, "candidate")
    with pytest.raises(RecoveryFailure, match="UNSAFE_PATH"):
        recovery_status(root)


def test_missing_markers_in_normal_fresh_root_remain_writable(tmp_path):
    root = tmp_path / "fresh"
    root.mkdir()
    assert not recovery_hold_present(root)
    assert recovery_status(root)["status"] == "LOCAL_WRITER_POLICY_ONLY"
    assert configure_writer(root, "initial-writer")["status"] == "WRITER_CONFIGURED_POLICY_ONLY"


def test_one_deleted_marker_still_blocks_and_status_is_incomplete(tmp_path):
    root = recovery_root(tmp_path)
    (root / HOLD_REL).unlink()
    assert recovery_hold_present(root)
    with pytest.raises(RecoveryFailure, match="RECOVERY_HOLD_MISSING"):
        recovery_status(root)
    with pytest.raises(WriterFailure, match="RECOVERY_HOLD"):
        configure_writer(root, "bypass")
