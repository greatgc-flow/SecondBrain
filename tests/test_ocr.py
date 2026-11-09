"""Slice 5: OCR approve/decline/record (5a) and verify/finalize/faults (5b); AT-17..AT-25, AT-27 (OCR part)."""
import hashlib
from pathlib import Path
import re
import shutil

import pytest

import helpers
from secondbrain import ocr, transcript
from secondbrain.errors import SbError
from secondbrain.ledger import load_item

FIXTURES = Path(__file__).parent / "fixtures"


tree = helpers.tree


def fails(root, code, function, *args, **kwargs):
    before = tree(root)
    with pytest.raises(SbError) as error:
        function(*args, **kwargs)
    assert error.value.code == code and error.value.exit == 2
    assert tree(root) == before, "a rejected request must not write"


@pytest.fixture
def fake_render(monkeypatch):
    calls = []

    def render(item, key, unit, target, dpi):
        calls.append((key, dpi))
        Path(target).write_bytes(f"image {key} dpi {dpi}".encode())
    monkeypatch.setattr(ocr, "_render", render)
    return calls


def units_item(root, statuses, state="ocr-in-progress", filename="doc.pdf", **kwargs):
    return helpers.make_item(root, state=state, classification="mixed", filename=filename, statuses=statuses, **kwargs)


def work_dir(root, item_id):
    return root / "work" / item_id


def work(root, item):
    return work_dir(root, item.meta["id"])


def put(root, item, key, body):
    path = work(root, item) / f"{key}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    return path


def status(item):
    return {k: u["status"] for k, u in load_item(item.path).meta["ocr"]["units"].items()}


def pdf_item(root):
    item = units_item(root, ["pending"], state="awaiting-approval", filename="two-pages.pdf")
    data = (FIXTURES / "mixed" / "two-pages.pdf").read_bytes()
    (item.path / "src" / "two-pages.pdf").write_bytes(data)
    meta = item.meta
    meta["size"] = len(data)
    meta["ocr"]["units"]["u0001"]["source"] = "p2"
    meta["triage"]["candidates"] = [{"id": "p2", "kind": "page", "page": 2, "priority": "high"}]
    meta["triage"]["coverage"].update(pages_total=2, pages_inspected=2)
    helpers.save_meta(item)
    return item


# ---------------------------------------------------------------- 5a approve

def test_at17_large_item_needs_acknowledgement(root, fake_render):
    item = units_item(root, ["pending"] * 25, state="awaiting-approval")
    fails(root, "large_requires_ack", ocr.approve, root, item.meta["id"])
    result = ocr.approve(root, item.meta["id"], yes_large=True)
    assert len(result["approved"]) == 25 and "leave this machine" in result["notice"]
    meta = load_item(item.path).meta
    assert meta["state"] == "ocr-in-progress" and meta["ocr"]["disposition"] == "approved" and meta["ocr"]["large_ack"]
    assert set(status(item).values()) == {"approved"}


def test_at17_cap_of_30_then_second_approval_then_full_flow(root, fake_render):
    item = units_item(root, ["pending"] * 31, state="awaiting-approval")
    item_id = item.meta["id"]
    ocr.approve(root, item_id, yes_large=True)
    values = list(status(item).values())
    assert values.count("approved") == 30 and values[-1] == "pending"
    ocr.approve(root, item_id)  # acknowledgement is first-call only
    assert set(status(item).values()) == {"approved"}
    fails(root, "invalid_request", ocr.approve, root, item_id)  # nothing left to approve
    for n in range(1, 32):
        put(root, item, f"u{n:04}", f"text {n}")
    assert len(ocr.record(root, item_id, "cx", "m")["recorded"]) == 31
    keys = [f"u{n:04}" for n in range(1, 32)]
    assert ocr.verify(root, item_id, "cc", "m", ok=keys)["result"] == "finalized"
    assert load_item(item.path).meta["state"] == "ready" and not work(root, item).exists()


