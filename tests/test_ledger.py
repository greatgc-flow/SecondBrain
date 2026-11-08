from hashlib import sha256
import json
import os
from types import SimpleNamespace
import unicodedata

import pytest

from helpers import DATE, add_summary, make_item, provenance, save_meta
from secondbrain.errors import SbError
from secondbrain.ledger import activity, load_item, load_stage, validate_meta, validate_stage


@pytest.mark.parametrize("classification,state,text,filename", [
    ("text-only", "ready", "native", "source.txt"),
    ("ocr-required", "awaiting-approval", "", "source.pdf"),
    ("mixed", "ocr-in-progress", "native", "source.pdf"),
    ("mixed", "ready", "native", "source.pdf"),
    ("unknown", "awaiting-approval", "native", "source.md"),
    ("unknown", "ready", "native", "source.md"),
    ("unsupported", "unsupported", None, "source.xyz"),
    (None, "failed", None, "source.pdf"),
])
def test_at16_all_states_validate(root, classification, state, text, filename):
    item = make_item(root, classification=classification, state=state, text=text, filename=filename)
    assert validate_meta(item.meta, item.path) == []
    loaded = load_item(item.path)
    assert loaded.meta == item.meta and loaded.warnings == []


@pytest.mark.parametrize("field,value", [
    ("schema", True), ("schema", 2), ("sha256", "z" * 64), ("id", "0" * 16),
    ("size", True), ("size", -1), ("size", 999), ("ext", ".TXT"),
    ("filename", "../escape.txt"), ("filename_nfc", "wrong"),
    ("aliases", ["z.txt", "a.txt"]), ("aliases", ["x", "x"]), ("aliases", ["source.txt"]),
    ("ingested_at", "2026-11-09"), ("ingested_at", "2026-11-09T01:00:00+01:00"),
    ("class", "anything"), ("class", None), ("state", "awaiting-approval"),
    ("conversion", None), ("has_native_text", None), ("error", {"code": "bad"}),
    ("ocr", {"disposition": "approved", "large_ack": False, "units": {}}),
])
def test_at16_corrupt_contract_is_not_modified(root, field, value):
    item = make_item(root)
    item.meta[field] = value
    save_meta(item)
    before = {p: p.read_bytes() for p in item.path.rglob("*") if p.is_file()}
    with pytest.raises(SbError) as error:
        load_item(item.path)
    assert (error.value.code, error.value.exit) == ("corrupt_meta", 1)
    assert before == {p: p.read_bytes() for p in item.path.rglob("*") if p.is_file()}


@pytest.mark.parametrize("artifact", ["converted.md", "ocr/u0001.a1.md", "llm/summary.a1.md"])
@pytest.mark.parametrize("action", ["missing", "digest"])
def test_at16_referenced_artifacts_required(root, artifact, action):
    item = add_summary(make_item(root, filename="source.pdf", classification="mixed", state="ready", statuses=["verified"]))
    path = item.path / artifact
    if action == "missing":
        path.unlink()
    else:
        path.write_text("changed", encoding="utf-8")
    with pytest.raises(SbError) as error:
        load_item(item.path)
    assert error.value.code == "corrupt_meta"


def test_at16_orphans_warn_without_becoming_references(root):
    item = make_item(root)
    (item.path / "ocr").mkdir()
    (item.path / "ocr/u0001.a9.md").write_text("orphan", encoding="utf-8")
    loaded = load_item(item.path)
    assert [(w["code"], w["id"], w["path"]) for w in loaded.warnings] == [
        ("orphan", item.meta["id"], "ocr/u0001.a9.md")]
    assert loaded.meta == item.meta


def test_source_size_checked_without_rehash(root):
    item = make_item(root)
    source = item.path / "src/source.txt"
    source.write_bytes(b"x" * item.meta["size"])
    assert load_item(item.path).meta["sha256"] == item.meta["sha256"]


