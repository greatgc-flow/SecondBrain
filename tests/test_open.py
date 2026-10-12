"""Tests for sb open command and working copy isolation."""

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


def test_open_by_receipt_id_print_path(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test sb open <receipt_id> --print-path outputs the working copy path."""
    f1 = tmp_path / "inbox" / "notes.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("my notes", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    path_str = captured.out.strip()
    working_path = Path(path_str)
    assert working_path.is_file()
    assert working_path.read_text(encoding="utf-8") == "my notes"
    # Ensure it's under cache/open/<receipt_id>/notes.txt
    expected_parent = store_root / "cache" / "open" / receipt_id.lower()
    assert working_path.parent == expected_parent
    assert working_path.name == "notes.txt"


def test_open_by_sha256_prefix(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test sb open by sha256 prefix (>= 8 hex characters)."""
    f1 = tmp_path / "inbox" / "contract.pdf"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_bytes(b"%PDF-1.4 sample pdf content")

    res = capture_file(f1, store_root, __version__)
    sha256 = res["sha256"]
    prefix = sha256[:8]

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", prefix, "--print-path"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    working_path = Path(captured.out.strip())
    assert working_path.is_file()
    assert working_path.read_bytes() == b"%PDF-1.4 sample pdf content"


def test_open_json_output(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test sb open with --json flag."""
    f1 = tmp_path / "inbox" / "data.csv"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("a,b,c\n1,2,3\n", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "ok"
    assert data["id"] == receipt_id
    assert Path(data["path"]).is_file()
    assert data["opened"] is False


def test_open_launches_viewer_mocked(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that sb open launches the viewer when --print-path is not specified."""
    f1 = tmp_path / "inbox" / "view_me.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("view me content", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]

    launched_paths: list[str] = []

    from secondbrain import open_cmd

    monkeypatch.setattr(open_cmd, "launch_viewer", lambda path: launched_paths.append(str(path)))

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"verified {receipt_id}" in captured.out
    assert len(launched_paths) == 1
    assert Path(launched_paths[0]).is_file()


def test_open_tamper_detected_before_open(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that hash verification runs FIRST; tamper triggers exit 1 and nothing is opened."""
    f1 = tmp_path / "inbox" / "secret.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("top secret", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]
    sha = res["sha256"]

    # Tamper with the object
    obj_path = store_root / "objects" / sha[:2] / sha
    obj_path.write_bytes(b"tampered content")

    launched_paths: list[str] = []
    from secondbrain import open_cmd

    monkeypatch.setattr(open_cmd, "launch_viewer", lambda path: launched_paths.append(str(path)))

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id])
    assert exc_info.value.code == 1
    assert len(launched_paths) == 0

    # Ensure nothing was created in cache/open
    cache_open_dir = store_root / "cache" / "open" / receipt_id.lower()
    assert not cache_open_dir.exists()

    # Also test with --json
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "--json", "open", receipt_id])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "error"
    assert "tamper" in data["error"].lower() or "mismatch" in data["error"].lower()


def test_open_missing_object_fails_integrity(
    store_root: Path, tmp_path: Path
) -> None:
    """Test that a missing object fails with exit code 1."""
    f1 = tmp_path / "inbox" / "deleted.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("delete object", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]
    sha = res["sha256"]

    obj_path = store_root / "objects" / sha[:2] / sha
    obj_path.unlink()

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id])
    assert exc_info.value.code == 1


def test_open_ambiguous_prefix_fails(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that an ambiguous prefix lists candidates and exits with code 2."""
    f1 = tmp_path / "inbox" / "file1.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("content 1", encoding="utf-8")
    res1 = capture_file(f1, store_root, __version__)

    # Create a duplicate capture or synthetic receipt with matching sha256 prefix
    receipt1_path = store_root / "receipts" / "v1" / f"{res1['id']}.json"
    r1_data = json.loads(receipt1_path.read_text(encoding="utf-8"))

    # Create second receipt pointing to same sha or starting with same prefix
    r2_data = dict(r1_data)
    r2_id = res1["id"] + "-2"
    r2_data["id"] = r2_id
    receipt2_path = store_root / "receipts" / "v1" / f"{r2_id}.json"
    receipt2_path.write_text(json.dumps(r2_data), encoding="utf-8")

    prefix = res1["sha256"][:8]

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", prefix])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    err_text = captured.out + captured.err
    assert "ambiguous" in err_text.lower()
    assert res1["id"] in err_text
    assert r2_id in err_text


def test_open_short_prefix_fails(store_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that sha256 prefix shorter than 8 hex characters exits 2."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", "ba7816b"])  # 7 hex chars
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "at least 8" in (captured.out + captured.err).lower()


def test_open_nonexistent_id_fails(store_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that a nonexistent receipt ID exits 2."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", "cap-20261012t000000z-deadbeef"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "not found" in (captured.out + captured.err).lower()


def test_open_korean_filename(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test opening a file with Korean name preserves NFC form in working copy."""
    korean_name = "계약서_최종_2026년.txt"
    f1 = tmp_path / "inbox" / korean_name
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("한국어 내용 테스트", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    working_path = Path(captured.out.strip())
    assert working_path.is_file()
    assert working_path.name == korean_name
    assert working_path.read_text(encoding="utf-8") == "한국어 내용 테스트"


def test_open_windows_reserved_names_sanitised(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that Windows reserved names (CON, NUL, AUX, etc.) and trailing dots are sanitised."""
    test_cases = [
        ("CON.txt", "_CON.txt"),
        ("aux.md", "_aux.md"),
        ("nul", "_nul"),
        ("com1.log", "_com1.log"),
        ("trailing_dot.", "trailing_dot"),
    ]

    for orig_name, expected_name in test_cases:
        # Create source with a safe name on disk first
        safe_source = tmp_path / "inbox" / "temp.txt"
        safe_source.parent.mkdir(parents=True, exist_ok=True)
        safe_source.write_text(f"content for {orig_name}", encoding="utf-8")

        res = capture_file(safe_source, store_root, __version__)
        receipt_id = res["id"]

        # Modify receipt to simulate original_name being the reserved/trailing name
        receipt_path = store_root / "receipts" / "v1" / f"{receipt_id}.json"
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
        data["original_name"] = orig_name
        receipt_path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            main(["--root", str(store_root), "open", receipt_id, "--print-path"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        working_path = Path(captured.out.strip())
        assert working_path.is_file()
        assert working_path.name == expected_name


def test_open_working_copy_isolated_from_object(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that modifying working copy never mutates the original object."""
    f1 = tmp_path / "inbox" / "original.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("immutable original", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]
    sha = res["sha256"]

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    working_path = Path(captured.out.strip())

    # User modifies working copy (removes convenience read-only marker first)
    import stat
    import os
    os.chmod(working_path, stat.S_IWRITE | stat.S_IREAD)
    working_path.write_text("tampered working copy", encoding="utf-8")

    # The store object is completely unchanged
    obj_path = store_root / "objects" / sha[:2] / sha
    assert obj_path.read_text(encoding="utf-8") == "immutable original"

    # sb verify still exits 0 clean
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 0


def test_open_executable_association_policy(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test launch policy: refuse .bat/.exe/.cmd/.ps1/.lnk unless --force-launch; --print-path always works."""
    script_file = tmp_path / "inbox" / "deploy.bat"
    script_file.parent.mkdir(parents=True, exist_ok=True)
    script_file.write_text("@echo off\r\necho deploy\r\n", encoding="utf-8")

    res = capture_file(script_file, store_root, __version__)
    receipt_id = res["id"]

    launched_calls: list[str] = []
    from secondbrain import open_cmd

    monkeypatch.setattr(open_cmd, "launch_viewer", lambda path: launched_calls.append(str(path)))

    # 1. Plain sb open refuses launch and exits 2
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    err_out = captured.out + captured.err
    assert "refusing to launch" in err_out.lower()
    assert "--force-launch" in err_out
    assert len(launched_calls) == 0

    # 2. --print-path always works and exits 0
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    printed_path = Path(captured.out.strip())
    assert printed_path.is_file()
    assert printed_path.name == "deploy.bat"
    assert len(launched_calls) == 0

    # 3. --force-launch overrides refusal and launches
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--force-launch"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"verified {receipt_id}" in captured.out
    assert len(launched_calls) == 1
    assert Path(launched_calls[0]).name == "deploy.bat"


def test_open_executable_bypass_shapes(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test each launch policy bypass shape: case, trailing dot/space, double extension, NTFS stream, empty suffix."""
    from secondbrain import open_cmd

    launched_calls: list[str] = []
    monkeypatch.setattr(open_cmd, "launch_viewer", lambda path: launched_calls.append(str(path)))

    bypass_names = [
        "PAYLOAD.EXE",        # case
        "script.BAT",         # case
        "app.exe.",           # trailing dot
        "script.bat ",        # trailing space
        ".exe. ",             # trailing dot and space on dot-name
        "a.pdf.exe",          # double extension
        "a.txt:x.exe",        # NTFS stream
        ".exe",               # empty Path.suffix name
        ".bat",               # empty Path.suffix name
        ".jse",               # empty Path.suffix name and extended list
        "test.psm1",          # extended list
        "test.vbe",           # extended list
        "test.wsf",           # extended list
        "test.gadget",        # extended list
        "test.application",   # extended list
        "test.jar",           # extended list
        "test.reg",           # extended list
    ]

    for idx, name in enumerate(bypass_names):
        launched_calls.clear()
        f = tmp_path / "inbox" / f"f_{idx}.bin"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"content {idx}", encoding="utf-8")

        res = capture_file(f, store_root, __version__)
        receipt_id = res["id"]

        # Modify original_name in receipt to test the bypass shape
        receipt_path = store_root / "receipts" / "v1" / f"{receipt_id}.json"
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
        data["original_name"] = name
        receipt_path.write_text(json.dumps(data), encoding="utf-8")

        # Refusal without --force-launch (exit 2)
        with pytest.raises(SystemExit) as exc_info:
            main(["--root", str(store_root), "open", receipt_id])
        assert exc_info.value.code == 2, f"Failed to block bypass shape: {name}"
        captured = capsys.readouterr()
        err_text = captured.out + captured.err
        assert "refusing to launch" in err_text.lower()
        assert "--force-launch" in err_text
        assert len(launched_calls) == 0

        # --print-path succeeds
        with pytest.raises(SystemExit) as exc_info:
            main(["--root", str(store_root), "open", receipt_id, "--print-path"])
        assert exc_info.value.code == 0
        capsys.readouterr()

        # --force-launch succeeds and launches
        with pytest.raises(SystemExit) as exc_info:
            main(["--root", str(store_root), "open", receipt_id, "--force-launch"])
        assert exc_info.value.code == 0
        capsys.readouterr()
        assert len(launched_calls) == 1


def test_open_viewer_allow_list(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test allow-list: allowed types launch by default; excluded types (zip, etc.) require --force-launch."""
    from secondbrain import open_cmd

    launched_calls: list[str] = []
    monkeypatch.setattr(open_cmd, "launch_viewer", lambda path: launched_calls.append(str(path)))

    allowed_exts = [
        "txt", "md", "pdf", "png", "jpg", "jpeg", "gif", "webp", "bmp", "tif",
        "tiff", "svg", "csv", "json", "log", "html", "htm", "eml", "docx", "xlsx",
        "pptx", "mp3", "mp4", "m4a", "wav", "mov", "mkv", "webm"
    ]

    # Sample test across allow-list
    for ext in ["txt", "md", "pdf", "png", "json", "docx", "mp4"]:
        launched_calls.clear()
        f = tmp_path / "inbox" / f"sample.{ext}"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("data", encoding="utf-8")
        res = capture_file(f, store_root, __version__)
        with pytest.raises(SystemExit) as exc_info:
            main(["--root", str(store_root), "open", res["id"]])
        assert exc_info.value.code == 0
        capsys.readouterr()
        assert len(launched_calls) == 1

    # ZIP is explicitly excluded from allow-list -> requires --force-launch
    f_zip = tmp_path / "inbox" / "archive.zip"
    f_zip.parent.mkdir(parents=True, exist_ok=True)
    f_zip.write_bytes(b"PK\x03\x04zipdata")
    res_zip = capture_file(f_zip, store_root, __version__)

    launched_calls.clear()
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", res_zip["id"]])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "refusing to launch" in (captured.out + captured.err).lower()
    assert len(launched_calls) == 0

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", res_zip["id"], "--force-launch"])
    assert exc_info.value.code == 0
    capsys.readouterr()
    assert len(launched_calls) == 1


def test_open_reparse_point_rejection(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that open rejects reparse point leaves and ancestors."""
    f1 = tmp_path / "inbox" / "safe.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("safe content", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]

    from secondbrain import open_cmd

    # Test reparse point leaf rejection
    working_dir = store_root / "cache" / "open" / receipt_id.lower()
    working_dir.mkdir(parents=True, exist_ok=True)
    symlink_leaf = working_dir / "safe.txt"

    # Simulate leaf being a reparse point
    monkeypatch.setattr(open_cmd, "is_reparse_point", lambda path: path == symlink_leaf)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 1  # Integrity error on reparse point leaf


def test_open_toctou_copy_tamper_detected(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that corrupting destination after copy (hook between copy and hash check) triggers exit 1."""
    f1 = tmp_path / "inbox" / "doc.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("doc content", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]

    from secondbrain import open_cmd

    hook_called = False

    def corrupt_destination_after_copy(staging_path: Path) -> None:
        nonlocal hook_called
        hook_called = True
        assert staging_path.is_file(), "Staging destination file must exist before tampering"
        staging_path.write_bytes(b"tampered bytes in destination staging file")

    monkeypatch.setattr(open_cmd, "_test_hook_after_copy", corrupt_destination_after_copy)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 1
    assert hook_called is True


def test_open_preserves_existing_working_copy_on_failure(
    store_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that existing working copy is preserved if subsequent copy/verification fails."""
    f1 = tmp_path / "inbox" / "notes.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("original valid notes", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]

    # 1. First open succeeds and establishes working copy
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 0
    working_path = Path(capsys.readouterr().out.strip())
    assert working_path.is_file()
    assert working_path.read_text(encoding="utf-8") == "original valid notes"

    from secondbrain import open_cmd

    # 2. Corrupt destination after copy on subsequent open
    def corrupt_destination_after_copy(staging_path: Path) -> None:
        staging_path.write_bytes(b"tampered staging bytes")

    monkeypatch.setattr(open_cmd, "_test_hook_after_copy", corrupt_destination_after_copy)

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 1

    # 3. Existing working copy must NOT be lost or deleted!
    assert working_path.is_file()
    assert working_path.read_text(encoding="utf-8") == "original valid notes"


def test_open_malformed_receipt_json_fails_cleanly(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that valid JSON with malformed receipt schema produces exit 1 and does not crash."""
    f1 = tmp_path / "inbox" / "file.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("test", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]

    # Write valid JSON with missing sha256 and wrong types
    receipt_file = store_root / "receipts" / "v1" / f"{receipt_id}.json"
    receipt_file.write_text('{"id": 12345, "invalid_schema": true}', encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "integrity error" in (captured.out + captured.err).lower()


def test_open_staged_copy_is_read_only(
    store_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that staged working copy is set read-only (os.chmod / FILE_ATTRIBUTE_READONLY) before launch."""
    import stat
    import sys

    f1 = tmp_path / "inbox" / "document.txt"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("read-only document", encoding="utf-8")

    res = capture_file(f1, store_root, __version__)
    receipt_id = res["id"]

    # 1. Open stages copy and sets read-only
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 0
    working_path = Path(capsys.readouterr().out.strip())
    assert working_path.is_file()

    # Check read-only mode flag
    st_mode = working_path.stat().st_mode
    assert (st_mode & stat.S_IWRITE) == 0, "Working copy must be read-only"

    # On Windows, verify Win32 FILE_ATTRIBUTE_READONLY (0x1)
    if sys.platform == "win32":
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(working_path))
        assert attrs != -1 and (attrs & 0x1) != 0, "FILE_ATTRIBUTE_READONLY must be set on Windows"

    # Direct modification fails with PermissionError / OSError
    with pytest.raises(OSError):
        working_path.write_text("forbidden write", encoding="utf-8")

    # 2. Re-running open successfully overwrites existing read-only working copy and leaves it read-only
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id, "--print-path"])
    assert exc_info.value.code == 0
    re_opened_path = Path(capsys.readouterr().out.strip())
    assert re_opened_path.is_file()
    assert (re_opened_path.stat().st_mode & stat.S_IWRITE) == 0
    assert re_opened_path.read_text(encoding="utf-8") == "read-only document"


