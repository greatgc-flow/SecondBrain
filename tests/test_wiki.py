"""Slice 6: wiki build, swap, recovery, projections, fences, escaping (AT-30..AT-33)."""
import hashlib
import json
import os
from pathlib import Path
import re

import pytest

import helpers
from secondbrain import fsutil, wiki
from secondbrain.errors import SbError


tree = helpers.tree


def page(root, item):
    return (root / "wiki" / "sources" / f"{item.meta['id']}.md").read_text(encoding="utf-8")


def make_all_states(root):
    make = helpers.make_item
    items = {
        "text": make(root, filename="a-text.txt"),
        "empty": make(root, filename="b-empty.txt", text=""),
        "pending": make(root, state="awaiting-approval", filename="c-pending.pdf", statuses=["pending", "pending"]),
        "progress": make(root, state="ocr-in-progress", filename="d-progress.pdf",
                         statuses=["verified", "recorded", "approved", "pending"]),
        "verified": make(root, state="ready", classification="mixed", filename="e-verified.pdf", statuses=["verified", "verified"]),
        "unsupported": make(root, state="unsupported", filename="f.xyz"),
        "failed": make(root, state="failed", filename="g-failed.pdf"),
        "unknown": make(root, state="awaiting-approval", classification="unknown", filename="h-unknown.md"),
        "declined": make(root, state="ready", classification="unknown", filename="i-declined.md"),
    }
    helpers.add_summary(items["text"], "A summary.")
    return items


def test_at30_build_twice_identical_and_only_expected_files(root):
    items = make_all_states(root)
    raws_before = tree(root / "raws")
    result = wiki.build(root)
    first = tree(root / "wiki")
    assert not result["errors"] and not result["warnings"]
    tag_files = {f"tags/{t}.md" for i in items.values() for t in wiki.tags(i.meta)}
    assert sorted(first) == sorted(["index.md"] + [f"sources/{i.meta['id']}.md" for i in items.values()] + sorted(tag_files))
    assert result["pages"] == len(first)
    wiki.build(root)
    assert tree(root / "wiki") == first
    assert tree(root / "raws") == raws_before
    assert not (root / "wiki.tmp").exists() and not (root / "wiki.old").exists()
    assert b"\r" not in b"".join(first.values())


def test_at30_corrupt_item_reported_and_skipped(root):
    good = helpers.make_item(root, filename="good.txt")
    bad = helpers.make_item(root, filename="bad.txt")
    (bad.path / "meta.json").write_text("{", encoding="utf-8")
    result = wiki.build(root)
    assert [e["code"] for e in result["errors"]] == ["corrupt_meta"] and result["errors"][0]["id"] == bad.meta["id"]
    assert sorted(tree(root / "wiki")) == ["index.md", f"sources/{good.meta['id']}.md", "tags/class-text-only.md",
                                           "tags/collected-2026-11.md", "tags/ext-txt.md"]


def test_at30_staging_and_hidden_dirs_ignored(root):
    helpers.make_item(root, filename="good.txt")
    (root / "raws" / ".staging" / "tmp-1").mkdir(parents=True)
    result = wiki.build(root)
    assert result["pages"] == 1 + 1 + 3 and not result["errors"]  # index, source, three tag pages


def test_at30_empty_root_builds_index_only(root):
    wiki.build(root)
    assert sorted(tree(root / "wiki")) == ["index.md"]


def reference_wiki(root):
    wiki.build(root)
    return tree(root / "wiki")


def test_fault_partial_wiki_tmp_keeps_old_wiki_and_next_build_recovers(root, monkeypatch):
    make_all_states(root)
    good = reference_wiki(root)
    original, calls = wiki.write_text, []

    def failing(path, text):
        calls.append(path)
        if len(calls) == 3:
            raise OSError("fault after partial wiki.tmp")
        original(path, text)
    monkeypatch.setattr(wiki, "write_text", failing)
    with pytest.raises(SbError) as error:
        wiki.build(root)
    assert error.value.code == "io_error"
    assert (root / "wiki.tmp").is_dir() and tree(root / "wiki") == good
    monkeypatch.setattr(wiki, "write_text", original)
    wiki.build(root)
    assert tree(root / "wiki") == good and not (root / "wiki.tmp").exists()