def test_at18_pdf_page_rendered_and_commands(root):
    import pdfplumber
    item = pdf_item(root)
    result = ocr.approve(root, item.meta["id"])
    assert result["approved"] == ["u0001"]
    png = work(root, item) / "u0001.png"
    with pdfplumber.open(FIXTURES / "mixed" / "two-pages.pdf") as pdf:
        pdf.pages[1].to_image(resolution=200).save(root / "page2.png")
        pdf.pages[0].to_image(resolution=200).save(root / "page1.png")
    assert png.read_bytes() == (root / "page2.png").read_bytes() != (root / "page1.png").read_bytes()
    commands = (work(root, item) / "COMMANDS.txt").read_text(encoding="utf-8")
    assert "ocr-v1" in commands and "verify-v1" in commands and f"--stream ocr-{item.meta['id']}-1" in commands
    assert f'"{png}"' in commands and png.is_absolute() and "first 5" in commands and "at most 2 asks" in commands


def test_dpi_option_changes_rendering(root):
    import pdfplumber
    item = pdf_item(root)
    ocr.approve(root, item.meta["id"], dpi=300)
    with pdfplumber.open(FIXTURES / "mixed" / "two-pages.pdf") as pdf:
        pdf.pages[1].to_image(resolution=300).save(root / "p300.png")
    assert (work(root, item) / "u0001.png").read_bytes() == (root / "p300.png").read_bytes()


def test_commands_ask_grouping_of_three_with_stream_names(root, fake_render):
    item = units_item(root, ["pending"] * 7, state="awaiting-approval")
    ocr.approve(root, item.meta["id"])
    commands = (work(root, item) / "COMMANDS.txt").read_text(encoding="utf-8")
    asks = [l for l in commands.splitlines() if l.startswith("peerhub ask cx")]
    assert len(asks) == 3
    assert [len(re.findall(r'Open (.*?)\. Transcribe', a)[0].split(", ")) for a in asks] == [3, 3, 1]
    assert [re.search(r"--stream (\S+)", a)[1] for a in asks] == [f"ocr-{item.meta['id']}-{n}" for n in (1, 2, 3)]
    files = [l for l in commands.splitlines() if " Files: " in l]
    assert len(files) == 3 + 3  # three transcription asks and three verify groups (7 units)
    assert f'"{work(root, item) / "u0001.png"}"' in files[0]


def test_commands_peerhub_lines_have_no_inner_quotes(root, fake_render):
    item = units_item(root, ["pending"] * 4, state="awaiting-approval")
    ocr.approve(root, item.meta["id"])
    commands = (work(root, item) / "COMMANDS.txt").read_text(encoding="utf-8")
    lines = [l for l in commands.splitlines() if l.startswith("peerhub ask")]
    assert len(lines) == 4  # 2 asks + 2 verify groups
    for line in lines:
        match = re.fullmatch(r'peerhub ask (cx|cc) -p \1\.effort -w "[^"]+"(?: --writable)? --stream \S+ "([^"\$`]+)"', line)
        assert match, line
        # write asks (cx transcription) need --writable; read-only verify asks (cc) must not have it
        assert (" --writable " in line) == (match[1] == "cx"), line
        assert "u0001.png" in line or "u0004.png" in line  # relative names inside the -w folder
        assert str(work(root, item)) not in match[2]


def test_at19_assets_and_rasters_copied_byte_equal(root, subprocess_spy):
    asset = (FIXTURES / "ocr" / "photo.png").read_bytes()
    item = units_item(root, ["pending"], state="awaiting-approval", filename="slides.pptx")
    (item.path / "media").mkdir()
    (item.path / "media" / "image1.png").write_bytes(asset)
    unit = item.meta["ocr"]["units"]["u0001"]
    unit.update(kind="asset", source="media/image1.png")
    item.meta["conversion"]["media"] = [{"file": "media/image1.png", "sha256": hashlib.sha256(asset).hexdigest()}]
    helpers.save_meta(item)
    raster = helpers.make_item(root, state="awaiting-approval", classification="ocr-required", filename="photo.jpg")
    ocr.approve(root, item.meta["id"])
    ocr.approve(root, raster.meta["id"])
    assert (work(root, item) / "u0001.png").read_bytes() == asset
    assert (work(root, raster) / "u0001.jpg").read_bytes() == (raster.path / "src" / "photo.jpg").read_bytes()
    assert subprocess_spy == []


