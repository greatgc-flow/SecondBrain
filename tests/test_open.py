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

    launched = False
    from secondbrain import open_cmd

    monkeypatch.setattr(open_cmd, "launch_viewer", lambda path: globals().update(launched=True))

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "open", receipt_id])
    assert exc_info.value.code == 1
    assert not launched

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
    r2_id = res1["id"] + "-copy"
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

    # User modifies working copy
    working_path.write_text("tampered working copy", encoding="utf-8")

    # The store object is completely unchanged
    obj_path = store_root / "objects" / sha[:2] / sha
    assert obj_path.read_text(encoding="utf-8") == "immutable original"

    # sb verify still exits 0 clean
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(store_root), "verify"])
    assert exc_info.value.code == 0
