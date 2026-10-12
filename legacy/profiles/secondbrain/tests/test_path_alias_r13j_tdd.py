"""R13-J RED: lexical parent traversal must never defeat backup root isolation.

All fixtures are synthetic. Parent-components are rejected rather than
normalized after validation, on both POSIX and Windows.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))
from brain_core.backup import BackupFailure, create_backup, verify_backup, restore_backup
from test_backup_r12_tdd import fixture


def test_snapshot_destination_parent_alias_inside_source_rejected_without_mutation(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    hop = tmp_path / "hop"
    hop.mkdir()
    aliased = hop / ".." / root.name / "unexpected"
    assert aliased.resolve() == root / "unexpected"
    with pytest.raises(BackupFailure, match="UNSAFE_DESTINATION"):
        create_backup(root, aliased)
    assert not (root / "unexpected").exists()


def test_snapshot_destination_parent_alias_to_source_ancestor_rejected(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    hop = tmp_path / "hop"
    hop.mkdir()
    assert (hop / "..").resolve() == tmp_path
    with pytest.raises(BackupFailure, match="UNSAFE_DESTINATION"):
        create_backup(root, hop / "..")
    assert not (tmp_path / "manifest.json").exists()


def test_restore_destination_parent_alias_inside_snapshot_rejected_without_mutation(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    snapshot = tmp_path / "snapshot"
    create_backup(root, snapshot)
    hop = tmp_path / "hop"
    hop.mkdir()
    aliased = hop / ".." / snapshot.name / "unwanted-restored-root"
    with pytest.raises(BackupFailure, match="UNSAFE_DESTINATION"):
        restore_backup(snapshot, aliased)
    assert not (snapshot / "unwanted-restored-root").exists()
    assert verify_backup(snapshot)["status"].startswith("LOCAL_SNAPSHOT_VERIFIED")


def test_source_root_parent_alias_rejected_before_creating_snapshot(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    hop = tmp_path / "hop"
    hop.mkdir()
    source_alias = hop / ".." / root.name
    snapshot = tmp_path / "no-snapshot"
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        create_backup(source_alias, snapshot)
    assert not snapshot.exists()


def test_snapshot_parent_alias_rejected_before_restore_destination(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    snapshot = tmp_path / "snapshot"
    create_backup(root, snapshot)
    hop = tmp_path / "hop"
    hop.mkdir()
    snapshot_alias = hop / ".." / snapshot.name
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        verify_backup(snapshot_alias)
    target = tmp_path / "no-restored-root"
    with pytest.raises(BackupFailure, match="UNSAFE_PATH"):
        restore_backup(snapshot_alias, target)
    assert not target.exists()


def test_ordinary_clean_sibling_paths_still_work(tmp_path):
    root, _, _ = fixture(tmp_path, n=1)
    snapshot = tmp_path / "sibling snapshot"
    created = create_backup(root, snapshot)
    assert verify_backup(snapshot)["manifest_sha256"] == created["manifest_sha256"]
    restored = restore_backup(snapshot, tmp_path / "clean restore")
    assert restored["status"] == "LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED"