@pytest.mark.parametrize("name", ["slides.pptx", "image.hwp", "image.hwpx", "image.xlsx"])
def test_at19_real_containers_ingest_then_approve(root, subprocess_spy, name):
    from secondbrain import ingest
    shutil.copyfile(FIXTURES / "mixed" / name, root / "inbox" / name)
    result = ingest.ingest(root)
    assert not result["errors"], result["errors"]
    item_id = result["items"][0]["id"]
    directory = root / "raws" / item_id
    meta = load_item(directory).meta
    assert meta["class"] == "mixed" and meta["state"] == "awaiting-approval" and meta["ocr"]["units"]
    converted, conversion, calls = (directory / "converted.md").read_bytes(), meta["conversion"], len(subprocess_spy)
    assert [m["file"] for m in conversion["media"]] == [u["source"] for u in meta["ocr"]["units"].values()]
    ocr.approve(root, item_id)
    for key, unit in meta["ocr"]["units"].items():
        assert unit["kind"] == "asset"
        scratch = work_dir(root, item_id) / (key + Path(unit["source"]).suffix)
        assert scratch.read_bytes() == (directory / unit["source"]).read_bytes()  # the committed source image
    # approve never converts: no new subprocess, converted.md and the conversion ledger unchanged
    assert len(subprocess_spy) == calls and (directory / "converted.md").read_bytes() == converted
    assert load_item(directory).meta["conversion"] == conversion


def test_approve_rerenders_missing_scratch_for_approved_units(root, fake_render):
    item = units_item(root, ["pending", "pending"], state="awaiting-approval")
    ocr.approve(root, item.meta["id"])
    (work(root, item) / "u0002.png").unlink()
    assert ocr.approve(root, item.meta["id"])["approved"] == []
    assert (work(root, item) / "u0002.png").is_file() and set(status(item).values()) == {"approved"}


def test_approve_guards_write_nothing(root, fake_render):
    awaiting = units_item(root, ["pending"], state="awaiting-approval")
    ready = helpers.make_item(root, filename="r.txt")
    unknown = helpers.make_item(root, state="awaiting-approval", classification="unknown", filename="u.md")
    fails(root, "unknown_id", ocr.approve, root, "0123456789abcdef")
    fails(root, "unknown_id", ocr.approve, root, "../raws")
    fails(root, "state_not_allowed", ocr.approve, root, ready.meta["id"])
    fails(root, "no_units", ocr.approve, root, unknown.meta["id"])
    for bad in (0, -1, "300", 1.5):
        fails(root, "invalid_request", ocr.approve, root, awaiting.meta["id"], dpi=bad)


def test_approve_render_failure_leaves_meta_untouched(root):
    item = units_item(root, ["pending"], state="awaiting-approval")  # synthetic bytes are not a PDF
    before = (item.path / "meta.json").read_bytes()
    with pytest.raises(SbError) as error:
        ocr.approve(root, item.meta["id"])
    assert error.value.code == "io_error" and (item.path / "meta.json").read_bytes() == before


# ---------------------------------------------------------------- decline

def test_at24_decline_makes_ready_and_view_is_converted_text(root):
    item = units_item(root, ["pending"], state="awaiting-approval")
    assert ocr.decline(root, item.meta["id"])["result"] == "declined"
    loaded = load_item(item.path)
    assert loaded.meta["state"] == "ready" and loaded.meta["ocr"]["disposition"] == "declined"
    assert transcript.view(loaded) == (item.path / "converted.md").read_text(encoding="utf-8") and not (item.path / "ocr").exists()


def test_at11_decline_unknown_item_and_state_guards(root, fake_render):
    unknown = helpers.make_item(root, state="awaiting-approval", classification="unknown", filename="u.md")
    ocr.decline(root, unknown.meta["id"])
    assert load_item(unknown.path).meta["ocr"]["disposition"] == "declined"
    ready = helpers.make_item(root, filename="r.txt")
    fails(root, "state_not_allowed", ocr.decline, root, ready.meta["id"])


