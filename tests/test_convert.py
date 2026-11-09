"""DESIGN r9 §3: table cross-product, real report shape, and staged adapter."""
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import re
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


def test_unit_overflow_is_reported_at_the_enumeration_boundary(root, monkeypatch):
    directory, stage = stage_file(root, "ocr/scan.pdf")
    install_converter(monkeypatch, directory)
    monkeypatch.setattr(convert, "run_report", lambda *args: convert.adapt_report(raw(), ".pdf"))
    def overflow(*args):
        raise SbError("too_many_units", 1)
    monkeypatch.setattr(convert, "enumerate_units", overflow)
    outcome = convert.classify_item(directory, stage)
    assert outcome["class"] is None and outcome["state"] == "failed"
    assert outcome["error"]["code"] == outcome["reason"] == "too_many_units"


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
    monkeypatch.setattr(convert, "_make_converter", lambda ext: Converter())
    return calls


def test_gate_1b_probes_have_explicit_r9_plain_text_expectations():
    probes = sorted(REPORTS.glob("*.probe.json"))
    assert len(probes) == 36
    for path in probes:
        data = json.loads(path.read_text(encoding="utf-8"))
        expected = data.get("design_row_class_state_reason_r9", data["design_row_class_state_reason"])
        assert len(expected) == 4
        if data["fixture"] == "text/korean-cp949.txt" or data["fixture"].startswith("llm/") and data["fixture"].endswith(".json"):
            assert data["design_row_class_state_reason_r9"] == [11, "text-only", "ready", None]


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


# One explicit expectation per table row, plus meaningful boundaries/shortcuts.
# Detailed reasons and boundary behavior stay in these representative cases.
ROW_CASES = [
    pytest.param(".pdf", {"size": 0}, (None, "failed", "empty_file"), id="row-01-empty"),
    pytest.param(".mp3", {}, ("unsupported", "unsupported", "extension_not_allowed"), id="row-02-audio"),
    pytest.param(".png", {}, ("ocr-required", "awaiting-approval", "raster"), id="row-03-raster"),
    pytest.param(".pdf", {"conversion_error": "unsupported"}, ("unsupported", "unsupported", "no_converter"), id="row-04-no-converter"),
    pytest.param(".pdf", {"conversion_error": "dependency"}, ("unsupported", "unsupported", "missing_dependency"), id="row-04-dependency"),
    pytest.param(".pdf", {"conversion_error": "conversion"}, (None, "failed", "FileConversionException"), id="row-05-conversion"),
    pytest.param(".pdf", {"conversion_error": "other"}, (None, "failed", "ValueError"), id="row-05-other"),
    pytest.param(".pdf", {"step_error": "report_failed"}, (None, "failed", "report_failed"), id="row-06-exit"),
    pytest.param(".pdf", {"step_error": "report_invalid"}, (None, "failed", "report_invalid"), id="row-06-invalid"),
    pytest.param(".pdf", {"report": "row-07.json"}, (None, "failed", "no_candidate_ids"), id="row-07-no-candidates"),
    pytest.param(".pdf", {"report": "row-08.json", "unit_count": 1, "native": False}, ("ocr-required", "awaiting-approval", None), id="row-08-scan"),
    pytest.param(".pdf", {"report": "row-09.json", "unit_count": 1, "native": True}, ("mixed", "awaiting-approval", None), id="row-09-mixed"),
    pytest.param(".docx", {"report": "row-10.json", "native": True}, ("unknown", "awaiting-approval", "no_units"), id="row-10-no-assets"),
    pytest.param(".pdf", {"report": "row-11.json", "native": True}, ("text-only", "ready", None), id="row-11-text"),
    pytest.param(".pdf", {"report": "row-11.json", "native": False}, ("text-only", "ready", "empty_document"), id="row-11-empty"),
    pytest.param(".md", {"report": "row-12.json", "native": True}, ("unknown", "awaiting-approval", "media_not_inspected"), id="row-12-unknown"),
    pytest.param(".txt", {"native": True}, ("text-only", "ready", None), id="plain-text-no-report"),
    pytest.param(".txt", {"native": False}, ("text-only", "ready", "empty_document"), id="plain-text-empty-conversion"),
    pytest.param(".mp3", {"size": 0}, (None, "failed", "empty_file"), id="empty-before-extension"),
    pytest.param(".png", {"conversion_error": "other"}, ("ocr-required", "awaiting-approval", "raster"), id="raster-before-converter"),
    pytest.param(".mp3", {"conversion_error": "other"}, ("unsupported", "unsupported", "extension_not_allowed"), id="extension-before-converter"),
    pytest.param(".pdf", {"conversion_error": "conversion", "step_error": "report_failed"}, (None, "failed", "FileConversionException"), id="conversion-before-report"),
]