def test_fault_after_wiki_old_rename_recovers(root, fault_after):
    make_all_states(root)
    good = reference_wiki(root)
    fault_after("wiki.old")
    with pytest.raises(SbError):
        wiki.build(root)
    assert not (root / "wiki").exists() and (root / "wiki.old").is_dir() and (root / "wiki.tmp").is_dir()
    wiki.build(root)
    assert tree(root / "wiki") == good
    assert not (root / "wiki.tmp").exists() and not (root / "wiki.old").exists()


def test_fault_after_tmp_swapped_in_recovers(root, fault_after):
    make_all_states(root)
    good = reference_wiki(root)
    fault_after("wiki")
    with pytest.raises(SbError):
        wiki.build(root)
    assert (root / "wiki").is_dir() and (root / "wiki.old").is_dir()
    wiki.build(root)
    assert tree(root / "wiki") == good and not (root / "wiki.old").exists()


def test_recover_rules(root):
    (root / "wiki.tmp").mkdir()
    (root / "wiki.tmp" / "x").write_text("x", encoding="utf-8")
    (root / "wiki.old").mkdir()
    (root / "wiki.old" / "keep.md").write_text("old", encoding="utf-8")
    wiki.recover(root)  # wiki.old without wiki is renamed back
    assert (root / "wiki" / "keep.md").read_text(encoding="utf-8") == "old"
    assert not (root / "wiki.old").exists() and not (root / "wiki.tmp").exists()
    (root / "wiki.old").mkdir()
    wiki.recover(root)  # wiki.old with wiki is deleted
    assert not (root / "wiki.old").exists() and (root / "wiki" / "keep.md").exists()


def test_at30_reparse_point_wiki_old_refused(root, monkeypatch):
    helpers.make_item(root, filename="good.txt")
    (root / "wiki.old").mkdir()
    (root / "wiki.old" / "keep.md").write_text("old", encoding="utf-8")
    original = fsutil.is_reparse_point
    monkeypatch.setattr(fsutil, "is_reparse_point", lambda p: Path(p) == root / "wiki.old" or original(p))
    with pytest.raises(SbError) as error:
        wiki.build(root)
    assert error.value.code == "io_error"
    assert (root / "wiki.old" / "keep.md").exists() and not (root / "wiki").exists()


def test_at31_index_sort_columns_and_label(root):
    # AT-31 name; Windows rejects "<", so use a legal markdown-hostile variant there.
    name = "[x](y) <b>`z` #!.txt" if os.name != "nt" else "[x](y) &lt;b&gt; `z` #!.txt"
    helpers.make_item(root, filename="b.txt")
    helpers.make_item(root, filename="B2.txt")
    helpers.make_item(root, filename="a.txt")
    hostile = helpers.make_item(root, filename=name)
    wiki.build(root)
    rows = [l for l in (root / "wiki" / "index.md").read_text(encoding="utf-8").splitlines() if l.startswith("| ") and "---" not in l][1:]
    labels = [r.split(" | ")[0][2:] for r in rows]
    assert len(rows) == 4
    # casefold order: "[x](y)..." sorts before letters
    assert labels[0] == f"[{fsutil.esc(name)}](sources/{hostile.meta['id']}.md)"
    assert [re.match(r"\[.*\]\((.*)\)", l)[1].split("/")[0] for l in labels] == ["sources"] * 4
    for r in rows:
        cells = r.strip("| ").split(" | ")
        assert len(cells) == 8
        assert re.search(r"\(sources/[0-9a-f]{16}\.md\)$", cells[0])
        assert cells[4] == "2026-11-09" and cells[7] == "no"
    assert [l.split("](")[0][1:] for l in labels[1:]] == ["a.txt", "b.txt", "B2.txt"]


def test_at31_ties_break_by_id_and_nfc_sort(root):
    import unicodedata
    nfd = helpers.make_item(root, filename=unicodedata.normalize("NFD", "한글.txt"))
    plain = helpers.make_item(root, filename="Z.txt")
    twin = helpers.make_item(root, filename="z.txt")
    wiki.build(root)
    ids = re.findall(r"sources/([0-9a-f]{16})\.md", (root / "wiki" / "index.md").read_text(encoding="utf-8"))
    first = sorted([plain.meta["id"], twin.meta["id"]])
    assert ids == first + [nfd.meta["id"]]
    assert "한글.txt" in page(root, nfd)  # title uses NFC
    assert page(root, nfd).startswith("# 한글.txt\n")