def test_decline_abandons_in_progress_item_keeping_verified_units(root, fake_render):
    item = units_item(root, ["verified", "recorded", "approved", "pending"], filename="p.pdf")
    work(root, item).mkdir(parents=True)
    (work(root, item) / "u0003.png").write_bytes(b"png")
    assert ocr.decline(root, item.meta["id"])["result"] == "declined"
    loaded = load_item(item.path)
    assert loaded.meta["state"] == "ready" and loaded.meta["ocr"]["disposition"] == "declined"
    assert status(item) == {"u0001": "verified", "u0002": "recorded", "u0003": "approved", "u0004": "pending"}
    assert not work(root, item).exists() and not loaded.warnings
    assert "Verified synthetic OCR 1." in transcript.view(loaded) and "OCR 2." not in transcript.view(loaded)
    fails(root, "state_not_allowed", ocr.approve, root, item.meta["id"])


# ---------------------------------------------------------------- 5a record

def test_at20_record_copies_text_with_provenance(root):
    item = units_item(root, ["approved"])
    body = (FIXTURES / "peer-output" / "u0001.md").read_bytes()
    put(root, item, "u0001", body)
    assert ocr.record(root, item.meta["id"], "CX", "model-1", dpi=300)["recorded"] == ["u0001"]
    loaded = load_item(item.path)
    assert not loaded.warnings and loaded.meta["state"] == "ocr-in-progress"
    unit = loaded.meta["ocr"]["units"]["u0001"]
    attempt = unit["attempts"][0]
    assert unit["status"] == "recorded" and (item.path / "ocr" / "u0001.a1.md").read_bytes() == body
    assert attempt["sha256"] == hashlib.sha256(body).hexdigest() and attempt["verified"] is None and attempt["result"] is None
    recorded = attempt["recorded"]
    assert (recorded["peer"], recorded["model"], recorded["method"], recorded["version"]) == ("cx", "model-1", "ocr-vision", None)
    assert recorded["params"] == {"prompt_rev": "ocr-v1", "dpi": 300, "unit_file": "u0001.png"}


def test_at21_only_files_of_approved_units_are_taken(root):
    item = units_item(root, ["approved", "pending"])
    put(root, item, "u0002", "pending unit output")
    put(root, item, "u9999", "unknown unit")
    (root / "x.md").write_text("outside", encoding="utf-8")
    fails(root, "missing_output", ocr.record, root, item.meta["id"], "cx", "m")
    put(root, item, "u0001", "valid")
    assert ocr.record(root, item.meta["id"], "cx", "m")["recorded"] == ["u0001"]
    assert sorted(p.name for p in (item.path / "ocr").iterdir()) == ["u0001.a1.md"]
    assert status(item) == {"u0001": "recorded", "u0002": "pending"}


def test_at21_size_and_utf8_limits_are_all_or_nothing(root):
    item = units_item(root, ["approved", "approved"])
    put(root, item, "u0001", "ok")
    put(root, item, "u0002", b"a" * (1024 * 1024 + 1))
    fails(root, "invalid_request", ocr.record, root, item.meta["id"], "cx", "m")
    put(root, item, "u0002", b"\xff\xfe broken")
    fails(root, "invalid_request", ocr.record, root, item.meta["id"], "cx", "m")
    put(root, item, "u0002", b"a" * (1024 * 1024))
    assert ocr.record(root, item.meta["id"], "cx", "m")["recorded"] == ["u0001", "u0002"]


def test_record_guards(root):
    awaiting = units_item(root, ["pending"], state="awaiting-approval")
    progress = units_item(root, ["approved"], filename="p.pdf")
    put(root, progress, "u0001", "text")
    fails(root, "state_not_allowed", ocr.record, root, awaiting.meta["id"], "cx", "m")
    fails(root, "unknown_id", ocr.record, root, "0123456789abcdef", "cx", "m")
    fails(root, "invalid_request", ocr.record, root, progress.meta["id"], "1x", "m")
    fails(root, "invalid_request", ocr.record, root, progress.meta["id"], "cx", "")
    fails(root, "invalid_request", ocr.record, root, progress.meta["id"], "cx", "m", dpi=0)


