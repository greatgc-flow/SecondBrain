from copy import deepcopy
import hashlib

import pytest

from helpers import make_item
from secondbrain.transcript import accepted_text_present, has_native_text, source_digest, view


@pytest.mark.parametrize("text, expected", [
    ("", False), ("![invoice 123](media/image.png)", False), ("[IMAGE]", False),
    ("<!-- invisible 한글 123 -->", False), ("| --- | :---: |\n| | |", False),
    ("data:image/png;base64,ABCD1234==", False), ("![](data:image/png;base64,ABCD)", False),
    ("한글", True), ("123", True), ("plain text", True), ("←☆", False),
    ("![broken](", True), ("<!-- unclosed text", True),
])
def test_at07_native_text(text, expected):
    assert has_native_text(text) is expected


def test_view_only_verified_and_pure(root):
    item = make_item(root, filename="source.pdf", classification="mixed", state="ocr-in-progress", statuses=["verified", "recorded", "pending"])
    before_meta = deepcopy(item.meta)
    before_files = {p: p.read_bytes() for p in item.path.rglob("*") if p.is_file()}
    expected = "Synthetic text 123.\n\n## OCR u0001 (source p1; transcribed cx/synthetic-model 2026-11-09T00:00:00Z; verified cc/synthetic-model 2026-11-09T00:00:00Z)\n\nVerified synthetic OCR 1."
    assert view(item) == expected
    assert source_digest(item) == hashlib.sha256(expected.encode("utf-8")).hexdigest()
    assert "OCR 2" not in view(item)
    assert before_meta == item.meta
    assert before_files == {p: p.read_bytes() for p in item.path.rglob("*") if p.is_file()}


def test_orphan_conversion_is_not_a_transcript(root):
    item = make_item(root, classification="unsupported", state="unsupported", text=None)
    (item.path / "converted.md").write_text("orphan text")
    assert view(item) == ""
    assert accepted_text_present(item) is False


@pytest.mark.parametrize("text, expected", [("[illegible]\n[no text]", False), ("[no text] 123", True)])
def test_accepted_ocr_text_excludes_only_markers(root, text, expected):
    item = make_item(root, filename="scan.pdf", classification="ocr-required", text="", statuses=["verified"])
    (item.path / "ocr/u0001.a1.md").write_text(text, encoding="utf-8")
    assert accepted_text_present(item) is expected


def test_empty_native_transcript_and_decline(root):
    item = make_item(root, filename="unknown.md", classification="unknown", text="native 123")
    assert accepted_text_present(item) is True
    assert view(item) == "native 123"


def test_view_keeps_recorded_text_line_endings(root):
    item = make_item(root, text="First\r\nSecond\n")
    assert view(item) == "First\r\nSecond\n"
