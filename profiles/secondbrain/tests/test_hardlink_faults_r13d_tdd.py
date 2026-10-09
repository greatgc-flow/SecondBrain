"""R13-D RED: reject filesystem hardlinks (not only symlinks/junctions).

Only synthetic roots; assumes OS can create local same-volume hardlinks.
Hardlinks are not byte corruption: existing SHA validation still matches.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))
from brain_core.backup import BackupFailure, create_backup, verify_backup, restore_backup
from brain_core.capture import capture_file
from brain_core.writer import configure_writer, publish_capture
from brain_core.custody import commit_capture
from brain_core.object import create_object
from brain_core.recovery import RecoveryFailure, recovery_status
from ci_cross_runner_drill import produce_fixture


def make_snapshot(tmp_path):
    transfer = tmp_path / "synthetic"
    produce_fixture(transfer)
    return transfer / "snapshot"


def alias_to_outside(source: Path, outside: Path):
    source.rename(outside)
    try:
        os.link(outside, source)
    except (OSError, NotImplementedError) as exc:
        outside.rename(source)
        pytest.skip("same-volume hardlinks not supported: " + str(exc))
    assert source.read_bytes() == outside.read_bytes()
    assert source.stat().st_nlink >= 2


def source_root(tmp_path):
    root = tmp_path / "source root"; root.mkdir()
    src = tmp_path / "synthetic file.txt"; src.write_bytes(b"no private evidence\x00")
    auth = configure_writer(root, "one-writer")
    cap = capture_file(root, src, "ci_1", "test")
    publish_capture(root, "ci_1", cap["capture_id"], "one-writer", auth["writer_epoch"])
    commit_capture(root, "ci_1", cap["capture_id"], "one-writer", auth["writer_epoch"])
    create_object(root, "ci_1", cap["capture_id"], "one-writer", auth["writer_epoch"])
    return root, cap


def test_source_capture_hardlink_outside_root_refused_pre_destination(tmp_path):
    root, cap = source_root(tmp_path)
    file = root / "00_Inbox" / "Drop" / "ci_1" / cap["capture_id"] / "payload"
    outside = tmp_path / "alias-original"
    alias_to_outside(file, outside)
    folder = tmp_path / "must-never-complete"
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        create_backup(root, folder)
    assert not folder.exists()


def test_source_record_hardlink_refused_even_with_matching_json(tmp_path):
    root, cap = source_root(tmp_path)
    file = root / "90_System/writer/authority.json"
    alias_to_outside(file, tmp_path / "metadata-original")
    target = tmp_path / "no-snapshot"
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        create_backup(root, target)
    assert not target.exists()


@pytest.mark.parametrize("which", ["payload", "manifest", "marker"])
def test_snapshot_hardlinked_data_or_metadata_refused(tmp_path, which):
    folder = make_snapshot(tmp_path)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    file = (folder / "data" / manifest["files"][0]["path"] if which == "payload" else
            folder / ("manifest.json" if which == "manifest" else ".complete"))
    outside = tmp_path / ("outside-" + which)
    alias_to_outside(file, outside)
    # All SHA and size checks would pass without inode alias checks.
    target = tmp_path / ("restore-not-created-" + which)
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        verify_backup(folder)
    with pytest.raises(BackupFailure):
        restore_backup(folder, target)
    assert not target.exists()


def test_existing_restored_root_data_hardlink_never_idempotently_accepted(tmp_path):
    folder = make_snapshot(tmp_path)
    target = tmp_path / "restored"
    restore_backup(folder, target)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    path = target / manifest["files"][0]["path"]
    alias_to_outside(path, tmp_path / "outside-restored")
    with pytest.raises(BackupFailure, match="DESTINATION_CONFLICT"):
        restore_backup(folder, target)
    assert recovery_status(target)["status"] == "RECOVERED_READ_ONLY"


@pytest.mark.parametrize("which", ["recovery-hold.json", "recovery-sentinel.json"])
def test_restored_recovery_authority_markers_must_not_be_hardlinks(tmp_path, which):
    folder = make_snapshot(tmp_path)
    target = tmp_path / "restored"
    restore_backup(folder, target)
    marker = target / "90_System" / "writer" / which
    alias_to_outside(marker, tmp_path / "outside-recovery-marker")
    with pytest.raises(RecoveryFailure, match="UNSAFE_PATH"):
        recovery_status(target)
    with pytest.raises(BackupFailure, match="DESTINATION_CONFLICT"):
        restore_backup(folder, target)


def test_hardlink_snapshot_cli_returns_nonzero_no_restore(tmp_path):
    folder = make_snapshot(tmp_path)
    file = folder / ".complete"
    alias_to_outside(file, tmp_path / "outside-marker")
    cli = [sys.executable, str(PROFILE / "brain.py"), "backup", "verify",
           str(folder), "--json"]
    run = subprocess.run(cli, capture_output=True, text=True)
    assert run.returncode == 3, run.stderr
    assert json.loads(run.stdout)["error_code"] == "UNSAFE_PATH"


def test_regular_content_dedup_is_not_mistaken_for_hardlink(tmp_path):
    folder = make_snapshot(tmp_path)
    assert verify_backup(folder)["capture_count"] == 3
    restored = tmp_path / "restore"
    assert restore_backup(folder, restored)["object_count"] == 2
    assert all((folder / "data" / json.loads(
        (folder / "manifest.json").read_bytes())["files"][i]["path"]).stat().st_nlink == 1
        for i in range(3))
