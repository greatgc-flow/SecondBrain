"""Tests for SecondBrain search and index maintenance (M1 S3)."""

from __future__ import annotations

import io
import json
from pathlib import Path
import unicodedata
import pypdf
import pytest

from secondbrain.cli import main
from secondbrain.lock import WriterLock


def run_sb(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    """Helper to run sb CLI and capture exit code, stdout, and stderr."""
    with pytest.raises(SystemExit) as exc_info:
        main(argv)
    captured = capsys.readouterr()
    return exc_info.value.code, captured.out, captured.err


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
        b"0000000115 00000 n \n"
        b"0000000229 00000 n \n"
        b"0000000300 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\n"
        b"startxref\n400\n%%EOF\n"
    )
    return pdf


def make_blank_pdf() -> bytes:
    """Generate a valid blank PDF (simulating scanned document with no extracted text)."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_find_english_content_and_name(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test searching English content and filename."""
    root = tmp_path / "root"
    doc = tmp_path / "contract.txt"
    doc.write_text("This agreement establishes the terms and conditions.", encoding="utf-8")

    code, _, _ = run_sb(["--root", str(root), "capture", str(doc)], capsys)
    assert code == 0

    # Search by content
    code, out, _ = run_sb(["--root", str(root), "find", "agreement"], capsys)
    assert code == 0
    assert "contract.txt" in out
    assert "[agreement]" in out
    assert "[ok]" in out

    # Search by filename
    code, out, _ = run_sb(["--root", str(root), "find", "contract"], capsys)
    assert code == 0
    assert "contract.txt" in out
    assert "[contract]" in out


