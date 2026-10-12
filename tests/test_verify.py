"""Tests for sb verify command and verification engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pytest

from secondbrain.capture import capture_file
from secondbrain.cli import main
from secondbrain import __version__


@pytest.fixture
def store_root(tmp_path: Path) -> Path:
    """Create a temporary root outside cloud sync for testing."""
    root = tmp_path / "SecondBrain"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_verify_clean_store(store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that sb verify passes on a clean store with exit code 0."""
    # Capture two files (one ascii, one with Korean text)
    f1 = tmp_path / "inbox" / "hello.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("hello world", encoding="utf-8")

    f2 = tmp_path / "inbox" / "문서.txt"
    f2.write_text("안녕하세요", encoding="utf-8")

    res1 = capture_file(f1, store_root, __version__)
    res2 = capture_file(f2, store_root, __version__)

    assert res1["id"] is not None
    assert res2["id"] is not None

    # Test text output
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "OK receipts=2 objects=2 missing=0 corrupt=0 orphan=0" in captured.out

    # Test JSON output
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "ok"
    assert data["receipts"] == 2
    assert data["objects"] == 2
    assert data["missing"] == 0
    assert data["corrupt"] == 0
    assert data["orphan"] == 0
    assert data["invalid_receipts"] == 0
    assert data["temp_files"] == 0
    assert data["problems"] == []