def test_at27_hostile_peer_output_is_stored_as_data_only(root):
    item = units_item(root, ["approved"])
    hostile = (FIXTURES / "peer-output" / "hostile-instructions.md").read_bytes()
    put(root, item, "u0001", hostile)
    before = tree(root)
    ocr.record(root, item.meta["id"], "cx", "m")
    after = tree(root)
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    assert changed == {f"raws/{item.meta['id']}/ocr/u0001.a1.md", f"raws/{item.meta['id']}/meta.json"}
    assert after[f"raws/{item.meta['id']}/ocr/u0001.a1.md"] == hostile


# ---------------------------------------------------------------- 5b verify

def test_at22_verify_request_validation(root):
    item = units_item(root, ["recorded", "recorded", "approved"])
    item_id = item.meta["id"]
    fails(root, "same_peer", ocr.verify, root, item_id, "CX", "m", ok=["u0001"])
    fails(root, "invalid_request", ocr.verify, root, item_id, "cc", "m")
    fails(root, "invalid_request", ocr.verify, root, item_id, "cc", "m", ok=["u0001"], mismatch=["u0001"])
    fails(root, "invalid_request", ocr.verify, root, item_id, "cc", "m", ok=["u0003"])
    fails(root, "invalid_request", ocr.verify, root, item_id, "cc", "m", ok=["u0042"])
    fails(root, "invalid_request", ocr.verify, root, item_id, "1x", "m", ok=["u0001"])
    fails(root, "invalid_request", ocr.verify, root, item_id, "cc", "", ok=["u0001"])
    result = ocr.verify(root, item_id, "cc", "m2", ok=["u0001"])
    assert result["result"] == "verified"
    loaded = load_item(item.path)
    attempt = loaded.meta["ocr"]["units"]["u0001"]["attempts"][0]
    assert loaded.meta["state"] == "ocr-in-progress" and attempt["result"] == "ok"
    assert attempt["verified"]["peer"] == "cc" and attempt["verified"]["method"] == "ocr-verify"
    assert attempt["verified"]["params"] == {"prompt_rev": "verify-v1"} and attempt["verified"]["model"] == "m2"
    assert status(item) == {"u0001": "verified", "u0002": "recorded", "u0003": "approved"}


def test_verify_accumulates_and_every_unit_needs_verification(root):
    item = units_item(root, ["recorded", "recorded"])
    ocr.verify(root, item.meta["id"], "cc", "m", ok=["u0001"])
    assert load_item(item.path).meta["state"] == "ocr-in-progress"
    fails(root, "invalid_request", ocr.verify, root, item.meta["id"], "cc", "m", ok=["u0001"])  # already verified
    assert ocr.verify(root, item.meta["id"], "cc", "m", ok=["u0002"])["result"] == "finalized"


def test_at23_mismatch_reopens_unit_and_blocks_stale_rerecord(root):
    item = units_item(root, ["recorded"])
    item_id = item.meta["id"]
    first = (item.path / "ocr" / "u0001.a1.md").read_bytes()
    put(root, item, "u0001", first)
    ocr.verify(root, item_id, "cc", "m", mismatch=["u0001"])
    loaded = load_item(item.path)
    assert status(item) == {"u0001": "approved"} and loaded.meta["ocr"]["units"]["u0001"]["attempts"][0]["result"] == "mismatch"
    assert (item.path / "ocr" / "u0001.a1.md").read_bytes() == first and not (work(root, item) / "u0001.md").exists()
    put(root, item, "u0001", first)
    fails(root, "stale_output", ocr.record, root, item_id, "cx", "m")
    put(root, item, "u0001", "corrected text")
    ocr.record(root, item_id, "cx", "m")
    assert (item.path / "ocr" / "u0001.a2.md").read_bytes() == b"corrected text"
    assert ocr.verify(root, item_id, "cc", "m", ok=["u0001"])["result"] == "finalized"
    final = load_item(item.path)
    assert final.meta["state"] == "ready" and not work(root, item).exists() and not final.warnings
    assert [a["result"] for a in final.meta["ocr"]["units"]["u0001"]["attempts"]] == ["mismatch", "ok"]


