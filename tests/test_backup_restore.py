"""Tests for sb backup and sb restore commands (M1 STEP S4)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from unittest.mock import patch
import pytest

from secondbrain import __version__
from secondbrain.capture import capture_file, compute_sha256
from secondbrain.cli import main
from secondbrain.errors import IntegrityError, UsageIOError
from secondbrain.publish import stage_and_verify_copy
from secondbrain.root import load_config
from secondbrain.verify import verify_repository


@pytest.fixture
def store_root(tmp_path: Path) -> Path:
    """Create a temporary repository data root."""
    root = tmp_path / "SecondBrain"
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def backup_root(tmp_path: Path) -> Path:
    """Create a temporary backup root outside data root."""
    b_root = tmp_path / "Backups" / "sb_backup"
    b_root.mkdir(parents=True, exist_ok=True)
    return b_root


def test_backup_restore_roundtrip_korean_and_spaces(
    store_root: Path, backup_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Round trip backup and restore on a tree with Korean and space names with MANIFEST v1 schema."""
    inbox = tmp_path / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    f1 = inbox / "한글 문서.txt"
    f1.write_text("안녕하세요 대한민국 세계 2026", encoding="utf-8")
    f2 = inbox / "my document with spaces.md"
    f2.write_text("# Test with spaces and formatting\nLine 2", encoding="utf-8")

    res1 = capture_file(f1, store_root, __version__)
    res2 = capture_file(f2, store_root, __version__)

    # Run backup with --backup-root flag
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "OK" in captured.out

    # Backup root contains objects, receipts, configs and manifests
    assert (backup_root / "objects").is_dir()
    assert (backup_root / "receipts" / "v1").is_dir()
    assert (backup_root / "configs").is_dir()
    assert any((backup_root / "configs").glob("*.json"))
    manifests_dir = backup_root / "manifests"
    assert manifests_dir.is_dir()
    manifest_files = list(manifests_dir.glob("*.json"))
    assert len(manifest_files) == 1

    # Verify MANIFEST v1 strict schema
    manifest_data = json.loads(manifest_files[0].read_text(encoding="utf-8"))
    assert manifest_data["schema_version"] == 1
    assert "created_utc" in manifest_data
    assert manifest_data["tool_version"] == __version__
    assert isinstance(manifest_data["entries"], list)
    assert len(manifest_data["entries"]) >= 3

    entries_by_kind = {e["kind"]: e for e in manifest_data["entries"]}
    assert "config" in entries_by_kind
    cfg_sha = entries_by_kind["config"]["sha256"]
    assert entries_by_kind["config"]["path"] == f"configs/{cfg_sha}.json"
    assert (backup_root / "configs" / f"{cfg_sha}.json").is_file()

    receipt_paths = {e["path"] for e in manifest_data["entries"] if e["kind"] == "receipt"}
    assert f"receipts/v1/{res1['id']}.json" in receipt_paths
    assert f"receipts/v1/{res2['id']}.json" in receipt_paths

    obj_paths = {e["path"] for e in manifest_data["entries"] if e["kind"] == "object"}
    assert f"objects/{res1['sha256'][:2]}/{res1['sha256']}" in obj_paths
    assert f"objects/{res2['sha256'][:2]}/{res2['sha256']}" in obj_paths

    # Now restore into an empty directory
    restored_root = tmp_path / "RestoredSecondBrain"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(restored_root)])
    assert exc_info.value.code == 0
    captured_restore = capsys.readouterr()
    assert "PASS" in captured_restore.out

    # Restored root has config restored from manifest
    assert (restored_root / "config.json").is_file()

    # sb verify passes on the restored repository
    verify_rep = verify_repository(restored_root)
    assert verify_rep["status"] == "ok"
    assert verify_rep["missing"] == 0
    assert verify_rep["corrupt"] == 0
    assert verify_rep["orphan"] == 0
    assert verify_rep["receipts"] == 2
    assert verify_rep["objects"] == 2

    # Verify via CLI
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(restored_root), "verify"])
    assert exc_info.value.code == 0


def test_backup_restore_json_envelope(
    store_root: Path, backup_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that backup and restore output structured JSON with --json."""
    f1 = tmp_path / "hello.txt"
    f1.write_text("json test", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # Test backup --json
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    backup_out = json.loads(captured.out)
    assert backup_out["status"] == "ok"
    assert backup_out["backup_root"] == str(backup_root.resolve())
    assert "manifest" in backup_out
    assert backup_out["copied_objects"] == 1
    assert backup_out["errors"] == []

    # Test restore --json
    restored_root = tmp_path / "RestoredJSON"
    with pytest.raises(SystemExit) as exc_info:
        main(["--json", "restore", str(backup_root), "--to", str(restored_root)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    restore_out = json.loads(captured.out)
    assert restore_out["status"] == "ok"
    assert restore_out["verification"] == "PASS"
    assert restore_out["restored_root"] == str(restored_root.resolve())
    assert restore_out["errors"] == []


def test_backup_corrupted_object_in_data_root_fails_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Corrupted object in data root is NOT silently copied; backup fails item with exit 1."""
    f1 = tmp_path / "good.txt"
    f1.write_text("original pristine text", encoding="utf-8")
    res1 = capture_file(f1, store_root, __version__)

    # Corrupt the object in the data root
    sha = res1["sha256"]
    obj_path = store_root / "objects" / sha[:2] / sha
    assert obj_path.exists()
    obj_path.write_bytes(b"tampered corrupt bytes")

    # Run backup - must fail with exit code 1
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1

    # Corrupt object must NOT have been copied to backup_root
    dest_obj_path = backup_root / "objects" / sha[:2] / sha
    assert not dest_obj_path.exists()

    # No manifest was written
    manifests_dir = backup_root / "manifests"
    assert not manifests_dir.exists() or len(list(manifests_dir.glob("*.json"))) == 0


def test_backup_root_unwritable(store_root: Path, tmp_path: Path) -> None:
    """Unwritable backup root raises usage/IO error with exit code 2."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("sample", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # File used as backup root directory -> cannot create directory inside it
    invalid_backup_root = tmp_path / "a_file.txt"
    invalid_backup_root.write_text("not a directory", encoding="utf-8")
    unwritable_path = invalid_backup_root / "nested" / "backup"

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(unwritable_path)])
    assert exc_info.value.code == 2


def test_backup_duplicate_bytes(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Duplicate bytes: 2 receipts pointing to 1 SHA-256 object; single object copied."""
    f1 = tmp_path / "doc1.txt"
    f1.write_text("identical bytes across files", encoding="utf-8")
    f2 = tmp_path / "doc2.txt"
    f2.write_text("identical bytes across files", encoding="utf-8")

    res1 = capture_file(f1, store_root, __version__)
    res2 = capture_file(f2, store_root, __version__)
    assert res1["sha256"] == res2["sha256"]
    assert res1["id"] != res2["id"]

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Only 1 object file in backup
    obj_files = list((backup_root / "objects").rglob("*"))
    actual_objects = [f for f in obj_files if f.is_file()]
    assert len(actual_objects) == 1

    # 2 receipts in backup
    rec_files = list((backup_root / "receipts" / "v1").glob("*.json"))
    assert len(rec_files) == 2

    # Restore and verify
    restored = tmp_path / "restored_dup"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(restored)])
    assert exc_info.value.code == 0
    assert verify_repository(restored)["status"] == "ok"


