"""DESIGN r9 §3: table cross-product, real report shape, and staged adapter."""
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import unicodedata

import pytest

from secondbrain import convert
from secondbrain.errors import SbError
from secondbrain.fsutil import write_json_atomic
from secondbrain.ledger import load_stage, validate_meta
from helpers import DATE

FIXTURES = Path(__file__).parent / "fixtures"
REPORTS = FIXTURES / "reports"


def raw(name="row-08.json"):
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def stage_file(root, source="text/plain.txt"):
    directory = root / "raws/.staging/tmp-1"
    path = FIXTURES / source
    (directory / "src").mkdir(parents=True)
    shutil.copyfile(path, directory / "src" / path.name)
    stage = {"relpath": path.name, "filename": path.name, "charset": "cp949" if path.name == "korean-cp949.txt" else None,
             "claimed_at": DATE}
    write_json_atomic(directory / "stage.json", stage)
    return directory, stage


def install_converter(monkeypatch, directory, *, text="native text", error=None, media=False):
    calls = []
    class Converter:
        def convert(self, source, **kwargs):
            pending = load_stage(directory)["conversion"]
            assert pending["sha256"] is None
            assert pending["activity"]["params"]["charset"] == kwargs["charset"]
            assert Path(source).is_absolute() and Path(source).is_file()
            calls.append((source, kwargs))
            if error is not None:
                raise error
            if media:
                target = Path(kwargs["extract_media"])
                target.mkdir(exist_ok=True)
                (target / "b.png").write_bytes(b"original b")
                (target / "a.png").write_bytes(b"original a")
            return SimpleNamespace(text_content=text)
    monkeypatch.setattr(convert, "_make_converter", lambda: Converter())
    return calls


def test_gate_1b_probe_classifications_are_labeled_r8():
    probes = sorted(REPORTS.glob("*.probe.json"))
    assert len(probes) == 36
    for path in probes:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["design_revision"] == "r8", path
        assert len(data["design_row_class_state_reason"]) == 4


def test_at06_sample_adapter_is_field_exact_and_pure():
    report = raw("sample-ocr-report-png.json")
    before = deepcopy(report)
    assert convert.adapt_report(report, ".png") == {
        "decision": "ocr_recommended", "coverage": {"state": "complete", "pages_total": None, "pages_inspected": 0},
        "scope": "inspected", "image_occurrences": 0,
        "candidates": [{"id": "image", "kind": "image", "page": None, "priority": "high"}], "issues": []}
    assert report == before


@pytest.mark.parametrize("name", ["missing-coverage.json", "wrong-types.json", "dup-ids.json", "bad-page-id.json", "row-06.json"])
def test_at06_committed_malformed_reports(name):
    with pytest.raises(SbError) as error:
        convert.adapt_report(raw(name), ".pdf")
    assert (error.value.code, error.value.exit) == ("report_invalid", 1)


@pytest.mark.parametrize("change", ["schema-bool", "decision", "coverage-state", "missing-count", "bool-count", "negative-count", "over-count", "scope", "image-count", "candidate-kind", "candidate-priority", "candidate-page", "candidate-bound", "candidates-type", "issues-type", "issue-code"])
def test_at06_bad_types_and_missing_fields(change):
    report = raw()
    if change == "schema-bool": report["schema_version"] = True
    if change == "decision": report["decision"] = "maybe"
    if change == "coverage-state": report["coverage"]["state"] = "maybe"
    if change == "missing-count": report["coverage"].pop("pages_total")
    if change == "bool-count": report["coverage"]["pages_total"] = True
    if change == "negative-count": report["coverage"]["pages_total"] = -1
    if change == "over-count": report["coverage"]["pages_inspected"] = 2
    if change == "scope": report["summary"]["scope"] = None
    if change == "image-count": report["summary"]["image_occurrences"] = True
    if change == "candidate-kind": report["candidates"][0]["kind"] = None
    if change == "candidate-priority": report["candidates"][0]["priority"] = 1
    if change == "candidate-page": report["candidates"][0]["page"] = True
    if change == "candidate-bound": report["candidates"][0]["id"] = "p2"
    if change == "candidates-type": report["candidates"] = {}
    if change == "issues-type": report["issues"] = {}
    if change == "issue-code": report["issues"] = [{"code": 1}]
    with pytest.raises(SbError) as error:
        convert.adapt_report(report, ".pdf")
    assert error.value.code == "report_invalid"