def test_verify_on_ready_item_cleans_stale_scratch(root):
    item = helpers.make_item(root, filename="r.txt")
    stale = work(root, item)
    stale.mkdir(parents=True)
    (stale / "u0001.png").write_bytes(b"x")
    assert ocr.verify(root, item.meta["id"], "cc", "m")["result"] == "cleaned" and not stale.exists()
    assert ocr.verify(root, item.meta["id"], "cc", "m")["result"] == "cleaned"  # nothing left, still fine


def test_verify_on_ready_item_keeps_llm_scratch(root):
    item = helpers.make_item(root, filename="r.txt")
    scratch = work(root, item)
    (scratch / "llm").mkdir(parents=True)
    (scratch / "llm" / "summary.md").write_bytes(b"s")
    (scratch / "u0001.png").write_bytes(b"x")
    assert ocr.verify(root, item.meta["id"], "cc", "m")["result"] == "cleaned"
    assert sorted(p.relative_to(scratch).as_posix() for p in scratch.rglob("*")) == ["llm", "llm/summary.md"]


def test_ready_cleanup_keeps_llm_in_place_without_parking(root, monkeypatch):
    import os
    item = helpers.make_item(root, filename="r.txt")
    scratch = work(root, item)
    (scratch / "llm").mkdir(parents=True)
    (scratch / "llm/prompt.txt").write_bytes(b"keep in place")
    (scratch / "u0001.png").write_bytes(b"discard")
    def refuse_move(*args, **kwargs):
        pytest.fail("cleanup must never park or restore LLM scratch")
    monkeypatch.setattr(os, "replace", refuse_move)
    assert ocr.verify(root, item.meta["id"], "cc", "m")["result"] == "cleaned"
    assert tree(scratch) == {"llm/prompt.txt": b"keep in place"}
    assert sorted(p.name for p in scratch.parent.iterdir()) == [item.meta["id"]]


def test_cleanup_keeping_llm_has_safe_delete_protections(root, monkeypatch):
    import os
    import stat
    from secondbrain import fsutil
    item = helpers.make_item(root, filename="r.txt")
    scratch = work(root, item)
    (scratch / "llm").mkdir(parents=True)
    (scratch / "llm" / "summary.md").write_bytes(b"s")
    (scratch / "u0001.png").write_bytes(b"x")
    (scratch / "u0002.png").write_bytes(b"y")
    original = fsutil.is_reparse_point
    monkeypatch.setattr(fsutil, "is_reparse_point", lambda p: Path(p) == scratch / "u0002.png" or original(p))
    before = tree(root)
    with pytest.raises(SbError) as error:  # a reparse point refuses the whole cleanup, before any delete
        ocr.verify(root, item.meta["id"], "cc", "m")
    assert error.value.code == "io_error" and tree(root) == before
    monkeypatch.undo()
    os.chmod(scratch / "u0001.png", stat.S_IREAD)  # read-only scratch is still removed
    assert ocr.verify(root, item.meta["id"], "cc", "m")["result"] == "cleaned"
    assert tree(scratch) == {"llm/summary.md": b"s"}


def test_verify_state_guards(root):
    awaiting = units_item(root, ["pending"], state="awaiting-approval")
    fails(root, "state_not_allowed", ocr.verify, root, awaiting.meta["id"], "cc", "m", ok=["u0001"])
    fails(root, "unknown_id", ocr.verify, root, "0123456789abcdef", "cc", "m", ok=["u0001"])


def test_at25_fault_after_meta_write_then_verify_cleans(root, fault_after):
    item = units_item(root, ["recorded"])
    put(root, item, "u0001", "scratch text")
    (work(root, item) / "u0001.png").write_bytes(b"png")
    fault_after("meta.json")
    with pytest.raises(SbError) as error:
        ocr.verify(root, item.meta["id"], "cc", "m", ok=["u0001"])
    assert error.value.code == "io_error"
    assert load_item(item.path).meta["state"] == "ready" and work(root, item).is_dir()
    result = ocr.verify(root, item.meta["id"], "cc", "m")
    assert result["result"] == "cleaned" and not work(root, item).exists()


