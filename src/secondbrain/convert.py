"""DESIGN §3 conversion and classification; no ingest or OCR command imports."""
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess

from .errors import ErrorCode, SbError
from .fsutil import checked_path, sha256_file, write_json_atomic
from .ledger import activity, validate_stage
from .transcript import has_native_text

PLAIN_TEXT_EXTENSIONS = frozenset({".txt", ".csv", ".log", ".json", ".xml"})
MARKUP_EXTENSIONS = frozenset({".md", ".html", ".htm"})
CONTAINER_EXTENSIONS = frozenset({".docx", ".pptx", ".xlsx", ".hwp", ".hwpx"})
RASTER_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"})
CONVERTIBLE_EXTENSIONS = PLAIN_TEXT_EXTENSIONS | MARKUP_EXTENSIONS | CONTAINER_EXTENSIONS | {".pdf"}
ALLOWED_EXTENSIONS = CONVERTIBLE_EXTENSIONS | RASTER_EXTENSIONS


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _count(value, nullable=False, minimum=0):
    _require(nullable and value is None or type(value) is int and value >= minimum, "Invalid report count")


def adapt_report(report, ext):
    """Reduce observed 0.3.5 evidence to the exact persisted triage fields."""
    try:
        _require(type(report["schema_version"]) is int and report["schema_version"] == 1, "Unsupported report schema")
        decision = report["decision"]
        _require(decision in {"ocr_recommended", "review", "no_candidates", "unknown"}, "Invalid decision")
        coverage = {name: report["coverage"][name] for name in ("state", "pages_total", "pages_inspected")}
        _require(coverage["state"] in {"complete", "partial", "none", "not_applicable"}, "Invalid coverage")
        for name in ("pages_total", "pages_inspected"):
            _count(coverage[name], nullable=True)
        if coverage["pages_total"] is not None and coverage["pages_inspected"] is not None:
            _require(coverage["pages_inspected"] <= coverage["pages_total"], "Inspected pages exceed total")
        scope = report["summary"]["scope"]
        occurrences = report["summary"]["image_occurrences"]
        _require(isinstance(scope, str), "Invalid summary scope")
        _count(occurrences)
        _require(isinstance(report["candidates"], list), "Invalid candidates")
        candidates, ids = [], set()
        for value in report["candidates"]:
            candidate = {name: value[name] for name in ("id", "kind", "page", "priority")}
            for name in ("id", "kind", "priority"):
                _require(isinstance(candidate[name], str), "Invalid candidate field")
            _count(candidate["page"], nullable=True, minimum=1)
            _require(candidate["id"] not in ids, "Duplicate candidate id")
            ids.add(candidate["id"])
            if ext.lower() == ".pdf":
                _require(re.fullmatch(r"p[1-9][0-9]*", candidate["id"]), "Invalid PDF candidate id")
                if coverage["pages_total"] is not None:
                    _require(int(candidate["id"][1:]) <= coverage["pages_total"], "PDF candidate exceeds page count")
            candidates.append(candidate)
        _require(isinstance(report["issues"], list), "Invalid issues")
        issues = [issue["code"] for issue in report["issues"]]
        _require(all(isinstance(code, str) for code in issues), "Invalid issue code")
        return {"decision": decision, "coverage": coverage, "scope": scope,
                "image_occurrences": occurrences, "candidates": candidates, "issues": issues[:20]}
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise SbError(ErrorCode.REPORT_INVALID, 1, str(error)) from error


def _local_file(source):
    if isinstance(source, str) and re.match(r"(?:[a-z][a-z0-9+.-]*://|data:)", source, flags=re.I):
        raise SbError(ErrorCode.IO_ERROR, 1, "A local regular file is required")
    try:
        path = Path(source).resolve(strict=True)
        if not path.is_file():
            raise OSError("A local regular file is required")
        return path
    except (OSError, ValueError, TypeError) as error:
        raise SbError(ErrorCode.IO_ERROR, 1, str(error)) from error


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "Duplicate report JSON key")
        result[key] = value
    return result


