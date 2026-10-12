"""R13-K RED: identical-byte manifest/marker leaf replacement must not pass.

Synthetic files only; one controlled, deterministic race at the metadata/read
boundary. This does not model malicious parent-directory ABA swaps.
"""
from __future__ import annotations

from pathlib import Path
import sys
import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))
from brain_core.backup import BackupFailure, create_backup, verify_backup, restore_backup
from test_backup_r12_tdd import fixture


@pytest.mark.parametrize("which", ["manifest.json", ".complete"])
@pytest.mark.parametrize("operation", ["verify", "restore"])
def test_same_bytes_leaf_swap_during_snapshot_control_read_is_rejected(tmp_path, monkeypatch, which, operation):
    root, _, _ = fixture(tmp_path, n=1)
    snapshot = tmp_path / "snapshot"
    create_backup(root, snapshot)
    chosen = snapshot / which
    original = Path.read_bytes
    replaced = [False]

    def swap_when_read(path):
        data = original(path)
        if Path(path) == chosen and not replaced[0]:
            replaced[0] = True
            # A new ordinary, unique inode with the very same bytes and no
            # symlinks/hardlinks. Hash/manifest validation alone misses this.
            staging = tmp_path / "replacement"
            staging.write_bytes(data)
            staging.replace(chosen)
        return data

    monkeypatch.setattr(Path, "read_bytes", swap_when_read)
    restore_to = tmp_path / "must-not-restore"
    with pytest.raises(BackupFailure, match="SNAPSHOT_TAMPERED"):
        if operation == "verify":
            verify_backup(snapshot)
        else:
            restore_backup(snapshot, restore_to)
    assert replaced[0]
    assert not restore_to.exists()


def test_ordinary_unmodified_snapshot_control_files_are_valid(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    snapshot = tmp_path / "snapshot"
    created = create_backup(root, snapshot)
    assert verify_backup(snapshot)["manifest_sha256"] == created["manifest_sha256"]
    result = restore_backup(snapshot, tmp_path / "new-root")
    assert result["status"] == "LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED"