def test_at05_full_domain_is_mece():
    """One lightweight MECE check; the §3 predicates and outputs are table data.

    AT-05's domain fixes successful prechecks and a produced report: rows 1/6
    remain in ROW_CASES. Plain-text inputs never carry a report. Downstream
    axes still vary after shortcuts, to check that earlier rows exclude them.
    """
    from markitdown import UnsupportedFormatException, MissingDependencyException, FileConversionException
    errors = {None: None, "unsupported": UnsupportedFormatException("unsupported"),
              "dependency": MissingDependencyException("dependency"),
              "conversion": FileConversionException("conversion"), "other": ValueError("other")}
    convertible = {"ext": (".pdf", ".docx", ".md", ".txt")}
    reported = {"ext": (".pdf", ".docx", ".md"), "exception": (None,)}
    recommended = {**reported, "decision": ("ocr_recommended", "review")}
    # Each row contains OR clauses; fields within a clause are AND conditions.
    # Wildcard fields are absent. Expected outputs are declared, never computed.
    rows = [
        (2, [{"ext": (".mp3",)}], ("unsupported", "unsupported")),
        (3, [{"ext": (".png",)}], ("ocr-required", "awaiting-approval")),
        (4, [{**convertible, "exception": ("unsupported", "dependency")}], ("unsupported", "unsupported")),
        (5, [{**convertible, "exception": ("conversion", "other")}], (None, "failed")),
        (7, [{**recommended, "candidates": (False,)}], (None, "failed")),
        (8, [{**recommended, "candidates": (True,), "units": (True,), "native": (False,)}], ("ocr-required", "awaiting-approval")),
        (9, [{**recommended, "candidates": (True,), "units": (True,), "native": (True,)}], ("mixed", "awaiting-approval")),
        (10, [{**recommended, "candidates": (True,), "units": (False,)}], ("unknown", "awaiting-approval")),
        (11, [{"ext": (".txt",), "exception": (None,)},
              {**reported, "decision": ("no_candidates",), "coverage": ("complete", "not_applicable")}], ("text-only", "ready")),
        (12, [{**reported, "decision": ("unknown",)},
              {**reported, "decision": ("no_candidates",), "coverage": ("partial", "none")}], ("unknown", "awaiting-approval")),
    ]
    names = ("ext", "exception", "decision", "coverage", "candidates", "units", "native")
    domain = product((".pdf", ".docx", ".md", ".txt", ".png", ".mp3"), errors,
                     ("ocr_recommended", "review", "no_candidates", "unknown"),
                     ("complete", "partial", "none", "not_applicable"), (False, True), (False, True), (False, True))
    checked = 0
    for values in domain:
        case = dict(zip(names, values))
        matches = [(number, declared) for number, clauses, declared in rows
                   if any(all(case[name] in accepted for name, accepted in clause.items()) for clause in clauses)]
        assert len(matches) == 1, (case, matches)
        triage = None if case["ext"] == ".txt" else {
            "decision": case["decision"], "coverage": {"state": case["coverage"], "pages_total": 1, "pages_inspected": 1},
            "scope": "inspected", "image_occurrences": 1, "issues": [],
            "candidates": [{"id": "p1", "kind": "page", "page": 1, "priority": "high"}] if case["candidates"] else []}
        result = convert.classify(case["ext"], conversion_error=errors[case["exception"]], triage=triage,
                                  native=case["native"], units={"u0001": {}} if case["units"] else {}, date=DATE)
        assert (result["class"], result["state"]) == matches[0][1], (case, matches[0], result)
        checked += 1
    assert checked == 3840


