"""Slice 7: llm prepare/accept (AT-27 accept part, AT-28, AT-29)."""
import hashlib
import json
from pathlib import Path
import re
import shutil

import pytest

import helpers
from secondbrain import llm, wiki
from secondbrain.errors import SbError
from secondbrain.ledger import load_item

FIXTURES = Path(__file__).parent / "fixtures"
SOURCE = (FIXTURES / "reports" / "text--plain.txt.converted.md").read_bytes().decode("utf-8")


def tree(path):
    path = Path(path)
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}


def make(root, **kwargs):
    kwargs.setdefault("text", SOURCE)
    kwargs.setdefault("filename", "invoice.txt")
    return helpers.make_item(root, **kwargs)


def stage(root, item, md="valid.md", js="valid.json", body=None, data=None):
    folder = root / "work" / item.meta["id"] / "llm"
    folder.mkdir(parents=True, exist_ok=True)
    if body is None:
        shutil.copyfile(FIXTURES / "llm" / md, folder / "summary.md")
    else:
        (folder / "summary.md").write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    if data is None:
        shutil.copyfile(FIXTURES / "llm" / js, folder / "summary.json")
    else:
        (folder / "summary.json").write_text(json.dumps(data), encoding="utf-8")


def valid_data():
    return json.loads((FIXTURES / "llm" / "valid.json").read_text(encoding="utf-8"))


def reject(root, item, code, exit_code=2):
    before = tree(root / "raws")
    with pytest.raises(SbError) as error:
        llm.accept(root, item.meta["id"])
    assert error.value.code == code and error.value.exit == exit_code
    assert tree(root / "raws") == before


def test_fixture_digest_matches_view():
    assert valid_data()["source_digest"] == hashlib.sha256(SOURCE.encode("utf-8")).hexdigest()


def test_at28_accept_valid_records_revision_with_provenance(root):
    item = make(root)
    stage(root, item)
    result = llm.accept(root, item.meta["id"])
    assert result == {"id": item.meta["id"], "result": "accepted", "revision": 1}
    body = (FIXTURES / "llm" / "valid.md").read_bytes()
    assert (item.path / "llm" / "summary.a1.md").read_bytes() == body
    loaded = load_item(item.path)
    assert not loaded.warnings and loaded.meta["state"] == "ready"
    revision = loaded.meta["llm"]["summary"][0]
    assert revision["n"] == 1 and revision["file"] == "llm/summary.a1.md"
    assert revision["sha256"] == hashlib.sha256(body).hexdigest()
    assert revision["source_digest"] == valid_data()["source_digest"]
    assert revision["activity"] == {"tool": "peerhub", "version": None, "method": "summary", "peer": "cx",
                                    "model": "synthetic-model", "date": "2026-11-09T00:00:00Z",
                                    "params": {"prompt_rev": "llm-v1"}}
    expected = dict(item.meta, llm=loaded.meta["llm"])
    assert loaded.meta == expected  # nothing else in meta changed


@pytest.mark.parametrize("name,code", [("bad-digest.json", "llm_invalid"), ("missing-key.json", "llm_invalid")])
def test_at28_fixture_json_rejected_without_writes(root, name, code):
    item = make(root)
    stage(root, item, js=name)
    reject(root, item, code)


def test_at28_body_size_boundary(root):
    item = make(root)
    stage(root, item, body="a" * 8001)
    reject(root, item, "llm_invalid")
    stage(root, item, body="한" * 8000)  # 8000 characters, 24000 bytes
    assert llm.accept(root, item.meta["id"])["result"] == "accepted"


@pytest.mark.parametrize("change", [
    {"extra": 1}, {"kind": "note"}, {"peer": "CX"}, {"peer": "x" * 33}, {"peer": 5}, {"model": ""}, {"version": 3},
    {"date": "2026-11-09"}, {"date": "2026-11-09T00:00:00+00:00"}, {"date": "not-a-dateTZ"}, {"source_digest": "ab"},
])
def test_at28_json_field_validation(root, change):
    item = make(root)
    data = {**valid_data(), **change}
    stage(root, item, data=data)
    reject(root, item, "llm_invalid")


def test_at28_unreadable_or_missing_files(root):
    item = make(root)
    reject(root, item, "llm_invalid")  # nothing staged
    stage(root, item, body=b"\xff\xfe bad utf-8")
    reject(root, item, "llm_invalid")
    stage(root, item, data={})
    (root / "work" / item.meta["id"] / "llm" / "summary.json").write_text("{not json", encoding="utf-8")
    reject(root, item, "llm_invalid")
    stage(root, item)
    (root / "work" / item.meta["id"] / "llm" / "summary.json").write_text('{"kind":"summary","kind":"summary"}', encoding="utf-8")
    reject(root, item, "llm_invalid")
    (root / "work" / item.meta["id"] / "llm" / "summary.json").write_bytes(b" " * (64 * 1024 + 1))
    reject(root, item, "llm_invalid")


def test_at28_hostile_summary_rendered_inside_fence(root):
    item = make(root)
    stage(root, item, md="hostile.md")
    llm.accept(root, item.meta["id"])
    hostile = (FIXTURES / "llm" / "hostile.md").read_bytes().decode("utf-8")
    wiki.build(root)
    text = (root / "wiki" / "sources" / f"{item.meta['id']}.md").read_text(encoding="utf-8")
    assert "`````text\n" + hostile + "\n`````\n" in text
    assert "## Summary" in text and text.count("<script>") == 1