def test_at25_fault_after_copy_before_meta_then_record_again(root, fault_after):
    item = units_item(root, ["approved"])
    put(root, item, "u0001", "text")
    fault_after("u0001.a1.md")
    with pytest.raises(SbError) as error:
        ocr.record(root, item.meta["id"], "cx", "m")
    assert error.value.code == "io_error"
    loaded = load_item(item.path)
    assert [w["code"] for w in loaded.warnings] == ["orphan"] and not loaded.meta["ocr"]["units"]["u0001"]["attempts"]
    ocr.record(root, item.meta["id"], "cx", "m")
    loaded = load_item(item.path)
    assert not loaded.warnings and len(loaded.meta["ocr"]["units"]["u0001"]["attempts"]) == 1
    assert (item.path / "ocr" / "u0001.a1.md").read_bytes() == b"text"


def test_effective_dpi_is_persisted_listed_and_inherited_by_record(root, fake_render):
    item = units_item(root, ["pending"] * 31, state="awaiting-approval")
    item_id = item.meta["id"]
    ocr.approve(root, item_id, yes_large=True, dpi=300)
    assert "--dpi" not in (work(root, item) / "COMMANDS.txt").read_text(encoding="utf-8")  # record inherits per unit
    for n in range(1, 31):
        put(root, item, f"u{n:04}", f"text {n}")
    ocr.record(root, item_id, "cx", "m")  # no --dpi: inherits 300
    attempts = [u["attempts"][0]["recorded"]["params"]["dpi"] for u in load_item(item.path).meta["ocr"]["units"].values() if u["attempts"]]
    assert attempts == [300] * 30
    fake_render.clear()
    ocr.approve(root, item_id)  # a later batch uses the default unless --dpi is given
    assert fake_render == [("u0031", 200)]
    put(root, item, "u0031", "last")
    ocr.record(root, item_id, "cx", "m", dpi=150)  # an explicit value wins
    assert load_item(item.path).meta["ocr"]["units"]["u0031"]["attempts"][0]["recorded"]["params"]["dpi"] == 150


def test_second_approve_with_other_dpi_keeps_earlier_units_provenance(root, fake_render):
    item = units_item(root, ["pending"] * 32, state="awaiting-approval")
    item_id = item.meta["id"]
    ocr.approve(root, item_id, yes_large=True, dpi=150)  # u0001..u0030 at 150, not yet recorded
    ocr.approve(root, item_id, dpi=300)  # u0031..u0032 at 300
    for n in (1, 30, 31, 32):
        put(root, item, f"u{n:04}", f"text {n}")
    ocr.record(root, item_id, "cx", "m")
    units = load_item(item.path).meta["ocr"]["units"]
    assert {k: u["attempts"][0]["recorded"]["params"]["dpi"] for k, u in units.items() if u["attempts"]} == {
        "u0001": 150, "u0030": 150, "u0031": 300, "u0032": 300}


def test_record_without_any_approve_dpi_defaults_to_200(root):
    item = units_item(root, ["approved"])
    put(root, item, "u0001", "text")
    ocr.record(root, item.meta["id"], "cx", "m")
    assert load_item(item.path).meta["ocr"]["units"]["u0001"]["attempts"][0]["recorded"]["params"]["dpi"] == 200