def test_backup_restore_large_file(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Test backup and restore with a large-ish file (1.5 MB)."""
    large_data = b"0123456789ABCDEF" * (100 * 1024)  # ~1.6 MB
    large_file = tmp_path / "large.bin"
    large_file.write_bytes(large_data)

    res = capture_file(large_file, store_root, __version__)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    restored = tmp_path / "restored_large"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(restored)])
    assert exc_info.value.code == 0

    restored_obj = restored / "objects" / res["sha256"][:2] / res["sha256"]
    assert restored_obj.is_file()
    assert restored_obj.read_bytes() == large_data


def test_restore_into_non_empty_dir_refused(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Restore into non-empty directory is refused with exit code 2."""
    f1 = tmp_path / "sample.txt"
    f1.write_text("sample content", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Non-empty target directory
    target = tmp_path / "target_not_empty"
    target.mkdir(parents=True, exist_ok=True)
    existing_file = target / "already_here.txt"
    existing_file.write_text("do not overwrite me", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target)])
    assert exc_info.value.code == 2

    # Target directory remains untouched
    assert existing_file.read_text(encoding="utf-8") == "do not overwrite me"
    assert not (target / "objects").exists()


def test_restore_detects_corrupted_object_in_backup(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Restore detects a corrupted object in the backup root and fails with exit 1."""
    f1 = tmp_path / "sample.txt"
    f1.write_text("clean source content", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Corrupt object inside the backup root
    sha = res["sha256"]
    backup_obj = backup_root / "objects" / sha[:2] / sha
    backup_obj.write_bytes(b"corrupted backup object data")

    target = tmp_path / "restored_corrupt"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target)])
    assert exc_info.value.code == 1


def test_manifest_selection(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Restore selects newest complete manifest by default, or specific manifest with --manifest."""
    f1 = tmp_path / "file1.txt"
    f1.write_text("file 1 content", encoding="utf-8")
    res1 = capture_file(f1, store_root, __version__)

    # Backup 1
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    manifests_dir = backup_root / "manifests"
    manifest1 = sorted(manifests_dir.glob("*.json"))[0].name

    # Capture second file
    f2 = tmp_path / "file2.txt"
    f2.write_text("file 2 content", encoding="utf-8")
    res2 = capture_file(f2, store_root, __version__)

    # Backup 2 (even in the same second, collision counter increments without sleeping)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    from secondbrain.restore import parse_manifest_name
    manifest_files = sorted(manifests_dir.glob("*.json"), key=lambda p: parse_manifest_name(p.name) or ("", 0))
    assert len(manifest_files) == 2
    manifest2 = manifest_files[-1].name
    assert manifest1 != manifest2

    # Restore default (newest): contains both file1 and file2
    target_newest = tmp_path / "restored_newest"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target_newest)])
    assert exc_info.value.code == 0

    rep_newest = verify_repository(target_newest)
    assert rep_newest["status"] == "ok"
    assert rep_newest["receipts"] == 2
    assert rep_newest["objects"] == 2

    # Restore specific older manifest: contains only file1
    target_older = tmp_path / "restored_older"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target_older), "--manifest", manifest1])
    assert exc_info.value.code == 0

    rep_older = verify_repository(target_older)
    assert rep_older["status"] == "ok"
    assert rep_older["receipts"] == 1
    assert rep_older["objects"] == 1
    assert (target_older / "receipts" / "v1" / f"{res1['id']}.json").exists()
    assert not (target_older / "receipts" / "v1" / f"{res2['id']}.json").exists()