@pytest.mark.parametrize("ext,options,expected", ROW_CASES)
def test_at05_table_rows_and_shortcuts(ext, options, expected):
    from markitdown import UnsupportedFormatException, MissingDependencyException, FileConversionException
    errors = {"unsupported": UnsupportedFormatException("no converter"),
              "dependency": MissingDependencyException("dependency"), "conversion": FileConversionException("bad conversion"), "other": ValueError("other")}
    options = dict(options)
    if "report" in options:
        options["triage"] = convert.adapt_report(raw(options.pop("report")), ext)
    if "conversion_error" in options:
        options["conversion_error"] = errors[options["conversion_error"]]
    if "step_error" in options:
        options["step_error"] = SbError(options["step_error"], 1)
    options["units"] = {f"u{n:04}": {} for n in range(1, options.pop("unit_count", 0) + 1)}
    result = convert.classify(ext, date=DATE, **options)
    assert (result["class"], result["state"], result["reason"]) == expected
    assert (result["error"] is not None) == (result["state"] == "failed")
    if result["error"] is not None:
        assert result["error"]["date"] == DATE
    if expected[2] in {"FileConversionException", "ValueError"}:
        assert result["error"]["code"] == "conversion_failed"


@pytest.mark.parametrize("coverage,expected", [
    ("complete", ("text-only", "ready", None)), ("not_applicable", ("text-only", "ready", None)),
    ("partial", ("unknown", "awaiting-approval", "inspection_issue")),
    ("none", ("unknown", "awaiting-approval", "inspection_issue")),
])
def test_at05_no_candidates_coverage_boundaries(coverage, expected):
    triage = convert.adapt_report(raw("row-11.json"), ".pdf")
    triage["coverage"]["state"] = coverage
    triage["issues"] = ["inspection_issue"]
    result = convert.classify(".pdf", triage=triage, native=True)
    assert (result["class"], result["state"], result["reason"]) == expected


@pytest.mark.parametrize("native,expected", [(False, "ocr-required"), (True, "mixed")])
def test_at05_review_keeps_candidates_under_partial_coverage(native, expected):
    triage = convert.adapt_report(raw(), ".pdf")
    triage["decision"] = "review"
    triage["coverage"].update(state="partial", pages_total=2, pages_inspected=1)
    before = deepcopy(triage)
    result = convert.classify(".pdf", triage=triage, native=native, units={"u0001": {}})
    assert (result["class"], result["state"], result["reason"]) == (expected, "awaiting-approval", None)
    assert triage == before


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
    assert len(calls) == 1 and calls[0][1]["charset"] is None
    hint = calls[0][1]["stream_info"]
    assert (hint.extension, hint.mimetype, hint.charset) == (ext, "text/plain", None)
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
    _, cls, state, reason = probe.get("design_row_class_state_reason_r9", probe["design_row_class_state_reason"])
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
def test_at08_real_whole_plain_text_set(root, ext, body, subprocess_spy, monkeypatch):
    import mimetypes
    # Reproduce a host with no useful extension-to-text MIME mapping.
    monkeypatch.setattr(mimetypes, "guess_type", lambda *a, **kw: ("application/octet-stream", None))
    directory, stage = stage_file(root)
    source = directory / ("src/plain" + ext)
    (directory / "src/plain.txt").rename(source)
    source.write_bytes(body.encode("utf-8"))
    stage.update(filename=source.name, relpath=source.name)
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


def test_at08_log_without_charset_is_text_only(root, subprocess_spy):
    directory, stage = stage_file(root)
    source = directory / "src/plain.log"
    (directory / "src/plain.txt").rename(source)
    source.write_bytes(b"Synthetic log 123\n")
    stage.update(filename=source.name, relpath=source.name)
    write_json_atomic(directory / "stage.json", stage)
    result = convert.classify_item(directory, stage)
    assert (result["class"], result["state"], result["reason"]) == ("text-only", "ready", None)
    assert result["triage"] is None and subprocess_spy == []


def test_explicit_cp949_is_honored_when_autodetection_is_wrong(root):
    directory, stage = stage_file(root)
    (directory / "src/plain.txt").write_bytes("가".encode("cp949"))
    stage["charset"] = "cp949"
    write_json_atomic(directory / "stage.json", stage)
    result = convert.classify_item(directory, stage)
    assert result["conversion"]["activity"]["params"]["charset"] == "cp949"
    assert (directory / "converted.md").read_bytes() == "가".encode("utf-8")