def test_multi_batch_flow_ignores_already_recorded_units(root, fake_render):
    item = units_item(root, ["pending"] * 31, state="awaiting-approval")
    item_id = item.meta["id"]
    ocr.approve(root, item_id, yes_large=True)
    for n in range(1, 31):
        put(root, item, f"u{n:04}", f"text {n}")
    assert len(ocr.record(root, item_id, "cx", "m")["recorded"]) == 30
    assert (work(root, item) / "u0001.md").exists()  # leftover scratch of a recorded unit
    fake_render.clear()
    assert ocr.approve(root, item_id)["approved"] == ["u0031"]
    assert fake_render == [("u0031", 200)]  # recorded units are not re-rendered
    commands = (work(root, item) / "COMMANDS.txt").read_text(encoding="utf-8")
    asks = [l for l in commands.splitlines() if l.startswith("peerhub ask cx")]
    assert len(asks) == 1 and "Open u0031.png." in asks[0] and "u0001" not in asks[0]
    put(root, item, "u0031", "text 31")
    assert ocr.record(root, item_id, "cx", "m")["recorded"] == ["u0031"]  # leftovers of recorded units are ignored
    units = load_item(item.path).meta["ocr"]["units"]
    assert all(len(u["attempts"]) == 1 for u in units.values())


def test_transcript_view_follows_record_and_verify(root):
    item = units_item(root, ["approved", "approved"])
    item_id = item.meta["id"]
    converted = (item.path / "converted.md").read_text(encoding="utf-8")
    put(root, item, "u0001", "first text")
    put(root, item, "u0002", "second text")
    ocr.record(root, item_id, "cx", "m")
    assert transcript.view(load_item(item.path)) == converted  # recorded text is not in the view
    ocr.verify(root, item_id, "cc", "m", ok=["u0001"], mismatch=["u0002"])
    view = transcript.view(load_item(item.path))
    assert "first text" in view and "## OCR u0001 (source p1;" in view and "second text" not in view
    put(root, item, "u0002", "second text, corrected")
    ocr.record(root, item_id, "cx", "m")
    assert "corrected" not in transcript.view(load_item(item.path))  # recorded again, still unverified
    assert ocr.verify(root, item_id, "cc", "m", ok=["u0002"])["result"] == "finalized"
    final = transcript.view(load_item(item.path))
    assert final.index("first text") < final.index("second text, corrected") and "## OCR u0002 (source p2;" in final
    assert "second text\n" not in final.replace("second text, corrected", "")


def test_at17_large_boundary_is_21_units(root, fake_render):
    twenty = units_item(root, ["pending"] * 20, state="awaiting-approval", filename="twenty.pdf")
    twentyone = units_item(root, ["pending"] * 21, state="awaiting-approval", filename="twentyone.pdf")
    fails(root, "large_requires_ack", ocr.approve, root, twentyone.meta["id"])
    assert len(ocr.approve(root, twenty.meta["id"])["approved"]) == 20
    assert not load_item(twenty.path).meta["ocr"]["large_ack"]


def test_fault_in_approve_before_meta_then_retry_succeeds(root, fake_render, monkeypatch):
    item = units_item(root, ["pending", "pending"], state="awaiting-approval")
    original, armed = ocr.write_json_atomic, [True]

    def failing(path, value):
        if armed.pop() if armed else False:
            raise OSError("fault before meta.json")
        original(path, value)
    monkeypatch.setattr(ocr, "write_json_atomic", failing)
    with pytest.raises(SbError) as error:
        ocr.approve(root, item.meta["id"])
    assert error.value.code == "io_error"
    assert status(item) == {"u0001": "pending", "u0002": "pending"} and (work(root, item) / "u0001.png").is_file()
    assert ocr.approve(root, item.meta["id"])["approved"] == ["u0001", "u0002"]
    assert load_item(item.path).meta["state"] == "ocr-in-progress"


def test_at22_literal_pending_key_is_rejected(root):
    item = units_item(root, ["recorded", "pending"])
    fails(root, "invalid_request", ocr.verify, root, item.meta["id"], "cc", "m", ok=["u0002"])


def test_reparse_scratch_dir_refused_on_cleanup(root, monkeypatch):
    from secondbrain import fsutil
    item = helpers.make_item(root, filename="r.txt")
    stale = work(root, item)
    stale.mkdir(parents=True)
    original = fsutil.is_reparse_point
    monkeypatch.setattr(fsutil, "is_reparse_point", lambda p: Path(p) == stale or original(p))
    with pytest.raises(SbError) as error:
        ocr.verify(root, item.meta["id"], "cc", "m")
    assert error.value.code == "io_error" and stale.is_dir()