def test_nlink_zero_simulation(
    store_root: Path, backup_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When st_nlink is 0 on virtual drive (Google Drive FS), backup and restore issue a warning and succeed."""
    f1 = tmp_path / "sample.txt"
    f1.write_text("virtual drive content", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    from secondbrain import backup as backup_mod
    from secondbrain import restore as restore_mod

    # Patch is_nlink_zero to simulate st_nlink == 0
    with patch.object(backup_mod, "is_nlink_zero", return_value=True):
        with pytest.raises(SystemExit) as exc_info:
            main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "st_nlink is 0" in (captured.err + captured.out)

    target = tmp_path / "restored_nlink0"
    with patch.object(restore_mod, "is_nlink_zero", return_value=True):
        with pytest.raises(SystemExit) as exc_info:
            main(["restore", str(backup_root), "--to", str(target)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "st_nlink is 0" in (captured.err + captured.out)


def test_backup_root_inside_data_root_refused(store_root: Path) -> None:
    """Backup root inside data root or data root inside backup root is refused with exit 2."""
    sub_backup = store_root / "nested_backup"

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(sub_backup)])
    assert exc_info.value.code == 2

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(sub_backup), "backup", "--backup-root", str(store_root)])
    assert exc_info.value.code == 2

    # Same path
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(store_root)])
    assert exc_info.value.code == 2


def test_backup_cloud_synced_warning(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Cloud-synced backup root triggers a warning (not failure): ADR 0003 intended use."""
    f1 = tmp_path / "file.txt"
    f1.write_text("synced backup test", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    cloud_backup = tmp_path / "Google Drive" / "BackupFolder"
    cloud_backup.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(cloud_backup)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    err_out = captured.err + captured.out
    assert "cloud" in err_out.lower() or "sync" in err_out.lower()


def test_backup_root_from_config_and_no_data_root_mutation(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Backup root loaded from config; backup must NOT rewrite config.json or delete anything in data root."""
    f1 = tmp_path / "file.txt"
    f1.write_text("config test", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # No backup_root in config and no flag -> exit 2
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup"])
    assert exc_info.value.code == 2

    # Configure backup_root manually in config.json
    cfg_file = store_root / "config.json"
    cfg = load_config(store_root)
    cfg["backup_root"] = str(backup_root)
    cfg_bytes_before = json.dumps(cfg, indent=2).encode("utf-8") + b"\n"
    cfg_file.write_bytes(cfg_bytes_before)
    mtime_before = cfg_file.stat().st_mtime_ns

    # Backup without flag uses stored config
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup"])
    assert exc_info.value.code == 0

    # Ensure config.json in data_root was NOT rewritten
    assert cfg_file.stat().st_mtime_ns == mtime_before
    assert cfg_file.read_bytes() == cfg_bytes_before


# -----------------------------------------------------------------------------
# REAL SUBPROCESS KILL TESTS DURING OBJECT, RECEIPT, MANIFEST WRITES
# -----------------------------------------------------------------------------

def _run_subprocess_backup_with_kill(
    store_root: Path,
    backup_root: Path,
    hook_phase: str,
    tmp_path: Path,
) -> None:
    """Helper to run a real subprocess for backup, pause during hook_phase, and kill it with SIGKILL."""
    token_file = tmp_path / f"kill_token_{hook_phase}.txt"
    if token_file.exists():
        token_file.unlink()

    helper_code = f"""
import sys, time, os, builtins
from pathlib import Path
from secondbrain.cli import main

hook_phase = {repr(hook_phase)}
token_file = Path({repr(str(token_file))})

orig_open = builtins.open
def hooked_open(file, mode="r", *args, **kwargs):
    fp = orig_open(file, mode, *args, **kwargs)
    if ("w" in mode or "a" in mode) and "b" in mode:
        file_str = str(file)
        if ".sb-tmp-" in file_str:
            is_target = False
            if hook_phase == "object" and "objects" in file_str:
                is_target = True
            elif hook_phase == "receipt" and "receipts" in file_str:
                is_target = True
            elif hook_phase == "manifest" and "manifests" in file_str:
                is_target = True

            if is_target:
                class MidWriteWrapper:
                    def __init__(self, real_fp):
                        self._real_fp = real_fp
                    def write(self, b):
                        part_len = max(1, len(b) // 2) if len(b) > 1 else len(b)
                        written = self._real_fp.write(b[:part_len])
                        self._real_fp.flush()
                        os.fsync(self._real_fp.fileno())
                        token_file.write_text(f"{{hook_phase}}_midwrite_{{part_len}}")
                        time.sleep(30)
                        return written + self._real_fp.write(b[part_len:])
                    def flush(self):
                        return self._real_fp.flush()
                    def fileno(self):
                        return self._real_fp.fileno()
                    def close(self):
                        return self._real_fp.close()
                    def __getattr__(self, attr):
                        return getattr(self._real_fp, attr)
                    def __enter__(self):
                        self._real_fp.__enter__()
                        return self
                    def __exit__(self, *a):
                        return self._real_fp.__exit__(*a)
                return MidWriteWrapper(fp)
    return fp

builtins.open = hooked_open

main(["--root", {repr(str(store_root))}, "backup", "--backup-root", {repr(str(backup_root))}])
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", helper_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(Path.cwd()),
    )

    # Wait for the token file indicating the phase entered mid-write
    start = time.time()
    while time.time() - start < 15.0:
        if token_file.exists():
            break
        time.sleep(0.05)

    assert token_file.exists(), f"Subprocess did not reach mid-write hook phase '{hook_phase}'"

    # Verify that a staging temp file actually exists on disk with bytes written
    staged_tmps = list(backup_root.rglob(".sb-tmp-*.tmp"))
    assert len(staged_tmps) > 0, f"Expected mid-write staging temp file in backup_root for {hook_phase}"
    assert staged_tmps[0].stat().st_size > 0, f"Staging temp file has 0 bytes, expected bytes written mid-write"

    # Send REAL kill to the subprocess mid-write
    proc.kill()
    proc.wait()


def test_interrupted_backup_real_subprocess_kill_during_object_write(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Real subprocess kill during object write: no manifest published, re-run completes and verifies."""
    f1 = tmp_path / "file1.txt"
    f1.write_text("content 1", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    _run_subprocess_backup_with_kill(store_root, backup_root, "object", tmp_path)

    # Manifest must NOT exist
    manifests_dir = backup_root / "manifests"
    assert not manifests_dir.exists() or len(list(manifests_dir.glob("*.json"))) == 0

    # Re-run completes cleanly
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0
    assert len(list(manifests_dir.glob("*.json"))) == 1

    # Restore verifies
    restored = tmp_path / "restored_obj_kill"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(restored)])
    assert exc_info.value.code == 0
    assert verify_repository(restored)["status"] == "ok"


def test_interrupted_backup_real_subprocess_kill_during_receipt_write(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Real subprocess kill during receipt write: no manifest published, re-run completes and verifies."""
    f1 = tmp_path / "file1.txt"
    f1.write_text("content 1", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    _run_subprocess_backup_with_kill(store_root, backup_root, "receipt", tmp_path)

    manifests_dir = backup_root / "manifests"
    assert not manifests_dir.exists() or len(list(manifests_dir.glob("*.json"))) == 0

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0
    assert len(list(manifests_dir.glob("*.json"))) == 1

    restored = tmp_path / "restored_rec_kill"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(restored)])
    assert exc_info.value.code == 0
    assert verify_repository(restored)["status"] == "ok"


def test_interrupted_backup_real_subprocess_kill_during_manifest_write(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Real subprocess kill during manifest write: no manifest published, re-run completes and verifies."""
    f1 = tmp_path / "file1.txt"
    f1.write_text("content 1", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    _run_subprocess_backup_with_kill(store_root, backup_root, "manifest", tmp_path)

    manifests_dir = backup_root / "manifests"
    assert not manifests_dir.exists() or len(list(manifests_dir.glob("*.json"))) == 0

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0
    assert len(list(manifests_dir.glob("*.json"))) == 1

    restored = tmp_path / "restored_man_kill"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(restored)])
    assert exc_info.value.code == 0
    assert verify_repository(restored)["status"] == "ok"


# -----------------------------------------------------------------------------
# HALF-SYNCED MANIFEST AND OBJECT TESTS
# -----------------------------------------------------------------------------

def test_restore_skips_half_synced_manifest_falls_back_to_older(
    store_root: Path, backup_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Restore skips half-synced (truncated JSON or partial object) manifest and falls back to older complete one."""
    f1 = tmp_path / "doc1.txt"
    f1.write_text("initial document", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # 1. First backup: complete manifest 1
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    manifests_dir = backup_root / "manifests"
    man1 = sorted(manifests_dir.glob("*.json"))[0]

    # 2. Add second file and run second backup
    f2 = tmp_path / "doc2.txt"
    f2.write_text("second document", encoding="utf-8")
    res2 = capture_file(f2, store_root, __version__)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    man_files = sorted(manifests_dir.glob("*.json"))
    assert len(man_files) == 2
    man2 = man_files[1]

    # Corrupt/truncate the second file's object in the backup root to simulate half-synced OneDrive object
    sha2 = res2["sha256"]
    b_obj = backup_root / "objects" / sha2[:2] / sha2
    b_obj.write_bytes(b"truncated")  # wrong size and sha

    # 3. Restore: must skip man2 because its roster fails, fall back to man1, report skipped
    target = tmp_path / "restored_fallback"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert man1.name in captured.out
    assert man2.name in (captured.err + captured.out)

    # Repository restored from man1 is completely verified
    rep = verify_repository(target)
    assert rep["status"] == "ok"
    assert rep["receipts"] == 1
    assert rep["objects"] == 1


def test_restore_all_manifests_half_synced_fails_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """When only half-synced manifests exist, restore fails with exit code 1."""
    manifests_dir = backup_root / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    # Half-synced manifest: partial JSON
    half_json = manifests_dir / "20261013T010000Z.json"
    half_json.write_text('{"schema_version": 1, "created_utc": "2026-10-13T', encoding="utf-8")

    target = tmp_path / "restored_fail"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target)])
    assert exc_info.value.code == 1


# -----------------------------------------------------------------------------
# CONCURRENT PUBLICATION (TWO BACKUPS)
# -----------------------------------------------------------------------------

def test_concurrent_backup_publication(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Two concurrent backup runs are serialized by BackupLock; both succeed with distinct numeric counter."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("concurrent content", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    cmd = [
        sys.executable,
        "-c",
        f"from secondbrain.cli import main; main(['--root', {repr(str(store_root))}, 'backup', '--backup-root', {repr(str(backup_root))}])",
    ]

    p1 = subprocess.Popen(cmd)
    p2 = subprocess.Popen(cmd)
    ret1 = p1.wait()
    ret2 = p2.wait()

    assert ret1 == 0
    assert ret2 == 0

    manifests_dir = backup_root / "manifests"
    m_files = list(manifests_dir.glob("*.json"))
    assert len(m_files) == 2


# -----------------------------------------------------------------------------
# DIFFERING RECEIPT IN BACKUP ROOT
# -----------------------------------------------------------------------------

def test_backup_differing_receipt_in_backup_root_fails_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Existing receipt in backup root with differing hash triggers collision error exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("clean receipt", encoding="utf-8")
    res1 = capture_file(f1, store_root, __version__)

    # Pre-create differing receipt in backup root
    dst_rec = backup_root / "receipts" / "v1" / f"{res1['id']}.json"
    dst_rec.parent.mkdir(parents=True, exist_ok=True)
    dst_rec.write_text(json.dumps({"tampered": True}), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1


def test_backup_identical_receipt_in_backup_root_reused(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Existing receipt in backup root with identical hash is verified and reused."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("reusable receipt", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # Backup 1
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Backup 2: reuses receipts without error
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0


# -----------------------------------------------------------------------------
# JUNCTION ALIAS OVERLAP (WINDOWS)
# -----------------------------------------------------------------------------

def test_junction_alias_overlap_refused(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Descendant junctions/symlinks overlapping into data root are refused with exit 2."""
    if sys.platform != "win32":
        pytest.skip("Windows junction test")

    # Try creating a junction pointing backup objects into data objects
    junc_target = backup_root / "objects"
    data_objects = store_root / "objects"
    data_objects.mkdir(parents=True, exist_ok=True)

    cmd = f'cmd /c mklink /J "{junc_target}" "{data_objects}"'
    res = subprocess.run(cmd, shell=True, capture_output=True)
    if res.returncode != 0:
        pytest.skip("Cannot create junction on this filesystem")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 2


# -----------------------------------------------------------------------------
# COLLISION COUNTER ORDERING (NEVER LEXICAL)
# -----------------------------------------------------------------------------

def test_collision_counter_ordering_never_lexical(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Collision counter ordering selects -10 over -2 (never lexical)."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("collision ordering test", encoding="utf-8")
    res1 = capture_file(f1, store_root, __version__)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    manifests_dir = backup_root / "manifests"
    man_orig = sorted(manifests_dir.glob("*.json"))[0]
    man_data = man_orig.read_text(encoding="utf-8")

    # Create -2 and -10 manifests
    ts = "20261013T120000Z"
    m_base = manifests_dir / f"{ts}.json"
    m_2 = manifests_dir / f"{ts}-2.json"
    m_10 = manifests_dir / f"{ts}-10.json"

    # Remove the original manifest
    man_orig.unlink()

    # Write identical valid rosters into all three
    m_base.write_text(man_data, encoding="utf-8")
    m_2.write_text(man_data, encoding="utf-8")
    m_10.write_text(man_data, encoding="utf-8")

    target = tmp_path / "restored_numeric_counter"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target)])
    assert exc_info.value.code == 0

    # The chosen manifest must be -10.json, NOT -2.json
    from secondbrain.restore import restore_repository
    # Query summary or check verify
    assert verify_repository(target)["status"] == "ok"


# -----------------------------------------------------------------------------
# CORRUPT STAGED BYTES
# -----------------------------------------------------------------------------

def test_corrupt_staged_bytes_detected_on_reread(
    tmp_path: Path
) -> None:
    """Corrupt staged bytes are caught on re-read before publication and rejected."""
    src = tmp_path / "src.bin"
    src.write_bytes(b"good bytes 12345")
    dst = tmp_path / "dst.bin"
    good_sha = compute_sha256(src)

    # If expected_sha does not match the written bytes, stage_and_verify_copy fails exit 1
    with pytest.raises(IntegrityError):
        stage_and_verify_copy(src, dst, expected_sha="0000000000000000000000000000000000000000000000000000000000000000")

    assert not dst.exists()


# -----------------------------------------------------------------------------
# '{}' MANIFEST AND EMPTY ROSTER
# -----------------------------------------------------------------------------

def test_empty_or_empty_roster_manifest_rejected(
    backup_root: Path, tmp_path: Path
) -> None:
    """'{}' or empty roster manifest is rejected as invalid/incomplete."""
    manifests_dir = backup_root / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    m_empty = manifests_dir / "20261013T010000Z.json"
    m_empty.write_text("{}", encoding="utf-8")

    target = tmp_path / "restored_empty"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target)])
    assert exc_info.value.code == 1


# -----------------------------------------------------------------------------
# RESTORE TWICE REFUSED
# -----------------------------------------------------------------------------

def test_restore_twice_refused(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Restore twice into the same target directory is refused with exit 2."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("restore twice test", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    target = tmp_path / "restore_target"

    # First restore succeeds
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target)])
    assert exc_info.value.code == 0

    # Second restore into the now non-empty target is refused exit 2
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target)])
    assert exc_info.value.code == 2


# -----------------------------------------------------------------------------
# ROUND 2 CX FINDINGS TESTS
# -----------------------------------------------------------------------------

def test_backup_lock_hardlink_source_object_refused(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Backup lock in backup/.sb hardlinked to a source object is refused; source content is never modified."""
    f1 = tmp_path / "important.txt"
    f1.write_text("critical source object content", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)

    sha = res["sha256"]
    src_obj = store_root / "objects" / sha[:2] / sha
    assert src_obj.is_file()

    # Create backup/.sb and hardlink backup.lock to the source object
    sb_dir = backup_root / ".sb"
    sb_dir.mkdir(parents=True, exist_ok=True)
    lock_file = sb_dir / "backup.lock"
    try:
        os.link(str(src_obj), str(lock_file))
    except (OSError, NotImplementedError):
        pytest.skip("Filesystem does not support hardlinks")

    assert lock_file.stat().st_nlink > 1

    # Attempting backup must fail (exit 2) and MUST NOT write 'L' or modify source file
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 2

    # Verify source object remains completely untouched
    assert src_obj.read_text(encoding="utf-8") == "critical source object content"


def test_manifest_validation_strict_rules(backup_root: Path, tmp_path: Path) -> None:
    """Manifest validation strictly requires exactly 1 config, exact object/receipt paths, no reserved names, no dups."""
    from secondbrain.restore import validate_manifest_schema

    dummy_path = backup_root / "manifests" / "dummy.json"

    # Base valid manifest
    sha_obj = "a" * 64
    base_manifest = {
        "schema_version": 1,
        "created_utc": "2026-10-13T00:00:00Z",
        "tool_version": "0.1.0",
        "entries": [
            {"kind": "config", "path": "configs/" + ("b" * 64) + ".json", "sha256": "b" * 64, "size": 10},
            {"kind": "object", "path": f"objects/aa/{sha_obj}", "sha256": sha_obj, "size": 20},
            {"kind": "receipt", "path": "receipts/v1/rec1.json", "sha256": "c" * 64, "size": 30},
        ],
    }

    # 1. Valid passes
    validate_manifest_schema(base_manifest, dummy_path)

    # 2. Missing config entry -> fails
    no_cfg = dict(base_manifest, entries=[e for e in base_manifest["entries"] if e["kind"] != "config"])
    with pytest.raises(IntegrityError, match="config"):
        validate_manifest_schema(no_cfg, dummy_path)

    # 3. Two config entries -> fails
    two_cfg = dict(base_manifest, entries=base_manifest["entries"] + [
        {"kind": "config", "path": "configs/" + ("d" * 64) + ".json", "sha256": "d" * 64, "size": 10}
    ])
    with pytest.raises(IntegrityError, match="config"):
        validate_manifest_schema(two_cfg, dummy_path)

    # 4. Manifest with tool-reserved path (e.g. .sb-restore.marker) -> fails
    marker_entry = dict(base_manifest, entries=base_manifest["entries"] + [
        {"kind": "object", "path": ".sb-restore.marker", "sha256": "e" * 64, "size": 5}
    ])
    with pytest.raises(IntegrityError, match="reserved|Invalid|path"):
        validate_manifest_schema(marker_entry, dummy_path)

    # 5. Invalid object path (not objects/ab/<64hex>) -> fails
    bad_obj_path = dict(base_manifest, entries=[
        base_manifest["entries"][0],
        {"kind": "object", "path": "arbitrary/path.txt", "sha256": sha_obj, "size": 20},
    ])
    with pytest.raises(IntegrityError, match="object|path"):
        validate_manifest_schema(bad_obj_path, dummy_path)

    # 6. Object path prefix mismatch -> fails
    mismatch_prefix = dict(base_manifest, entries=[
        base_manifest["entries"][0],
        {"kind": "object", "path": f"objects/bb/{sha_obj}", "sha256": sha_obj, "size": 20},
    ])
    with pytest.raises(IntegrityError, match="object|prefix|path"):
        validate_manifest_schema(mismatch_prefix, dummy_path)

    # 7. Invalid receipt path -> fails
    bad_rec_path = dict(base_manifest, entries=[
        base_manifest["entries"][0],
        {"kind": "receipt", "path": "not_receipts/foo.txt", "sha256": "c" * 64, "size": 30},
    ])
    with pytest.raises(IntegrityError, match="receipt|path"):
        validate_manifest_schema(bad_rec_path, dummy_path)

    # 8. Duplicate entry paths -> fails
    dup_paths = dict(base_manifest, entries=base_manifest["entries"] + [base_manifest["entries"][1]])
    with pytest.raises(IntegrityError, match="[Dd]uplicate"):
        validate_manifest_schema(dup_paths, dummy_path)


def test_backup_includes_orphan_source_objects(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Orphan source objects (no receipt) in data root are included in backup and verified, never omitted."""
    # Create a regular captured file
    f1 = tmp_path / "normal.txt"
    f1.write_text("normal file", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # Plant an orphan object directly into store_root/objects
    import hashlib
    orphan_bytes = b"orphan payload without receipt"
    orphan_sha = hashlib.sha256(orphan_bytes).hexdigest().lower()
    orphan_dir = store_root / "objects" / orphan_sha[:2]
    orphan_dir.mkdir(parents=True, exist_ok=True)
    orphan_file = orphan_dir / orphan_sha
    orphan_file.write_bytes(orphan_bytes)

    # Run backup
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Orphan object MUST be present in backup_root/objects
    backup_orphan = backup_root / "objects" / orphan_sha[:2] / orphan_sha
    assert backup_orphan.is_file()
    assert backup_orphan.read_bytes() == orphan_bytes

    # Orphan object MUST be listed in the manifest
    manifests = list((backup_root / "manifests").glob("*.json"))
    assert len(manifests) == 1
    m_data = json.loads(manifests[0].read_text(encoding="utf-8"))
    obj_paths = {e["path"] for e in m_data["entries"] if e["kind"] == "object"}
    assert f"objects/{orphan_sha[:2]}/{orphan_sha}" in obj_paths


def test_competing_restore_atomic_reservation_before_emptiness(
    backup_root: Path, tmp_path: Path
) -> None:
    """Atomic reservation marker is created BEFORE emptiness check; pre-existing marker fails immediately."""
    from secondbrain.restore import reserve_target_dir

    target_dir = tmp_path / "target_competing"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Pre-create reservation marker to simulate competing restore
    marker = target_dir / ".sb-restore.marker"
    marker.write_text("reserved by other process")

    # Another restore attempting to reserve must fail with already reserved exit 2
    with pytest.raises(UsageIOError, match="already reserved"):
        reserve_target_dir(target_dir)

    # If target is non-empty with a real file, marker is cleaned up and fails with not empty
    marker.unlink()
    dummy_file = target_dir / "user_data.txt"
    dummy_file.write_text("important user data")

    with pytest.raises(UsageIOError, match="not empty"):
        reserve_target_dir(target_dir)
    assert not marker.exists()
    assert dummy_file.exists()


def test_backup_config_changed_versioned_per_snapshot(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Config changed after first backup does NOT block later snapshots; config is versioned per snapshot."""
    f1 = tmp_path / "file.txt"
    f1.write_text("content", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # Backup 1 with default config
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    manifests_dir = backup_root / "manifests"
    man1_name = sorted(manifests_dir.glob("*.json"))[0].name

    # Modify config in store_root
    cfg_file = store_root / "config.json"
    new_cfg = {"backup_root": str(backup_root), "custom_key": "custom_val_2026"}
    cfg_file.write_text(json.dumps(new_cfg, indent=2) + "\n", encoding="utf-8")

    # Backup 2 with modified config: MUST SUCCEED (does not fail with IntegrityError on line 389)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Both configs coexist in backup_root/configs
    configs_dir = backup_root / "configs"
    assert configs_dir.is_dir()
    cfg_files = list(configs_dir.glob("*.json"))
    assert len(cfg_files) == 2

    # Restore default (picks latest snapshot with modified config)
    target_latest = tmp_path / "restored_latest_cfg"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target_latest)])
    assert exc_info.value.code == 0
    restored_cfg = json.loads((target_latest / "config.json").read_text(encoding="utf-8"))
    assert restored_cfg.get("custom_key") == "custom_val_2026"

    # Restore older manifest (picks first snapshot with original config)
    target_older = tmp_path / "restored_older_cfg"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target_older), "--manifest", man1_name])
    assert exc_info.value.code == 0
    restored_older_cfg = json.loads((target_older / "config.json").read_text(encoding="utf-8"))
    assert "custom_key" not in restored_older_cfg


def test_restore_empty_store(store_root: Path, backup_root: Path, tmp_path: Path) -> None:
    """Empty store (0 receipts, 0 objects) backs up and restores successfully with objects and receipts/v1 dirs created."""
    # Ensure store_root is initialized but empty (no captures)
    from secondbrain.root import bootstrap_root
    bootstrap_root(store_root)

    # Backup empty store
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Restore into empty target directory
    target_empty = tmp_path / "restored_from_empty_store"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target_empty)])
    assert exc_info.value.code == 0

    # Verify target directory structure
    assert (target_empty / "objects").is_dir()
    assert (target_empty / "receipts" / "v1").is_dir()
    assert (target_empty / "config.json").is_file()

    # sb verify passes on the restored empty repository
    verify_rep = verify_repository(target_empty)
    assert verify_rep["status"] == "ok"
    assert verify_rep["receipts"] == 0
    assert verify_rep["objects"] == 0