def test_at31_index_ocr_coverage_summary_columns(root):
    items = make_all_states(root)
    wiki.build(root)
    index = (root / "wiki" / "index.md").read_text(encoding="utf-8")
    row = {name: next(l for l in index.splitlines() if f"sources/{i.meta['id']}.md" in l).strip("| ").split(" | ")
           for name, i in items.items()}
    assert row["text"][1:] == [".txt", "text-only", "ready", "2026-11-09", "none", "-", "yes"]
    assert row["pending"][5:7] == ["none", "complete"]
    assert row["progress"][5] == "3/4 approved, 2 recorded, 1 verified"
    assert row["verified"][5] == "2/2 approved, 2 recorded, 2 verified"
    assert row["declined"][5:7] == ["declined", "none"]
    assert row["failed"][2:4] == ["-", "failed"] and row["failed"][5] == "none" and row["failed"][6] == "-"


def test_at32_transcript_is_markdown_but_inert(root):
    hostile = ("# Title\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n<script>alert(1)</script>\n![x][r]\n![y](http://evil.example/y.png)\n\n"
               "[r]: http://evil.example/x.png\n[a](javascript:alert(1))\n[b](&#106;avascript:alert(1))\n[c]( data:text/html,x)\n"
               "[d](https://ok.example/a?b=1&c=2) [e](rel/page.md) [f](#top) [g](mailto:a@b.c)\n"
               "[s]: JavaScript:alert(1)\n> [t]: vbscript:x\n> quote <b>\n\\![z](http://e/z.png)\n````\n# tail\n")
    item = helpers.make_item(root, filename="h.txt", text=hostile)
    item.meta["aliases"] = ["](x).txt"]  # aliases are filenames: no "/" or ":" on Windows
    helpers.save_meta(item)
    raws_before = tree(root / "raws")
    wiki.build(root)
    text = page(root, item)
    body = text.split("## Transcript\n\n")[1]
    assert body.startswith("# Title\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n")  # rendered, not fenced
    assert "<" not in body and "&lt;script&gt;alert(1)&lt;/script&gt;" in body and "> quote &lt;b&gt;" in body
    assert "![" not in body.replace("&#33;[", "") and body.count("&#33;[") == 3
    for dead in ("javascript:", "JavaScript:", "vbscript:", "data:", "&#106;"):
        assert dead not in body, dead
    for live in ("(http://evil.example/y.png)", "[r]: http://evil.example/x.png", "(https://ok.example/a?b=1&c=2)",
                 "(rel/page.md)", "(#top)"):
        assert live in body
    assert "mailto:" not in body and "[a](#)" in body and "[s]: #" in body and "> [t]: #" in body
    # the only occurrence of untrusted alias is inside the json fence
    head, _, rest = text.partition("## Transcript")
    assert head.count("](x).txt") == 1 and "](x).txt" not in rest
    fence_start = head.index("```json")
    assert fence_start < head.index("](x).txt") < head.index("\n```\n", fence_start)
    assert tree(root / "raws") == raws_before


def test_at32_model_string_and_summary_stay_fenced(root):
    item = helpers.make_item(root, filename="s.txt")
    helpers.add_summary(item, "Summary ](http://x) ```` end\n<b>")
    item.meta["llm"]["summary"][0]["activity"]["model"] = "m](http:x)"
    helpers.save_meta(item)
    wiki.build(root)
    text = page(root, item)
    summary = text.split("## Summary\n\n")[1].split("## Transcript")[0]
    assert summary.startswith("`````text\nSummary ](http://x) ```` end\n<b>\n`````\n")
    head = text.split("## Summary")[0]
    assert head.index("```json") < head.index("m](http:x)") < head.rindex("\n```\n")


def test_fence_helper_sizes():
    assert wiki.fence("x") == "```text\nx\n```\n"
    assert wiki.fence("a ``` b").startswith("````text\n")
    assert wiki.fence("`` ```` `").startswith("`````text\n")