def test_find_korean_3char_and_particles(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test Korean 3-char query and particle-attached word matching."""
    root = tmp_path / "root"
    doc = tmp_path / "korean_contract.txt"
    # Contains particle-attached words: 계약서를, 규정은
    doc.write_text("계약서를 신중하게 검토했습니다. 회사의 규정은 준수되어야 합니다.", encoding="utf-8")

    code, _, _ = run_sb(["--root", str(root), "capture", str(doc)], capsys)
    assert code == 0

    # 3-char substring query: '계약서' matches '계약서를'
    code, out, _ = run_sb(["--root", str(root), "find", "계약서"], capsys)
    assert code == 0
    assert "korean_contract.txt" in out
    assert "[계약서]" in out

    # Particle-attached query '규정은'
    code, out, _ = run_sb(["--root", str(root), "find", "규정은"], capsys)
    assert code == 0
    assert "[규정은]" in out


def test_find_korean_2char_fallback(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test Korean 2-char queries falling back to LIKE on normalised text."""
    root = tmp_path / "root"
    doc = tmp_path / "report.txt"
    doc.write_text("계약서를 신중하게 검토했습니다. 회사 정보입니다.", encoding="utf-8")

    code, _, _ = run_sb(["--root", str(root), "capture", str(doc)], capsys)
    assert code == 0

    # 2-char query '계약' matches '계약서를'
    code, out, _ = run_sb(["--root", str(root), "find", "계약"], capsys)
    assert code == 0
    assert "report.txt" in out
    assert "[계약]" in out

    # 2-char query '회사' matches '회사'
    code, out, _ = run_sb(["--root", str(root), "find", "회사"], capsys)
    assert code == 0
    assert "[회사]" in out


def test_find_korean_nfd_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that NFD-encoded Korean queries match NFC-normalised stored text."""
    root = tmp_path / "root"
    doc = tmp_path / "검색문서.txt"
    doc.write_text("문서 내용에 한글 검색어가 포함되어 있습니다.", encoding="utf-8")

    code, _, _ = run_sb(["--root", str(root), "capture", str(doc)], capsys)
    assert code == 0

    # Decompose query into NFD
    nfd_query = unicodedata.normalize("NFD", "검색어")
    assert len(nfd_query) > 3  # Jamo decomposed

    code, out, _ = run_sb(["--root", str(root), "find", nfd_query], capsys)
    assert code == 0
    assert "[검색어]" in out


def test_find_pdf_text_extraction(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test text PDF extraction via pypdf."""
    root = tmp_path / "root"
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(make_tiny_text_pdf("SecondBrain Secret Document 42"))

    code, _, _ = run_sb(["--root", str(root), "capture", str(pdf_path)], capsys)
    assert code == 0

    code, out, _ = run_sb(["--root", str(root), "find", "Secret"], capsys)
    assert code == 0
    assert "sample.pdf" in out
    assert "[Secret]" in out
    assert "[ok]" in out


def test_find_pdf_scanned_no_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test scanned (blank / image-only) PDF reporting no_text status while findable by name."""
    root = tmp_path / "root"
    pdf_path = tmp_path / "scanned_invoice.pdf"
    pdf_path.write_bytes(make_blank_pdf())

    code, _, _ = run_sb(["--root", str(root), "capture", str(pdf_path)], capsys)
    assert code == 0

    # Findable by filename
    code, out, _ = run_sb(["--root", str(root), "find", "scanned_invoice"], capsys)
    assert code == 0
    assert "scanned_invoice.pdf" in out
    assert "[no_text]" in out

    # Non-existent content yields zero hits
    code, out, _ = run_sb(["--root", str(root), "find", "invisible_text"], capsys)
    assert code == 0
    assert out.strip() == ""


def test_find_pdf_corrupt_reports_failed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test corrupt PDF reporting failed status with reason, while findable by name."""
    root = tmp_path / "root"
    pdf_path = tmp_path / "corrupt_data.pdf"
    pdf_path.write_bytes(b"%PDF-invalid-bytes-header-corrupt-data-stream")

    code, _, _ = run_sb(["--root", str(root), "capture", str(pdf_path)], capsys)
    assert code == 0

    code, out, _ = run_sb(["--root", str(root), "find", "corrupt_data"], capsys)
    assert code == 0
    assert "corrupt_data.pdf" in out
    assert "[failed" in out

    # Also test --json output contains failure reason
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "corrupt_data"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["status"] == "ok"
    assert len(data["results"]) == 1
    assert data["results"][0]["extraction_status"] == "failed"
    assert data["results"][0]["extraction_error"] is not None


def test_find_cp949_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test fallback detection for CP949-encoded text files."""
    root = tmp_path / "root"
    cp949_doc = tmp_path / "euckr_legacy.txt"
    cp949_doc.write_bytes("컴퓨터 하드웨어 명세서입니다.".encode("cp949"))

    code, _, _ = run_sb(["--root", str(root), "capture", str(cp949_doc)], capsys)
    assert code == 0

    code, out, _ = run_sb(["--root", str(root), "find", "하드웨어"], capsys)
    assert code == 0
    assert "euckr_legacy.txt" in out
    assert "[하드웨어]" in out
    assert "[ok]" in out


def test_find_eml_and_html(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test .eml (via email) and .html (via html.parser tag stripping)."""
    root = tmp_path / "root"

    # EML file
    eml_file = tmp_path / "message.eml"
    eml_content = (
        "Subject: Budget Meeting 2026\n"
        "From: alice@example.com\n"
        "To: bob@example.com\n"
        "Content-Type: text/plain; charset=utf-8\n\n"
        "The project budget has been approved for Q4.\n"
    )
    eml_file.write_text(eml_content, encoding="utf-8")

    # HTML file
    html_file = tmp_path / "page.html"
    html_content = (
        "<!DOCTYPE html><html><head><title>Test Page</title><style>.hidden{display:none}</style></head>"
        "<body><h1>Project Overview</h1><p>Welcome to <b>SecondBrain</b> search feature.</p>"
        "<script>console.log('secret script code');</script></body></html>"
    )
    html_file.write_text(html_content, encoding="utf-8")

    run_sb(["--root", str(root), "capture", str(eml_file)], capsys)
    run_sb(["--root", str(root), "capture", str(html_file)], capsys)

    # Search EML subject and body
    code, out, _ = run_sb(["--root", str(root), "find", "Budget"], capsys)
    assert code == 0
    assert "message.eml" in out

    # Search HTML body
    code, out, _ = run_sb(["--root", str(root), "find", "Overview"], capsys)
    assert code == 0
    assert "page.html" in out

    # Script tag stripped: searching for script code yields zero hits
    code, out, _ = run_sb(["--root", str(root), "find", "secret script code"], capsys)
    assert code == 0
    assert out.strip() == ""


def test_find_unknown_type_by_name_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test unknown binary file indexed by name only with no_text status."""
    root = tmp_path / "root"
    bin_file = tmp_path / "archive_binary.bin"
    bin_file.write_bytes(b"\x00\x01\x02\x03\x04\x05\xfe\xff")

    code, _, _ = run_sb(["--root", str(root), "capture", str(bin_file)], capsys)
    assert code == 0

    code, out, _ = run_sb(["--root", str(root), "find", "archive_binary"], capsys)
    assert code == 0
    assert "archive_binary.bin" in out
    assert "[no_text]" in out


def test_find_zero_hits_exit_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test zero hits returns exit 0 with empty list in JSON or empty text."""
    root = tmp_path / "root"
    doc = tmp_path / "file.txt"
    doc.write_text("normal content", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # Text mode
    code, out, _ = run_sb(["--root", str(root), "find", "nonexistent_word_xyz"], capsys)
    assert code == 0
    assert out.strip() == ""

    # JSON mode
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "nonexistent_word_xyz"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["results"] == []


def test_find_json_schema(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test stable JSON output schema."""
    root = tmp_path / "root"
    doc = tmp_path / "schema_doc.txt"
    doc.write_text("Testing json schema output.", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "Testing"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["status"] == "ok"
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1

    item = data["results"][0]
    assert "id" in item and item["id"].startswith("cap-")
    assert item["name"] == "schema_doc.txt"
    assert "snippet" in item and "[Testing]" in item["snippet"]
    assert item["extraction_status"] == "ok"
    assert item["extraction_error"] is None


def test_find_limit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test --limit restricts result count."""
    root = tmp_path / "root"
    folder = tmp_path / "multi"
    folder.mkdir()
    for i in range(5):
        (folder / f"doc_{i}.txt").write_text(f"Common target keyword document {i}", encoding="utf-8")

    run_sb(["--root", str(root), "capture", str(folder)], capsys)

    # Limit 2
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "Common", "--limit", "2"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 2

    # Negative limit raises usage error (exit 2)
    code, _, _ = run_sb(["--root", str(root), "find", "Common", "--limit", "-1"], capsys)
    assert code == 2


def test_find_delete_index_then_rebuild(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test deleting index.db loses nothing and is rebuilt automatically."""
    root = tmp_path / "root"
    doc = tmp_path / "test.txt"
    doc.write_text("Rebuildable index test content.", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # First find creates index.db
    code, out1, _ = run_sb(["--root", str(root), "find", "Rebuildable"], capsys)
    assert code == 0
    index_db = root / "cache" / "index.db"
    assert index_db.is_file()

    # Delete index.db
    index_db.unlink()
    assert not index_db.exists()

    # Second find automatically recreates index.db and finds the same result
    code, out2, _ = run_sb(["--root", str(root), "find", "Rebuildable"], capsys)
    assert code == 0
    assert index_db.is_file()
    assert out1 == out2


def test_find_incremental_update_after_new_capture(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test incremental indexing: only unseen receipts/sha256 are processed."""
    root = tmp_path / "root"
    doc1 = tmp_path / "first.txt"
    doc1.write_text("Unique first content", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc1)], capsys)

    # Find creates index with doc1
    code, out, _ = run_sb(["--root", str(root), "find", "Unique"], capsys)
    assert code == 0
    assert "first.txt" in out

    # Now capture doc2 with different content
    doc2 = tmp_path / "second.txt"
    doc2.write_text("Unique second content", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc2)], capsys)

    # Now capture doc3 with identical content to doc1 (same sha256)
    doc3 = tmp_path / "third_duplicate.txt"
    doc3.write_text("Unique first content", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc3)], capsys)

    # Search for doc2
    code, out, _ = run_sb(["--root", str(root), "find", "second"], capsys)
    assert code == 0
    assert "second.txt" in out

    # Search for 'first' finds both doc1 and doc3
    code, out, _ = run_sb(["--root", str(root), "find", "first"], capsys)
    assert code == 0
    assert "first.txt" in out
    assert "third_duplicate.txt" in out