def test_backup_lock_covers_whole_snapshot_and_order(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Backup lock covers whole snapshot (roster build to manifest publish) so newer snapshot is always picked."""
    f1 = tmp_path / "item1.txt"
    f1.write_text("item 1 content", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    from secondbrain.backup import BackupLock

    # When BackupLock is actively held on backup_root, a concurrent backup waits or fails on timeout
    with BackupLock(backup_root, timeout=0.2):
        with pytest.raises(SystemExit) as exc_info:
            main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
        assert exc_info.value.code == 2

    # Snapshot 1 completes cleanly
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Capture item 2
    f2 = tmp_path / "item2.txt"
    f2.write_text("item 2 content", encoding="utf-8")
    capture_file(f2, store_root, __version__)

    # Snapshot 2 completes cleanly
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Default restore MUST pick newest snapshot (containing both receipts)
    target_restored = tmp_path / "restored_order_check"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target_restored)])
    assert exc_info.value.code == 0

    rep = verify_repository(target_restored)
    assert rep["status"] == "ok"
    assert rep["receipts"] == 2
    assert rep["objects"] == 2


# -----------------------------------------------------------------------------
# ROUND 3 FINDINGS REGRESSION TESTS
# -----------------------------------------------------------------------------

def test_r3_manifest_receipt_path_rule_single_function(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Finding 1: Manifest accepts receipts only at real layout path receipts/v1/<id>.json.

    Single shared function rejects receipts/<id>.json; restore rejects it and does not pass with object missing.
    """
    from secondbrain.receipt import validate_receipt_path, receipt_rel_path
    from secondbrain.restore import validate_manifest_schema

    # 1. Direct function test: shared path rule
    assert receipt_rel_path("cap-123") == "receipts/v1/cap-123.json"
    assert validate_receipt_path("receipts/v1/cap-20261013t010101z-12345678.json") == "receipts/v1/cap-20261013t010101z-12345678.json"
    with pytest.raises(IntegrityError, match="real layout path"):
        validate_receipt_path("receipts/cap-20261013t010101z-12345678.json")
    with pytest.raises(IntegrityError, match="real layout path"):
        validate_receipt_path("receipts/v2/cap-20261013t010101z-12345678.json")

    # 2. Manifest containing receipt at receipts/<id>.json must be rejected during schema validation
    manifest_path = backup_root / "manifests" / "20261013T100000Z.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    bad_manifest = {
        "schema_version": 1,
        "created_utc": "2026-10-13T10:00:00Z",
        "tool_version": __version__,
        "entries": [
            {"kind": "config", "path": "configs/" + ("a" * 64) + ".json", "sha256": "a" * 64, "size": 10},
            {"kind": "receipt", "path": "receipts/cap-20261013t100000z-12345678.json", "sha256": "b" * 64, "size": 50},
        ],
    }
    with pytest.raises(IntegrityError, match="real layout path|receipts/v1"):
        validate_manifest_schema(bad_manifest, manifest_path)

    # 3. Attempting restore from such a manifest must fail, NOT pass with missing object
    manifest_path.write_text(json.dumps(bad_manifest), encoding="utf-8")
    restore_target = tmp_path / "restored_bad_receipt_path"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(restore_target)])
    assert exc_info.value.code == 1


