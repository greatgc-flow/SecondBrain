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


def test_verify_tolerates_concurrent_capture_paused_stage(
    store_root: Path, tmp_path: Path
) -> None:
    """Pause capture between object and receipt publication: verify reports concurrent_activity, not false orphan."""
    from secondbrain.lock import WriterLock
    import hashlib

    f1 = tmp_path / "inbox" / "file1.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("first file", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # Simulate an active writer holding WriterLock with object published but no receipt yet
    content = b"concurrent in-flight bytes"
    sha = hashlib.sha256(content).hexdigest().lower()
    obj_dir = store_root / "objects" / sha[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    obj_file = obj_dir / sha
    obj_file.write_bytes(content)

    from secondbrain import verify as verify_mod

    # While WriterLock is held:
    with WriterLock(store_root):
        report = verify_mod.verify_repository(store_root)
        # Must NOT report orphan_object
        assert report["status"] == "ok"
        assert report["orphan"] == 0
        assert len(report["problems"]) == 0
        assert any(
            ca["code"] == "awaiting_receipt" and ca["id"] == sha
            for ca in report["concurrent_activity"]
        )

    # Now simulate writer publishing the receipt and releasing lock
    receipt_data = {
        "id": f"cap-20261012t120000z-{sha[:8]}",
        "sha256": sha,
        "original_name": "concurrent.txt",
        "source_path": str(tmp_path / "inbox" / "concurrent.txt"),
        "collected_at": "2026-10-12T12:00:00+00:00",
        "tool_version": __version__,
    }
    rec_file = store_root / "receipts" / "v1" / f"{receipt_data['id']}.json"
    rec_file.parent.mkdir(parents=True, exist_ok=True)
    rec_file.write_text(json.dumps(receipt_data), encoding="utf-8")

    report_after = verify_mod.verify_repository(store_root)
    assert report_after["status"] == "ok"
    assert report_after["orphan"] == 0
    assert report_after["missing"] == 0
    assert report_after["corrupt"] == 0
    assert len(report_after["problems"]) == 0


def test_verify_exit_codes(store_root: Path, tmp_path: Path) -> None:
    """Test verify exit codes: 0 clean, 1 integrity problem, 2 usage/IO error."""
    # Clean store with initialized objects and receipts directories: 0
    (store_root / "objects").mkdir(parents=True, exist_ok=True)
    (store_root / "receipts" / "v1").mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 0

    # Non-existent root: 2
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(non_existent), "verify"])
    assert exc_info.value.code == 2

    # Integrity problem (missing referenced object): 1
    f1 = tmp_path / "inbox" / "f.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("data", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)
    sha = res["sha256"]
    (store_root / "objects" / sha[:2] / sha).unlink()
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 1


def test_is_writer_locked_does_not_create_file(store_root: Path) -> None:
    """Test that is_writer_locked probes without creating writer.lock if missing."""
    from secondbrain.verify import is_writer_locked

    lock_path = store_root / "writer.lock"
    assert not lock_path.exists()
    assert is_writer_locked(store_root) is False
    assert not lock_path.exists(), "is_writer_locked must not create writer.lock!"


def test_is_writer_locked_probes_byte_zero(store_root: Path) -> None:
    """Test that is_writer_locked correctly detects byte zero writer lock."""
    from secondbrain.lock import WriterLock
    from secondbrain.verify import is_writer_locked

    assert is_writer_locked(store_root) is False

    with WriterLock(store_root):
        assert is_writer_locked(store_root) is True

    assert is_writer_locked(store_root) is False


