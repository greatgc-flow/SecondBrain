"""End-to-end acceptance test suite for SecondBrain M1 (Step S5).

Marker-free test suite driving the real CLI (subprocess python -m secondbrain ... with --json).
Tests ~100 mixed files (Korean names, spaces, long paths, duplicates, empty, locked),
full lifecycle (capture -> verify -> find -> open -> backup -> wipe -> restore -> verify -> find),
interruption recovery at multiple stages for capture and backup,
and cloud-synced backup root with simulated st_nlink == 0.
"""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest


def make_tiny_text_pdf(text: str) -> bytes:
    """Generate a minimal valid text PDF containing the given ASCII text."""
    content_stream = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode("ascii")
    length = len(content_stream)
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /Resources <</Font <</F1 4 0 R>>>> /MediaBox [0 0 612 792] /Contents 5 0 R>> endobj\n"
        b"4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"5 0 obj <</Length " + str(length).encode("ascii") + b">> stream\n"
        + content_stream + b"\nendstream\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"00000000115 00000 n \n"
        b"0000000229 00000 n \n"
        b"0000000300 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\n"
        b"startxref\n400\n%%EOF\n"
    )
    return pdf


def wipe_tree(path: Path) -> None:
    """Recursively wipe a directory tree, clearing read-only flags on Windows."""
    if not path.exists():
        return
    for root_dir, dirs, files in os.walk(path, topdown=False):
        for f in files:
            fp = Path(root_dir) / f
            try:
                os.chmod(fp, stat.S_IWRITE)
                fp.unlink()
            except OSError:
                pass
        for d in dirs:
            dp = Path(root_dir) / d
            try:
                dp.rmdir()
            except OSError:
                pass