def test_source_missing_and_invalid_json(root):
    item = make_item(root)
    (item.path / "src/source.txt").unlink()
    with pytest.raises(SbError):
        load_item(item.path)
    (item.path / "meta.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(SbError):
        load_item(item.path)


@pytest.mark.parametrize("change", ["status", "peer", "attempt-number", "attempt-path", "disposition", "triage", "version", "params", "large-ack"])
def test_nested_contract_rejected(root, change):
    item = make_item(root, filename="source.pdf", classification="mixed", statuses=["verified"])
    unit = item.meta["ocr"]["units"]["u0001"]
    if change == "status": unit["status"] = "recorded"
    if change == "peer": unit["attempts"][0]["verified"]["peer"] = "cx"
    if change == "attempt-number": unit["attempts"][0]["n"] = 2
    if change == "attempt-path": unit["attempts"][0]["file"] = "../outside.md"
    if change == "disposition": item.meta["ocr"]["disposition"] = "none"
    if change == "triage": item.meta["triage"]["coverage"]["pages_total"] = True
    if change == "version": item.meta["conversion"]["activity"]["version"] = "0.3.4"
    if change == "params": unit["attempts"][0]["recorded"]["params"].pop("dpi")
    if change == "large-ack": item.meta["ocr"]["large_ack"] = 1
    with pytest.raises(SbError):
        validate_meta(item.meta, item.path)


def test_media_references_and_orphans(root):
    item = make_item(root, filename="source.docx")
    (item.path / "media").mkdir()
    (item.path / "media/image.png").write_bytes(b"synthetic raster")
    item.meta["conversion"]["media"] = [{"file": "media/image.png", "sha256": sha256(b"synthetic raster").hexdigest()}]
    item.meta["conversion"]["activity"]["params"]["extract_media"] = True
    assert validate_meta(item.meta, item.path) == []
    item.meta["conversion"]["media"][0]["file"] = "src/source.docx"
    with pytest.raises(SbError):
        validate_meta(item.meta, item.path)


def test_stage_preclaim_pending_and_reconciliation(root):
    path = root / "raws/.staging/tmp-1"
    path.mkdir(parents=True)
    stage = {"relpath": "sub/source.txt", "filename": "source.txt", "charset": "cp949", "claimed_at": DATE}
    assert validate_stage(stage, path) == []
    (path / "src").mkdir()
    (path / "src/source.txt").write_bytes(b"source")
    digest = sha256(b"source").hexdigest()
    stage["identity"] = {"id": digest[:16], "sha256": digest, "size": 6}
    stage["conversion"] = {"activity": provenance(), "sha256": None}
    (path / "converted.md").write_text("completed before crash", encoding="utf-8")
    assert validate_stage(stage, path)[0]["code"] == "orphan"
    (path / "stage.json").write_text(json.dumps(stage), encoding="utf-8")
    assert load_stage(path) == stage
    stage["conversion"]["sha256"] = sha256((path / "converted.md").read_bytes()).hexdigest()
    stage["conversion"]["media"] = []
    assert validate_stage(stage, path) == []
    stage["filename"] = "../escape"
    with pytest.raises(SbError):
        validate_stage(stage, path)


def test_activity_and_invalid_request():
    record = activity("peerhub", None, "ocr-verify", peer="cc", model="synthetic", params={"prompt_rev": "verify-v1"}, date=DATE)
    assert record["date"] == DATE and record["version"] is None
    with pytest.raises(SbError) as error:
        activity("peerhub", None, "ocr-verify", peer="../cx", model="synthetic", params={"prompt_rev": "verify-v1"})
    assert error.value.code == "invalid_request"


@pytest.mark.parametrize("change", ["missing-conversion", "missing-report", "raster-conversion", "mixed-without-native"])
def test_at16_presence_rules(root, change):
    if change == "raster-conversion":
        item = make_item(root, filename="photo.png", classification="ocr-required", state="awaiting-approval", text="not raster conversion")
    else:
        item = make_item(root, filename="source.pdf", classification="mixed", state="ocr-in-progress")
        if change == "missing-conversion":
            item.meta["conversion"] = item.meta["has_native_text"] = None
        if change == "missing-report":
            item.meta["triage"] = None
        if change == "mixed-without-native":
            item.meta["has_native_text"] = False
    with pytest.raises(SbError):
        validate_meta(item.meta, item.path)


def test_valid_raster_without_conversion(root):
    item = make_item(root, filename="photo.png", classification="ocr-required", state="awaiting-approval", text=None)
    assert validate_meta(item.meta, item.path) == []


@pytest.mark.parametrize("change", ["schema", "coverage", "candidate-type", "candidate-duplicate", "candidate-bound", "issues", "attempt-fields", "attempt-history", "summary-number", "summary-digest", "summary-provenance"])
def test_at16_nested_types_and_histories(root, change):
    item = add_summary(make_item(root, filename="source.pdf", classification="mixed", state="ready"))
    unit = item.meta["ocr"]["units"]["u0001"]
    if change == "schema": item.meta.pop("filename_nfc")
    if change == "coverage": item.meta["triage"]["coverage"]["pages_inspected"] = 5
    if change == "candidate-type": item.meta["triage"]["candidates"][0]["page"] = "1"
    if change == "candidate-duplicate": item.meta["triage"]["candidates"] *= 2
    if change == "candidate-bound": item.meta["triage"]["candidates"][0]["id"] = "p10"
    if change == "issues": item.meta["triage"]["issues"] = ["one"] * 21
    if change == "attempt-fields": unit["attempts"][0]["recorded"]["peer"] = "CX"
    if change == "attempt-history": unit["attempts"].append(dict(unit["attempts"][0], n=2, file="ocr/u0001.a2.md"))
    if change == "summary-number": item.meta["llm"]["summary"][0]["n"] = True
    if change == "summary-digest": item.meta["llm"]["summary"][0]["source_digest"] = "bad"
    if change == "summary-provenance": item.meta["llm"]["summary"][0]["activity"]["method"] = "ocr-verify"
    with pytest.raises(SbError):
        validate_meta(item.meta, item.path)


def test_at16_json_duplicate_keys_rejected(root):
    item = make_item(root)
    file = item.path / "meta.json"
    file.write_text(file.read_text(encoding="utf-8").replace('"schema": 1', '"schema": 1, "schema": 1'), encoding="utf-8")
    with pytest.raises(SbError):
        load_item(item.path)


def test_at16_reparse_artifact_is_refused(root, monkeypatch):
    item = make_item(root)
    import secondbrain.fsutil as fsutil
    original = fsutil.is_reparse_point
    monkeypatch.setattr(fsutil, "is_reparse_point", lambda p: str(p).endswith("converted.md") or original(p))
    with pytest.raises(SbError) as error:
        load_item(item.path)
    assert error.value.code == "corrupt_meta"


def test_ocr_mismatch_history_remains_valid(root):
    item = make_item(root, filename="source.pdf", classification="mixed", state="ocr-in-progress", statuses=["recorded"])
    unit = item.meta["ocr"]["units"]["u0001"]
    unit["status"] = "approved"
    unit["attempts"][0].update(result="mismatch", verified=provenance("ocr-verify", "cc"))
    assert validate_meta(item.meta, item.path) == []


def test_activity_unit_file_is_a_provenance_string():
    record = provenance("ocr-vision")
    record["params"]["unit_file"] = "work/0123456789abcdef/u0001.png"
    assert activity(**record) == record


def test_committed_staging_ledger_is_retained_without_warning(root):
    item = make_item(root)
    (item.path / "stage.json").write_text('{"filename": "source.txt"}', encoding="utf-8")
    loaded = load_item(item.path)
    assert loaded.warnings == []
    assert (item.path / "stage.json").exists()


def test_valid_declined_ocr(root):
    item = make_item(root, filename="source.pdf", classification="mixed", state="awaiting-approval")
    item.meta["state"] = "ready"
    item.meta["ocr"]["disposition"] = "declined"
    assert validate_meta(item.meta, item.path) == []


def test_failed_conversion_reason_differs_from_error_code(root):
    item = make_item(root, state="failed")
    item.meta["reason"] = "FileConversionException"
    item.meta["error"]["code"] = "conversion_failed"
    save_meta(item)
    assert load_item(item.path).meta["reason"] == "FileConversionException"


@pytest.mark.parametrize("change", ["large-approval", "noncontiguous-keys", "not-a-candidate", "llm-not-ready", "llm-unsupported"])
def test_fable_missing_ledger_cases(root, change):
    if change == "large-approval":
        item = make_item(root, state="ocr-in-progress", statuses=["approved"] * 21)
        item.meta["ocr"]["large_ack"] = False
    elif change in {"noncontiguous-keys", "not-a-candidate"}:
        item = make_item(root, state="ocr-in-progress", statuses=["approved", "pending"])
        units = item.meta["ocr"]["units"]
        if change == "noncontiguous-keys":
            units["u0003"] = units.pop("u0002")
        else:
            units["u0001"]["source"] = "p3"
    else:
        item = add_summary(make_item(root))
        item.meta.update(state="awaiting-approval", **{"class": "unknown"})
        if change == "llm-unsupported":
            item.meta.update(state="unsupported", **{"class": "unsupported"})
    with pytest.raises(SbError) as error:
        validate_meta(item.meta, item.path)
    assert error.value.code == "corrupt_meta"


def test_committed_hidden_and_reparse_orphans_are_not_inbox_skips(root, monkeypatch):
    import secondbrain.ledger as ledger
    item = make_item(root)
    (item.path / ".hidden.md").write_bytes(b"orphan")
    (item.path / "linked-file").write_bytes(b"orphan")
    (item.path / "linked-dir").mkdir()
    (item.path / "linked-dir/child").write_bytes(b"do not traverse")
    original = ledger.is_reparse_point
    monkeypatch.setattr(ledger, "is_reparse_point", lambda p: p.name in {"linked-file", "linked-dir"} or original(p))
    loaded = load_item(item.path)
    assert [(w["path"], w["code"]) for w in loaded.warnings] == [
        (".hidden.md", "orphan"), ("linked-dir", "orphan"), ("linked-file", "orphan")]
    assert (item.path / "linked-dir/child").read_bytes() == b"do not traverse"


def test_nfc_equivalent_distinct_filename_is_still_an_orphan(root):
    name = "이름.txt"
    item = make_item(root, filename=name)
    decomposed = unicodedata.normalize("NFD", name)
    extra = item.path / "src" / decomposed
    extra.write_bytes(b"distinct unreferenced source")
    assert not extra.samefile(item.path / "src" / name)
    assert [w["path"] for w in load_item(item.path).warnings] == ["src/" + decomposed]


@pytest.mark.parametrize("name", ['source:stream.txt', '*.txt', 'q?.txt', 'a"b.txt', '<x>.txt', 'a|b.txt', 'CON.txt', 'aux', 'LPT1.log', 'COM9', 'name.', 'name '])
def test_windows_reserved_names_rejected_in_stage(root, monkeypatch, name):
    import secondbrain.ledger as ledger
    # Exercise Windows rules on both CI operating systems without changing os.name globally.
    monkeypatch.setattr(ledger, "os", SimpleNamespace(name="nt", walk=os.walk))
    stage = {"relpath": name, "filename": name, "charset": None, "claimed_at": DATE}
    with pytest.raises(SbError) as error:
        validate_stage(stage, root)
    assert error.value.code == "corrupt_meta"


def test_posix_volume_valid_name_is_not_rewritten(root, monkeypatch):
    import secondbrain.ledger as ledger
    monkeypatch.setattr(ledger, "os", SimpleNamespace(name="posix", walk=os.walk))
    stage = {"relpath": 'a?b*.txt', "filename": 'a?b*.txt', "charset": None, "claimed_at": DATE}
    assert validate_stage(stage, root) == []


def test_summary_helper_binds_view_and_peer_methods(root):
    from secondbrain.transcript import source_digest
    item = add_summary(make_item(root, classification="mixed", state="ready"))
    loaded = load_item(item.path)
    revision = loaded.meta["llm"]["summary"][-1]
    assert revision["source_digest"] == source_digest(loaded)
    assert revision["activity"]["method"] == "summary"
    assert loaded.meta["ocr"]["units"]["u0001"]["attempts"][-1]["verified"]["method"] == "ocr-verify"


@pytest.mark.parametrize("state", ["ready", "awaiting-approval", "ocr-in-progress", "unsupported", "failed"])
def test_shared_helper_defaults_build_valid_items_in_every_state(root, state):
    item = make_item(root, state=state)
    assert validate_meta(item.meta, item.path) == []


def test_shared_helper_default_ocr_has_no_native_text(root):
    item = make_item(root, classification="ocr-required", state="awaiting-approval")
    assert validate_meta(item.meta, item.path) == []


def test_valid_asset_source(root):
    item = make_item(root, filename="source.pdf", classification="mixed", state="awaiting-approval")
    item.meta["filename"] = item.meta["filename_nfc"] = "source.docx"
    (item.path / "src/source.pdf").rename(item.path / "src/source.docx")
    item.meta["ext"] = ".docx"
    media = item.path / "media"
    media.mkdir()
    (media / "image.png").write_bytes(b"image")
    item.meta["conversion"]["media"] = [{"file": "media/image.png", "sha256": sha256(b"image").hexdigest()}]
    item.meta["conversion"]["activity"]["params"]["extract_media"] = True
    item.meta["ocr"]["units"]["u0001"].update(source="media/image.png", kind="asset")
    assert validate_meta(item.meta, item.path) == []
