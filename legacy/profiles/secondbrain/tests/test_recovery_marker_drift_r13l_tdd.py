"""R13-L RED: equal-byte replacement of quarantine marker during validation.

Synthetic snapshots only; local leaf identity guard, not a distributed writer fence.
"""
from __future__ import annotations

from pathlib import Path
import sys
import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))

from brain_core.backup import BackupFailure, create_backup, restore_backup
from brain_core.recovery import RecoveryFailure, HOLD_REL, SENTINEL_REL, recovery_status
from test_backup_r12_tdd import fixture


@pytest.mark.parametrize("marker", [HOLD_REL, SENTINEL_REL])
@pytest.mark.parametrize("operation", ["status", "restore_retry"])
def test_equal_bytes_recovery_marker_leaf_swap_fails_closed(tmp_path, monkeypatch, marker, operation):
    source, _, _ = fixture(tmp_path, n=1)
    snapshot = tmp_path / "snapshot"
    create_backup(source, snapshot)
    recovered = tmp_path / "read-only-recovered"
    restore_backup(snapshot, recovered)
    chosen = recovered / marker
    original_read_bytes = Path.read_bytes
    did_replace = [False]

    def swap_after_read(self):
        value = original_read_bytes(self)
        if Path(self) == chosen and not did_replace[0]:
            did_replace[0] = True
            # Same bytes, distinct regular inode; not a symlink or hardlink.
            replacement = tmp_path / "replacement-ordinary-marker"
            replacement.write_bytes(value)
            replacement.replace(chosen)
        return value

    monkeypatch.setattr(Path, "read_bytes", swap_after_read)
    if operation == "status":
        with pytest.raises(RecoveryFailure, match="RECOVERY_HOLD_INVALID"):
            recovery_status(recovered)
    else:
        with pytest.raises(BackupFailure, match="DESTINATION_CONFLICT"):
            restore_backup(snapshot, recovered)
    assert did_replace[0]
    assert (recovered / "90_System/writer/authority.json").is_file()


def test_unchanged_recovery_markers_validate_and_repeat_restore(tmp_path):
    source, _, _ = fixture(tmp_path, n=1)
    snapshot = tmp_path / "snapshot"
    created = create_backup(source, snapshot)
    recovered = tmp_path / "read-only-recovered"
    restore_backup(snapshot, recovered)
    assert recovery_status(recovered)["manifest_sha256"] == created["manifest_sha256"]
    assert restore_backup(snapshot, recovered)["status"] == "RESTORE_ALREADY_VALID_LOCAL"