def run_cli(
    args: list[str],
    env_overrides: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> tuple[int, dict[str, Any] | None, str, str]:
    """Execute `python -m secondbrain <args>` via subprocess and parse JSON stdout."""
    env = dict(os.environ)
    # Ensure current source tree is prioritized in PYTHONPATH
    src_dir = str(Path(__file__).resolve().parents[1] / "src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = src_dir

    if env_overrides:
        env.update(env_overrides)

    cmd = [sys.executable, "-m", "secondbrain", *args]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=timeout,
    )

    json_data: dict[str, Any] | None = None
    if proc.stdout.strip():
        try:
            json_data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass

    return proc.returncode, json_data, proc.stdout, proc.stderr


def create_acceptance_dataset(
    base_dir: Path,
) -> tuple[list[Path], Path | None, list[str]]:
    """Create ~100 mixed files covering all required categories.

    Categories:
    - Korean names (.txt, .md, .png)
    - Spaces in names (.txt, .md)
    - Long paths (>200 chars if OS allows, else skipped with reason)
    - Duplicates (same bytes, different names)
    - Empty files (0 bytes)
    - Binary files (.png, .bin)
    - Text PDFs (.pdf)
    - Locked file placeholder (returned separately for locking)
    """
    files: list[Path] = []
    skipped_reasons: list[str] = []

    # 1. Plain text with Korean and English content (40 files)
    korean_words = [
        "기획서", "보고서", "회의록", "계약서", "일기", "메모", "영수증", "분석표",
        "명세서", "제안서", "지침서", "매뉴얼", "동의서", "확인서", "소견서",
    ]
    for i in range(20):
        kw = korean_words[i % len(korean_words)]
        p = base_dir / f"문서_{i:02d}_{kw}.txt"
        p.write_text(
            f"안녕하세요 대한민국 2026 SecondBrain 개인 아카이브 테스트 {kw} 내용 {i}번입니다.\n주요 안건과 검토 사항이 포함되어 있습니다.",
            encoding="utf-8",
        )
        files.append(p)

    english_words = [
        "architecture", "contract", "financial", "meeting", "protocol",
        "acceptance", "verification", "milestone", "preservation", "evidence",
        "blueprint", "security", "encryption", "benchmark", "analysis",
    ]
    for i in range(20):
        ew = english_words[i % len(english_words)]
        p = base_dir / f"document_{i:02d}_{ew}.txt"
        p.write_text(
            f"SecondBrain v0.1 personal knowledge preservation repository test.\nCategory: {ew} item {i}.\nDeterministic content for integrity verification.",
            encoding="utf-8",
        )
        files.append(p)

    # 2. Markdown files with formatting and spaces in filenames (30 files)
    for i in range(15):
        kw = korean_words[i % len(korean_words)]
        p = base_dir / f"노트 정리 {i:02d} {kw} 최종.md"
        p.write_text(
            f"# {kw} 요약 노트 {i}\n\n- 항목 1: 한국어 마크다운 검색 테스트\n- 항목 2: 색인 및 형태소 테스트 {kw}\n",
            encoding="utf-8",
        )
        files.append(p)

    for i in range(15):
        ew = english_words[i % len(english_words)]
        p = base_dir / f"personal notes {i:02d} {ew} draft.md"
        p.write_text(
            f"# Markdown Note {i}: {ew}\n\n## Section 1\nDetailed research on {ew} and system design.\n",
            encoding="utf-8",
        )
        files.append(p)

    # 3. Small text PDF files (10 files)
    for i in range(10):
        p = base_dir / f"report_{i:02d}_certified.pdf"
        p.write_bytes(make_tiny_text_pdf(f"SecondBrain PDF Report Number {i} Confidential"))
        files.append(p)

    # 4. Small PNG / binary files (10 files)
    # Minimal 1x1 8-bit RGBA PNG
    minimal_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
        b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    for i in range(5):
        p = base_dir / f"이미지_사진_{i:02d}.png"
        p.write_bytes(minimal_png)
        files.append(p)

    for i in range(5):
        p = base_dir / f"binary_sample_{i:02d}.bin"
        p.write_bytes(f"BINARY_MAGIC_{i:03d}\x00\xff\xfe\x01\x02\x03".encode("latin1"))
        files.append(p)

    # 5. Duplicates: distinct names sharing identical bytes (10 files)
    # 5 duplicates of a Korean text file
    dup_korean_content = "완전히 동일한 바이트를 가진 중복 문서 내용입니다. 해시는 공유되고 영수증은 개별 생성됩니다.".encode("utf-8")
    for i in range(5):
        p = base_dir / f"중복문서_복사본_{i:02d}.txt"
        p.write_bytes(dup_korean_content)
        files.append(p)

    # 5 duplicates of an English text file
    dup_english_content = b"Identical byte payload across multiple acquisitions for deduplication test."
    for i in range(5):
        p = base_dir / f"duplicate_copy_{i:02d}_shared.txt"
        p.write_bytes(dup_english_content)
        files.append(p)

    # 6. Empty files (0 bytes) (4 files)
    empty_names = ["empty_korean_빈문서.txt", "empty_english.txt", "empty_note.md", "empty_binary.bin"]
    for name in empty_names:
        p = base_dir / name
        p.write_bytes(b"")
        files.append(p)

    # 7. Long path (>200 chars if OS allows, else skipped with reason) (1 file)
    long_dir = base_dir / ("sub_" + "very_long_nested_path_directory_component_" * 3)
    long_file_path = long_dir / "deeply_nested_long_path_target_document_for_acceptance_testing_exceeding_two_hundred_characters.txt"
    try:
        long_dir.mkdir(parents=True, exist_ok=True)
        long_file_path.write_text("Payload in a very long path (>200 characters).", encoding="utf-8")
        if len(str(long_file_path)) > 200:
            files.append(long_file_path)
        else:
            skipped_reasons.append(f"Long path created but length {len(str(long_file_path))} <= 200")
            files.append(long_file_path)
    except OSError as exc:
        skipped_reasons.append(f"Long path (>200 chars) skipped: OS error '{exc}'")

    # 8. File intended to be locked / open-for-write
    locked_file = base_dir / "시스템_잠금문서_locked.txt"
    locked_file.write_text("이 파일은 캡처 실행 중 쓰기 전용으로 잠겨 있어야 합니다.", encoding="utf-8")
    files.append(locked_file)

    return files, locked_file, skipped_reasons


class WindowsFileLock:
    """Exclusive lock on a file using Windows CreateFileW with FILE_SHARE_NONE."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle: int = -1

    def acquire(self) -> bool:
        if sys.platform != "win32":
            return False
        GENERIC_READ = 0x80000000
        GENERIC_WRITE = 0x40000000
        FILE_SHARE_NONE = 0
        OPEN_EXISTING = 3
        self.handle = ctypes.windll.kernel32.CreateFileW(
            str(self.path),
            GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_NONE,
            None,
            OPEN_EXISTING,
            0,
            None,
        )
        return self.handle != -1 and self.handle != 0

    def release(self) -> None:
        if sys.platform == "win32" and self.handle not in (-1, 0):
            ctypes.windll.kernel32.CloseHandle(self.handle)
            self.handle = -1

    def __enter__(self) -> WindowsFileLock:
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        self.release()


def test_acceptance_m1_full_lifecycle(tmp_path: Path) -> None:
    """End-to-end acceptance test covering the entire SecondBrain M1 lifecycle.

    ~100 mixed files -> capture (with locked file error, then retry convergence)
    -> verify -> find (Korean + English) -> open -> backup (in cloud-synced path)
    -> wipe data root -> restore -> verify -> find again
    -> assert identical hashes, receipt IDs, and counts.
    """
    inbox = tmp_path / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    data_root = tmp_path / "SecondBrain"
    data_root.mkdir(parents=True, exist_ok=True)
    # Cloud-synced-like backup root
    cloud_backup_root = tmp_path / "Google Drive" / "SecondBrainBackup"

    # Step 0: Generate ~100 mixed files
    files, locked_file, skipped = create_acceptance_dataset(inbox)
    total_files = len(files)
    assert total_files >= 90, f"Expected ~100 files, got {total_files}"

    # Step 1: Capture with locked / open-for-write file (Windows) or unreadable file (POSIX)
    file_lock = None
    if sys.platform == "win32":
        if locked_file:
            file_lock = WindowsFileLock(locked_file)
            if not file_lock.acquire():
                pytest.skip("Windows exclusive lock could not be acquired for locked-file simulation")
    elif locked_file:
        os.chmod(locked_file, 0)
        permission_denied = False
        try:
            with open(locked_file, "rb"):
                pass
        except (PermissionError, OSError):
            permission_denied = True
        if not permission_denied:
            os.chmod(locked_file, stat.S_IRUSR | stat.S_IWUSR)
            pytest.skip("chmod(0) did not enforce permission denial (running as privileged/root POSIX)")

    try:
        # Initial capture with locked/unreadable file present: should report error on locked file and exit 2
        rc, out_json, stdout, stderr = run_cli([
            "--root", str(data_root), "--json", "capture", str(inbox)
        ])
        assert rc == 2, f"Expected exit code 2 when locked/unreadable file is present, got {rc}. Stderr: {stderr}"
        assert out_json is not None
        assert out_json["status"] == "error"
        assert out_json["failed"] >= 1
        assert any("locked" in str(e).lower() or "permission" in str(e).lower() for e in out_json["errors"])
        # Completed captures must remain valid per design.md
        assert out_json["captured"] == total_files - 1
    finally:
        if file_lock:
            file_lock.release()
        elif locked_file and sys.platform != "win32":
            os.chmod(locked_file, stat.S_IRUSR | stat.S_IWUSR)

    # Capture the previously locked file now that it is unlocked
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "capture", str(locked_file)
    ])
    assert rc == 0, f"Capture of unlocked file failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert out_json["captured"] == 1

    # Also capture one existing file again to test duplicate acquisition receipt creation with object reuse
    sample_file = files[0]
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "capture", str(sample_file)
    ])
    assert rc == 0
    assert out_json is not None
    assert out_json["captured"] == 1
    assert out_json["reused_objects"] == 1

    expected_total_receipts = total_files + 1

    # Step 2: Verify data root
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "verify"
    ])
    assert rc == 0, f"Verify failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert out_json["status"] == "ok"
    assert out_json["receipts"] == expected_total_receipts
    assert out_json["missing"] == 0
    assert out_json["corrupt"] == 0
    assert out_json["orphan"] == 0
    total_objects_initial = out_json["objects"]
    # Due to duplicates and empty files sharing objects, objects < receipts
    assert total_objects_initial < total_files, "Deduplication failed: objects should be less than receipts"

    # Step 3: Find with Korean and English queries
    # Korean query
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "find", "기획서"
    ])
    assert rc == 0, f"Korean find failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert out_json["status"] == "ok"
    assert len(out_json["results"]) >= 1
    korean_hit_id = out_json["results"][0]["id"]
    assert any("기획서" in r["name"] or "기획서" in r.get("snippet", "") for r in out_json["results"])

    # English query
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "find", "confidential"
    ])
    assert rc == 0, f"English find failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert out_json["status"] == "ok"
    assert len(out_json["results"]) >= 1

    # Short query (< 3 chars) testing LIKE fallback
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "find", "문서"
    ])
    assert rc == 0, f"Short query find failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert out_json["status"] == "ok"
    assert len(out_json["results"]) >= 1

    # Step 4: Open working copy
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "open", korean_hit_id, "--print-path"
    ])
    assert rc == 0, f"Open failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert out_json["status"] == "ok"
    working_copy_path = Path(out_json["path"])
    assert working_copy_path.is_file(), f"Working copy path does not exist: {working_copy_path}"
    # Verify read-only attribute was applied
    file_mode = working_copy_path.stat().st_mode
    assert not (file_mode & stat.S_IWUSR) or (sys.platform == "win32" and not (file_mode & stat.S_IWRITE))

    # Step 5: Backup into cloud-synced folder with simulated st_nlink == 0
    rc, out_json, stdout, stderr = run_cli(
        ["--root", str(data_root), "--json", "backup", "--backup-root", str(cloud_backup_root)],
        env_overrides={"_SB_SIMULATE_NLINK_ZERO": "1"},
    )
    assert rc == 0, f"Backup failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert out_json["status"] == "ok"
    # Check cloud-sync warning and st_nlink==0 warning on stderr
    assert "appears to be cloud-synced" in stderr or "Google Drive" in stderr
    assert "st_nlink is 0" in stderr

    manifest_name = out_json["manifest"]
    assert manifest_name.endswith(".json")
    manifest_path = cloud_backup_root / "manifests" / manifest_name
    assert manifest_path.is_file()

    # Collect fingerprints of pre-wipe state
    pre_wipe_receipts = {
        p.name: json.loads(p.read_text(encoding="utf-8"))
        for p in (data_root / "receipts" / "v1").glob("*.json")
    }
    pre_wipe_objects = {
        p.name: p.read_bytes()
        for p in (data_root / "objects").glob("*/*")
        if p.is_file()
    }
    assert len(pre_wipe_receipts) == expected_total_receipts
    assert len(pre_wipe_objects) == total_objects_initial

    # Step 6: Wipe data root completely
    wipe_tree(data_root)
    data_root.mkdir(parents=True, exist_ok=True)
    assert not any(data_root.iterdir()), "Data root was not cleanly wiped"

    # Step 7: Restore from cloud backup into wiped data root
    rc, out_json, stdout, stderr = run_cli(
        ["--json", "restore", str(cloud_backup_root), "--to", str(data_root)],
        env_overrides={"_SB_SIMULATE_NLINK_ZERO": "1"},
    )
    assert rc == 0, f"Restore failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert out_json["status"] == "ok"
    assert "PASS" in stdout or out_json.get("status") == "ok"
    assert "st_nlink is 0" in stderr

    # Step 8: Verify restored repository
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "verify"
    ])
    assert rc == 0, f"Post-restore verify failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert out_json["status"] == "ok"
    assert out_json["missing"] == 0
    assert out_json["corrupt"] == 0
    assert out_json["orphan"] == 0
    assert out_json["receipts"] == expected_total_receipts
    assert out_json["objects"] == total_objects_initial

    # Step 9: Find again on restored repository (derived index rebuilt & functional)
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "find", "기획서"
    ])
    assert rc == 0, f"Post-restore Korean find failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert len(out_json["results"]) >= 1

    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "find", "confidential"
    ])
    assert rc == 0, f"Post-restore English find failed with code {rc}. Stderr: {stderr}"
    assert out_json is not None
    assert len(out_json["results"]) >= 1

    # Step 10: Assert identical receipt and object hashes between pre-wipe and restored
    post_wipe_receipts = {
        p.name: json.loads(p.read_text(encoding="utf-8"))
        for p in (data_root / "receipts" / "v1").glob("*.json")
    }
    post_wipe_objects = {
        p.name: p.read_bytes()
        for p in (data_root / "objects").glob("*/*")
        if p.is_file()
    }

    assert len(post_wipe_receipts) == len(pre_wipe_receipts)
    assert set(post_wipe_receipts.keys()) == set(pre_wipe_receipts.keys())
    for r_name, r_data in pre_wipe_receipts.items():
        restored_r = post_wipe_receipts[r_name]
        assert restored_r["id"] == r_data["id"]
        assert restored_r["sha256"] == r_data["sha256"]
        assert restored_r["original_name"] == r_data["original_name"]

    assert len(post_wipe_objects) == len(pre_wipe_objects)
    assert set(post_wipe_objects.keys()) == set(pre_wipe_objects.keys())
    for o_name, o_bytes in pre_wipe_objects.items():
        assert post_wipe_objects[o_name] == o_bytes


def test_acceptance_m1_capture_interruption_and_recovery(tmp_path: Path) -> None:
    """Interruption testing: kill capture at several stages, assert rerun converges without corruption or duplicate objects."""
    data_root = tmp_path / "SecondBrain"
    data_root.mkdir(parents=True, exist_ok=True)
    inbox = tmp_path / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    test_file = inbox / "중요한_계약서.txt"
    test_file.write_text("Interruption test payload content with Korean 계약서 2026", encoding="utf-8")

    # Stage 1: Terminate mid-write
    rc, _, _, stderr = run_cli(
        ["--root", str(data_root), "--json", "capture", str(test_file)],
        env_overrides={"_SB_TEST_TERMINATE_STAGE": "mid_write"},
    )
    assert rc == 44, f"Expected exact hook exit code 44 for mid_write, got {rc}. Stderr: {stderr}"
    # Evidence stage was reached: bytes staged, but no object or receipt published
    stage1_tmps = list((data_root / "objects").glob(".sb-tmp-stage-*.tmp"))
    assert len(stage1_tmps) == 1, "Expected one staged temp file at mid_write stage"
    assert stage1_tmps[0].read_bytes() == test_file.read_bytes()
    assert len(list((data_root / "objects").glob("*/*"))) == 0
    assert len(list((data_root / "receipts" / "v1").glob("*.json"))) == 0

    # Rerun converges cleanly
    rc, out_json, _, _ = run_cli(["--root", str(data_root), "--json", "capture", str(test_file)])
    assert rc == 0
    assert out_json is not None and out_json["captured"] == 1
    sha1 = out_json["results"][0]["sha256"]

    # Verify no corruption or orphan
    rc, out_json, _, _ = run_cli(["--root", str(data_root), "--json", "verify"])
    assert rc == 0
    assert out_json is not None
    assert out_json["missing"] == 0 and out_json["corrupt"] == 0 and out_json["orphan"] == 0

    # Stage 2: Terminate after staging (temp file written, but object not yet published)
    file2 = inbox / "후속_문서.txt"
    file2.write_text("Second interruption stage: after staging temp file", encoding="utf-8")
    staged_before = set((data_root / "objects").glob(".sb-tmp-stage-*.tmp"))
    rc, _, _, stderr = run_cli(
        ["--root", str(data_root), "--json", "capture", str(file2)],
        env_overrides={"_SB_TEST_TERMINATE_STAGE": "after_staging"},
    )
    assert rc == 42, f"Expected exact hook exit code 42 for after_staging, got {rc}. Stderr: {stderr}"
    # Evidence stage was reached: complete new temp file, no new object or receipt
    stage2_tmps = set((data_root / "objects").glob(".sb-tmp-stage-*.tmp")) - staged_before
    assert len(stage2_tmps) == 1, "Expected one new staged temp file at after_staging stage"
    assert next(iter(stage2_tmps)).read_bytes() == file2.read_bytes()
    assert len(list((data_root / "objects").glob("*/*"))) == 1
    assert len(list((data_root / "receipts" / "v1").glob("*.json"))) == 1

    # Rerun converges cleanly
    rc, out_json, _, _ = run_cli(["--root", str(data_root), "--json", "capture", str(file2)])
    assert rc == 0
    assert out_json is not None and out_json["captured"] == 1

    rc, out_json, _, _ = run_cli(["--root", str(data_root), "--json", "verify"])
    assert rc == 0
    assert out_json is not None
    assert out_json["missing"] == 0 and out_json["corrupt"] == 0 and out_json["orphan"] == 0

    # Stage 3: Terminate after object publish (object published, receipt not yet written)
    file3 = inbox / "세번째_문서.txt"
    file3.write_text("Third interruption stage: after object published", encoding="utf-8")
    rc, _, _, stderr = run_cli(
        ["--root", str(data_root), "--json", "capture", str(file3)],
        env_overrides={"_SB_TEST_TERMINATE_STAGE": "after_object"},
    )
    assert rc == 43, f"Expected exact hook exit code 43 for after_object, got {rc}. Stderr: {stderr}"
    # Evidence stage was reached: third object published, third receipt not yet written
    stage3_objects = list((data_root / "objects").glob("*/*"))
    assert len(stage3_objects) == 3
    assert any(obj.read_bytes() == file3.read_bytes() for obj in stage3_objects)
    assert len(list((data_root / "receipts" / "v1").glob("*.json"))) == 2

    # At this point, the object exists on disk without a receipt (temporary unreferenced object)
    # Rerun must recognize existing object, reuse it, write receipt, and not duplicate objects
    rc, out_json, _, _ = run_cli(["--root", str(data_root), "--json", "capture", str(file3)])
    assert rc == 0
    assert out_json is not None
    assert out_json["captured"] == 1
    assert out_json["results"][0]["object"] == "reused"

    # Verify must pass with 0 missing, 0 corrupt, 0 orphan
    rc, out_json, _, _ = run_cli(["--root", str(data_root), "--json", "verify"])
    assert rc == 0
    assert out_json is not None
    assert out_json["missing"] == 0 and out_json["corrupt"] == 0 and out_json["orphan"] == 0
    assert out_json["receipts"] == 3
    assert out_json["objects"] == 3


def test_acceptance_m1_backup_interruption_and_recovery(tmp_path: Path) -> None:
    """Interruption testing: kill backup at multiple stages (mid-objects, mid-receipts, before manifest).

    Assert that no partial manifest is published, rerun completes, and restore verifies cleanly.
    """
    data_root = tmp_path / "SecondBrain"
    data_root.mkdir(parents=True, exist_ok=True)
    backup_root = tmp_path / "Backups" / "sb_backup"
    backup_root.mkdir(parents=True, exist_ok=True)
    inbox = tmp_path / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    # Capture 5 distinct files
    for i in range(5):
        f = inbox / f"file_{i:02d}.txt"
        f.write_text(f"Backup interruption payload item {i}", encoding="utf-8")
        run_cli(["--root", str(data_root), "--json", "capture", str(f)])

    # Stage 1: Kill backup mid-objects
    marker_stage1 = tmp_path / "backup_stage1.marker"
    rc, _, _, stderr = run_cli(
        ["--root", str(data_root), "--json", "backup", "--backup-root", str(backup_root)],
        env_overrides={
            "_SB_TEST_BACKUP_TERMINATE_STAGE": "mid_objects",
            "_SB_TEST_BACKUP_MARKER": str(marker_stage1),
        },
    )
    assert rc == 51, f"Expected exact hook exit code 51 for mid_objects, got {rc}. Stderr: {stderr}"
    assert marker_stage1.is_file(), "Evidence marker file was not written for mid_objects stage"
    assert marker_stage1.read_text(encoding="utf-8") == "mid_objects"
    # Evidence stage was reached: at least 1 object was copied, but not all; receipts not copied yet
    stage1_objects = list((backup_root / "objects").glob("*/*"))
    assert 1 <= len(stage1_objects) < 5, f"Expected partial objects in backup root, got {len(stage1_objects)}"
    assert not (backup_root / "receipts" / "v1").exists() or len(list((backup_root / "receipts" / "v1").glob("*.json"))) == 0
    # No manifest must have been created yet
    manifests_dir = backup_root / "manifests"
    assert not manifests_dir.exists() or len(list(manifests_dir.glob("*.json"))) == 0

    # Restoring from this incomplete state must fail cleanly
    restore_target = tmp_path / "restored_attempt_1"
    rc, _, _, _ = run_cli(["--json", "restore", str(backup_root), "--to", str(restore_target)])
    assert rc == 2

    # Stage 2: Kill backup mid-receipts
    marker_stage2 = tmp_path / "backup_stage2.marker"
    rc, _, _, stderr = run_cli(
        ["--root", str(data_root), "--json", "backup", "--backup-root", str(backup_root)],
        env_overrides={
            "_SB_TEST_BACKUP_TERMINATE_STAGE": "mid_receipts",
            "_SB_TEST_BACKUP_MARKER": str(marker_stage2),
        },
    )
    assert rc == 52, f"Expected exact hook exit code 52 for mid_receipts, got {rc}. Stderr: {stderr}"
    assert marker_stage2.is_file(), "Evidence marker file was not written for mid_receipts stage"
    assert marker_stage2.read_text(encoding="utf-8") == "mid_receipts"
    # Evidence stage was reached: all objects copied, partial receipts copied
    assert len(list((backup_root / "objects").glob("*/*"))) == 5
    stage2_receipts = list((backup_root / "receipts" / "v1").glob("*.json"))
    assert 1 <= len(stage2_receipts) < 5, f"Expected partial receipts in backup root, got {len(stage2_receipts)}"
    assert not manifests_dir.exists() or len(list(manifests_dir.glob("*.json"))) == 0

    # Stage 3: Kill backup before manifest publish
    marker_stage3 = tmp_path / "backup_stage3.marker"
    rc, _, _, stderr = run_cli(
        ["--root", str(data_root), "--json", "backup", "--backup-root", str(backup_root)],
        env_overrides={
            "_SB_TEST_BACKUP_TERMINATE_STAGE": "before_manifest",
            "_SB_TEST_BACKUP_MARKER": str(marker_stage3),
        },
    )
    assert rc == 53, f"Expected exact hook exit code 53 for before_manifest, got {rc}. Stderr: {stderr}"
    assert marker_stage3.is_file(), "Evidence marker file was not written for before_manifest stage"
    assert marker_stage3.read_text(encoding="utf-8") == "before_manifest"
    # Evidence stage was reached: all 5 objects, all 5 receipts, and config copied, but no manifest
    assert len(list((backup_root / "objects").glob("*/*"))) == 5
    assert len(list((backup_root / "receipts" / "v1").glob("*.json"))) == 5
    assert len(list((backup_root / "configs").glob("*.json"))) >= 1
    assert not manifests_dir.exists() or len(list(manifests_dir.glob("*.json"))) == 0

    # Rerun backup without termination hook: must converge and publish manifest atomically
    rc, out_json, stdout, stderr = run_cli(
        ["--root", str(data_root), "--json", "backup", "--backup-root", str(backup_root)]
    )
    assert rc == 0, f"Backup completion failed: {stderr}"
    assert out_json is not None
    assert out_json["status"] == "ok"
    manifest_name = out_json["manifest"]
    assert (backup_root / "manifests" / manifest_name).is_file()

    # Restore from converged backup into clean directory
    restore_final = tmp_path / "restored_final"
    rc, out_json, stdout, stderr = run_cli(
        ["--json", "restore", str(backup_root), "--to", str(restore_final)]
    )
    assert rc == 0, f"Restore failed: {stderr}"

    # Verify restored directory
    rc, out_json, _, _ = run_cli(["--root", str(restore_final), "--json", "verify"])
    assert rc == 0
    assert out_json is not None
    assert out_json["missing"] == 0 and out_json["corrupt"] == 0 and out_json["orphan"] == 0
    assert out_json["receipts"] == 5
    assert out_json["objects"] == 5


def test_acceptance_m1_kill_capture_subprocess_mid_write(tmp_path: Path) -> None:
    """Interruption testing: terminate capture subprocess mid-write and assert rerun converges cleanly."""
    data_root = tmp_path / "SecondBrain"
    data_root.mkdir(parents=True, exist_ok=True)
    inbox = tmp_path / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    # Fixture size must exceed one copy chunk (65,536 bytes) so write is genuinely partial
    chunk_size = 65536
    fixture_size = chunk_size * 4  # 256 KiB
    payload_file = inbox / "mid_write_kill_target.bin"
    payload_file.write_bytes(b"A" * fixture_size)
    assert payload_file.stat().st_size > chunk_size, "Hook fixture must exceed one copy chunk"

    marker_file = tmp_path / "mid_write.marker"

    env = dict(os.environ)
    src_dir = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["_SB_TEST_MID_WRITE_MARKER"] = str(marker_file)
    env["_SB_TEST_MID_WRITE_MARKER_BYTES"] = str(chunk_size)

    proc = subprocess.Popen(
        [sys.executable, "-m", "secondbrain", "--root", str(data_root), "--json", "capture", str(payload_file)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for hook to write marker file after partial staged write exceeding one copy chunk
    deadline = time.time() + 5.0
    while not marker_file.exists():
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            pytest.fail(
                f"Capture subprocess exited prematurely ({proc.returncode}). Stderr: {stderr.decode('utf-8', errors='replace')}"
            )
        if time.time() > deadline:
            proc.kill()
            pytest.fail("Timed out waiting for capture mid-write marker file")
        time.sleep(0.01)

    # Marker written: partial staged write confirmed. Terminate process mid-write.
    proc.terminate()
    try:
        proc.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2.0)

    # Evidence of partial staged write: a tool temp file exists with partial bytes
    staged_tmps = list((data_root / "objects").glob(".sb-tmp*"))
    assert len(staged_tmps) >= 1, "Expected partial staged temp file to remain after mid-write termination"
    assert staged_tmps[0].stat().st_size >= chunk_size, "Staged temp file must have received at least one copy chunk"
    assert staged_tmps[0].stat().st_size < fixture_size, "Staged temp write must be partial (less than total fixture size)"

    # Rerun must clean leftover temp files, succeed, and converge cleanly with exit 0
    rc, out_json, stdout, stderr = run_cli([
        "--root", str(data_root), "--json", "capture", str(payload_file)
    ])
    assert rc == 0, f"Rerun failed: {stderr}"
    assert out_json is not None
    assert out_json["captured"] == 1

    # Verify repository has no corruption or orphans
    rc, out_json, _, _ = run_cli(["--root", str(data_root), "--json", "verify"])
    assert rc == 0
    assert out_json is not None
    assert out_json["missing"] == 0 and out_json["corrupt"] == 0 and out_json["orphan"] == 0
    assert out_json["receipts"] == 1
    assert out_json["objects"] == 1