def run_report(source, output):
    """Run real triage into the caller's staging/scratch path; discard the JSON."""
    source = _local_file(source)
    output = Path(os.path.abspath(output))
    checked_path(output.parent, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        try:
            process = subprocess.run(["markitdown-gc", str(source), "--ocr-report", "-o", str(output)],
                                     capture_output=True, text=True, encoding="utf-8")
        except OSError as error:
            raise SbError(ErrorCode.REPORT_FAILED, 1, str(error)) from error
        if process.returncode != 0:
            raise SbError(ErrorCode.REPORT_FAILED, 1, process.stderr or "Report command failed")
        try:
            text = output.read_text(encoding="utf-8")
        except UnicodeError as error:
            raise SbError(ErrorCode.REPORT_INVALID, 1, str(error)) from error
        except OSError as error:
            raise SbError(ErrorCode.REPORT_FAILED, 1, str(error)) from error
        try:
            report = json.loads(text, object_pairs_hook=_unique_pairs)
        except ValueError as error:
            raise SbError(ErrorCode.REPORT_INVALID, 1, str(error)) from error
        return adapt_report(report, source.suffix)
    finally:
        output.unlink(missing_ok=True)


def _make_converter():
    # Lazy import: denied extensions and rasters never even initialize the tool.
    from markitdown import MarkItDown
    return MarkItDown(enable_plugins=False)


def _conversion_record(directory, conversion_activity):
    media = []
    media_directory = checked_path(directory, "media")
    if media_directory.exists():
        for path in sorted(media_directory.iterdir(), key=lambda p: p.name):
            path = checked_path(directory, path)
            if path.is_file():
                media.append({"file": "media/" + path.name, "sha256": sha256_file(path)})
    return {"activity": conversion_activity, "sha256": sha256_file(directory / "converted.md"), "media": media}


def convert_document(directory, stage):
    """Persist intent first; reconcile completed bytes; never replace valid output.

    Only backend/encoding exceptions become conversion_failed with their original
    exception as __cause__. Filesystem faults propagate for startup recovery.
    """
    directory = Path(os.path.abspath(directory))
    validate_stage(stage, directory)
    source = _local_file(checked_path(directory, "src/" + stage["filename"]))
    if source.suffix.lower() not in CONVERTIBLE_EXTENSIONS:
        raise SbError(ErrorCode.INVALID_REQUEST, 2, "Source must not reach the converter")
    previous = stage.get("conversion")
    if previous is not None and previous["sha256"] is not None:
        return previous
    converted = checked_path(directory, "converted.md")
    if converted.exists() and previous is None:
        raise SbError(ErrorCode.CORRUPT_META, 1, "Completed conversion has no ledger intent")
    if previous is None:
        previous = {"activity": activity("markitdown-gc", version("markitdown-gc"), "convert",
                                        params={"charset": stage["charset"], "extract_media": source.suffix.lower() in CONTAINER_EXTENSIONS}),
                    "sha256": None}
        stage["conversion"] = previous
        write_json_atomic(directory / "stage.json", stage)
    if not converted.exists():
        params = previous["activity"]["params"]
        options = {"charset": params["charset"]}
        if params["charset"] is not None:
            # 0.3.5 reads charset from StreamInfo, not from the bare keyword.
            # Keep the declared keyword too; the hint makes it effective.
            from markitdown import StreamInfo
            options["stream_info"] = StreamInfo(charset=params["charset"])
        if params["extract_media"]:
            options["extract_media"] = str(checked_path(directory, "media"))
        try:
            data = _make_converter().convert(str(source), **options).text_content.encode("utf-8")
        except Exception as error:
            raise SbError(ErrorCode.CONVERSION_FAILED, 1, str(error)) from error
        temporary = checked_path(directory, "converted.md.tmp")
        with temporary.open("wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, converted)
    stage["conversion"] = _conversion_record(directory, previous["activity"])
    write_json_atomic(directory / "stage.json", stage)
    return stage["conversion"]


def enumerate_units(ext, triage=None, media=()):
    ext = ext.lower()
    if ext in RASTER_EXTENSIONS:
        sources, kind = ["self"], "raster"
    elif triage is None or triage["decision"] not in {"ocr_recommended", "review"}:
        return {}
    elif ext == ".pdf":
        sources = sorted((candidate["id"] for candidate in triage["candidates"]), key=lambda s: int(s[1:]))
        kind = "page"
    elif ext in CONTAINER_EXTENSIONS:
        sources, kind = sorted(asset["file"] for asset in media), "asset"
    else:
        return {}
    if len(sources) > 9999:
        raise SbError(ErrorCode.TOO_MANY_UNITS, 1, "More than 9999 OCR units")
    return {f"u{n:04}": {"source": source, "kind": kind, "status": "pending", "attempts": []}
            for n, source in enumerate(sources, 1)}


def classify(ext, *, size=1, path=None, conversion_error=None, report_error=None, triage=None, native=None, units=None, date=None):
    """Apply the first matching §3 row; arguments are already adapted stage data."""
    ext = ext.lower()
    def result(cls, state, reason=None, code=None, message=None):
        error = None if code is None else {"code": str(code), "message": message or str(reason),
                                          "date": date or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
        return {"class": cls, "state": state, "reason": reason, "error": error}
    def failed(code, message=None, reason=None):
        return result(None, "failed", str(code) if reason is None else reason, code, message)
    if size == 0:
        return failed(ErrorCode.EMPTY_FILE)
    if path is not None and len(str(path)) > 240:
        return failed(ErrorCode.PATH_TOO_LONG)
    if ext not in ALLOWED_EXTENSIONS:
        return result("unsupported", "unsupported", "extension_not_allowed")
    if ext in RASTER_EXTENSIONS:
        return result("ocr-required", "awaiting-approval", "raster")
    if conversion_error is not None:
        from markitdown import UnsupportedFormatException, MissingDependencyException
        if isinstance(conversion_error, (UnsupportedFormatException, MissingDependencyException)):
            return result("unsupported", "unsupported", "no_converter" if isinstance(conversion_error, UnsupportedFormatException) else "missing_dependency")
        return failed(ErrorCode.CONVERSION_FAILED, str(conversion_error), type(conversion_error).__name__)
    if ext in PLAIN_TEXT_EXTENSIONS:
        return result("text-only", "ready", None if native else "empty_document")
    if report_error is not None:
        return failed(report_error.code, str(report_error))
    if triage is None:
        return failed(ErrorCode.REPORT_INVALID)
    if triage["decision"] in {"ocr_recommended", "review"}:
        if not triage["candidates"]:
            return failed(ErrorCode.NO_CANDIDATE_IDS)
        if units:
            if len(units) > 9999:
                return failed(ErrorCode.TOO_MANY_UNITS)
            return result("mixed" if native else "ocr-required", "awaiting-approval")
        return result("unknown", "awaiting-approval", "no_units")
    if triage["decision"] == "no_candidates" and triage["coverage"]["state"] in {"complete", "not_applicable"}:
        return result("text-only", "ready", None if native else "empty_document")
    return result("unknown", "awaiting-approval", next(iter(triage["issues"]), None))


def classify_item(directory, stage):
    """Run §3 on an already staged source; return fields for committed meta.

    Stage intent remains pending after backend failure. Completed conversion,
    native-text and triage outputs are reused only after ledger validation.
    """
    directory = Path(os.path.abspath(directory))
    validate_stage(stage, directory)
    source = _local_file(checked_path(directory, "src/" + stage["filename"]))
    ext, size = source.suffix.lower(), source.stat().st_size
    conversion = triage = native = None
    units = {}
    def finish(outcome):
        ocr = {"disposition": "none", "large_ack": False,
               "units": units if outcome["class"] in {"ocr-required", "mixed"} else {}}
        stage.update(outcome, ocr=ocr)
        write_json_atomic(directory / "stage.json", stage)
        return {**outcome, "conversion": conversion, "triage": triage, "has_native_text": native, "ocr": ocr}
    # The 240-character check concerns the planned committed src path, before
    # ingest claims it. A staging path can be longer than that destination.
    if size == 0 or ext not in CONVERTIBLE_EXTENSIONS:
        if size and ext in RASTER_EXTENSIONS:
            units = enumerate_units(ext)
        return finish(classify(ext, size=size))
    try:
        conversion = convert_document(directory, stage)
    except SbError as error:
        if error.code != ErrorCode.CONVERSION_FAILED:
            raise
        return finish(classify(ext, conversion_error=error.__cause__))
    if "has_native_text" not in stage:
        stage["has_native_text"] = has_native_text((directory / "converted.md").read_bytes().decode("utf-8"))
        write_json_atomic(directory / "stage.json", stage)
    native = stage["has_native_text"]
    if type(native) is not bool:
        raise SbError(ErrorCode.CORRUPT_META, 1, "Invalid cached native-text flag")
    if ext not in PLAIN_TEXT_EXTENSIONS:
        try:
            if stage.get("triage") is None:
                stage["triage"] = run_report(source, directory / "report.json")
                write_json_atomic(directory / "stage.json", stage)
            triage = stage["triage"]
        except SbError as error:
            if error.code not in {ErrorCode.REPORT_FAILED, ErrorCode.REPORT_INVALID}:
                raise
            return finish(classify(ext, report_error=error))
    if triage is None or triage["decision"] not in {"ocr_recommended", "review"} or triage["candidates"]:
        try:
            units = enumerate_units(ext, triage, conversion["media"])
        except SbError as error:
            return finish(classify(ext, report_error=error))
    return finish(classify(ext, triage=triage, native=native, units=units))