def test_at06_issues_capped_and_extra_tool_evidence_ignored():
    report = raw()
    report["issues"] = [{"code": f"issue-{n}", "detail": "tool evidence"} for n in range(25)]
    assert convert.adapt_report(report, ".pdf")["issues"] == [f"issue-{n}" for n in range(20)]
    report["issues"][-1]["code"] = None
    with pytest.raises(SbError):
        convert.adapt_report(report, ".pdf")


@pytest.mark.parametrize("path", sorted(p for p in REPORTS.glob("*.probe.json")))
def test_at06_every_characterized_real_report(path):
    probe = json.loads(path.read_text(encoding="utf-8"))
    report = json.loads((FIXTURES / probe["report"]).read_text(encoding="utf-8"))
    triage = convert.adapt_report(report, Path(probe["fixture"]).suffix)
    assert triage["decision"] == report["decision"]
    assert triage["coverage"]["state"] == report["coverage"]["state"]


# AT-05: independently list the mutually exclusive row predicates. The classifier
# must match exactly one, including impossible downstream values after a shortcut.
TABLE_CASES = list(product((".pdf", ".docx", ".md", ".txt", ".png", ".mp3"),
                          (None, "unsupported", "dependency", "conversion", "other"),
                          ("ocr_recommended", "review", "no_candidates", "unknown"),
                          ("complete", "partial", "none", "not_applicable"), (False, True), (False, True), (False, True)))


@pytest.mark.parametrize("ext,exception,decision,coverage,candidates,units,native", TABLE_CASES)
def test_at05_classification_cross_product(ext, exception, decision, coverage, candidates, units, native):
    from markitdown import UnsupportedFormatException, MissingDependencyException, FileConversionException
    errors = {None: None, "unsupported": UnsupportedFormatException("no converter"),
              "dependency": MissingDependencyException("dependency"), "conversion": FileConversionException("bad conversion"), "other": ValueError("other")}
    triage = {"decision": decision, "coverage": {"state": coverage, "pages_total": 1, "pages_inspected": 1},
              "scope": "inspected", "image_occurrences": 1, "candidates": [{"id": "p1", "kind": "page", "page": 1, "priority": "high"}] if candidates else [], "issues": ["inspection_issue"]}
    if ext == ".txt":
        triage = None  # r9: the entire plain-text set never carries a report.
    raster, denied = ext == ".png", ext == ".mp3"
    downstream = not raster and not denied and exception is None
    reported = downstream and ext != ".txt"
    recommended = decision in {"ocr_recommended", "review"}
    matches = {
        2: denied, 3: not denied and raster,
        4: not denied and not raster and exception in {"unsupported", "dependency"},
        5: not denied and not raster and exception in {"conversion", "other"},
        7: reported and recommended and not candidates,
        8: reported and recommended and candidates and units and not native,
        9: reported and recommended and candidates and units and native,
        10: reported and recommended and candidates and not units,
        11: downstream and (ext == ".txt" or decision == "no_candidates" and coverage in {"complete", "not_applicable"}),
        12: reported and (decision == "unknown" or decision == "no_candidates" and coverage in {"partial", "none"}),
    }
    row, = [number for number, matched in matches.items() if matched]
    expected = {2: ("unsupported", "unsupported", "extension_not_allowed"), 3: ("ocr-required", "awaiting-approval", "raster"),
                4: ("unsupported", "unsupported", "no_converter" if exception == "unsupported" else "missing_dependency"),
                5: (None, "failed", type(errors[exception]).__name__), 7: (None, "failed", "no_candidate_ids"),
                8: ("ocr-required", "awaiting-approval", None), 9: ("mixed", "awaiting-approval", None),
                10: ("unknown", "awaiting-approval", "no_units"),
                11: ("text-only", "ready", None if native else "empty_document"), 12: ("unknown", "awaiting-approval", "inspection_issue")}[row]
    result = convert.classify(ext, conversion_error=errors[exception], triage=triage, native=native,
                              units={"u0001": {}} if units else {}, date=DATE)
    assert (result["class"], result["state"], result["reason"]) == expected
    assert (result["error"] is not None) == (result["state"] == "failed")
    if row == 5:
        assert result["error"]["code"] == "conversion_failed"