def test_verify_one_flipped_byte_corrupt(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that a corrupt object (one flipped byte) is detected with exit code 1."""
    f1 = tmp_path / "inbox" / "doc.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_bytes(b"A" * 100)

    res = capture_file(f1, store_root, __version__)
    sha = res["sha256"]
    obj_path = store_root / "objects" / sha[:2] / sha
    assert obj_path.is_file()

    # Flip one byte
    content = bytearray(obj_path.read_bytes())
    content[0] ^= 0x01
    obj_path.write_bytes(bytes(content))

    # sb verify exits 1
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "corrupt" in (captured.out + captured.err).lower()

    # sb --json verify exits 1 and reports problem
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "error"
    assert data["corrupt"] == 1
    problem = next(p for p in data["problems"] if p["code"] == "corrupt_object")
    assert problem["id"] == sha
    assert str(obj_path) in problem["path"]


def test_verify_deleted_object_missing(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that a deleted object is detected as missing with exit code 1."""
    f1 = tmp_path / "inbox" / "doc.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("to be deleted", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    sha = res["sha256"]
    obj_path = store_root / "objects" / sha[:2] / sha
    assert obj_path.is_file()
    obj_path.unlink()

    # sb verify exits 1
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 1
    capsys.readouterr()

    # sb --json verify
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "error"
    assert data["missing"] == 1
    problem = next(p for p in data["problems"] if p["code"] == "missing_object")
    assert problem["id"] == res["id"] or problem["id"] == sha


def test_verify_extra_object_orphan(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that an unreferenced object is detected as an orphan with exit code 1."""
    f1 = tmp_path / "inbox" / "doc.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("legit file", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # Plant orphan object
    orphan_bytes = b"orphan content 12345"
    import hashlib

    orphan_sha = hashlib.sha256(orphan_bytes).hexdigest().lower()
    orphan_dir = store_root / "objects" / orphan_sha[:2]
    orphan_dir.mkdir(parents=True, exist_ok=True)
    orphan_path = orphan_dir / orphan_sha
    orphan_path.write_bytes(orphan_bytes)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 1
    capsys.readouterr()

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "error"
    assert data["orphan"] == 1
    problem = next(p for p in data["problems"] if p["code"] == "orphan_object")
    assert problem["id"] == orphan_sha


def test_verify_truncated_receipt_json(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that a truncated or invalid receipt is detected with exit code 1."""
    f1 = tmp_path / "inbox" / "doc.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("normal file", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)

    receipt_path = store_root / "receipts" / "v1" / f"{res['id']}.json"
    assert receipt_path.is_file()
    # Truncate receipt JSON
    receipt_path.write_text('{"id": "incomplete...', encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 1
    capsys.readouterr()

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "error"
    assert data["invalid_receipts"] == 1
    problem = next(p for p in data["problems"] if p["code"] == "invalid_receipt")
    assert problem["path"] == str(receipt_path)


def test_verify_leftover_tool_temp_file(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that a leftover tool temp file is detected and reported with exit code 1."""
    f1 = tmp_path / "inbox" / "doc.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("clean", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    temp_path = store_root / "objects" / ".sb-tmp-stage-999-deadbeef.tmp"
    temp_path.write_bytes(b"leftover temporary bytes")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 1
    capsys.readouterr()

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "error"
    assert data["temp_files"] == 1
    problem = next(p for p in data["problems"] if p["code"] == "temp_file")
    assert str(temp_path) in problem["path"]


def test_verify_read_only_never_fixes_or_deletes(
    store_root: Path, tmp_path: Path
) -> None:
    """Test that verify is read-only and does not delete or alter any files."""
    f1 = tmp_path / "inbox" / "doc.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("clean", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)

    # Corrupt object
    sha = res["sha256"]
    obj_path = store_root / "objects" / sha[:2] / sha
    obj_path.write_bytes(b"bad bytes")

    # Add orphan
    orphan_dir = store_root / "objects" / "ff"
    orphan_dir.mkdir(parents=True, exist_ok=True)
    orphan_path = orphan_dir / ("f" * 64)
    orphan_path.write_bytes(b"orphan")

    # Add leftover temp file
    temp_path = store_root / "objects" / ".sb-tmp-leftover-123.tmp"
    temp_path.write_bytes(b"temp")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 1

    # Verify everything remains on disk unchanged
    assert obj_path.read_bytes() == b"bad bytes"
    assert orphan_path.read_bytes() == b"orphan"
    assert temp_path.read_bytes() == b"temp"


def test_verify_does_not_hold_writer_lock(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that verify does not hold writer lock so concurrent writer can acquire it."""
    f1 = tmp_path / "inbox" / "file1.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("first file", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    from secondbrain.lock import WriterLock
    from secondbrain import verify as verify_mod

    lock_acquired_during_verify = False
    original_scan = verify_mod.scan_objects

    def hooked_scan(root: Path) -> Any:
        nonlocal lock_acquired_during_verify
        # Attempt to acquire WriterLock while verify is executing
        with WriterLock(root):
            lock_acquired_during_verify = True
        return original_scan(root)

    monkeypatch.setattr(verify_mod, "scan_objects", hooked_scan)

    result = verify_mod.verify_repository(store_root)
    assert result["status"] == "ok"
    assert lock_acquired_during_verify is True


def test_verify_tolerates_concurrent_capture_simulated(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate a capture occurring while verify is scanning."""
    f1 = tmp_path / "inbox" / "file1.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("first file", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    f2 = tmp_path / "inbox" / "file2.txt"
    f2.write_text("concurrent file", encoding="utf-8")

    from secondbrain import verify as verify_mod

    captured_concurrently = False
    original_scan = verify_mod.scan_objects

    def hooked_scan(root: Path) -> Any:
        nonlocal captured_concurrently
        res = original_scan(root)
        if not captured_concurrently:
            # Capture file2 concurrently right after objects are scanned
            capture_file(f2, store_root, __version__)
            captured_concurrently = True
        return res

    monkeypatch.setattr(verify_mod, "scan_objects", hooked_scan)

    result = verify_mod.verify_repository(store_root)
    assert result["status"] == "ok"
    assert result["problems"] == []
    assert result["objects"] >= 2
    assert result["receipts"] >= 2


def test_verify_exit_codes(store_root: Path, tmp_path: Path) -> None:
    """Test verify exit codes: 0 clean, 1 integrity problem, 2 usage/IO error."""
    # Empty/clean store: 0
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 0

    # Non-existent root: 2
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(non_existent), "verify"])
    assert exc_info.value.code == 2

    # Integrity problem: 1
    f1 = tmp_path / "inbox" / "f.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("data", encoding="utf-8")
    capture_file(f1, store_root, __version__)
    # Delete objects directory
    import shutil

    shutil.rmtree(store_root / "objects")
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 1
