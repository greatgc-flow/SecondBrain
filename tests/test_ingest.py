"""Slice 4: claim/commit, recovery, identity and first-missing-step retry."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unicodedata

import pytest

from secondbrain import convert, ingest
from secondbrain.errors import SbError
from secondbrain.fsutil import write_json_atomic
from secondbrain.ledger import load_item, load_stage
from helpers import DATE, make_item

FIXTURES = Path(__file__).parent / "fixtures"


def drop(root, name="source.txt", data=b"Synthetic original 123"):
    path = root / "inbox" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def fixture(root, name, received=None):
    return drop(root, received or Path(name).name, (FIXTURES / name).read_bytes())


def committed(root):
    return [load_item(p) for p in sorted((root / "raws").iterdir()) if not p.name.startswith(".")]


def stages(root):
    return sorted((root / "raws/.staging").glob("tmp-*"))


@pytest.fixture
def tool(monkeypatch):
    """Stub only external work; exercise the real durable conversion adapter."""
    calls = SimpleNamespace(convert=[], report=[], error=None, report_error=None, text="Native 123", media=False)
    class Tool:
        def convert(self, source, **options):
            directory = Path(source).parent.parent
            stage = load_stage(directory)
            assert stage["identity"]["sha256"] == sha256(Path(source).read_bytes()).hexdigest()
            assert stage["conversion"]["sha256"] is None
            calls.convert.append((Path(source), options))
            if calls.error:
                raise calls.error
            if calls.media:
                media = Path(options["extract_media"])
                media.mkdir(exist_ok=True)
                (media / "a.png").write_bytes(b"original asset")
            return SimpleNamespace(text_content=calls.text)
    def report(source, output):
        calls.report.append(Path(source))
        if calls.report_error:
            raise SbError(calls.report_error, 1)
        name = "row-09.json" if calls.media else "row-11.json"
        return convert.adapt_report(json.loads((FIXTURES / "reports" / name).read_text(encoding="utf-8")), Path(source).suffix)
    monkeypatch.setattr(convert, "_make_converter", lambda ext: Tool())
    monkeypatch.setattr(convert, "run_report", report)
    return calls


def test_at01_two_payload_renames_and_source_identity(root, tool, monkeypatch):
    source = drop(root, "sub/기획서.pdf")
    original = source.read_bytes()
    moves = []
    replace, rename = os.replace, os.rename
    def claim(src, dst, *args, **kwargs):
        if Path(src) == source:
            stage = load_stage(Path(dst).parent.parent)
            assert stage["relpath"] == "sub/기획서.pdf" and "identity" not in stage
            moves.append((Path(src), Path(dst)))
        return replace(src, dst, *args, **kwargs)
    def commit(src, dst, *args, **kwargs):
        assert (Path(src) / "meta.json").is_file()
        moves.append((Path(src), Path(dst)))
        return rename(src, dst, *args, **kwargs)
    monkeypatch.setattr(os, "replace", claim)
    monkeypatch.setattr(os, "rename", commit)
    result = ingest.ingest(root)
    item, = committed(root)
    assert not result["errors"] and result["items"] == [{"id": item.meta["id"], "result": "new"}]
    assert item.meta["sha256"] == sha256(original).hexdigest()
    assert item.meta["filename"] == "기획서.pdf" and item.meta["filename_nfc"] == "기획서.pdf"
    assert (item.path / "src/기획서.pdf").read_bytes() == original and not source.exists()
    assert len(moves) == 2 and moves[0][1].parent.name == "src" and moves[1][1] == item.path
    assert not stages(root) and not item.warnings


@pytest.mark.parametrize("state", ["ready", "awaiting-approval", "ocr-in-progress", "unsupported", "failed"])
def test_at02_at03_duplicate_and_alias_in_every_state(root, tool, state):
    item = make_item(root, state=state)
    original = (item.path / "src" / item.meta["filename"]).read_bytes()
    before = (item.path / "meta.json").read_bytes()
    drop(root, item.meta["filename"], original)
    result = ingest.ingest(root)
    assert result["items"] == [{"id": item.meta["id"], "result": "duplicate"}]
    assert (item.path / "meta.json").read_bytes() == before
    drop(root, "z-copy.pdf", original)
    assert ingest.ingest(root)["items"][0]["result"] == "alias_added"
    after = load_item(item.path).meta
    expected = deepcopy(item.meta)
    expected["aliases"] = ["z-copy.pdf"]
    assert after == expected
    drop(root, "a-copy.pdf", original)
    ingest.ingest(root)
    assert load_item(item.path).meta["aliases"] == ["a-copy.pdf", "z-copy.pdf"]
    before = (item.path / "meta.json").read_bytes()
    drop(root, "z-copy.pdf", original)
    assert ingest.ingest(root)["items"][0]["result"] == "duplicate"
    assert (item.path / "meta.json").read_bytes() == before
    assert len(committed(root)) == 1 and not stages(root) and tool.convert == tool.report == []


def test_at04_collision_is_flagged_and_never_resumed(root, tool, monkeypatch):
    item = make_item(root)
    source = drop(root, "collision.txt", b"different original")
    digest = item.meta["id"] + "0" * 48
    assert digest != item.meta["sha256"]
    monkeypatch.setattr(ingest, "sha256_file", lambda path: digest)
    before = (item.path / "meta.json").read_bytes()
    result = ingest.ingest(root)
    assert [e["code"] for e in result["errors"]] == ["id_collision"]
    directory, = stages(root)
    assert load_stage(directory)["collision"] is True
    assert (directory / "src/collision.txt").read_bytes() == b"different original" and not source.exists()
    snapshot = {p.relative_to(directory).as_posix(): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    result = ingest.ingest(root)
    assert [w["code"] for w in result["warnings"]] == ["staged_collision"]
    assert not result["errors"] and not result["items"]
    assert snapshot == {p.relative_to(directory).as_posix(): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    assert (item.path / "meta.json").read_bytes() == before and not tool.convert


@pytest.mark.parametrize("step", ["stage.json", "claim", "identity", "conversion_pending", "converted.md", "conversion", "triage", "meta.json", "commit"])
def test_at26_all_durable_boundaries_recover_once(root, tool, fault_after, step):
    source = drop(root, "하위/보고서 v2.hwp")
    data = source.read_bytes()
    fault_after(step)
    first = ingest.ingest(root, charset="cp949")
    assert first["errors"][0]["code"] == "io_error"
    if step == "stage.json":
        assert source.read_bytes() == data
    output_before = [(p, p.read_bytes(), p.stat().st_mtime_ns) for p in (root / "raws").rglob("converted.md")]
    result = ingest.ingest(root)
    assert not result["errors"]
    item, = committed(root)
    assert (item.path / "src" / source.name).read_bytes() == data and not source.exists() and not stages(root)
    assert item.meta["conversion"]["activity"]["params"]["charset"] == (None if step == "stage.json" else "cp949")
    assert len(tool.convert) == 1
    assert len(tool.report) == 1
    if output_before:
        assert (item.path / "converted.md").read_bytes() == output_before[0][1]
        assert (item.path / "converted.md").stat().st_mtime_ns == output_before[0][2]


@pytest.mark.parametrize("name", ["stage.json", "meta.json", "converted.md"])
def test_at26_payload_cannot_clobber_ledgers(root, tool, fault_after, name):
    data = b"Exact payload bytes"
    drop(root, name, data)
    fault_after("claim")
    assert ingest.ingest(root)["errors"]
    assert not ingest.ingest(root)["errors"]
    item, = committed(root)
    assert (item.path / "src" / name).read_bytes() == data
    assert json.loads((item.path / "stage.json").read_text(encoding="utf-8"))["filename"] == name


@pytest.mark.parametrize("ledger", [False, True])
def test_recovery_removes_unclaimed_stage_only(root, tool, ledger):
    directory = root / "raws/.staging/tmp-1"
    directory.mkdir(parents=True)
    if ledger:
        write_json_atomic(directory / "stage.json", {"filename": "unclaimed.txt", "relpath": "unclaimed.txt", "charset": "cp949", "claimed_at": DATE})
    untouched = drop(root, ".unclaimed.txt")
    assert not ingest.ingest(root)["errors"]
    assert not directory.exists() and untouched.exists() and not tool.convert


def test_recovery_duplicate_after_alias_commit_is_idempotent(root, tool, fault_after):
    item = make_item(root)
    drop(root, "alias.txt", (item.path / "src" / item.meta["filename"]).read_bytes())
    fault_after("meta.json")
    assert ingest.ingest(root)["errors"]
    assert stages(root) and load_item(item.path).meta["aliases"] == ["alias.txt"]
    assert not ingest.ingest(root)["errors"] and not stages(root)
    assert load_item(item.path).meta["aliases"] == ["alias.txt"] and not tool.convert


def test_at14_retry_reuses_completed_conversion_and_assets(root, tool):
    tool.media = True
    tool.report_error = "report_failed"
    drop(root, "slides.pptx")
    first = ingest.ingest(root, charset="cp949")
    assert [e["code"] for e in first["errors"]] == ["report_failed"]
    item, = committed(root)
    assert item.meta["state"] == "failed" and item.meta["conversion"]
    paths = [item.path / "converted.md", item.path / "media/a.png", item.path / "src/slides.pptx"]
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
    tool.report_error = None
    result = ingest.ingest(root, retry=True, charset="utf-8")
    assert result["items"] == [{"id": item.meta["id"], "result": "retried"}] and not result["errors"]
    after = load_item(item.path).meta
    assert (after["class"], after["state"]) == ("mixed", "awaiting-approval")
    assert after["conversion"]["activity"]["params"]["charset"] == "cp949"
    assert after["ocr"]["units"]["u0001"]["source"] == "media/a.png"
    assert len(tool.convert) == 1 and len(tool.report) == 2
    assert before == [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]


def test_retry_conversion_without_output_can_take_explicit_charset(root, tool):
    tool.error = ValueError("synthetic")
    drop(root)
    assert ingest.ingest(root)["errors"][0]["code"] == "conversion_failed"
    item, = committed(root)
    assert item.meta["conversion"] is None and not (item.path / "converted.md").exists()
    tool.error = None
    assert not ingest.ingest(root, retry=True, charset="cp949")["errors"]
    assert load_item(item.path).meta["conversion"]["activity"]["params"]["charset"] == "cp949"
    assert len(tool.convert) == 2


@pytest.mark.parametrize("step", ["conversion_pending", "converted.md", "conversion", "triage", "meta.json"])
def test_retry_faults_never_redo_completed_output(root, tool, fault_after, step):
    tool.error = ValueError("first attempt has no completed output")
    drop(root, "source.pdf")
    ingest.ingest(root)
    item, = committed(root)
    tool.error = None
    fault_after(step)
    failed = ingest.ingest(root, retry=True)
    assert failed["errors"][0]["code"] == "io_error"
    result = ingest.ingest(root, retry=True)
    assert not result["errors"] and load_item(item.path).meta["state"] == "ready"
    assert len(tool.convert) == 2


@pytest.mark.parametrize("state", ["ready", "awaiting-approval", "ocr-in-progress", "unsupported"])
def test_retry_skips_other_states_without_any_writes(root, tool, state):
    item = make_item(root, state=state)
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in item.path.rglob("*") if p.is_file()}
    assert ingest.ingest(root, retry=True)["items"] == [{"id": item.meta["id"], "result": "skipped"}]
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in item.path.rglob("*") if p.is_file()}
    assert not tool.convert


def test_failed_new_item_is_not_retried_twice_in_one_run(root, tool):
    tool.error = ValueError("synthetic")
    drop(root)
    result = ingest.ingest(root, retry=True)
    assert result["items"][0]["result"] == "new" and len(tool.convert) == 1


def test_invalid_charset_is_rejected_before_writes(root):
    source = drop(root)
    with pytest.raises(SbError) as error:
        ingest.ingest(root, charset="not-a-real-charset")
    assert (error.value.code, error.value.exit) == ("invalid_request", 2)
    assert source.exists() and not (root / "raws").exists()


def test_missing_inbox_is_io_error_without_creating_layout(tmp_path):
    root = tmp_path / "absent"
    with pytest.raises(SbError) as error:
        ingest.ingest(root)
    assert (error.value.code, error.value.exit) == ("io_error", 1) and not root.exists()


def test_at35_long_destination_is_rejected_before_claim(root, tool):
    source = drop(root, "가" * 200 + ".txt")
    result = ingest.ingest(root)
    assert [e["code"] for e in result["errors"]] == ["path_too_long"]
    assert source.exists() and not stages(root) and not tool.convert


def test_at35_nfd_filename_stays_exact(root, tool):
    name = unicodedata.normalize("NFD", "이름.txt")
    drop(root, name)
    ingest.ingest(root)
    item, = committed(root)
    assert item.meta["filename"] == name and (item.path / "src" / name).name == name
    assert item.meta["filename_nfc"] == unicodedata.normalize("NFC", name)


def test_at35_failed_claim_leaves_inbox_intact(root, tool, monkeypatch):
    source = drop(root)
    replace = os.replace
    def fail(src, dst):
        if Path(src) == source:
            raise OSError("volume rejected received name")
        return replace(src, dst)
    monkeypatch.setattr(os, "replace", fail)
    assert ingest.ingest(root)["errors"][0]["code"] == "io_error"
    assert source.exists() and not tool.convert


def test_at36_hidden_and_reparse_are_skipped_without_following(root, tool, monkeypatch):
    import secondbrain.fsutil as fsutil
    hidden = drop(root, ".hidden")
    nested = drop(root, ".hidden-dir/file.txt")
    link = drop(root, "junction/untouched.txt").parent
    original = fsutil.is_reparse_point
    is_reparse = lambda path: Path(path) == link or original(path)
    monkeypatch.setattr(fsutil, "is_reparse_point", is_reparse)
    monkeypatch.setattr(ingest, "is_reparse_point", is_reparse)
    result = ingest.ingest(root)
    assert sorted(w["code"] for w in result["warnings"]) == ["skipped_hidden", "skipped_hidden", "skipped_reparse"]
    assert hidden.exists() and nested.exists() and (link / "untouched.txt").exists()
    assert not result["items"] and not tool.convert


def test_snapshot_is_relative_path_sorted_and_fixed_before_processing(root, tool, monkeypatch):
    drop(root, "z.txt", b"z")
    drop(root, "a/deep.txt", b"a")
    original = convert.classify_item
    def late(directory, stage):
        drop(root, "late.txt", b"late")
        return original(directory, stage)
    monkeypatch.setattr(convert, "classify_item", late)
    assert not ingest.ingest(root)["errors"]
    assert [p.name for p, _ in tool.convert] == ["deep.txt", "z.txt"]
    assert (root / "inbox/late.txt").exists()


@pytest.mark.parametrize("retry", [False, True])
def test_corrupt_committed_meta_is_reported_preserved_and_blocks_duplicate(root, tool, retry):
    item = make_item(root)
    data = (item.path / "src" / item.meta["filename"]).read_bytes()
    (item.path / "meta.json").write_bytes(b"{")
    drop(root, "copy.txt", data)
    result = ingest.ingest(root, retry=retry)
    assert "corrupt_meta" in [e["code"] for e in result["errors"]]
    assert (item.path / "meta.json").read_bytes() == b"{" and stages(root) and not tool.convert


def test_corrupt_staged_artifact_is_not_overwritten_or_committed(root, tool, fault_after):
    drop(root)
    fault_after("conversion")
    ingest.ingest(root)
    directory, = stages(root)
    (directory / "converted.md").write_bytes(b"tampered")
    assert ingest.ingest(root)["errors"][0]["code"] == "corrupt_meta"
    assert (directory / "converted.md").read_bytes() == b"tampered" and len(tool.convert) == 1
    assert not committed(root)


def test_staged_meta_must_agree_with_ledger_before_commit(root, tool, fault_after):
    drop(root)
    fault_after("meta.json")
    ingest.ingest(root)
    directory, = stages(root)
    meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
    meta["filename"] = "tampered.txt"
    write_json_atomic(directory / "meta.json", meta)
    assert ingest.ingest(root)["errors"][0]["code"] == "corrupt_meta"
    assert directory.exists() and not committed(root) and len(tool.convert) == 1


def test_unreferenced_conversion_cannot_be_adopted_without_intent(root, tool, fault_after):
    drop(root)
    fault_after("claim")
    ingest.ingest(root)
    directory, = stages(root)
    (directory / "converted.md").write_bytes(b"unreferenced output")
    assert ingest.ingest(root)["errors"][0]["code"] == "corrupt_meta"
    assert (directory / "converted.md").read_bytes() == b"unreferenced output" and not tool.convert


def test_orphans_in_committed_items_are_warned_and_preserved(root, tool):
    item = make_item(root)
    orphan = item.path / "extra.txt"
    orphan.write_bytes(b"unreferenced")
    result = ingest.ingest(root, retry=True)
    assert result["warnings"][0]["code"] == "orphan"
    assert orphan.read_bytes() == b"unreferenced" and not tool.convert


@pytest.mark.parametrize("ext", [".txt", ".csv", ".log", ".json", ".xml"])
def test_at08_plain_text_set_never_calls_report(root, tool, ext):
    drop(root, "source" + ext)
    assert not ingest.ingest(root)["errors"]
    item, = committed(root)
    assert item.meta["class"] == "text-only" and item.meta["state"] == "ready"
    assert item.meta["triage"] is None and not tool.report and len(tool.convert) == 1


def test_at11_candidates_without_extracted_images_have_no_units(root, tool, monkeypatch):
    drop(root, "empty-images.docx")
    triage = convert.adapt_report(json.loads((FIXTURES / "reports/row-10.json").read_text(encoding="utf-8")), ".docx")
    monkeypatch.setattr(convert, "run_report", lambda *args: triage)
    assert not ingest.ingest(root)["errors"]
    item, = committed(root)
    assert (item.meta["class"], item.meta["state"], item.meta["reason"]) == ("unknown", "awaiting-approval", "no_units")
    assert not item.meta["ocr"]["units"]


def test_staging_collision_flag_without_identity_is_corrupt(root, tool):
    directory = root / "raws/.staging/tmp-1"
    (directory / "src").mkdir(parents=True)
    (directory / "src/file.txt").write_bytes(b"original")
    write_json_atomic(directory / "stage.json", {"filename": "file.txt", "relpath": "file.txt", "charset": None,
                                               "claimed_at": DATE, "collision": True})
    result = ingest.ingest(root)
    assert result["errors"][0]["code"] == "corrupt_meta"
    assert (directory / "src/file.txt").read_bytes() == b"original"


def test_ag_b1_meta_present_recovery_has_classification_keys(root, tool, fault_after):
    drop(root, "source.pdf")
    fault_after("meta.json")
    assert ingest.ingest(root)["errors"][0]["code"] == "io_error"
    directory, = stages(root)
    stage = load_stage(directory)
    assert {"class", "state", "reason", "error", "ocr"} <= stage.keys()
    before = (directory / "meta.json").read_bytes()
    result = ingest.ingest(root)
    item, = committed(root)
    assert not result["errors"] and not stages(root)
    assert (item.path / "meta.json").read_bytes() == before
    assert len(tool.convert) == len(tool.report) == 1


@pytest.mark.parametrize("completed", [False, True])
def test_ag_b2_pending_conversion_recovery_respects_completed_output(root, tool, fault_after, completed):
    drop(root, "source.pdf")
    fault_after("converted.md" if completed else "conversion_pending")
    assert ingest.ingest(root)["errors"][0]["code"] == "io_error"
    directory, = stages(root)
    assert load_stage(directory)["conversion"]["sha256"] is None
    output = directory / "converted.md"
    assert output.exists() == completed
    stamp = output.stat().st_mtime_ns if completed else None
    assert not ingest.ingest(root)["errors"]
    item, = committed(root)
    assert len(tool.convert) == 1
    assert item.meta["conversion"]["sha256"] == sha256((item.path / "converted.md").read_bytes()).hexdigest()
    if completed:
        assert (item.path / "converted.md").stat().st_mtime_ns == stamp


def test_ag_b3_retained_stage_reuses_all_durable_outputs(root, tool, monkeypatch):
    # A valid report with no candidate ids fails classification after every
    # durable output has been recorded, including triage and native text.
    cached = convert.adapt_report(json.loads((FIXTURES / "reports/row-07.json").read_text(encoding="utf-8")), ".pdf")
    reports = []
    def report(*args):
        reports.append(True)
        return deepcopy(cached)
    monkeypatch.setattr(convert, "run_report", report)
    drop(root, "source.pdf")
    assert ingest.ingest(root)["errors"][0]["code"] == "no_candidate_ids"
    item, = committed(root)
    keys = ("conversion", "triage", "has_native_text")
    before = {key: item.meta[key] for key in keys}
    assert all(value is not None for value in before.values())
    assert {key: load_stage(item.path)[key] for key in keys} == before
    result = ingest.ingest(root, retry=True)
    assert result["items"] == [{"id": item.meta["id"], "result": "retried"}]
    assert [e["code"] for e in result["errors"]] == ["no_candidate_ids"]
    assert {key: load_item(item.path).meta[key] for key in keys} == before
    assert {key: load_stage(item.path)[key] for key in keys} == before
    assert len(tool.convert) == len(reports) == 1


def test_ag_invalid_conversion_activity_is_rejected_before_retry(root, tool, monkeypatch):
    item = make_item(root, state="failed", filename="source.pdf", text="Completed native text")
    item.meta["conversion"]["activity"] = None
    write_json_atomic(item.path / "meta.json", item.meta)
    before = (item.path / "meta.json").read_bytes()
    monkeypatch.setattr(ingest, "_retry", lambda *args: pytest.fail("corrupt meta must never reach retry"))
    result = ingest.ingest(root, retry=True)
    assert [e["code"] for e in result["errors"]] == ["corrupt_meta"]
    assert (item.path / "meta.json").read_bytes() == before and not tool.convert


def test_ag_missing_stage_filename_is_corrupt_and_preserves_payload(root, tool):
    directory = root / "raws/.staging/tmp-1"
    (directory / "src").mkdir(parents=True)
    payload = directory / "src/original.txt"
    payload.write_bytes(b"original payload")
    write_json_atomic(directory / "stage.json", {"relpath": "original.txt", "charset": None, "claimed_at": DATE})
    before = (directory / "stage.json").read_bytes()
    result = ingest.ingest(root)
    assert [e["code"] for e in result["errors"]] == ["corrupt_meta"]
    assert payload.read_bytes() == b"original payload" and (directory / "stage.json").read_bytes() == before


def test_ag_aliases_preserve_distinct_exact_unicode_spellings(root, tool):
    original = "이름.txt"
    alias = unicodedata.normalize("NFD", original)
    assert original != alias
    item = make_item(root, filename=original)
    data = (item.path / "src" / original).read_bytes()
    drop(root, alias, data)
    assert ingest.ingest(root)["items"][0]["result"] == "alias_added"
    assert load_item(item.path).meta["aliases"] == [alias]
    before = (item.path / "meta.json").read_bytes()
    drop(root, alias, data)
    assert ingest.ingest(root)["items"][0]["result"] == "duplicate"
    assert (item.path / "meta.json").read_bytes() == before and not tool.convert


def test_plain_ingest_does_not_scan_unrelated_committed_items(root, tool, monkeypatch):
    item = make_item(root)
    (item.path / "meta.json").write_bytes(b"{")
    load = ingest.load_item
    def only_target(directory):
        assert Path(directory) != item.path, "plain ingest must not read an unrelated committed item"
        return load(directory)
    monkeypatch.setattr(ingest, "load_item", only_target)
    drop(root, "new.txt", b"new distinct bytes")
    result = ingest.ingest(root)
    assert not result["errors"] and len(result["items"]) == 1
    assert result["items"][0]["result"] == "new"
    assert (item.path / "meta.json").read_bytes() == b"{"


@pytest.mark.parametrize("group", ["text", "ocr", "mixed", "unknown", "unsupported", "characterize", "failed"])
def test_real_fixture_ingest_matches_gate_and_retry(root, group):
    """AT-08–13 at the ingest boundary, with real 0.3.5 conversion/report."""
    paths = sorted((FIXTURES / group).iterdir())
    for path in paths:
        fixture(root, f"{group}/{path.name}")
    # CP949 has a per-command option, so ingest it separately.
    cp949 = root / "inbox/korean-cp949.txt"
    cp_bytes = cp949.read_bytes() if cp949.exists() else None
    if cp_bytes is not None:
        cp949.rename(root / "korean-cp949.held")
    result = ingest.ingest(root)
    if cp_bytes is not None:
        (root / "korean-cp949.held").rename(cp949)
        result["items"].extend(ingest.ingest(root, charset="cp949")["items"])
    assert len(result["items"]) == len(paths)
    by_name = {i.meta["filename"]: i for i in committed(root)}
    for path in paths:
        probe = json.loads((FIXTURES / "reports" / f"{group}--{path.name}.probe.json").read_text(encoding="utf-8"))
        expected = probe.get("design_row_class_state_reason_r9", probe["design_row_class_state_reason"])
        item = by_name[path.name]
        assert [item.meta["class"], item.meta["state"], item.meta["reason"]] == expected[1:]
        assert len(item.meta["ocr"]["units"]) == len(probe["units"])
        if path.suffix.lower() in convert.CONTAINER_EXTENSIONS and probe["media"]:
            assert (item.path / "media").is_dir()
            assert {asset["sha256"] for asset in item.meta["conversion"]["media"]} == {asset["sha256"] for asset in probe["media"]}
        assert (item.path / "src" / path.name).read_bytes() == path.read_bytes()
        if path.name == "korean-cp949.txt":
            assert (item.path / "converted.md").read_text(encoding="utf-8") == cp_bytes.decode("cp949")
            assert item.meta["conversion"]["activity"]["params"]["charset"] == "cp949"
        if group == "failed":
            assert item.meta["error"] is not None
    if group == "failed":
        retry = ingest.ingest(root, retry=True)
        assert len(retry["items"]) == len(paths) and all(i["result"] == "retried" for i in retry["items"])
        assert all(i.meta["state"] == "failed" for i in committed(root))
    assert not stages(root) and not list((root / "inbox").rglob("*"))