def test_fixture_checkout_preserves_binary_exact_bytes():
    attributes = (Path(__file__).resolve().parents[1] / ".gitattributes").read_text(encoding="utf-8")
    assert "tests/fixtures/** -text" in attributes.splitlines()
    for path in REPORTS.glob("*.probe.json"):
        probe = json.loads(path.read_text(encoding="utf-8"))
        assert sha256((FIXTURES / probe["fixture"]).read_bytes()).hexdigest() == probe["sha256"]
        if "artifact" in probe["conversion"]:
            expected = probe["conversion"]
            assert sha256((FIXTURES / expected["artifact"]).read_bytes()).hexdigest() == expected["sha256"]


@pytest.mark.parametrize("name,exit_code", [("invalid.json", 0), ("exit1.txt", 1)])
def test_at06_actual_error_fixture_through_runner(root, monkeypatch, name, exit_code):
    directory, stage = stage_file(root, "ocr/scan.pdf")
    output = directory / "report.json"
    fixture_bytes = (REPORTS / name).read_bytes()
    def report(args, **kwargs):
        if not exit_code:
            output.write_bytes(fixture_bytes)
        return SimpleNamespace(returncode=exit_code, stdout="", stderr=fixture_bytes.decode("utf-8"))
    monkeypatch.setattr(convert.subprocess, "run", report)
    with pytest.raises(SbError) as error:
        convert.run_report(directory / "src" / stage["filename"], output)
    assert error.value.code == ("report_failed" if exit_code else "report_invalid")
    assert not output.exists()


def test_report_output_reparse_is_refused_before_process_or_delete(root, monkeypatch):
    import secondbrain.fsutil as fsutil
    directory, stage = stage_file(root, "ocr/scan.pdf")
    output = directory / "report.json"
    output.write_bytes(b"preserve")
    original = fsutil.is_reparse_point
    monkeypatch.setattr(fsutil, "is_reparse_point", lambda p: Path(p) == output or original(p))
    monkeypatch.setattr(convert.subprocess, "run", lambda *a, **kw: pytest.fail("reparse output must be rejected"))
    with pytest.raises(SbError):
        convert.run_report(directory / "src" / stage["filename"], output)
    assert output.read_bytes() == b"preserve"


@pytest.mark.parametrize("ext,expected", [(".pdf", "PdfConverter"), (".docx", "DocxConverter"),
    (".pptx", "PptxConverter"), (".xlsx", "XlsxConverter"), (".hwp", "HwpConverter"),
    (".hwpx", "HwpConverter"), (".md", "PlainTextConverter"), (".html", "HtmlConverter"),
    (".htm", "HtmlConverter"), (".csv", "CsvConverter"), (".txt", "PlainTextConverter"),
    (".log", "PlainTextConverter"), (".json", "PlainTextConverter"), (".xml", "PlainTextConverter")])
def test_only_extension_selected_converter_is_registered(monkeypatch, ext, expected):
    import markitdown
    options, registered = [], []
    class Tool:
        def __init__(self, **kwargs): options.append(kwargs)
        def register_converter(self, converter): registered.append(type(converter).__name__)
    monkeypatch.setattr(markitdown, "MarkItDown", Tool)
    convert._make_converter(ext)
    assert options == [{"enable_builtins": False, "enable_plugins": False}]
    assert registered == [expected]


@pytest.mark.parametrize("optional_text", ["", "ExifTool metadata / optional audio output"])
def test_renamed_audio_never_reaches_optional_backends(root, monkeypatch, optional_text, subprocess_spy, network_guard):
    from markitdown import MarkItDown, StreamInfo, DocumentConverterResult
    from markitdown.converters import AudioConverter
    directory, stage = stage_file(root, "characterize/renamed-audio.pdf")
    audio_calls = []
    def guesses(self, *, file_stream, base_guess):
        # Simulate a sniffer recognizing MP3 behind the allowed PDF extension.
        # This private 0.3.5 hook must be reviewed when upgrading markitdown-gc.
        return [base_guess, StreamInfo(extension=".mp3", mimetype="audio/mpeg")]
    def audio(self, *args, **kwargs):
        audio_calls.append(True)
        return DocumentConverterResult(markdown=optional_text)
    monkeypatch.setattr(MarkItDown, "_get_stream_info_guesses", guesses)
    monkeypatch.setattr(AudioConverter, "convert", audio)
    network_calls_before = len(network_guard)
    result = convert.classify_item(directory, stage)
    assert (result["class"], result["state"], result["reason"]) == (None, "failed", "FileConversionException")
    assert result["error"]["code"] == "conversion_failed"
    assert audio_calls == [] and subprocess_spy == []
    assert len(network_guard) == network_calls_before