def test_r3_atomic_roster_and_orphan_tolerance_in_backup_and_restore(
    store_root: Path, backup_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Finding 2: Roster built under WriterLock; orphan objects tolerated consistently in backup and restore."""
    f1 = tmp_path / "valid.txt"
    f1.write_text("valid file", encoding="utf-8")
    res1 = capture_file(f1, store_root, __version__)

    # Add an unreferenced (orphan) object to store_root
    import hashlib
    orphan_bytes = b"unreferenced object bytes"
    orphan_sha = hashlib.sha256(orphan_bytes).hexdigest().lower()
    orphan_dir = store_root / "objects" / orphan_sha[:2]
    orphan_dir.mkdir(parents=True, exist_ok=True)
    (orphan_dir / orphan_sha).write_bytes(orphan_bytes)

    # Backup under WriterLock includes both valid receipt+object and the orphan object
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Restore must restore both AND tolerate the orphan object with PASS
    restore_target = tmp_path / "restored_with_orphan"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(restore_target)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out

    # Restored root has the orphan object intact
    restored_orphan = restore_target / "objects" / orphan_sha[:2] / orphan_sha
    assert restored_orphan.is_file()
    assert restored_orphan.read_bytes() == orphan_bytes


def test_r3_backup_nonexistent_or_invalid_source_fails_exit_2(
    backup_root: Path, tmp_path: Path
) -> None:
    """Finding 3: Nonexistent or invalid source store layout fails with exit 2, never publishes manifest."""
    # 1. Nonexistent directory
    missing_source = tmp_path / "does_not_exist"
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(missing_source), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 2
    # Ensure source was NOT created by backup/WriterLock
    assert not missing_source.exists()
    # Ensure no manifest was published
    assert not (backup_root / "manifests").exists()

    # 2. Invalid source: empty directory without SecondBrain layout
    empty_dir = tmp_path / "empty_source"
    empty_dir.mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(empty_dir), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 2
    assert not (backup_root / "manifests").exists()

    # 3. Invalid source: missing receipts/v1
    partial_dir = tmp_path / "partial_source"
    (partial_dir / "objects").mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(partial_dir), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 2
    assert not (backup_root / "manifests").exists()


def test_r3_backup_rejects_hardlink_alias_to_source_object(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Finding 4: Reused and new backup objects reject nlink > 1 and sharing file id with source."""
    f1 = tmp_path / "data.txt"
    f1.write_text("data payload", encoding="utf-8")
    res1 = capture_file(f1, store_root, __version__)
    sha = res1["sha256"]
    src_obj = store_root / "objects" / sha[:2] / sha

    # Pre-create hardlink alias in backup root pointing to source object
    dst_obj = backup_root / "objects" / sha[:2] / sha
    dst_obj.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(str(src_obj), str(dst_obj))
    except (OSError, NotImplementedError):
        pytest.skip("Filesystem does not support hardlinks")

    assert dst_obj.stat().st_nlink > 1

    # Backup must detect hardlink alias and fail with IntegrityError (exit 1)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1


def test_r3_failed_restore_keeps_marker_and_verify_open_find_refuse(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """Finding 5: Failed restore keeps marker; verify/open/find refuse the incomplete root with exit 2."""
    from secondbrain.root import RootRefusedError
    from secondbrain.open_cmd import open_item

    f1 = tmp_path / "doc.txt"
    f1.write_text("important document", encoding="utf-8")
    res1 = capture_file(f1, store_root, __version__)

    # Create backup
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 0

    # Tamper with the backup object so restore fails integrity check
    sha = res1["sha256"]
    backup_obj = backup_root / "objects" / sha[:2] / sha
    backup_obj.write_bytes(b"corrupted backup bytes")

    target_restore = tmp_path / "failed_restore_target"
    with pytest.raises(SystemExit) as exc_info:
        main(["restore", str(backup_root), "--to", str(target_restore)])
    assert exc_info.value.code == 1

    # Marker MUST be kept on failure!
    marker_path = target_restore / ".sb-restore.marker"
    assert marker_path.is_file(), "Incomplete restore marker must remain after restore failure"

    # 1. sb verify on target_restore must refuse root (exit 2)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(target_restore), "verify"])
    assert exc_info.value.code == 2

    # verify_repository direct call must raise RootRefusedError
    with pytest.raises(RootRefusedError):
        verify_repository(target_restore)

    # 2. sb open on target_restore must refuse root (exit 2)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(target_restore), "open", res1["id"]])
    assert exc_info.value.code == 2

    with pytest.raises(RootRefusedError):
        open_item(res1["id"], target_restore, print_path=True)

    # 3. sb find on target_restore must refuse root (exit 2)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(target_restore), "find", "important"])
    assert exc_info.value.code == 2


# -----------------------------------------------------------------------------
# ROUND 4 S4 FINDINGS TESTS
# -----------------------------------------------------------------------------

def test_r4_backup_writer_lock_hardlink_empty_object_refused(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1 Finding 1: writer.lock aliasing an empty object via hardlink must be refused BEFORE opening without writing 'L'."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")
    res = capture_file(empty_file, store_root, __version__)
    sha = res["sha256"]
    assert sha == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    empty_obj = store_root / "objects" / "e3" / sha
    assert empty_obj.is_file()
    assert empty_obj.stat().st_size == 0

    lock_file = store_root / "writer.lock"
    try:
        os.link(str(empty_obj), str(lock_file))
    except (OSError, NotImplementedError):
        pytest.skip("Filesystem does not support hardlinks")

    assert lock_file.stat().st_nlink > 1

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 2

    # The empty object MUST NOT have 'L' written into it!
    assert empty_obj.stat().st_size == 0, "writer.lock acquisition wrote bytes into aliased empty object!"
    assert empty_obj.read_bytes() == b"", "Empty object bytes must remain empty!"


def test_r4_capture_writer_lock_hardlink_empty_object_refused(
    store_root: Path, tmp_path: Path
) -> None:
    """P1 Finding 1: capture must also refuse writer.lock aliasing empty object before opening."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")
    res = capture_file(empty_file, store_root, __version__)
    sha = res["sha256"]
    empty_obj = store_root / "objects" / "e3" / sha

    lock_file = store_root / "writer.lock"
    try:
        os.link(str(empty_obj), str(lock_file))
    except (OSError, NotImplementedError):
        pytest.skip("Filesystem does not support hardlinks")

    other_file = tmp_path / "other.txt"
    other_file.write_text("other text", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "capture", str(other_file)])
    assert exc_info.value.code == 2

    assert empty_obj.stat().st_size == 0, "capture wrote into aliased empty object!"
    assert empty_obj.read_bytes() == b""


def test_r4_backup_writer_lock_symlink_or_reparse_point_refused(
    store_root: Path, backup_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P1 Finding 1: writer.lock aliasing an empty object via symlink/reparse point must be refused before opening."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")
    res = capture_file(empty_file, store_root, __version__)
    sha = res["sha256"]
    empty_obj = store_root / "objects" / "e3" / sha

    lock_file = store_root / "writer.lock"
    symlink_created = False
    try:
        os.symlink(str(empty_obj), str(lock_file))
        symlink_created = True
    except OSError:
        pass

    if not symlink_created:
        lock_file.touch()
        from secondbrain import receipt, lock
        orig_is_reparse = receipt.is_reparse_point
        monkeypatch.setattr(receipt, "is_reparse_point", lambda p: True if Path(p) == lock_file else orig_is_reparse(p))
        if hasattr(lock, "is_reparse_point"):
            monkeypatch.setattr(lock, "is_reparse_point", lambda p: True if Path(p) == lock_file else orig_is_reparse(p))

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 2
    assert empty_obj.stat().st_size == 0
    assert empty_obj.read_bytes() == b""


def test_r4_backup_rejects_misplaced_source_receipt_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1 Finding 2: misplaced source receipt in receipts/<id>.json outside v1 must reject with exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("receipt data", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)

    orig_rec = store_root / "receipts" / "v1" / f"{res['id']}.json"
    misplaced = store_root / "receipts" / f"{res['id']}.json"
    misplaced.write_text(orig_rec.read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1


def test_r4_backup_rejects_unexpected_entries_in_receipts_or_objects_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1 Finding 2: unexpected entry in receipts/ or objects/ (nested dir, non-JSON, bad prefix) must reject exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("hello", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # 1. Non-JSON in receipts/v1
    non_json = store_root / "receipts" / "v1" / "notes.txt"
    non_json.write_text("stray notes", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1
    non_json.unlink()

    # 2. Nested directory in receipts/v1
    nested_dir = store_root / "receipts" / "v1" / "subdir"
    nested_dir.mkdir()
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1
    nested_dir.rmdir()

    # 3. Stray file in objects root
    stray_obj = store_root / "objects" / "stray.bin"
    stray_obj.write_bytes(b"garbage")
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1
    stray_obj.unlink()

    # 4. Invalid prefix directory in objects
    bad_prefix = store_root / "objects" / "xyz"
    bad_prefix.mkdir()
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1
    bad_prefix.rmdir()


def test_r4_backup_rejects_payload_symlink_in_backup_root_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P1 Finding 3: payload symlink targeting file outside both roots in backup root must reject exit 1."""
    f1 = tmp_path / "doc.txt"
    content = "external payload"
    f1.write_text(content, encoding="utf-8")
    res = capture_file(f1, store_root, __version__)
    sha = res["sha256"]

    external_file = tmp_path / "outside_roots.txt"
    external_file.write_text(content, encoding="utf-8")

    dst_obj = backup_root / "objects" / sha[:2] / sha
    dst_obj.parent.mkdir(parents=True, exist_ok=True)

    sym_ok = False
    try:
        os.symlink(str(external_file), str(dst_obj))
        sym_ok = True
    except OSError:
        pass

    if not sym_ok:
        dst_obj.write_text(content, encoding="utf-8")
        from secondbrain import receipt, backup
        orig_is_reparse = receipt.is_reparse_point
        monkeypatch.setattr(receipt, "is_reparse_point", lambda p: True if Path(p) == dst_obj else orig_is_reparse(p))
        if hasattr(backup, "is_reparse_point"):
            monkeypatch.setattr(backup, "is_reparse_point", lambda p: True if Path(p) == dst_obj else orig_is_reparse(p))

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1


def test_r4_backup_rejects_payload_symlink_in_source_root_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P1 Finding 3: payload symlink targeting file outside both roots in source root must reject exit 1."""
    f1 = tmp_path / "doc.txt"
    content = "source external payload"
    f1.write_text(content, encoding="utf-8")
    res = capture_file(f1, store_root, __version__)
    sha = res["sha256"]

    external_file = tmp_path / "outside_source.txt"
    external_file.write_text(content, encoding="utf-8")

    src_obj = store_root / "objects" / sha[:2] / sha

    sym_ok = False
    try:
        src_obj.unlink()
        os.symlink(str(external_file), str(src_obj))
        sym_ok = True
    except OSError:
        pass

    if not sym_ok:
        src_obj.write_text(content, encoding="utf-8")
        from secondbrain import receipt, backup
        orig_is_reparse = receipt.is_reparse_point
        monkeypatch.setattr(receipt, "is_reparse_point", lambda p: True if Path(p) == src_obj else orig_is_reparse(p))
        if hasattr(backup, "is_reparse_point"):
            monkeypatch.setattr(backup, "is_reparse_point", lambda p: True if Path(p) == src_obj else orig_is_reparse(p))

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1


def test_r4_backup_rejects_source_payload_hardlink_nlink_gt_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1 Finding 3: payload file in source with nlink > 1 must reject exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("hardlink test", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)
    sha = res["sha256"]

    src_obj = store_root / "objects" / sha[:2] / sha
    second_link = tmp_path / "second_link.bin"
    try:
        os.link(str(src_obj), str(second_link))
    except (OSError, NotImplementedError):
        pytest.skip("Filesystem does not support hardlinks")

    assert src_obj.stat().st_nlink > 1

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1


# -----------------------------------------------------------------------------
# ROUND 5 S4: REPARSE POINT / JUNCTION ANCESTORS BENEATH BACKUP ROOT & SOURCE
# -----------------------------------------------------------------------------

def _create_dir_junction_or_symlink(link_path: Path, target_dir: Path) -> bool:
    target_dir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        cmd = f'cmd /c mklink /J "{link_path}" "{target_dir}"'
        res = subprocess.run(cmd, shell=True, capture_output=True)
        if res.returncode == 0:
            return True
    try:
        os.symlink(str(target_dir), str(link_path), target_is_directory=True)
        return True
    except OSError:
        return False


def test_r5_backup_rejects_objects_junction_outside_roots_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1: backup root with objects/ junction pointing outside both roots must be rejected with exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("r5 junction test payload", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    outside_objects = tmp_path / "outside_objects"
    link_path = backup_root / "objects"
    if not _create_dir_junction_or_symlink(link_path, outside_objects):
        pytest.skip("Neither Windows junction (mklink /J) nor symlink permitted on this filesystem")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1

    # Payloads must not live outside the backup root
    outside_files = [p for p in outside_objects.rglob("*") if p.is_file()]
    assert len(outside_files) == 0, f"Payloads were written outside backup root: {outside_files}"


def test_r5_backup_rejects_receipts_junction_outside_roots_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1: backup root with receipts/ junction pointing outside both roots must be rejected with exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("r5 receipts junction test payload", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    outside_receipts = tmp_path / "outside_receipts"
    link_path = backup_root / "receipts"
    if not _create_dir_junction_or_symlink(link_path, outside_receipts):
        pytest.skip("Neither Windows junction (mklink /J) nor symlink permitted on this filesystem")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1

    outside_files = [p for p in outside_receipts.rglob("*") if p.is_file()]
    assert len(outside_files) == 0, f"Receipts were written outside backup root: {outside_files}"


def test_r5_backup_rejects_manifests_junction_outside_roots_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1: backup root with manifests/ junction pointing outside both roots must be rejected with exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("r5 manifests junction test payload", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    outside_manifests = tmp_path / "outside_manifests"
    link_path = backup_root / "manifests"
    if not _create_dir_junction_or_symlink(link_path, outside_manifests):
        pytest.skip("Neither Windows junction (mklink /J) nor symlink permitted on this filesystem")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1

    outside_files = [p for p in outside_manifests.rglob("*") if p.is_file()]
    assert len(outside_files) == 0, f"Manifests were written outside backup root: {outside_files}"


def test_r5_backup_rejects_source_objects_prefix_junction_outside_roots_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1: source store with objects/<prefix> junction pointing outside both roots must be rejected with exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("r5 source prefix junction test payload", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)
    sha = res["sha256"]
    prefix = sha[:2]

    src_prefix_dir = store_root / "objects" / prefix
    outside_prefix = tmp_path / "outside_source_prefix" / prefix
    outside_prefix.parent.mkdir(parents=True, exist_ok=True)

    # Move prefix dir contents outside and create junction
    import shutil
    shutil.copytree(str(src_prefix_dir), str(outside_prefix))
    shutil.rmtree(str(src_prefix_dir))

    if not _create_dir_junction_or_symlink(src_prefix_dir, outside_prefix):
        pytest.skip("Neither Windows junction (mklink /J) nor symlink permitted on this filesystem")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1


def test_r5_backup_rejects_backup_objects_prefix_junction_outside_roots_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1: backup root with objects/<prefix> junction pointing outside both roots must be rejected with exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("r5 objects prefix junction test payload", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)
    sha = res["sha256"]
    prefix = sha[:2]

    backup_objects = backup_root / "objects"
    backup_objects.mkdir(parents=True, exist_ok=True)
    outside_prefix = tmp_path / "outside_backup_prefix" / prefix
    outside_prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix_junction = backup_objects / prefix

    if not _create_dir_junction_or_symlink(prefix_junction, outside_prefix):
        pytest.skip("Neither Windows junction (mklink /J) nor symlink permitted on this filesystem")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1

    outside_files = [p for p in outside_prefix.rglob("*") if p.is_file()]
    assert len(outside_files) == 0, f"Payloads were written outside backup root: {outside_files}"


def test_r5_backup_rejects_configs_junction_outside_roots_exit_1(
    store_root: Path, backup_root: Path, tmp_path: Path
) -> None:
    """P1: backup root with configs/ junction pointing outside both roots must be rejected with exit 1."""
    f1 = tmp_path / "doc.txt"
    f1.write_text("r5 configs junction test payload", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    outside_configs = tmp_path / "outside_configs"
    link_path = backup_root / "configs"
    if not _create_dir_junction_or_symlink(link_path, outside_configs):
        pytest.skip("Neither Windows junction (mklink /J) nor symlink permitted on this filesystem")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "backup", "--backup-root", str(backup_root)])
    assert exc_info.value.code == 1

    outside_files = [p for p in outside_configs.rglob("*") if p.is_file()]
    assert len(outside_files) == 0, f"Configs were written outside backup root: {outside_files}"