@pytest.mark.parametrize("options, reason", [({"size": 0}, "empty_file"), ({"path": "x" * 241}, "path_too_long"),
                                            ({"report_error": SbError("report_failed", 1)}, "report_failed"),
                                            ({"report_error": SbError("report_invalid", 1)}, "report_invalid")])
def test_at05_rows_one_and_six(options, reason):
    result = convert.classify(".pdf", date=DATE, **options)
    assert (result["class"], result["state"], result["reason"]) == (None, "failed", reason)
    assert result["error"]["date"] == DATE


def test_at18_numeric_pdf_keys_and_container_asset_order():
    report = raw()
    report["coverage"].update(pages_total=10, pages_inspected=10)
    report["candidates"] = [{"id": f"p{n}", "kind": "page", "page": n, "priority": "high"} for n in (10, 2, 1)]
    triage = convert.adapt_report(report, ".pdf")
    units = convert.enumerate_units(".pdf", triage, [])
    assert [u["source"] for u in units.values()] == ["p1", "p2", "p10"]
    assert list(units) == ["u0001", "u0002", "u0003"]
    assets = [{"file": "media/z.png", "sha256": "0" * 64}, {"file": "media/a.png", "sha256": "1" * 64}]
    units = convert.enumerate_units(".docx", triage, assets)
    assert [u["source"] for u in units.values()] == ["media/a.png", "media/z.png"]
    assert all(u["kind"] == "asset" and u["status"] == "pending" and u["attempts"] == [] for u in units.values())


def test_at18_no_unapproved_units_and_overflow():
    triage = convert.adapt_report(raw("row-11.json"), ".pdf")
    assert convert.enumerate_units(".pdf", triage, []) == {}
    assert convert.enumerate_units(".md", convert.adapt_report(raw(), ".md"), []) == {}
    media = [{"file": f"media/{n:05}.png"} for n in range(10000)]
    assert list(convert.enumerate_units(".docx", convert.adapt_report(raw(), ".docx"), media[:9999]))[-1] == "u9999"
    with pytest.raises(SbError) as error:
        convert.enumerate_units(".docx", convert.adapt_report(raw(), ".docx"), media)
    assert error.value.code == "too_many_units"


@pytest.mark.parametrize("ext", [".txt", ".csv", ".log", ".json", ".xml"])
def test_at08_whole_plain_text_set_skips_triage(root, monkeypatch, ext):
    """AT-08 r9 wording applies to the whole plain-text set, not just .txt."""
    directory, stage = stage_file(root)
    (directory / "src/plain.txt").rename(directory / ("src/plain" + ext))
    stage.update(filename="plain" + ext, relpath="plain" + ext)
    write_json_atomic(directory / "stage.json", stage)
    calls = install_converter(monkeypatch, directory, text="한글\r\n123\n")
    monkeypatch.setattr(convert, "run_report", lambda *a: pytest.fail("plain text must skip triage"))
    result = convert.classify_item(directory, stage)
    assert (result["class"], result["state"], result["triage"]) == ("text-only", "ready", None)
    assert len(calls) == 1 and calls[0][1] == {"charset": None}
    assert (directory / "converted.md").read_bytes() == "한글\r\n123\n".encode("utf-8")