def test_source_page_structure_and_link(root):
    item = helpers.make_item(root, filename="한 글 #1 (a).txt")
    helpers.add_summary(item)
    wiki.build(root)
    text = page(root, item)
    assert text.startswith("# 한 글 \\#1 \\(a\\).txt\n\n```json\n")
    assert not text.startswith("---")
    encoded = fsutil.percent_encode("한 글 #1 (a).txt")
    assert f"[Original file](../../raws/{item.meta['id']}/src/{encoded})" in text
    block = json.loads(text.split("```json\n")[1].split("\n```\n")[0])
    assert block["id"] == item.meta["id"] and block["filename"] == "한 글 #1 (a).txt"
    assert block["source_digest"] == hashlib.sha256(b"Synthetic text 123.").hexdigest()
    assert block["activities"]["convert"]["method"] == "convert" and block["activities"]["summary"]["method"] == "summary"
    assert text.index("## Summary") < text.index("## Transcript")
    assert text.endswith("## Transcript\n\nSynthetic text 123.\n") and "\nSynthetic text 123.\n```" not in text


def test_safety_pass_leaves_code_blocks_and_spans_untouched(root):
    code = ("Use `a < b` and ``x ![i](u) > y``.\n\n```c\nif (a < b && c > d) { /* ![x](javascript:1) <b> */ }\n```\n\n"
            "~~~\n<tag>\n~~~\n\n")
    prose = ("after <b>bold</b> and ![img](http://e/x.png) `unclosed\n\n    indented <i>\n\n| t |\n|---|\n| `a|<b>` |\n\n"
             "`x\n# <script>\n`\n\n[`l`]: javascript:alert(1)\n\n```not a fence `<b>`\n")
    item = helpers.make_item(root, filename="c.md", text=code + prose)
    wiki.build(root)
    body = page(root, item).split("## Transcript\n\n")[1]
    assert body.startswith(code)  # byte-identical: no &lt;, &gt; or &#33; inside code
    assert body[len(code):] == ("after &lt;b&gt;bold&lt;/b&gt; and &#33;[img](http://e/x.png) `unclosed\n\n    indented &lt;i&gt;\n\n"
                                "| t |\n|---|\n| `a|&lt;b&gt;` |\n\n`x\n# &lt;script&gt;\n`\n\n[`l`]: #\n\n"
                                "```not a fence `<b>`\n")  # indented code, table rows and multi-line "spans" are escaped like prose
    assert wiki.safe_markdown("```\n<x>\n") == "```\n<x>\n"  # an unclosed fence runs to the end, like Markdown
    assert wiki.safe_markdown("~~~\n<x>\n```\n<y>\n~~~~\n<z>") == "~~~\n<x>\n```\n<y>\n~~~~\n&lt;z&gt;"


def test_tags_pages_index_links_and_back_links(root):
    a = helpers.make_item(root, filename="a.txt")
    b = helpers.make_item(root, state="awaiting-approval", filename="b.pdf", statuses=["pending"])
    weird = helpers.make_item(root, filename="w.txt")
    weird.meta["ext"] = ".한글"  # not a plain ascii extension: bucketed, never a path
    assert wiki.tags(a.meta) == ["class-text-only", "collected-2026-11", "ext-txt"]
    assert wiki.tags(b.meta) == ["class-mixed", "collected-2026-11", "ext-pdf"]
    assert wiki.tags(weird.meta)[2] == "ext-other"
    wiki.build(root)
    index = (root / "wiki" / "index.md").read_text(encoding="utf-8")
    assert index.endswith("## Tags\n\n- [class-mixed](tags/class-mixed.md) (1)\n- [class-text-only](tags/class-text-only.md) (2)\n"
                          "- [collected-2026-11](tags/collected-2026-11.md) (3)\n- [ext-pdf](tags/ext-pdf.md) (1)\n- [ext-txt](tags/ext-txt.md) (2)\n")
    assert f"Tags: [class-text-only](../tags/class-text-only.md), [collected-2026-11](../tags/collected-2026-11.md), [ext-txt](../tags/ext-txt.md)" in page(root, a)
    tag = (root / "wiki" / "tags" / "ext-txt.md").read_text(encoding="utf-8")
    assert tag == f"# Tag: ext-txt\n\n[Index](../index.md)\n\n- [a.txt](../sources/{a.meta['id']}.md)\n- [w.txt](../sources/{weird.meta['id']}.md)\n"


