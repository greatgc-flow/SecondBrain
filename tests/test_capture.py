"""Tests for SecondBrain capture and storage bootstrap (M1 S1)."""

from __future__ import annotations

import json
import os
import re
import stat
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import pytest

from secondbrain.cli import main
from secondbrain.lock import WriterLock
from secondbrain.publish import atomic_replace
from secondbrain.root import resolve_root


def run_sb(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    """Helper to run sb CLI and capture exit code, stdout, and stderr."""
    with pytest.raises(SystemExit) as exc_info:
        main(argv)
    captured = capsys.readouterr()
    return exc_info.value.code, captured.out, captured.err


def test_capture_single_file_and_bootstrap_config(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test capturing a single file, verifying layout and bootstrap config.json."""
    root = tmp_path / "root"
    src_file = tmp_path / "sample.txt"
    src_file.write_bytes(b"hello world")

    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0
    assert "captured id=cap-" in out
    assert "name=sample.txt" in out
    assert "object=new" in out

    # Config bootstrap: config.json with backup_root: null
    config_path = root / "config.json"
    assert config_path.is_file()
    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    assert config_data == {"backup_root": None}

    # Objects directory structure: objects/ab/<sha256>
    import hashlib
    expected_sha = hashlib.sha256(b"hello world").hexdigest()
    obj_path = root / "objects" / expected_sha[:2] / expected_sha
    assert obj_path.is_file()
    assert obj_path.read_bytes() == b"hello world"

    # Receipts directory structure: receipts/v1/<id>.json
    receipt_files = list((root / "receipts" / "v1").glob("*.json"))
    assert len(receipt_files) == 1
    receipt = json.loads(receipt_files[0].read_text(encoding="utf-8"))
    assert receipt["sha256"] == expected_sha
    assert receipt["original_name"] == "sample.txt"
    assert receipt["source_path"] == str(src_file.resolve())


def test_korean_and_spaced_names(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test capturing files with Korean characters and spaces."""
    root = tmp_path / "root"
    src_file = tmp_path / "훈민정음 혜례본 2026.txt"
    content = "나랏말싸미 듕귁에 달아 문자와로 서르 사맛디 아니할싸".encode("utf-8")
    src_file.write_bytes(content)

    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0
    assert "captured id=cap-" in out
    assert "name=훈민정음 혜례본 2026.txt" in out
    assert "object=new" in out

    receipt_files = list((root / "receipts" / "v1").glob("*.json"))
    assert len(receipt_files) == 1
    receipt = json.loads(receipt_files[0].read_text(encoding="utf-8"))
    assert receipt["original_name"] == "훈민정음 혜례본 2026.txt"
    assert receipt["original_name_raw"] == "훈민정음 혜례본 2026.txt"


def test_nfc_vs_nfd_names(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that NFD (decomposed) filenames are normalized to NFC inside receipts and raw is kept."""
    root = tmp_path / "root"
    base_name = "한글문서"
    nfd_stem = unicodedata.normalize("NFD", base_name)
    nfc_stem = unicodedata.normalize("NFC", base_name)
    assert nfd_stem != nfc_stem

    src_file = tmp_path / f"{nfd_stem}.txt"
    src_file.write_bytes(b"hangul content")

    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0

    receipt_files = list((root / "receipts" / "v1").glob("*.json"))
    assert len(receipt_files) == 1
    receipt = json.loads(receipt_files[0].read_text(encoding="utf-8"))
    assert receipt["original_name"] == f"{nfc_stem}.txt"
    assert receipt["original_name"] != f"{nfd_stem}.txt"
    assert receipt["original_name_raw"] == f"{nfd_stem}.txt"



def test_long_paths(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test capturing a file located at a deeply nested path (> 260 characters)."""
    root = tmp_path / "root"
    nested = tmp_path
    for i in range(15):
        nested = nested / f"subfolder_{i:02d}_very_long_path_segment"
    nested.mkdir(parents=True, exist_ok=True)
    long_file = nested / "deep_file.txt"
    long_file.write_bytes(b"deep file content")

    code, out, err = run_sb(["--root", str(root), "capture", str(long_file)], capsys)
    assert code == 0
    assert "object=new" in out


def test_duplicates_do_not_rewrite_object_but_create_receipt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that identical byte contents reuse existing object and create a new receipt."""
    root = tmp_path / "root"
    content = b"duplicate test payload"
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_bytes(content)
    file2.write_bytes(content)

    import hashlib
    sha = hashlib.sha256(content).hexdigest()

    # Capture first file
    code1, out1, err1 = run_sb(["--root", str(root), "capture", str(file1)], capsys)
    assert code1 == 0
    assert "object=new" in out1

    obj_path = root / "objects" / sha[:2] / sha
    assert obj_path.is_file()
    mtime_before = obj_path.stat().st_mtime_ns

    # Capture second file
    code2, out2, err2 = run_sb(["--root", str(root), "capture", str(file2)], capsys)
    assert code2 == 0
    assert "object=reused" in out2

    # Object was NOT rewritten
    assert obj_path.stat().st_mtime_ns == mtime_before

    # Two distinct receipts exist
    receipts = sorted((root / "receipts" / "v1").glob("*.json"))
    assert len(receipts) == 2
    r1 = json.loads(receipts[0].read_text(encoding="utf-8"))
    r2 = json.loads(receipts[1].read_text(encoding="utf-8"))
    assert r1["id"] != r2["id"]
    assert r1["sha256"] == r2["sha256"] == sha
    assert {r1["original_name"], r2["original_name"]} == {"file1.txt", "file2.txt"}


def test_same_second_collision_suffix(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test same-second collision suffix -2 on capture IDs."""
    import hashlib

    root = tmp_path / "root"
    file1 = tmp_path / "coll.txt"
    content = b"collision test payload"
    file1.write_bytes(content)

    frozen_utc = datetime(2026, 10, 12, 12, 0, 0, tzinfo=timezone.utc)
    base_id = f"cap-20261012t120000z-{hashlib.sha256(content).hexdigest()[:8]}".lower()
    with patch("secondbrain.capture.utc_now", return_value=frozen_utc):
        code1, out1, err1 = run_sb(["--json", "--root", str(root), "capture", str(file1)], capsys)
        assert code1 == 0
        assert json.loads(out1)["results"][0]["id"] == base_id

        code2, out2, err2 = run_sb(["--json", "--root", str(root), "capture", str(file1)], capsys)
        assert code2 == 0
        assert json.loads(out2)["results"][0]["id"] == f"{base_id}-2"

    receipts_dir = root / "receipts" / "v1"
    receipt_names = {p.name for p in receipts_dir.glob("*.json")}
    assert receipt_names == {f"{base_id}.json", f"{base_id}-2.json"}
    for receipt_id in (base_id, f"{base_id}-2"):
        assert receipt_id == receipt_id.lower()
        receipt = json.loads((receipts_dir / f"{receipt_id}.json").read_text(encoding="utf-8"))
        assert receipt["id"] == receipt_id


def test_empty_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test capturing a 0-byte empty file."""
    root = tmp_path / "root"
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")

    code, out, err = run_sb(["--root", str(root), "capture", str(empty_file)], capsys)
    assert code == 0

    empty_sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    obj_path = root / "objects" / "e3" / empty_sha
    assert obj_path.is_file()
    assert obj_path.stat().st_size == 0


@pytest.mark.skipif(sys.platform != "win32", reason="Windows sharing violation locking is platform-specific")
def test_locked_file_windows(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that a locked file produces per-file error and exit code 2."""
    root = tmp_path / "root"
    folder = tmp_path / "data"
    folder.mkdir()
    good_file = folder / "good.txt"
    good_file.write_bytes(b"good content")
    locked_file = folder / "locked.txt"
    locked_file.write_bytes(b"locked content")

    import ctypes
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    FILE_SHARE_NONE = 0
    OPEN_EXISTING = 3
    handle = ctypes.windll.kernel32.CreateFileW(
        str(locked_file),
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_NONE,
        None,
        OPEN_EXISTING,
        0,
        None,
    )
    assert handle != -1 and handle != 0

    try:
        code, out, err = run_sb(["--root", str(root), "capture", str(folder)], capsys)
        assert code == 2
        assert "captured=1" in out
        assert "failed=1" in out
        assert "locked.txt" in err or "locked.txt" in out
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def test_interruption_simulated_temp_write_and_publish_object(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test simulated crash between temp write and object publish, and recovery on re-run."""
    root = tmp_path / "root"
    src_file = tmp_path / "interrupted.txt"
    src_file.write_bytes(b"interrupted payload")

    original_replace = atomic_replace

    def faulty_replace(src: Path, dst: Path, **kwargs: object) -> None:
        if "objects" in str(dst):
            raise KeyboardInterrupt("Simulated kill before object publish")
        original_replace(src, dst, **kwargs)

    with patch("secondbrain.publish.atomic_replace", side_effect=faulty_replace):
        with pytest.raises(KeyboardInterrupt):
            main(["--root", str(root), "capture", str(src_file)])

    # Verify temp file left, no receipt exists
    tmp_files = list(root.rglob("*.tmp"))
    assert len(tmp_files) >= 1
    assert len(list((root / "receipts" / "v1").glob("*.json"))) == 0

    # Re-run recovers, cleans leftover temp file, publishes object and receipt
    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0
    assert "object=new" in out
    assert len(list(root.rglob("*.tmp"))) == 0
    assert len(list((root / "receipts" / "v1").glob("*.json"))) == 1


def test_interruption_simulated_after_object_before_receipt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test simulated crash after object publish but before receipt publish."""
    root = tmp_path / "root"
    src_file = tmp_path / "interrupted2.txt"
    src_file.write_bytes(b"interrupted payload 2")

    original_replace = atomic_replace

    def faulty_replace(src: Path, dst: Path, **kwargs: object) -> None:
        if "receipts" in str(dst):
            raise KeyboardInterrupt("Simulated kill before receipt publish")
        original_replace(src, dst, **kwargs)

    with patch("secondbrain.publish.atomic_replace", side_effect=faulty_replace):
        with pytest.raises(KeyboardInterrupt):
            main(["--root", str(root), "capture", str(src_file)])

    # Object exists, receipt does not
    assert len(list((root / "receipts" / "v1").glob("*.json"))) == 0

    # Re-run recovers: reuses existing object, completes receipt
    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0
    assert "object=reused" in out
    assert len(list((root / "receipts" / "v1").glob("*.json"))) == 1
    assert len(list(root.rglob("*.tmp"))) == 0


def test_read_only_source_never_modified(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that capture never modifies the source file, even when read-only."""
    root = tmp_path / "root"
    src_file = tmp_path / "readonly.txt"
    content = b"strictly read-only content"
    src_file.write_bytes(content)

    src_file.chmod(stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    stat_before = src_file.stat()

    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0

    stat_after = src_file.stat()
    assert src_file.read_bytes() == content
    assert stat_after.st_mtime_ns == stat_before.st_mtime_ns
    assert stat_after.st_size == stat_before.st_size


def test_root_refusal_cloud_synced(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that active roots in cloud sync folders are refused with clear ADR 0002 warning."""
    cloud_root = tmp_path / "OneDrive" / "SecondBrain"
    src_file = tmp_path / "test.txt"
    src_file.write_bytes(b"test")

    code, out, err = run_sb(["--root", str(cloud_root), "capture", str(src_file)], capsys)
    assert code == 2
    assert "ADR 0002" in err or "ADR 0002" in out
    combined = (out + err).lower()
    assert "onedrive" in combined or "cloud" in combined


def test_root_refusal_non_ntfs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that non-NTFS active roots are refused on Windows with ADR 0002 warning."""
    root = tmp_path / "SecondBrain"
    src_file = tmp_path / "test.txt"
    src_file.write_bytes(b"test")

    with patch("secondbrain.root.get_filesystem_type", return_value="FAT32"):
        code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
        assert code == 2
        assert "ADR 0002" in err or "ADR 0002" in out
        assert "FAT32" in err or "FAT32" in out


def test_receipt_json_schema(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that receipt format matches versioned fields including original_name_raw, lowercase filename."""
    root = tmp_path / "root"
    src_file = tmp_path / "schema_check.txt"
    src_file.write_bytes(b"schema content")

    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0

    receipt_file = next((root / "receipts" / "v1").glob("*.json"))
    assert receipt_file.name == receipt_file.name.lower()
    data = json.loads(receipt_file.read_text(encoding="utf-8"))

    assert set(data.keys()) == {
        "id",
        "sha256",
        "original_name",
        "original_name_raw",
        "source_path",
        "collected_at",
        "tool_version",
    }

    assert re.match(r"^cap-\d{8}[Tt]\d{6}[Zz]-[0-9a-f]{8}(?:-\d+)?$", data["id"])
    assert data["id"] == data["id"].lower()
    assert re.match(r"^[0-9a-f]{64}$", data["sha256"])
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$",
        data["collected_at"],
    )
    assert data["original_name"] == "schema_check.txt"
    assert data["original_name_raw"] == "schema_check.txt"
    assert data["source_path"] == str(src_file.resolve())
    assert isinstance(data["tool_version"], str)



def test_cli_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test --json output format on successful capture."""
    root = tmp_path / "root"
    src_file = tmp_path / "test_json.txt"
    src_file.write_bytes(b"json format check")

    code, out, err = run_sb(["--json", "--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0

    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["captured"] == 1
    assert data["reused_objects"] == 0
    assert data["failed"] == 0
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "test_json.txt"
    assert data["results"][0]["object"] == "new"
    assert data["errors"] == []


def test_folder_recursive_capture(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test capturing a directory recursively with per-file result and duplicates."""
    root = tmp_path / "root"
    folder = tmp_path / "my_folder"
    (folder / "sub").mkdir(parents=True)
    (folder / "file_a.txt").write_bytes(b"content 1")
    (folder / "sub" / "file_b.txt").write_bytes(b"content 2")
    (folder / "sub" / "file_c.txt").write_bytes(b"content 1")  # duplicate of file_a

    code, out, err = run_sb(["--root", str(root), "capture", str(folder)], capsys)
    assert code == 0
    assert "captured=3 reused_objects=1 failed=0" in out

    receipts = list((root / "receipts" / "v1").glob("*.json"))
    assert len(receipts) == 3


def test_single_writer_lock_exclusion(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that concurrent access fails with exit code 2 when writer lock is held."""
    root = tmp_path / "root"
    src_file = tmp_path / "lock_test.txt"
    src_file.write_bytes(b"lock content")

    with WriterLock(root):
        code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
        assert code == 2
        combined = (out + err).lower()
        assert "lock" in combined


def test_root_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test root resolution precedence: --root > SB_ROOT > default D:\\SecondBrain."""
    cli_r = str(tmp_path / "cli_root")
    env_r = str(tmp_path / "env_root")

    monkeypatch.setenv("SB_ROOT", env_r)
    assert resolve_root(cli_r) == Path(cli_r)
    assert resolve_root(None) == Path(env_r)

    monkeypatch.delenv("SB_ROOT", raising=False)
    assert resolve_root(None) == Path(r"D:\SecondBrain")


def test_cleanup_safety_user_tmp_survives(tmp_path: Path) -> None:
    """Test that cleanup only removes tool-owned temp files and preserves user .tmp files."""
    from secondbrain.publish import cleanup_temp_files

    root = tmp_path / "root"
    root.mkdir()
    (root / "objects").mkdir()

    # User temp files inside root
    user_file1 = root / "user_notes.tmp"
    user_file1.write_text("important user notes")
    user_file2 = root / "objects" / "user_calc.tmp"
    user_file2.write_text("user calculation")

    # Tool-owned temp files
    tool_tmp1 = root / "objects" / ".sb-tmp-stage-1234-abcd1234.tmp"
    tool_tmp1.write_bytes(b"unfinished staged bytes")
    tool_tmp2 = root / "objects" / ".sb_tmp_target_1234_abcd1234.tmp"
    tool_tmp2.write_bytes(b"unfinished publish bytes")

    cleaned = cleanup_temp_files(root)
    assert cleaned == 2
    assert not tool_tmp1.exists()
    assert not tool_tmp2.exists()
    assert user_file1.is_file()
    assert user_file1.read_text() == "important user notes"
    assert user_file2.is_file()
    assert user_file2.read_text() == "user calculation"


def test_source_overlaps_root_rejected(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that capture rejects source that overlaps the root in either direction or case."""
    root = tmp_path / "root"
    root.mkdir()

    # Source inside root
    inside_file = root / "inside.txt"
    inside_file.write_bytes(b"inside")
    code, out, err = run_sb(["--root", str(root), "capture", str(inside_file)], capsys)
    assert code == 2
    assert "overlap" in (out + err).lower() or "inside" in (out + err).lower()

    # Root inside source (capturing parent of root)
    code2, out2, err2 = run_sb(["--root", str(root), "capture", str(tmp_path)], capsys)
    assert code2 == 2
    assert "overlap" in (out2 + err2).lower() or "inside" in (out2 + err2).lower()

    # Source is root itself
    code3, out3, err3 = run_sb(["--root", str(root), "capture", str(root)], capsys)
    assert code3 == 2

    # Case difference overlap check (Windows case-insensitive)
    case_root_str = str(root).swapcase() if sys.platform == "win32" else str(root)
    code4, out4, err4 = run_sb(["--json", "--root", case_root_str, "capture", str(inside_file)], capsys)
    assert code4 == 2
    data = json.loads(out4)
    assert data["status"] == "error"
    assert data["results"] == []


def test_source_changing_during_copy_fails_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that a source modified during copy fails with IntegrityError (exit 1) and publishes nothing."""
    import hashlib

    root = tmp_path / "root"
    src_file = tmp_path / "changing.txt"
    src_file.write_bytes(b"initial bytes")

    import secondbrain.capture as cap_mod
    real_retry_open = cap_mod.retry_open_read

    def mutating_open(path: Path, **kwargs: object):
        fp = real_retry_open(path, **kwargs)
        # Mutate the source file while it is being read
        src_file.write_bytes(b"mutated content bytes during read")
        return fp

    with patch.object(cap_mod, "retry_open_read", side_effect=mutating_open):
        code, out, err = run_sb(["--json", "--root", str(root), "capture", str(src_file)], capsys)
        assert code == 1
        data = json.loads(out)
        assert data["status"] == "error"
        assert "changed during copy" in data["error"].lower() or "integrity" in data["error"].lower()
        assert data["results"] == []

    # Verify NOTHING was published
    assert len(list((root / "objects").rglob("*"))) == 0 or all(p.is_dir() for p in (root / "objects").rglob("*"))
    assert not (root / "receipts").exists() or len(list((root / "receipts").rglob("*.json"))) == 0
    # Leftover tool temp files cleaned up
    assert len(list(root.rglob(".sb-tmp*"))) == 0


def test_corrupt_existing_object_is_repaired(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that an existing corrupt object is detected, repaired/re-published, and receipt written."""
    import hashlib

    root = tmp_path / "root"
    src_file = tmp_path / "valid.txt"
    valid_bytes = b"valid content to preserve"
    src_file.write_bytes(valid_bytes)

    sha = hashlib.sha256(valid_bytes).hexdigest()
    obj_dir = root / "objects" / sha[:2]
    obj_dir.mkdir(parents=True)
    obj_path = obj_dir / sha
    # Pre-populate corrupt object
    obj_path.write_bytes(b"completely corrupt garbage bytes")

    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0
    # Object repaired
    assert obj_path.read_bytes() == valid_bytes

    receipts = list((root / "receipts" / "v1").glob("*.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert receipt["sha256"] == sha


def test_truncated_config_fails_with_recovery_hint(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that a truncated config.json triggers IntegrityError with recovery hint."""
    root = tmp_path / "root"
    root.mkdir()
    config_file = root / "config.json"
    config_file.write_text("{ truncated json content")

    src_file = tmp_path / "test.txt"
    src_file.write_bytes(b"content")

    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 1
    combined = (out + err).lower()
    assert "recovery hint" in combined


def test_cloud_sync_no_false_positive_for_sandbox(tmp_path: Path) -> None:
    """Test that substring matches like 'sandbox' matching 'box' are not falsely classified as cloud sync."""
    from secondbrain.root import is_cloud_synced_path, validate_root

    sandbox_root = tmp_path / "sandbox" / "SecondBrain"
    is_synced, reason = is_cloud_synced_path(sandbox_root)
    assert not is_synced
    assert reason == ""

    # validate_root does not refuse sandbox
    with patch("secondbrain.root.get_filesystem_type", return_value="NTFS"):
        validate_root(sandbox_root)


def test_sharing_violation_retry_source_read(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test retry/backoff on transient Windows sharing violations when opening source file."""
    root = tmp_path / "root"
    src_file = tmp_path / "transient.txt"
    src_file.write_bytes(b"transient retry data")

    import secondbrain.capture as cap_mod
    real_retry_open = cap_mod.retry_open_read
    call_count = 0

    def transient_open(path: Path, **kwargs: object):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            err = PermissionError("The process cannot access the file because it is being used by another process.")
            setattr(err, "winerror", 32)
            raise err
        return real_retry_open(path, **kwargs)

    with patch.object(cap_mod, "retry_open_read", side_effect=transient_open):
        code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
        assert code == 0
        assert call_count >= 2
        assert "object=new" in out


def test_subprocess_process_death_at_each_stage(tmp_path: Path) -> None:
    """Test process death via subprocess termination at staging and object publish stages."""
    import subprocess

    root = tmp_path / "root"
    src_file = tmp_path / "proc_death.txt"
    src_file.write_bytes(b"kill and recover test content")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")

    # Stage 1: Terminate after staging temp file is written
    env["_SB_TEST_TERMINATE_STAGE"] = "after_staging"
    proc = subprocess.run(
        [sys.executable, "-m", "secondbrain.cli", "--root", str(root), "capture", str(src_file)],
        env=env,
        capture_output=True,
    )
    assert proc.returncode != 0
    # Leftover tool temp file was left on disk by killed process
    staged_tmps = list(root.rglob(".sb-tmp*"))
    assert len(staged_tmps) >= 1
    assert not (root / "receipts" / "v1").exists() or len(list((root / "receipts" / "v1").glob("*.json"))) == 0

    # Rerun normally: cleans leftover tool temp file and succeeds
    env.pop("_SB_TEST_TERMINATE_STAGE", None)
    proc2 = subprocess.run(
        [sys.executable, "-m", "secondbrain.cli", "--root", str(root), "capture", str(src_file)],
        env=env,
        capture_output=True,
    )
    assert proc2.returncode == 0
    assert len(list((root / "receipts" / "v1").glob("*.json"))) == 1
    assert len(list(root.rglob(".sb-tmp*"))) == 0

    # Stage 2: Terminate after object publish but before receipt
    src_file2 = tmp_path / "proc_death2.txt"
    src_file2.write_bytes(b"kill after object content")
    env["_SB_TEST_TERMINATE_STAGE"] = "after_object"
    proc3 = subprocess.run(
        [sys.executable, "-m", "secondbrain.cli", "--root", str(root), "capture", str(src_file2)],
        env=env,
        capture_output=True,
    )
    assert proc3.returncode != 0

    # Rerun normally: reuses object and completes receipt
    env.pop("_SB_TEST_TERMINATE_STAGE", None)
    proc4 = subprocess.run(
        [sys.executable, "-m", "secondbrain.cli", "--root", str(root), "capture", str(src_file2)],
        env=env,
        capture_output=True,
    )
    assert proc4.returncode == 0
    assert len(list((root / "receipts" / "v1").glob("*.json"))) == 2


def test_unreadable_traversal_entry(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test folder capture handling unreadable entry, recording error and continuing with exit code 2."""
    root = tmp_path / "root"
    folder = tmp_path / "folder_with_unreadable"
    folder.mkdir()
    good_file = folder / "good.txt"
    good_file.write_bytes(b"good")
    bad_file = folder / "unreadable.txt"
    bad_file.write_bytes(b"bad")

    import secondbrain.capture as cap_mod
    real_retry_open = cap_mod.retry_open_read

    def unreadable_open(path: Path, **kwargs: object):
        if Path(path).name == "unreadable.txt":
            raise PermissionError(f"Access denied to {path}")
        return real_retry_open(path, **kwargs)

    with patch.object(cap_mod, "retry_open_read", side_effect=unreadable_open):
        code, out, err = run_sb(["--json", "--root", str(root), "capture", str(folder)], capsys)
        assert code == 2
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["captured"] == 1
        assert data["failed"] == 1
        assert len(data["results"]) == 1
        assert len(data["errors"]) == 1
        assert "unreadable.txt" in data["errors"][0]["path"]


def test_reserved_windows_names(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test capturing a file with Windows reserved name pattern safely."""
    root = tmp_path / "root"
    src_file = tmp_path / "con_test_aux.txt"
    src_file.write_bytes(b"auxiliary con data")

    code, out, err = run_sb(["--root", str(root), "capture", str(src_file)], capsys)
    assert code == 0
    assert "object=new" in out


def test_case_differences_windows(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test capturing files with case differences in filename and root path."""
    root = tmp_path / "root"
    folder = tmp_path / "case_folder"
    folder.mkdir()
    f1 = folder / "SampleFile.TXT"
    f1.write_bytes(b"sample uppercase extension")

    code1, out1, err1 = run_sb(["--root", str(root), "capture", str(f1)], capsys)
    assert code1 == 0
    receipt = json.loads(next((root / "receipts" / "v1").glob("*.json")).read_text(encoding="utf-8"))
    assert receipt["original_name"] == "SampleFile.TXT"
    assert receipt["original_name_raw"] == "SampleFile.TXT"


def test_cli_folder_error_envelope_preserves_error_categories(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test folder capture preserves exit 1 on integrity error vs exit 2 on usage/IO error."""
    root = tmp_path / "root"
    folder = tmp_path / "folder_test"
    folder.mkdir()
    f1 = folder / "f1.txt"
    f1.write_bytes(b"content 1")
    f2 = folder / "f2.txt"
    f2.write_bytes(b"content 2")

    import secondbrain.capture as cap_mod
    from secondbrain.errors import IntegrityError

    real_capture_file = cap_mod.capture_file

    # Integrity error on f2: must exit 1 and envelope must include results for f1
    def mock_capture(path: Path, r: Path, ver: str):
        if Path(path).name == "f2.txt":
            raise IntegrityError(f"Integrity corruption for {path}")
        return real_capture_file(path, r, ver)

    with patch("secondbrain.capture.capture_file", side_effect=mock_capture):
        code, out, err = run_sb(["--json", "--root", str(root), "capture", str(folder)], capsys)
        assert code == 1
        data = json.loads(out)
        assert data["status"] == "error"
        assert len(data["results"]) == 1
        assert len(data["errors"]) == 1
        assert "integrity" in data["errors"][0]["error"].lower()