@pytest.mark.parametrize("source", ["ocr/photo.png", "unsupported/clip.mp3", "unsupported/data.xyz", "unsupported/legacy.doc", "failed/zero-bytes.txt"])
def test_at12_shortcuts_never_reach_converter_or_report(root, monkeypatch, source):
    directory, stage = stage_file(root, source)
    monkeypatch.setattr(convert, "_make_converter", lambda: pytest.fail("forbidden converter call"))
    monkeypatch.setattr(convert, "run_report", lambda *a: pytest.fail("forbidden report call"))
    result = convert.classify_item(directory, stage)
    expected = "ocr-required" if source.startswith("ocr/") else None if source.startswith("failed/") else "unsupported"
    assert result["class"] == expected
    assert result["conversion"] is result["triage"] is result["has_native_text"] is None
    assert bool(result["ocr"]["units"]) == source.startswith("ocr/")


def test_container_ledger_first_media_and_no_reconversion(root, monkeypatch):
    directory, stage = stage_file(root, "mixed/slides.pptx")
    calls = install_converter(monkeypatch, directory, media=True)
    monkeypatch.setattr(convert, "run_report", lambda *a: convert.adapt_report(raw(), ".pptx"))
    first = convert.classify_item(directory, stage)
    (directory / "media/orphan.png").write_bytes(b"ignored")
    second = convert.classify_item(directory, load_stage(directory))
    assert first == second and len(calls) == 1
    assert calls[0][1]["extract_media"] == str((directory / "media").resolve())
    assert [m["file"] for m in first["conversion"]["media"]] == ["media/a.png", "media/b.png"]
    assert len(second["ocr"]["units"]) == 2


def test_completed_output_reconciled_after_crash(root, monkeypatch, fault_after):
    directory, stage = stage_file(root)
    calls = install_converter(monkeypatch, directory)
    fault_after("converted.md")
    with pytest.raises(OSError, match="fault"):
        convert.classify_item(directory, stage)
    assert load_stage(directory)["conversion"]["sha256"] is None
    result = convert.classify_item(directory, load_stage(directory))
    assert result["class"] == "text-only" and len(calls) == 1


@pytest.mark.parametrize("code", ["report_failed", "report_invalid"])
def test_report_failure_preserves_conversion_for_retry(root, monkeypatch, code):
    directory, stage = stage_file(root, "mixed/slides.pptx")
    calls = install_converter(monkeypatch, directory, media=True)
    def fail(*args):
        raise SbError(code, 1, "simulated report failure")
    monkeypatch.setattr(convert, "run_report", fail)
    failed = convert.classify_item(directory, stage)
    before = (directory / "converted.md").read_bytes()
    assert failed["class"] is None and failed["reason"] == code and failed["triage"] is None
    monkeypatch.setattr(convert, "run_report", lambda *a: convert.adapt_report(raw(), ".pptx"))
    result = convert.classify_item(directory, load_stage(directory))
    assert result["class"] == "mixed" and len(calls) == 1
    assert (directory / "converted.md").read_bytes() == before


@pytest.mark.parametrize("mode", ["missing", "changed", "unledgered"])
def test_referenced_corruption_and_unledgered_output_are_not_reconverted(root, monkeypatch, mode):
    directory, stage = stage_file(root)
    calls = install_converter(monkeypatch, directory)
    convert.classify_item(directory, stage)
    if mode == "missing": (directory / "converted.md").unlink()
    if mode == "changed": (directory / "converted.md").write_bytes(b"changed")
    if mode == "unledgered":
        stage.pop("conversion")
        write_json_atomic(directory / "stage.json", stage)
    with pytest.raises(SbError) as error:
        convert.classify_item(directory, load_stage(directory))
    assert error.value.code == "corrupt_meta" and len(calls) == 1


@pytest.mark.parametrize("payload, exit_code, expected", [(b"{broken", 0, "report_invalid"),
    (b'{"schema_version":1,"schema_version":1}', 0, "report_invalid"), (b"\xff", 0, "report_invalid"),
    (b"{}", 1, "report_failed"), (None, 0, "report_failed")])