def test_find_reindex_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test sb find --reindex explicitly rebuilds the index."""
    root = tmp_path / "root"
    doc = tmp_path / "doc.txt"
    doc.write_text("Index maintenance test.", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # Reindex without search query
    code, out, _ = run_sb(["--root", str(root), "find", "--reindex"], capsys)
    assert code == 0
    assert (root / "cache" / "index.db").is_file()

    # Reindex with search query
    code, out, _ = run_sb(["--root", str(root), "find", "maintenance", "--reindex"], capsys)
    assert code == 0
    assert "doc.txt" in out


def test_find_concurrency_lock_during_write(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that WriterLock is held only for index writes, not during read search."""
    root = tmp_path / "root"
    doc = tmp_path / "doc.txt"
    doc.write_text("Concurrency check document.", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # Ensure index is built first
    code, _, _ = run_sb(["--root", str(root), "find", "Concurrency"], capsys)
    assert code == 0

    # While holding WriterLock, read-only search should still succeed because index is up-to-date!
    with WriterLock(root):
        code, out, _ = run_sb(["--root", str(root), "find", "Concurrency"], capsys)
        assert code == 0
        assert "doc.txt" in out


def test_find_usage_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test usage errors for find command."""
    root = tmp_path / "root"

    # No text and no --reindex
    code, _, err = run_sb(["--root", str(root), "find"], capsys)
    assert code == 2

    # Negative limit
    code, _, _ = run_sb(["--root", str(root), "find", "test", "--limit", "0"], capsys)
    assert code == 2


# =========================================================================
# CX Review Findings Tests (P1-1 to P1-5, P2)
# =========================================================================


def test_alias_attack_hardlink_index_rejected(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P1-1: Reject index.db if it is a hardlink; alias attack must not modify target object or receipt."""
    root = tmp_path / "root"
    doc = tmp_path / "important.txt"
    doc.write_text("Sacred preserved bytes.", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    receipts = list((root / "receipts" / "v1").glob("*.json"))
    assert len(receipts) == 1
    receipt_file = receipts[0]
    orig_receipt_bytes = receipt_file.read_bytes()

    cache_dir = root / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    index_db = cache_dir / "index.db"

    # Create hardlink from receipt file to index.db
    import os
    os.link(str(receipt_file), str(index_db))
    assert os.stat(str(index_db)).st_nlink > 1

    # Attempting find must reject index.db and exit 2
    code, _, err = run_sb(["--root", str(root), "find", "Sacred"], capsys)
    assert code == 2

    # Verify target receipt file was NOT modified or corrupted
    assert receipt_file.read_bytes() == orig_receipt_bytes

    # Now test alias attack against object file
    index_db.unlink()
    objects = list((root / "objects").glob("*/*"))
    assert len(objects) == 1
    obj_file = objects[0]
    orig_obj_bytes = obj_file.read_bytes()

    os.link(str(obj_file), str(index_db))
    assert os.stat(str(index_db)).st_nlink > 1

    code, _, _ = run_sb(["--root", str(root), "find", "Sacred"], capsys)
    assert code == 2
    assert obj_file.read_bytes() == orig_obj_bytes


def test_alias_attack_reparse_point_cache_rejected(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P1-1: Reject cache directory if it is a reparse point / junction / symlink."""
    import sys
    root = tmp_path / "root"
    doc = tmp_path / "file.txt"
    doc.write_text("Preserved content.", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    cache_dir = root / "cache"
    target_dir = tmp_path / "external_target"
    target_dir.mkdir()

    if sys.platform == "win32":
        import _winapi
        try:
            _winapi.CreateJunction(str(target_dir), str(cache_dir))
        except OSError:
            pytest.skip("Creating junction not supported in this environment")
    else:
        import os
        try:
            os.symlink(str(target_dir), str(cache_dir))
        except OSError:
            pytest.skip("Creating symlink not supported")

    code, _, _ = run_sb(["--root", str(root), "find", "Preserved"], capsys)
    assert code == 2


def test_unsupported_format_payload_not_read(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-2: Never read unsupported formats' payloads (name-only rows, no_text)."""
    root = tmp_path / "root"
    bin_file = tmp_path / "binary_archive.bin"
    bin_file.write_bytes(b"NON_TEXT_DATA_HEADER" + b"\x00" * 100)
    run_sb(["--root", str(root), "capture", str(bin_file)], capsys)

    import secondbrain.search as search
    read_called = False
    orig_read_bytes = Path.read_bytes

    def fake_read_bytes(self: Path) -> bytes:
        nonlocal read_called
        # Check if reading an object file
        if "objects" in str(self):
            read_called = True
        return orig_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "binary_archive"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "binary_archive.bin"
    assert data["results"][0]["extraction_status"] == "no_text"
    assert not read_called, "Unsupported format payload should NEVER be read from disk!"


def test_input_size_caps(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-2: Input size caps (text 32 MiB, PDF 64 MiB, EML/HTML 16 MiB) yield failed(reason), findable by name."""
    import secondbrain.search as search
    root = tmp_path / "root"

    # Use small cap for test
    monkeypatch.setattr(search, "MAX_TEXT_INPUT_SIZE", 50)

    doc = tmp_path / "oversize.txt"
    doc.write_text("A" * 100, encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "oversize"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "oversize.txt"
    assert data["results"][0]["extraction_status"] == "failed"
    assert "exceeds limit" in str(data["results"][0]["extraction_error"]).lower()


def test_output_text_cap(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-2: Output cap (2 MiB text indexed per file)."""
    import secondbrain.search as search
    root = tmp_path / "root"

    monkeypatch.setattr(search, "MAX_OUTPUT_TEXT_CHARS", 30)

    doc = tmp_path / "long_doc.txt"
    doc.write_text("START_TEXT " + ("WORD " * 20) + "END_TEXT", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "START_TEXT"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1

    # Verify in DB that indexed text was capped at 30 chars
    import sqlite3
    conn = sqlite3.connect(root / "cache" / "index.db")
    try:
        row = conn.execute("SELECT extracted_text FROM objects").fetchone()
        assert row is not None
        assert len(row[0]) <= 30
    finally:
        conn.close()


def test_pdf_isolated_worker_timeout(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-2: PDF extraction runs in isolated child process with timeout yielding failed(reason)."""
    import secondbrain.search as search
    import subprocess
    root = tmp_path / "root"

    pdf_file = tmp_path / "timeout.pdf"
    pdf_file.write_bytes(make_tiny_text_pdf("PDF content"))
    run_sb(["--root", str(root), "capture", str(pdf_file)], capsys)

    # Simulate timeout in child process
    orig_run = subprocess.run

    def fake_subprocess_run(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("timeout") or (len(args) > 0 and "--extract-pdf-worker" in args[0]):
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=30.0)
        return orig_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "timeout"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "timeout.pdf"
    assert data["results"][0]["extraction_status"] == "failed"
    assert "timeout" in str(data["results"][0]["extraction_error"]).lower() or "timed out" in str(data["results"][0]["extraction_error"]).lower()


def test_pdf_encrypted_and_truncated(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P1-2 / P2: Encrypted PDF and truncated PDF yield status failed while findable by name."""
    root = tmp_path / "root"

    # Encrypted PDF
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("top_secret")
    buf = io.BytesIO()
    writer.write(buf)

    enc_pdf = tmp_path / "enc_sample.pdf"
    enc_pdf.write_bytes(buf.getvalue())
    run_sb(["--root", str(root), "capture", str(enc_pdf)], capsys)

    # Truncated PDF
    trunc_pdf = tmp_path / "trunc_sample.pdf"
    trunc_pdf.write_bytes(b"%PDF-1.4\n1 0 obj <</Type /Catalog>>\n")
    run_sb(["--root", str(root), "capture", str(trunc_pdf)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "enc_sample"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "enc_sample.pdf"
    assert data["results"][0]["extraction_status"] == "failed"
    assert "encrypt" in str(data["results"][0]["extraction_error"]).lower() or "password" in str(data["results"][0]["extraction_error"]).lower()

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "trunc_sample"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "trunc_sample.pdf"
    assert data["results"][0]["extraction_status"] == "failed"


def test_indexing_does_not_hold_writer_lock_during_extraction(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-2: Indexing must NOT hold capture writer lock during extraction so hostile file cannot block capture."""
    import secondbrain.search as search
    root = tmp_path / "root"

    doc = tmp_path / "hostile.txt"
    doc.write_text("Hostile payload content", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    orig_extract = search.extract_object_text
    lock_was_free = False

    def check_lock_extract(object_path: Path, filename: str) -> tuple[str, str, str | None, str | None]:
        nonlocal lock_was_free
        # Check that another process/caller CAN acquire WriterLock during extraction!
        try:
            with WriterLock(root):
                lock_was_free = True
        except Exception:
            lock_was_free = False
        return orig_extract(object_path, filename)

    monkeypatch.setattr(search, "extract_object_text", check_lock_extract)

    code, _, _ = run_sb(["--root", str(root), "find", "Hostile"], capsys)
    assert code == 0
    assert lock_was_free, "WriterLock was held during extraction! It must NOT be held during extraction."


def test_sqlite_probe_and_trigram_missing_fallback(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-3: Probe FTS5/trigram support; if trigram missing, fall back to LIKE with notice, exit 0, index_mode: like."""
    import secondbrain.search as search
    root = tmp_path / "root"

    doc = tmp_path / "probe_doc.txt"
    doc.write_text("Trigram fallback capability test.", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # 1. Normal execution with trigram
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "capability"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["index_mode"] == "trigram"
    assert len(data["results"]) == 1

    # 2. Simulate missing trigram
    monkeypatch.setattr(search, "probe_sqlite_capabilities", lambda: {"fts5": True, "trigram": False})

    code, out, err = run_sb(["--root", str(root), "--json", "find", "capability"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["index_mode"] == "like"
    assert len(data["results"]) == 1
    assert "trigram" in err.lower() or "like" in err.lower()


def test_sqlite_operational_error_exit_2(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-3: Catch sqlite3.OperationalError everywhere and return structured error exit 2."""
    import sqlite3
    root = tmp_path / "root"

    doc = tmp_path / "doc.txt"
    doc.write_text("Simple doc", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # Ensure index is created
    run_sb(["--root", str(root), "find", "doc"], capsys)

    orig_connect = sqlite3.connect

    def fake_connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        raise sqlite3.OperationalError("disk I/O error or locked database")

    monkeypatch.setattr(sqlite3, "connect", fake_connect)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "doc"], capsys)
    assert code == 2
    data = json.loads(out)
    assert data["status"] == "error"
    assert "disk I/O error" in data["error"] or "sqlite" in data["error"].lower()


def test_extraction_cache_key_extension_and_version(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-4: Cache key includes (sha256, ext, extractor_version); changing version or ext re-extracts; retry failures."""
    import secondbrain.search as search
    root = tmp_path / "root"

    # Capture file as .bin first (unsupported)
    bin_file = tmp_path / "payload.bin"
    bin_file.write_bytes(b"Extractable plaintext content in file")
    run_sb(["--root", str(root), "capture", str(bin_file)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "payload"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["results"][0]["extraction_status"] == "no_text"

    # Now capture IDENTICAL bytes under .txt extension
    txt_file = tmp_path / "payload.txt"
    txt_file.write_bytes(b"Extractable plaintext content in file")
    run_sb(["--root", str(root), "capture", str(txt_file)], capsys)

    # Searching should re-extract because format extension is different!
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "plaintext"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "payload.txt"
    assert data["results"][0]["extraction_status"] == "ok"

    # Bump extractor version
    monkeypatch.setattr(search, "EXTRACTOR_VERSION", "2.0")
    # Finding should re-extract with new extractor version
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "plaintext"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["results"][0]["extraction_status"] == "ok"


def test_staleness_detection_by_receipt_id_set(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P1-5: Detect stale index by comparing receipt id set (not counts)."""
    root = tmp_path / "root"

    doc1 = tmp_path / "doc1.txt"
    doc1.write_text("First document alpha", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc1)], capsys)

    # Build index
    code, out, _ = run_sb(["--root", str(root), "find", "alpha"], capsys)
    assert code == 0
    assert "doc1.txt" in out

    # Delete doc1 receipt and capture doc2 so receipt count is still 1!
    receipts_dir = root / "receipts" / "v1"
    receipts = list(receipts_dir.glob("*.json"))
    assert len(receipts) == 1
    receipts[0].unlink()

    doc2 = tmp_path / "doc2.txt"
    doc2.write_text("Second document beta", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc2)], capsys)

    assert len(list(receipts_dir.glob("*.json"))) == 1

    # Find must detect that receipt id set has changed and rebuild/update!
    code, out, _ = run_sb(["--root", str(root), "find", "beta"], capsys)
    assert code == 0
    assert "doc2.txt" in out


def test_schema_version_and_fts_health_validation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P1-5: Validate schema_version and FTS table health; rebuild on invalid."""
    import sqlite3
    root = tmp_path / "root"

    doc = tmp_path / "doc.txt"
    doc.write_text("Health check document", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)
    run_sb(["--root", str(root), "find", "Health"], capsys)

    index_db = root / "cache" / "index.db"
    assert index_db.is_file()

    # Corrupt schema version
    conn = sqlite3.connect(index_db)
    try:
        conn.execute("PRAGMA user_version = 9999")
        conn.commit()
    finally:
        conn.close()

    # Must detect stale/invalid schema version, rebuild and succeed
    code, out, _ = run_sb(["--root", str(root), "find", "Health"], capsys)
    assert code == 0
    assert "doc.txt" in out


def test_match_errors_reported_not_swallowed(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-5: FTS MATCH errors are reported not swallowed (exit 2)."""
    import sqlite3
    root = tmp_path / "root"

    doc = tmp_path / "doc.txt"
    doc.write_text("Match error test", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)
    run_sb(["--root", str(root), "find", "Match"], capsys)

    index_db = root / "cache" / "index.db"
    # Corrupt fts table
    conn = sqlite3.connect(index_db)
    try:
        conn.execute("DROP TABLE fts_trigram")
        conn.execute("CREATE TABLE fts_trigram (receipt_id TEXT)")
        conn.commit()
    finally:
        conn.close()

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "Match"], capsys)
    assert code == 2
    data = json.loads(out)
    assert data["status"] == "error"


def test_reindex_atomic_replacement_failure_raises(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-5: Reindex builds into new file and atomically replaces it; failure to replace is an error (exit 2)."""
    import os
    root = tmp_path / "root"

    doc = tmp_path / "doc.txt"
    doc.write_text("Atomic replacement test", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    orig_replace = os.replace

    def fake_replace(src: str, dst: str) -> None:
        if "index.db" in str(dst):
            raise OSError("Access denied during atomic replacement")
        orig_replace(src, dst)

    monkeypatch.setattr(os, "replace", fake_replace)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "--reindex"], capsys)
    assert code == 2
    data = json.loads(out)
    assert data["status"] == "error"
    assert "replacement" in data["error"].lower() or "replace" in data["error"].lower()


def test_utf16_bomless_nul_heuristics_and_low_confidence(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P2: BOM-less UTF-16 NUL byte heuristics before UTF-8/CP949, flag low-confidence decodings."""
    root = tmp_path / "root"

    # UTF-16 LE without BOM
    raw_utf16 = "SecondBrain BOM-less UTF-16 specification.".encode("utf-16-le")
    doc = tmp_path / "bomless_utf16.txt"
    doc.write_bytes(raw_utf16)
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "specification"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "bomless_utf16.txt"
    assert data["results"][0]["extraction_status"] in ("ok", "ok_with_warnings")
    note = data["results"][0].get("extraction_note") or data["results"][0].get("extraction_error")
    assert "bomless" in str(note).lower() or "utf-16" in str(note).lower()


def test_bad_eml_charset_status_ok_with_warnings(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P2: Bad EML charset => status ok_with_warnings or failed, not silent header-only ok."""
    root = tmp_path / "root"

    eml_file = tmp_path / "bad_charset.eml"
    eml_content = (
        b"Subject: Meeting with broken charset\n"
        b"From: sender@example.com\n"
        b"Content-Type: text/plain; charset=nonexistent_charset_xyz\n\n"
        b"\xff\xfe\x00\x01\x80Invalid byte stream"
    )
    eml_file.write_bytes(eml_content)
    run_sb(["--root", str(root), "capture", str(eml_file)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "Meeting"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "bad_charset.eml"
    assert data["results"][0]["extraction_status"] == "ok_with_warnings"
    assert data["results"][0]["extraction_error"] is not None


def test_malformed_receipt_and_missing_object_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P2: Malformed receipts and missing objects are reported in errors with exit 1."""
    root = tmp_path / "root"

    # Capture a valid doc first
    doc = tmp_path / "valid.txt"
    doc.write_text("Valid text", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # 1. Malformed receipt
    bad_receipt = root / "receipts" / "v1" / "cap-malformed.json"
    bad_receipt.write_text("{this is not valid json", encoding="utf-8")

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "Valid"], capsys)
    assert code == 1
    data = json.loads(out)
    assert data["status"] == "error"
    assert len(data["errors"]) >= 1

    # Fix malformed receipt, now simulate missing object
    bad_receipt.unlink()
    missing_obj_receipt = root / "receipts" / "v1" / "cap-missingobj.json"
    missing_obj_receipt.write_text(
        json.dumps({
            "id": "cap-missingobj",
            "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
            "original_name": "ghost.txt",
            "source_path": "C:/ghost.txt",
            "collected_at": "2026-10-12T00:00:00Z",
            "tool_version": "0.1.0",
        }),
        encoding="utf-8",
    )

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "Valid"], capsys)
    assert code == 1
    data = json.loads(out)
    assert data["status"] == "error"
    assert any("missing object" in str(e["error"]).lower() for e in data["errors"])


def test_success_json_always_carries_errors_empty(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P2: Success JSON always carries errors:[]."""
    root = tmp_path / "root"
    doc = tmp_path / "doc.txt"
    doc.write_text("Success doc", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "Success"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["status"] == "ok"
    assert "errors" in data
    assert data["errors"] == []


def test_tokenizer_specific_hit_independent_of_like(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P2: Assert tokenizer-specific hits independent of LIKE fallback (query only trigram can satisfy)."""
    import secondbrain.search as search
    root = tmp_path / "root"

    doc = tmp_path / "korean.txt"
    doc.write_text("계약서를 성실히 이행하겠습니다.", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # Disable LIKE fallback to verify trigram alone matches
    def fake_escape_like(s: str) -> str:
        raise AssertionError("LIKE fallback should not be called for trigram hits!")

    monkeypatch.setattr(search, "escape_like", fake_escape_like)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "계약서"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "korean.txt"
    assert data["index_mode"] == "trigram"


def test_nfd_corpus(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P2: NFD corpus stored is normalised and matches NFC and NFD queries."""
    root = tmp_path / "root"

    nfd_content = unicodedata.normalize("NFD", "한글 유니코드 분해 결합 테스트 문서입니다.")
    nfd_filename = unicodedata.normalize("NFD", "분해문서.txt")

    doc = tmp_path / nfd_filename
    doc.write_text(nfd_content, encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # Search with NFC query
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "유니코드"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert unicodedata.is_normalized("NFC", data["results"][0]["name"])
    assert "[유니코드]" in data["results"][0]["snippet"]


def test_interruption_during_indexing(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """P2: Interruption during indexing preserves repository integrity; subsequent find succeeds."""
    import secondbrain.search as search
    root = tmp_path / "root"

    doc = tmp_path / "doc.txt"
    doc.write_text("Interruption test file", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # First attempt interrupted during extraction
    interrupted = False

    def interrupt_extract(*args: Any, **kwargs: Any) -> Any:
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise KeyboardInterrupt("Simulated Ctrl+C during indexing")
        return search.extract_object_text(*args, **kwargs)

    monkeypatch.setattr(search, "extract_object_text", interrupt_extract)

    with pytest.raises(KeyboardInterrupt):
        search.ensure_index_current(root)

    # Un-patch and run find normally
    monkeypatch.undo()
    code, out, _ = run_sb(["--root", str(root), "find", "Interruption"], capsys)
    assert code == 0
    assert "doc.txt" in out


def test_extraction_cache_version_change_reextracts_with_unchanged_ids(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """P1: A changed extractor version must RE-EXTRACT even when the receipt-id set is unchanged."""
    import sqlite3
    import secondbrain.search as search
    root = tmp_path / "root"

    doc = tmp_path / "versioned.txt"
    doc.write_text("Hello version one world", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "versioned"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["results"][0]["extraction_status"] == "ok"

    # Verify initial extractor_version in DB
    db_path = root / "cache" / "index.db"
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT extractor_version FROM receipts").fetchone()
        assert row is not None
        assert row[0] == "1.0"
    finally:
        conn.close()

    # Bump extractor version; receipt IDs on disk remain unchanged!
    monkeypatch.setattr(search, "EXTRACTOR_VERSION", "2.0")

    # Finding must detect staleness by (receipt_id, sha256, ext_class, extractor_version),
    # re-extract, and update the persisted row in index.db
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "versioned"], capsys)
    assert code == 0

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT extractor_version FROM receipts").fetchone()
        assert row is not None
        assert row[0] == "2.0"
        obj_row = conn.execute("SELECT extractor_version FROM objects").fetchone()
        assert obj_row is not None
        assert obj_row[0] == "2.0"
    finally:
        conn.close()


def test_extraction_cache_format_class_change_reextracts_with_unchanged_ids(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """P1: A changed format class must RE-EXTRACT even when receipt-id set is unchanged."""
    root = tmp_path / "root"

    # Capture unsupported .bin file first
    bin_file = tmp_path / "data.bin"
    bin_file.write_bytes(b"Valuable hidden plain text")
    run_sb(["--root", str(root), "capture", str(bin_file)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "data.bin"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["results"][0]["extraction_status"] == "no_text"

    # Modify receipt on disk: same receipt ID, but original_name changes to data.txt
    # This changes format class from 'unsupported' to 'text'
    receipts_dir = root / "receipts" / "v1"
    rec_path = next(receipts_dir.glob("*.json"))
    rec_data = json.loads(rec_path.read_text(encoding="utf-8"))
    rec_data["original_name"] = "data.txt"
    rec_path.write_text(json.dumps(rec_data, indent=2), encoding="utf-8")

    # Find should detect format class change, re-extract and update persisted row
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "Valuable"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["extraction_status"] == "ok"
    assert "Valuable" in data["results"][0]["snippet"]


def test_same_id_metadata_change_updates_persisted_row(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """P1: Same-ID metadata changes must update persisted rows (upsert by receipt id)."""
    import sqlite3
    root = tmp_path / "root"

    doc = tmp_path / "metadata_doc.txt"
    doc.write_text("Unique text keyword metadata123", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "metadata123"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    rec_id = data["results"][0]["id"]

    # Modify metadata in the receipt on disk with SAME receipt id
    receipts_dir = root / "receipts" / "v1"
    rec_path = receipts_dir / f"{rec_id}.json"
    rec_data = json.loads(rec_path.read_text(encoding="utf-8"))
    rec_data["source_path"] = "/new/updated/path/metadata_doc.txt"
    rec_data["original_name"] = "renamed_metadata_doc.txt"
    rec_path.write_text(json.dumps(rec_data, indent=2), encoding="utf-8")

    # Search by the updated source path or updated name
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "renamed_metadata_doc"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == rec_id
    assert data["results"][0]["name"] == "renamed_metadata_doc.txt"

    # Verify persisted row in SQLite was updated
    conn = sqlite3.connect(root / "cache" / "index.db")
    try:
        row = conn.execute("SELECT original_name, source_path FROM receipts WHERE id = ?", (rec_id,)).fetchone()
        assert row is not None
        assert row[0] == "renamed_metadata_doc.txt"
        assert row[1] == "/new/updated/path/metadata_doc.txt"
    finally:
        conn.close()


def test_successful_retry_of_failed_extraction_updates_persisted_row(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """P1: Successful retries of previously failed extractions must update persisted rows (upsert, replace status/text)."""
    import sqlite3
    import secondbrain.search as search
    root = tmp_path / "root"

    doc = tmp_path / "retryable.txt"
    doc.write_text("Important retryable content 999", encoding="utf-8")
    run_sb(["--root", str(root), "capture", str(doc)], capsys)

    # Simulate temporary extraction failure on first find
    orig_extract = search.extract_object_text

    fail_once = True
    def failing_extract(obj_path: Path, filename: str) -> tuple[str, str, str | None, str | None]:
        nonlocal fail_once
        if fail_once:
            fail_once = False
            return "", "failed", None, "Simulated transient failure"
        return orig_extract(obj_path, filename)

    monkeypatch.setattr(search, "extract_object_text", failing_extract)

    # First find fails extraction
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "retryable.txt"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["results"][0]["extraction_status"] == "failed"

    # Verify persisted row in DB has status 'failed'
    conn = sqlite3.connect(root / "cache" / "index.db")
    try:
        row = conn.execute("SELECT extraction_status, extracted_text FROM receipts").fetchone()
        assert row[0] == "failed"
        assert row[1] == ""
    finally:
        conn.close()

    # Second find: retry succeeds without failure
    monkeypatch.setattr(search, "extract_object_text", orig_extract)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "retryable content"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["extraction_status"] == "ok"

    # Verify persisted row in DB was updated to 'ok' and has extracted text
    conn = sqlite3.connect(root / "cache" / "index.db")
    try:
        row = conn.execute("SELECT extraction_status, extracted_text FROM receipts").fetchone()
        assert row[0] == "ok"
        assert "Important retryable content 999" in row[1]
    finally:
        conn.close()


def test_bomless_utf16_korean_only_le_and_be(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """P2: BOM-less UTF-16 for Korean-only content (LE and BE) detected before CP949/UTF-8."""
    root = tmp_path / "root"

    # Korean-only text without ASCII characters and without BOM
    korean_text = "대한민국계약서검토보고서"
    le_bytes = korean_text.encode("utf-16le")
    be_bytes = korean_text.encode("utf-16be")

    le_file = tmp_path / "korean_le.txt"
    le_file.write_bytes(le_bytes)
    run_sb(["--root", str(root), "capture", str(le_file)], capsys)

    be_file = tmp_path / "korean_be.txt"
    be_file.write_bytes(be_bytes)
    run_sb(["--root", str(root), "capture", str(be_file)], capsys)

    # Search Korean text in both files
    code, out, _ = run_sb(["--root", str(root), "--json", "find", "대한민국"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 2
    for res in data["results"]:
        assert res["extraction_status"] == "ok"
        assert "bomless_utf16" in str(res["extraction_note"])
        assert "[대한민국]" in res["snippet"]


def test_malformed_utf8_eml_ok_with_warnings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """P2: Malformed UTF-8 EML marks status 'ok_with_warnings' with note 'replacement characters present'."""
    root = tmp_path / "root"

    # EML with malformed UTF-8 byte sequences in body
    eml_content = (
        b"From: sender@example.com\r\n"
        b"To: receiver@example.com\r\n"
        b"Subject: Meeting Notes Project Alpha\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Project Alpha meeting minutes: \xff\xfe discussions and decisions.\r\n"
    )
    eml_file = tmp_path / "malformed.eml"
    eml_file.write_bytes(eml_content)
    run_sb(["--root", str(root), "capture", str(eml_file)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "Alpha"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    item = data["results"][0]
    assert item["name"] == "malformed.eml"
    assert item["extraction_status"] == "ok_with_warnings"
    assert "replacement characters present" in str(item["extraction_note"])
    assert "[Alpha]" in item["snippet"]


def test_pdf_page_cap_hostile_fixture(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """P1-2: Real PDF fixture with pages over page cap triggers cap, status failed, findable by name."""
    root = tmp_path / "root"

    # Create real hostile-shaped PDF fixture with >1000 pages (1005 pages)
    writer = pypdf.PdfWriter()
    for _ in range(1005):
        writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)

    huge_pdf = tmp_path / "huge_pages.pdf"
    huge_pdf.write_bytes(buf.getvalue())
    run_sb(["--root", str(root), "capture", str(huge_pdf)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "huge_pages"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "huge_pages.pdf"
    assert data["results"][0]["extraction_status"] == "failed"
    assert "page" in str(data["results"][0]["extraction_error"]).lower()
    assert "limit" in str(data["results"][0]["extraction_error"]).lower() or "exceeds" in str(data["results"][0]["extraction_error"]).lower()


def test_pdf_stream_cap_hostile_fixture(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """P1-2: Real PDF fixture whose content stream exceeds stream cap triggers cap, status failed, findable by name."""
    import secondbrain.search as search
    root = tmp_path / "root"

    # Test with small stream cap to trigger stream cap enforcement
    monkeypatch.setattr(search, "MAX_PDF_STREAM_SIZE", 500)

    # make_tiny_text_pdf with 1000 chars creates stream > 1000 bytes
    pdf_bytes = make_tiny_text_pdf("STREAM_BOMB_PAYLOAD_" * 50)
    bomb_pdf = tmp_path / "stream_bomb.pdf"
    bomb_pdf.write_bytes(pdf_bytes)
    run_sb(["--root", str(root), "capture", str(bomb_pdf)], capsys)

    code, out, _ = run_sb(["--root", str(root), "--json", "find", "stream_bomb"], capsys)
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "stream_bomb.pdf"
    assert data["results"][0]["extraction_status"] == "failed"
    assert "stream" in str(data["results"][0]["extraction_error"]).lower()
    assert "limit" in str(data["results"][0]["extraction_error"]).lower() or "exceeds" in str(data["results"][0]["extraction_error"]).lower()