def test_at33_banners_per_row(root):
    items = make_all_states(root)
    wiki.build(root)
    pages = {name: page(root, item) for name, item in items.items()}

    assert "text\nempty document\n" in pages["empty"] and "empty document" not in pages["text"]
    assert "```text\nOCR pending approval: 2 units, coverage complete\n```" in pages["pending"]
    assert "```text\nOCR in progress: 3/4 approved, 2 recorded, 1 verified\n```" in pages["progress"]
    assert "```text\nOCR verified: 2 units\n```" in pages["verified"]
    assert "```text\nunsupported: extension_not_allowed\n```" in pages["unsupported"]
    assert "## Transcript" not in pages["unsupported"]
    assert "```text\nfailed: SyntheticError, 2026-11-09T00:00:00Z\n```" in pages["failed"]
    assert "## Transcript" not in pages["failed"]  # no converted.md
    assert "```text\nnot inspected: media_not_inspected\n```" in pages["unknown"]
    assert "```text\nnot inspected: media_not_inspected, declined\n```" in pages["declined"]


def test_at33_failed_with_converted_md_keeps_transcript(root):
    item = helpers.make_item(root, state="failed", filename="g.pdf", text="Converted before failure.")
    wiki.build(root)
    assert "## Transcript" in page(root, item) and "Converted before failure." in page(root, item)


def test_at33_declined_and_verified_coverage_banner(root):
    declined = helpers.make_item(root, state="ready", classification="mixed", filename="d.pdf", statuses=["pending"])
    declined.meta["ocr"]["disposition"] = "declined"
    helpers.save_meta(declined)
    partial = helpers.make_item(root, state="ready", classification="mixed", filename="p.pdf", statuses=["verified"])
    partial.meta["triage"]["coverage"]["state"] = "partial"
    helpers.save_meta(partial)
    wiki.build(root)
    assert "```text\nOCR declined\n```" in page(root, declined)
    assert "```text\nOCR verified: 1 units, coverage partial\n```" in page(root, partial)


def test_at33_only_verified_text_in_view(root):
    items = make_all_states(root)
    mismatch = helpers.make_item(root, state="ocr-in-progress", filename="m.pdf", statuses=["recorded"])
    attempt = mismatch.meta["ocr"]["units"]["u0001"]["attempts"][0]
    attempt["result"] = "mismatch"
    attempt["verified"] = helpers.provenance("ocr-verify", "cc")
    mismatch.meta["ocr"]["units"]["u0001"]["status"] = "approved"
    helpers.save_meta(mismatch)
    wiki.build(root)
    progress = page(root, items["progress"])
    assert "Verified synthetic OCR 1." in progress and "## OCR u0001 (source p1;" in progress
    assert "Verified synthetic OCR 2." not in progress  # recorded, not verified
    assert "## OCR u0002" not in progress and "## OCR u0003" not in progress
    assert "Verified synthetic OCR 1." not in page(root, mismatch)
    assert "## OCR" not in page(root, items["pending"])


def test_at33_declined_partial_coverage_and_raster_pending_banner(root):
    declined = helpers.make_item(root, state="ready", classification="mixed", filename="d.pdf", statuses=["pending"])
    declined.meta["ocr"]["disposition"] = "declined"
    declined.meta["triage"]["coverage"]["state"] = "partial"
    helpers.save_meta(declined)
    raster = helpers.make_item(root, state="awaiting-approval", classification="ocr-required", filename="photo.png")
    wiki.build(root)
    assert "```text\nOCR declined, coverage partial\n```" in page(root, declined)
    assert "```text\nOCR pending approval: 1 units, coverage n/a\n```" in page(root, raster)


def test_transcript_gate_follows_the_ledger_not_the_file_system(root):
    # DESIGN §2 artifact rule: an unreferenced converted.md is an orphan and never enters the wiki.
    orphan = helpers.make_item(root, state="failed", filename="g.pdf")
    (orphan.path / "converted.md").write_bytes(b"unreferenced text")
    referenced = helpers.make_item(root, state="failed", filename="h.pdf", text="Converted.")
    wiki.build(root)
    assert "## Transcript" not in page(root, orphan) and "unreferenced text" not in page(root, orphan)
    assert "## Transcript" in page(root, referenced) and "Converted." in page(root, referenced)


def test_index_has_no_extra_blank_line(root):
    helpers.make_item(root, filename="a.txt")
    wiki.build(root)
    assert (root / "wiki" / "index.md").read_text(encoding="utf-8").startswith("# SecondBrain index\n\n| Source")