def test_at06_report_runner_failures(root, monkeypatch, payload, exit_code, expected):
    directory, stage = stage_file(root, "ocr/scan.pdf")
    output = directory / "report.json"
    def report(args, **kwargs):
        assert args[0] == "markitdown-gc" and args[2:4] == ["--ocr-report", "-o"]
        if payload is not None: output.write_bytes(payload)
        return SimpleNamespace(returncode=exit_code, stderr="simulated", stdout="")
    monkeypatch.setattr(convert.subprocess, "run", report)
    with pytest.raises(SbError) as error:
        convert.run_report(directory / "src" / stage["filename"], output)
    assert error.value.code == expected and not output.exists()


@pytest.mark.parametrize("source", ["http://x", "file:///tmp/input.txt", "data:text/plain,hello"])
def test_local_source_contract_rejects_uris_before_tool_calls(root, monkeypatch, source):
    monkeypatch.setattr(convert.subprocess, "run", lambda *a, **kw: pytest.fail("URI report call"))
    with pytest.raises(SbError):
        convert.run_report(source, root / "report.json")


REAL_CASES = sorted(p for group in ("text", "ocr", "mixed", "unknown", "unsupported", "characterize", "failed")
                    for p in (FIXTURES / group).iterdir() if p.is_file())


@pytest.mark.parametrize("source", REAL_CASES, ids=lambda p: p.parent.name + "/" + p.name)
def test_real_tool_classification_matches_characterization(root, source, subprocess_spy):
    directory, stage = stage_file(root, source.relative_to(FIXTURES).as_posix())
    result = convert.classify_item(directory, stage)
    probe = raw(source.parent.name + "--" + source.name + ".probe.json")
    _, cls, state, reason = probe["design_row_class_state_reason"]
    if source.suffix.lower() in {".txt", ".csv", ".log", ".json", ".xml"} and source.stat().st_size:
        cls, state, reason = "text-only", "ready", None
    assert (result["class"], result["state"], result["reason"]) == (cls, state, reason)
    assert len(result["ocr"]["units"]) == len(probe["units"])
    should_report = source.suffix.lower() not in convert.PLAIN_TEXT_EXTENSIONS and result["conversion"] is not None
    assert len(subprocess_spy) == int(should_report)
    assert not (directory / "report.json").exists()
    if result["conversion"]:
        assert sorted(m["sha256"] for m in result["conversion"]["media"]) == sorted(m["sha256"] for m in probe["media"])
        converted = (directory / "converted.md").read_bytes().decode("utf-8")
        expected_text = (FIXTURES / probe["conversion"]["artifact"]).read_bytes().decode("utf-8")
        # Only image-link destinations depend on the staging directory.
        for medium in probe["media"]:
            import re
            converted = re.sub(r"!\[([^\]]*)\]\([^)]*" + re.escape(medium["file"]) + r"\)", r"![\1](MEDIA)", converted)
            expected_text = re.sub(r"!\[([^\]]*)\]\([^)]*" + re.escape(medium["file"]) + r"\)", r"![\1](MEDIA)", expected_text)
        assert converted == expected_text
    # Construct a committed ledger projection to keep the adapter compatible
    # with the already-reviewed foundation schema, without running ingest.
    data = (directory / "src" / stage["filename"]).read_bytes()
    identity = sha256(data).hexdigest()
    meta = {"schema": 1, "id": identity[:16], "sha256": identity, "size": len(data), "ext": source.suffix.lower(),
            "filename": source.name, "filename_nfc": unicodedata.normalize("NFC", source.name),
            "aliases": [], "ingested_at": DATE, "llm": None, **result}
    committed = directory.with_name(identity[:16])
    directory.rename(committed)
    assert validate_meta(meta, committed) == []