def test_verify_unreadable_file_exits_2(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that IO errors (unreadable/locked files) exit 2 instead of integrity error exit 1."""
    f1 = tmp_path / "inbox" / "locked.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("locked content", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    from secondbrain import verify as verify_mod

    # Simulate an unreadable object file due to OS sharing violation or permission error
    def failing_compute_sha(path: Path) -> str:
        raise PermissionError("Simulated file locked by indexer / sharing violation")

    monkeypatch.setattr(verify_mod, "compute_sha256", failing_compute_sha)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 2  # Must be exit 2 (Usage/IO error), NOT exit 1!
    capsys.readouterr()

    # Also test JSON envelope on exit 2
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "io_error"
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["io_errors"]) >= 1


def test_verify_json_envelope_always_has_results(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that verify JSON envelope always has 'results' present across clean and error states."""
    # 1. Clean store
    f1 = tmp_path / "inbox" / "item.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("test item", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1
    assert data["results"][0]["receipts"] == 1
    assert data["results"][0]["objects"] == 1

    # 2. Corrupt store (tamper with object)
    obj_files = list((store_root / "objects").rglob("[0-9a-f]" * 64))
    assert len(obj_files) == 1
    obj_files[0].write_bytes(b"corrupted bytes")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    data_err = json.loads(captured.out)
    assert "results" in data_err
    assert isinstance(data_err["results"], list)
    assert data_err["corrupt"] == 1


def test_verify_strict_object_layout_and_uppercase_rejection(
    store_root: Path, tmp_path: Path
) -> None:
    """Test that nested object layouts and uppercase names/hashes are detected as corrupt_object."""
    f1 = tmp_path / "inbox" / "file.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("content", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)
    sha = res["sha256"]

    from secondbrain.verify import verify_repository

    # 1. Plant an uppercase object name in a new prefix directory
    upper_dir = store_root / "objects" / "ee"
    upper_dir.mkdir(parents=True, exist_ok=True)
    uppercase_sha = "ee" + ("A" * 62)
    upper_obj = upper_dir / uppercase_sha
    upper_obj.write_bytes(b"uppercase content")

    report = verify_repository(store_root)
    assert report["corrupt"] >= 1
    assert any("uppercase" in str(p.get("error", "")).lower() or uppercase_sha in p.get("id", "") for p in report["problems"])
    upper_obj.unlink()

    # 2. Plant a nested directory inside prefix directory
    nested_dir = store_root / "objects" / sha[:2] / "nested_sub"
    nested_dir.mkdir(parents=True, exist_ok=True)
    (nested_dir / "bad.txt").write_bytes(b"nested")

    report2 = verify_repository(store_root)
    assert report2["corrupt"] >= 1
    assert any("nested" in str(p.get("error", "")).lower() for p in report2["problems"])


def test_verify_duplicate_receipt_ids_and_filename_mismatch(
    store_root: Path, tmp_path: Path
) -> None:
    """Test that duplicate receipt IDs and filename/ID mismatches are detected as invalid_receipt."""
    f1 = tmp_path / "inbox" / "file.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("content", encoding="utf-8")
    res = capture_file(f1, store_root, __version__)
    rec_id = res["id"]

    from secondbrain.verify import verify_repository

    receipt_file = store_root / "receipts" / "v1" / f"{rec_id}.json"
    rec_data = json.loads(receipt_file.read_text(encoding="utf-8"))

    # 1. Filename / ID mismatch
    mismatched_file = store_root / "receipts" / "v1" / f"cap-20261012t120000z-{res['sha256'][:8]}.json"
    mismatched_file.write_text(json.dumps(rec_data), encoding="utf-8")

    report = verify_repository(store_root)
    assert report["invalid_receipts"] >= 1
    assert any("mismatch" in str(p.get("error", "")).lower() for p in report["problems"])
    mismatched_file.unlink()

    # 2. Duplicate receipt ID under another filename
    dup_file = store_root / "receipts" / "v1" / f"{rec_id}-2.json"
    dup_data = dict(rec_data)  # has id == rec_id, but different file
    dup_file.write_text(json.dumps(dup_data), encoding="utf-8")

    report2 = verify_repository(store_root)
    assert report2["invalid_receipts"] >= 1
    dup_file.unlink()


def test_verify_strict_store_check_missing_directories(
    store_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that missing or non-directory objects/, receipts/, or receipts/v1/ is an error ('not a SecondBrain store', exit 2)."""
    # 1. Bare store root without objects/ and receipts/
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 2
    err_text = capsys.readouterr().err.lower()
    assert "not a secondbrain store" in err_text

    # 2. Has objects/ but missing receipts/
    (store_root / "objects").mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 2
    err_text = capsys.readouterr().err.lower()
    assert "not a secondbrain store" in err_text

    # 3. Has objects/ and receipts/ present but receipts/v1/ missing
    (store_root / "receipts").mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 2
    err_text = capsys.readouterr().err.lower()
    assert "not a secondbrain store" in err_text

    # 4. Has receipts/v1 but objects is a regular file
    import shutil
    shutil.rmtree(store_root / "objects")
    (store_root / "receipts" / "v1").mkdir(parents=True, exist_ok=True)
    (store_root / "objects").write_text("i am a file not a directory")
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 2
    err_text = capsys.readouterr().err.lower()
    assert "not a secondbrain store" in err_text

    # 5. Clean when layout directories exist (an EMPTY but valid store created by capture)
    (store_root / "objects").unlink()
    (store_root / "objects").mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 0


def test_verify_mixed_io_and_integrity_failures_reports_both_exits_2(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test mixed IO and integrity failures: report both, exit code = 2 if any IO error else 1."""
    # Capture two files
    f1 = tmp_path / "inbox" / "file1.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("file 1 content", encoding="utf-8")
    res1 = capture_file(f1, store_root, __version__)

    f2 = tmp_path / "inbox" / "file2.txt"
    f2.write_text("file 2 content", encoding="utf-8")
    res2 = capture_file(f2, store_root, __version__)

    sha1 = res1["sha256"]
    sha2 = res2["sha256"]

    # 1. Cause integrity failure on sha1 (flip byte)
    obj1 = store_root / "objects" / sha1[:2] / sha1
    content = bytearray(obj1.read_bytes())
    content[0] ^= 0x01
    obj1.write_bytes(bytes(content))

    # 2. Cause IO error on sha2
    from secondbrain import verify as verify_mod
    original_compute = verify_mod.compute_sha256
    obj2 = store_root / "objects" / sha2[:2] / sha2

    def failing_compute(path: Path) -> str:
        if path.resolve() == obj2.resolve():
            raise PermissionError("Simulated locked file / sharing violation")
        return original_compute(path)

    monkeypatch.setattr(verify_mod, "compute_sha256", failing_compute)

    # Human-readable output check
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 2  # Exit code 2 because of IO error precedence!
    captured = capsys.readouterr()
    err_out = captured.out + captured.err
    assert "corrupt" in err_out.lower()
    assert "io_error" in err_out.lower() or "locked file" in err_out.lower()

    # JSON output check: both problems and io_errors must be reported
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 2
    captured_json = capsys.readouterr()
    data = json.loads(captured_json.out)
    assert len(data["problems"]) >= 1
    assert any(p["code"] == "corrupt_object" for p in data["problems"])
    assert len(data["io_errors"]) >= 1
    assert any(p["code"] == "io_error" for p in data["io_errors"])


def test_verify_orphan_reconciliation_rescans_receipts(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test orphan reconciliation: re-scan receipts once more after object scan so publication completing between scans is not reported as orphan."""
    # Capture an initial file so store is valid
    f1 = tmp_path / "inbox" / "base.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("base", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # Place an object directly in objects/
    import hashlib
    content = b"concurrent publication item"
    sha = hashlib.sha256(content).hexdigest().lower()
    obj_dir = store_root / "objects" / sha[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    obj_file = obj_dir / sha
    obj_file.write_bytes(content)

    from secondbrain import verify as verify_mod
    original_scan_objects = verify_mod.scan_objects

    receipt_published_during_verify = False

    def hook_scan_objects(root: Path) -> Any:
        # Run normal scan objects first (object is seen)
        res = original_scan_objects(root)
        # Now simulate publication completing between scans: publish receipt and release lock!
        nonlocal receipt_published_during_verify
        rec_data = {
            "id": f"cap-20261012t150000z-{sha[:8]}",
            "sha256": sha,
            "original_name": "completed_item.txt",
            "source_path": str(tmp_path / "inbox" / "completed_item.txt"),
            "collected_at": "2026-10-12T15:00:00+00:00",
            "tool_version": __version__,
        }
        rec_path = store_root / "receipts" / "v1" / f"{rec_data['id']}.json"
        rec_path.write_text(json.dumps(rec_data), encoding="utf-8")
        receipt_published_during_verify = True
        return res

    monkeypatch.setattr(verify_mod, "scan_objects", hook_scan_objects)

    report = verify_mod.verify_repository(store_root)
    assert receipt_published_during_verify is True
    # The item must NOT be reported as an orphan!
    assert report["status"] == "ok"
    assert report["orphan"] == 0
    assert len(report["problems"]) == 0


def test_verify_orphans_reported_as_possible_concurrent_activity_when_writer_locked(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When a writer lock is observed, unreferenced objects are reported with severity 'possible_concurrent_activity' (exit 0)."""
    import hashlib
    from secondbrain.lock import WriterLock

    f1 = tmp_path / "inbox" / "seed.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("seed file", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # Place an unreferenced object
    orphan_bytes = b"in-flight capture payload"
    sha = hashlib.sha256(orphan_bytes).hexdigest().lower()
    obj_dir = store_root / "objects" / sha[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    (obj_dir / sha).write_bytes(orphan_bytes)

    # 1. With WriterLock held: verify exits 0, reports severity 'possible_concurrent_activity' in text and JSON
    with WriterLock(store_root):
        with pytest.raises(SystemExit) as exc_info:
            main(["--root", str(store_root), "verify"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "possible_concurrent_activity" in captured.out
        assert sha in captured.out

        with pytest.raises(SystemExit) as exc_info:
            main(["--root", str(store_root), "--json", "verify"])
        assert exc_info.value.code == 0
        captured_json = capsys.readouterr()
        data = json.loads(captured_json.out)
        assert data["status"] == "ok"
        assert data["orphan"] == 0
        assert len(data["concurrent_activity"]) >= 1
        ca_item = next(ca for ca in data["concurrent_activity"] if ca["id"] == sha)
        assert ca_item["severity"] == "possible_concurrent_activity"

    # 2. When lock is released and scan is stable: same unreferenced object is a hard orphan (exit 1)
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 1
    captured_err = capsys.readouterr()
    assert "FAIL" in captured_err.out
    assert "orphan=1" in captured_err.out


def test_verify_unstable_scan_reports_possible_concurrent_activity(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """When the scan is not stable (receipts changed between scans), unreferenced objects are reported with severity 'possible_concurrent_activity'."""
    import hashlib

    # Initialize store with valid directories
    f1 = tmp_path / "inbox" / "file1.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("initial", encoding="utf-8")
    capture_file(f1, store_root, __version__)

    # Plant two objects: obj1 will receive a receipt during reconciliation pass, obj2 will remain unreferenced
    content1 = b"object one"
    sha1 = hashlib.sha256(content1).hexdigest().lower()
    (store_root / "objects" / sha1[:2]).mkdir(parents=True, exist_ok=True)
    (store_root / "objects" / sha1[:2] / sha1).write_bytes(content1)

    content2 = b"object two without receipt"
    sha2 = hashlib.sha256(content2).hexdigest().lower()
    (store_root / "objects" / sha2[:2]).mkdir(parents=True, exist_ok=True)
    (store_root / "objects" / sha2[:2] / sha2).write_bytes(content2)

    from secondbrain import verify as verify_mod
    original_scan_receipts = verify_mod.scan_receipts

    def hook_scan_receipts(root: Path) -> Any:
        res = original_scan_receipts(root)
        # Publish receipt for sha1 after initial receipt scan so reconciliation pass detects mutation
        rec1_data = {
            "id": f"cap-20261012t160000z-{sha1[:8]}",
            "sha256": sha1,
            "original_name": "item1.txt",
            "source_path": str(tmp_path / "inbox" / "item1.txt"),
            "collected_at": "2026-10-12T16:00:00+00:00",
            "tool_version": __version__,
        }
        rec1_path = store_root / "receipts" / "v1" / f"{rec1_data['id']}.json"
        rec1_path.write_text(json.dumps(rec1_data), encoding="utf-8")
        return res

    monkeypatch.setattr(verify_mod, "scan_receipts", hook_scan_receipts)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "verify"])
    assert exc_info.value.code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "ok"
    assert data["orphan"] == 0
    assert any(
        ca["id"] == sha2 and ca["severity"] == "possible_concurrent_activity"
        for ca in data["concurrent_activity"]
    )