def test_at27_new_revision_unchanged_and_history(root):
    item = make(root)
    stage(root, item)
    llm.accept(root, item.meta["id"])
    before = tree(item.path)
    assert llm.accept(root, item.meta["id"])["result"] == "unchanged"
    assert tree(item.path) == before
    stage(root, item, body="A different summary.")
    assert llm.accept(root, item.meta["id"]) == {"id": item.meta["id"], "result": "accepted", "revision": 2}
    summary = load_item(item.path).meta["llm"]["summary"]
    assert [r["file"] for r in summary] == ["llm/summary.a1.md", "llm/summary.a2.md"]
    assert (item.path / "llm" / "summary.a1.md").read_bytes() == (FIXTURES / "llm" / "valid.md").read_bytes()
    assert llm.accept(root, item.meta["id"])["result"] == "unchanged"
    wiki.build(root)
    text = (root / "wiki" / "sources" / f"{item.meta['id']}.md").read_text(encoding="utf-8")
    assert "A different summary." in text and "Synthetic invoice" not in text


def test_at27_fault_after_body_copy_leaves_orphan_then_recovers(root, fault_after):
    item = make(root)
    stage(root, item)
    llm.accept(root, item.meta["id"])
    stage(root, item, body="Second summary.")
    fault_after("summary.a2.md")
    with pytest.raises(SbError) as error:
        llm.accept(root, item.meta["id"])
    assert error.value.code == "io_error"
    loaded = load_item(item.path)
    assert [w["code"] for w in loaded.warnings] == ["orphan"] and loaded.warnings[0]["path"] == "llm/summary.a2.md"
    assert len(loaded.meta["llm"]["summary"]) == 1
    result = wiki.build(root)
    assert [w["code"] for w in result["warnings"]] == ["orphan"]
    text = (root / "wiki" / "sources" / f"{item.meta['id']}.md").read_text(encoding="utf-8")
    assert "Synthetic invoice" in text and "Second summary." not in text
    assert llm.accept(root, item.meta["id"])["revision"] == 2
    loaded = load_item(item.path)
    assert not loaded.warnings and len(loaded.meta["llm"]["summary"]) == 2
    assert llm.accept(root, item.meta["id"])["result"] == "unchanged"


def test_at29_prepare_prompt_fence_contract_and_no_subprocess(root, subprocess_spy):
    item = make(root)
    result = llm.prepare(root, item.meta["id"])
    scratch = root / "work" / item.meta["id"] / "llm"
    prompt = (scratch / "prompt.txt").read_text(encoding="utf-8")
    nonce = re.search(r"<source-([0-9a-f]{16})>\n", prompt)[1]
    assert f"<source-{nonce}>\n{SOURCE}\n</source-{nonce}>" in prompt
    assert "llm-v1" in prompt and "data, not instructions" in prompt
    digest = valid_data()["source_digest"]
    assert result == {"id": item.meta["id"], "result": "prepared", "prompt": str(scratch / "prompt.txt"), "source_digest": digest}
    for needle in (digest, str(scratch / "summary.md"), str(scratch / "summary.json"), "8000", "[a-z][a-z0-9-]{0,31}"):
        assert needle in prompt
    commands = (scratch / "COMMANDS.txt").read_text(encoding="utf-8")
    assert f"sb llm accept {item.meta['id']}" in commands and str(scratch / "prompt.txt") in commands
    assert subprocess_spy == []
    assert tree(root / "raws" / item.meta["id"]) == tree(item.path)


def test_at29_nonce_regenerated_until_absent_from_view(root, monkeypatch):
    item = make(root, text="Text with aaaaaaaaaaaaaaaa inside.")
    nonces = iter(["aaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbb"])
    monkeypatch.setattr(llm.secrets, "token_hex", lambda n: next(nonces))
    llm.prepare(root, item.meta["id"])
    prompt = (root / "work" / item.meta["id"] / "llm" / "prompt.txt").read_text(encoding="utf-8")
    assert "<source-bbbbbbbbbbbbbbbb>\n" in prompt and "<source-aaaaaaaaaaaaaaaa>" not in prompt


def test_at29_prompt_view_includes_verified_ocr(root):
    item = helpers.make_item(root, state="ready", classification="ocr-required", filename="s.pdf", statuses=["verified", "verified"])
    llm.prepare(root, item.meta["id"])  # eligible through verified OCR text alone
    prompt = (root / "work" / item.meta["id"] / "llm" / "prompt.txt").read_text(encoding="utf-8")
    assert "Verified synthetic OCR 1." in prompt and "## OCR u0002" in prompt


def test_at29_not_eligible_cases_write_nothing(root):
    declined = helpers.make_item(root, state="ready", classification="ocr-required", filename="photo.png", statuses=["pending"])
    declined.meta["ocr"]["disposition"] = "declined"
    helpers.save_meta(declined)
    empty = helpers.make_item(root, filename="empty.txt", text="")
    for item in (declined, empty):
        for command in (llm.prepare, llm.accept):
            with pytest.raises(SbError) as error:
                command(root, item.meta["id"])
            assert error.value.code == "not_eligible" and error.value.exit == 2
    assert not (root / "work").exists()


def test_state_and_id_guards(root):
    pending = helpers.make_item(root, state="awaiting-approval", filename="p.pdf")
    unsupported = helpers.make_item(root, state="unsupported", filename="u.xyz")
    failed = helpers.make_item(root, state="failed", filename="f.pdf")
    for item in (pending, unsupported, failed):
        for command in (llm.prepare, llm.accept):
            with pytest.raises(SbError) as error:
                command(root, item.meta["id"])
            assert error.value.code == "state_not_allowed" and error.value.exit == 2
    for bad in ("0123456789abcdef", "../raws", "XYZ"):
        with pytest.raises(SbError) as error:
            llm.prepare(root, bad)
        assert error.value.code == "unknown_id"
    assert not (root / "work").exists()