@pytest.mark.parametrize("ext,body", [(".txt", "Synthetic 123\n"), (".csv", "item,amount\nsynthetic,42\n"),
                                     (".log", "Synthetic log 123\n"), (".json", '{"synthetic":123}\n'),
                                     (".xml", "<doc>Synthetic 123</doc>\n")])
def test_at08_real_whole_plain_text_set(root, ext, body, subprocess_spy):
    directory, stage = stage_file(root)
    source = directory / ("src/plain" + ext)
    (directory / "src/plain.txt").rename(source)
    source.write_bytes(body.encode("utf-8"))
    stage.update(filename=source.name, relpath=source.name)
    if ext == ".log":
        # Python 3.15/Windows may have no text MIME mapping for .log; an explicit
        # charset is an approved API option and makes that conversion eligible.
        stage["charset"] = "utf-8"
    write_json_atomic(directory / "stage.json", stage)
    result = convert.classify_item(directory, stage)
    assert (result["class"], result["state"], result["triage"]) == ("text-only", "ready", None)
    assert result["has_native_text"] is True and subprocess_spy == []


def test_backend_without_completed_output_can_be_retried(root, monkeypatch):
    directory, stage = stage_file(root)
    first_calls = install_converter(monkeypatch, directory, error=ValueError("backend failed"))
    result = convert.classify_item(directory, stage)
    assert (result["reason"], result["error"]["code"]) == ("ValueError", "conversion_failed")
    assert result["conversion"] is None and not (directory / "converted.md").exists()
    second_calls = install_converter(monkeypatch, directory)
    result = convert.classify_item(directory, load_stage(directory))
    assert result["class"] == "text-only" and len(first_calls) == len(second_calls) == 1


def test_corrupt_cached_native_text_is_not_reused(root, monkeypatch):
    directory, stage = stage_file(root)
    calls = install_converter(monkeypatch, directory)
    convert.classify_item(directory, stage)
    stage["has_native_text"] = "wrong type"
    write_json_atomic(directory / "stage.json", stage)
    with pytest.raises(SbError) as error:
        convert.classify_item(directory, load_stage(directory))
    assert error.value.code == "corrupt_meta" and len(calls) == 1


def test_stage_root_is_checked_before_resolving_a_reparse_alias(root, monkeypatch):
    import secondbrain.fsutil as fsutil
    directory, stage = stage_file(root)
    calls = install_converter(monkeypatch, directory)
    alias = root / "stage-link"
    resolve, reparse = Path.resolve, fsutil.is_reparse_point
    monkeypatch.setattr(Path, "resolve", lambda p, *a, **kw: directory if p == alias else resolve(p, *a, **kw))
    monkeypatch.setattr(fsutil, "is_reparse_point", lambda p: Path(p) == alias or reparse(p))
    with pytest.raises(SbError):
        convert.classify_item(alias, stage)
    assert calls == []


def test_at08_log_without_charset_keeps_typed_tool_outcome(root, subprocess_spy):
    directory, stage = stage_file(root)
    source = directory / "src/plain.log"
    (directory / "src/plain.txt").rename(source)
    source.write_bytes(b"Synthetic log 123\n")
    stage.update(filename=source.name, relpath=source.name)
    write_json_atomic(directory / "stage.json", stage)
    result = convert.classify_item(directory, stage)
    # The host MIME registry can identify .log as text, or leave it unsupported.
    assert (result["class"], result["state"]) in {("text-only", "ready"), ("unsupported", "unsupported")}
    assert result["reason"] == ("no_converter" if result["class"] == "unsupported" else None)
    assert result["triage"] is None and subprocess_spy == []


def test_explicit_cp949_is_honored_when_autodetection_is_wrong(root):
    directory, stage = stage_file(root)
    (directory / "src/plain.txt").write_bytes("가".encode("cp949"))
    stage["charset"] = "cp949"
    write_json_atomic(directory / "stage.json", stage)
    result = convert.classify_item(directory, stage)
    assert result["conversion"]["activity"]["params"]["charset"] == "cp949"
    assert (directory / "converted.md").read_bytes() == "가".encode("utf-8")
