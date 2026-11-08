"""Schema-1 ledgers and referenced-artifact validation, with no command imports."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import unicodedata

from .errors import ErrorCode, SbError, WarningCode
from .fsutil import checked_path, is_reparse_point, sha256_file


@dataclass
class Item:
    path: Path
    meta: dict
    warnings: list = field(default_factory=list)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, names):
    _require(isinstance(value, dict) and set(value) == set(names.split()), f"Expected fields: {names}")


def _string(value, nullable=False):
    _require(isinstance(value, str) or nullable and value is None, "Expected string")


def _integer(value, minimum=0, nullable=False):
    _require(nullable and value is None or type(value) is int and value >= minimum, "Expected nonnegative integer")


def _boolean(value):
    _require(type(value) is bool, "Expected boolean")


def _hex(value, length=64):
    _require(isinstance(value, str) and re.fullmatch(f"[0-9a-f]{{{length}}}", value), "Invalid digest or id")


def _date(value):
    _require(isinstance(value, str) and "T" in value and value.endswith("Z"), "Expected UTC timestamp ending in Z")
    datetime.fromisoformat(value)


def _filename(value):
    _require(isinstance(value, str) and value not in {"", ".", ".."}
             and not any(c in value for c in "/\\\0"), "Invalid filename")


def _relative(value):
    _require(isinstance(value, str) and value and "\\" not in value and "\0" not in value, "Invalid artifact path")
    path = Path(value)
    _require(not path.is_absolute() and not path.drive and all(p not in {".", ".."} for p in value.split("/"))
             and "" not in value.split("/"), "Unsafe artifact path")
    return path


def _activity(value, method=None):
    _keys(value, "tool version method peer model date params")
    _string(value["tool"])
    _require(bool(value["tool"]), "Empty tool")
    _string(value["version"], nullable=True)
    _require(value["method"] in {"convert", "ocr-vision", "ocr-verify", "summary"}, "Invalid method")
    if method is not None:
        _require(value["method"] == method, "Wrong activity method")
    _date(value["date"])
    params = value["params"]
    if value["method"] == "convert":
        _require(value["tool"] == "markitdown-gc" and value["version"] == "0.3.5", "Wrong converter/version")
        _require(value["peer"] is None and value["model"] is None, "Conversion has no peer/model")
        _keys(params, "charset extract_media")
        _string(params["charset"], nullable=True)
        _boolean(params["extract_media"])
    else:
        _require(isinstance(value["peer"], str) and re.fullmatch(r"[a-z][a-z0-9-]{0,31}", value["peer"]), "Invalid peer id")
        _require(isinstance(value["model"], str) and value["model"], "Missing peer model")
        _keys(params, "prompt_rev dpi unit_file" if value["method"] == "ocr-vision" else "prompt_rev")
        _require(isinstance(params["prompt_rev"], str) and params["prompt_rev"], "Invalid prompt revision")
        if value["method"] == "ocr-vision":
            _integer(params["dpi"], minimum=1)
            _require(isinstance(params["unit_file"], str) and params["unit_file"], "Missing unit_file provenance")


def activity(tool, version, method, *, peer=None, model=None, params=None, date=None):
    value = {"tool": tool, "version": version, "method": method, "peer": peer, "model": model,
             "date": date if date is not None else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
             "params": {} if params is None else dict(params)}
    try:
        _activity(value)
    except (ValueError, TypeError, KeyError) as error:
        raise SbError(ErrorCode.INVALID_REQUEST, 2, str(error)) from error
    return value


def _identity(value):
    _hex(value["sha256"])
    _hex(value["id"], 16)
    _require(value["id"] == value["sha256"][:16], "Id differs from digest prefix")
    _integer(value["size"])


def _artifact(directory, name, digest, referenced):
    _relative(name)
    _hex(digest)
    _require(name not in referenced, "Artifact referenced more than once")
    path = checked_path(directory, name)
    _require(path.is_file(), f"Missing artifact: {name}")
    _require(sha256_file(path) == digest, f"Artifact digest mismatch: {name}")
    referenced.add(name)


def _conversion(value, directory, referenced, pending=False):
    if value is None:
        return
    if pending and value.get("sha256") is None:
        _require(set(value) in ({"activity", "sha256"}, {"activity", "sha256", "media"}), "Invalid pending conversion")
        _activity(value["activity"], "convert")
        return
    _keys(value, "activity sha256 media")
    _activity(value["activity"], "convert")
    _artifact(directory, "converted.md", value["sha256"], referenced)
    _require(isinstance(value["media"], list), "Expected media list")
    for media in value["media"]:
        _keys(media, "file sha256")
        _require(_relative(media["file"]).parts[0] == "media" and len(Path(media["file"]).parts) == 2, "Expected media/<asset>")
        _artifact(directory, media["file"], media["sha256"], referenced)


def _triage(value, pdf=False):
    if value is None:
        return
    _keys(value, "decision coverage scope image_occurrences candidates issues")
    _require(value["decision"] in {"ocr_recommended", "review", "no_candidates", "unknown"}, "Invalid triage decision")
    coverage = value["coverage"]
    _keys(coverage, "state pages_total pages_inspected")
    _require(coverage["state"] in {"complete", "partial", "none", "not_applicable"}, "Invalid coverage state")
    for name in ("pages_total", "pages_inspected"):
        _integer(coverage[name], nullable=True)
    if coverage["pages_total"] is not None and coverage["pages_inspected"] is not None:
        _require(coverage["pages_inspected"] <= coverage["pages_total"], "Inspected pages exceed total")
    _string(value["scope"])
    _integer(value["image_occurrences"])
    _require(isinstance(value["candidates"], list), "Expected candidate list")
    ids = set()
    for candidate in value["candidates"]:
        _keys(candidate, "id kind page priority")
        for name in ("id", "kind", "priority"):
            _string(candidate[name])
        _integer(candidate["page"], minimum=1, nullable=True)
        _require(candidate["id"] not in ids, "Duplicate candidate id")
        ids.add(candidate["id"])
        if pdf:
            _require(re.fullmatch(r"p[1-9][0-9]*", candidate["id"]), "Invalid PDF candidate id")
            if coverage["pages_total"] is not None:
                _require(int(candidate["id"][1:]) <= coverage["pages_total"], "PDF candidate outside page range")
    _require(isinstance(value["issues"], list) and len(value["issues"]) <= 20, "Invalid issues list")
    for code in value["issues"]:
        _string(code)


def _ocr(value, meta, directory, referenced):
    _keys(value, "disposition large_ack units")
    _require(value["disposition"] in {"none", "approved", "declined"}, "Invalid OCR disposition")
    _boolean(value["large_ack"])
    units = value["units"]
    _require(isinstance(units, dict) and len(units) <= 9999, "Invalid units")
    _require(bool(units) == (meta["class"] in {"ocr-required", "mixed"}), "Units/class mismatch")
    _require(sorted(units) == [f"u{n:04}" for n in range(1, len(units) + 1)], "Invalid unit keys")
    for key, unit in units.items():
        _keys(unit, "source kind status attempts")
        _require(unit["kind"] in {"page", "asset", "raster"}, "Invalid unit kind")
        _string(unit["source"])
        if unit["kind"] == "page":
            _require(meta["ext"] == ".pdf" and re.fullmatch(r"p[1-9][0-9]*", unit["source"]), "Invalid page source")
            _require(meta["triage"] is not None and unit["source"] in {c["id"] for c in meta["triage"]["candidates"]}, "Page is not a candidate")
        elif unit["kind"] == "asset":
            _require(meta["conversion"] is not None and unit["source"] in {m["file"] for m in meta["conversion"]["media"]}, "Asset is not conversion media")
        else:
            _require(unit["source"] == "self" and meta["ext"] in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}, "Invalid raster source")
            _require(len(units) == 1, "Raster must have one unit")
        _require(unit["status"] in {"pending", "approved", "recorded", "verified"}, "Invalid unit status")
        attempts = unit["attempts"]
        _require(isinstance(attempts, list), "Invalid attempt list")
        digests = set()
        for n, attempt in enumerate(attempts, 1):
            _keys(attempt, "n file sha256 recorded verified result")
            _integer(attempt["n"], minimum=1)
            _require(attempt["n"] == n and attempt["file"] == f"ocr/{key}.a{n}.md", "Invalid attempt number/path")
            _require(attempt["sha256"] not in digests, "Repeated OCR digest")
            digests.add(attempt["sha256"])
            _artifact(directory, attempt["file"], attempt["sha256"], referenced)
            _activity(attempt["recorded"], "ocr-vision")
            _require(attempt["result"] in {None, "ok", "mismatch"}, "Invalid verification result")
            _require((attempt["verified"] is None) == (attempt["result"] is None), "Result/activity mismatch")
            if attempt["verified"] is not None:
                _activity(attempt["verified"], "ocr-verify")
                _require(attempt["verified"]["peer"] != attempt["recorded"]["peer"], "Same OCR peer")
            if n < len(attempts):
                _require(attempt["result"] == "mismatch", "Only mismatches may precede a new attempt")
        last = attempts[-1]["result"] if attempts else None
        if unit["status"] in {"recorded", "verified"}:
            _require(bool(attempts) and last == ("ok" if unit["status"] == "verified" else None), "Status/last attempt mismatch")
        elif attempts:
            _require(last == "mismatch", "Pending/approved attempt must be mismatch")
    approved = any(u["status"] != "pending" for u in units.values())
    _require((value["disposition"] == "approved") == approved, "Disposition/unit mismatch")
    if approved and len(units) > 20:
        _require(value["large_ack"], "Missing large approval acknowledgement")
    if meta["state"] == "awaiting-approval":
        _require(value["disposition"] == "none", "Awaiting item has OCR disposition")
    if meta["state"] == "ocr-in-progress":
        _require(approved and not all(u["status"] == "verified" for u in units.values()), "Invalid in-progress item")
    if meta["state"] == "ready" and meta["class"] in {"ocr-required", "mixed", "unknown"}:
        _require(value["disposition"] == "declined" or approved and all(u["status"] == "verified" for u in units.values()), "OCR ready before disposition")
    if value["disposition"] == "declined":
        _require(meta["state"] == "ready" and meta["class"] in {"ocr-required", "mixed", "unknown"}, "Invalid decline")


def _llm(value, meta, directory, referenced):
    if value is None:
        return
    _keys(value, "summary")
    _require(isinstance(value["summary"], list) and value["summary"], "Empty summary history")
    _require(meta["state"] == "ready" and meta["class"] != "unsupported", "Summary on ineligible item")
    for n, revision in enumerate(value["summary"], 1):
        _keys(revision, "n file sha256 source_digest activity")
        _integer(revision["n"], minimum=1)
        _require(revision["n"] == n and revision["file"] == f"llm/summary.a{n}.md", "Invalid summary revision/path")
        _hex(revision["source_digest"])
        _activity(revision["activity"], "summary")
        _artifact(directory, revision["file"], revision["sha256"], referenced)


def _orphans(directory, referenced, identity):
    warnings = []
    for parent, dirs, files in os.walk(directory, followlinks=False):
        # Do not traverse reparse directories, including Windows junctions.
        for name in list(dirs):
            if is_reparse_point(Path(parent) / name):
                dirs.remove(name)
                files.append(name)
        for name in files:
            relative = (Path(parent) / name).relative_to(directory).as_posix()
            if relative not in referenced:
                warnings.append({"code": str(WarningCode.ORPHAN), "id": identity, "path": relative,
                                 "message": "Unreferenced artifact ignored"})
    return sorted(warnings, key=lambda w: w["path"])


def _validate_meta(meta, directory):
    _keys(meta, "schema id sha256 size ext filename filename_nfc aliases ingested_at class reason state conversion triage has_native_text ocr llm error")
    _require(type(meta["schema"]) is int and meta["schema"] == 1, "Unsupported meta schema")
    _identity(meta)
    _require(directory.name == meta["id"], "Directory/id mismatch")
    _filename(meta["filename"])
    _require(meta["filename_nfc"] == unicodedata.normalize("NFC", meta["filename"]), "Invalid NFC filename")
    _require(meta["ext"] == Path(meta["filename"]).suffix.lower(), "Invalid extension")
    aliases = meta["aliases"]
    _require(isinstance(aliases, list), "Expected aliases")
    for name in aliases:
        _filename(name)
    _require(aliases == sorted(set(aliases)) and meta["filename"] not in aliases, "Invalid aliases")
    _date(meta["ingested_at"])
    states = {"text-only": {"ready"}, "ocr-required": {"awaiting-approval", "ocr-in-progress", "ready"},
              "mixed": {"awaiting-approval", "ocr-in-progress", "ready"}, "unknown": {"awaiting-approval", "ready"},
              "unsupported": {"unsupported"}, None: {"failed"}}
    _require(meta["class"] in states and meta["state"] in states[meta["class"]], "Invalid class/state pair")
    _string(meta["reason"], nullable=True)
    source = checked_path(directory, "src/" + meta["filename"])
    _require(source.is_file() and source.stat().st_size == meta["size"], "Missing/wrong-size source")
    referenced = {"meta.json", "src/" + meta["filename"]}
    _conversion(meta["conversion"], directory, referenced)
    _require((meta["has_native_text"] is None) == (meta["conversion"] is None), "Native text/conversion mismatch")
    if meta["has_native_text"] is not None:
        _boolean(meta["has_native_text"])
    _triage(meta["triage"], meta["ext"] == ".pdf")
    rasters = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
    if meta["ext"] in rasters:
        _require(meta["conversion"] is None, "Raster must not have a conversion")
    if meta["class"] in {"text-only", "mixed", "unknown"} or meta["class"] == "ocr-required" and meta["ext"] not in rasters:
        _require(meta["conversion"] is not None, "Missing successful conversion")
    if meta["class"] == "mixed":
        _require(meta["has_native_text"] is True, "Mixed item requires native text")
    if meta["class"] == "ocr-required":
        _require(not meta["has_native_text"], "OCR-only item has native text")
    if meta["ext"] in {".pdf", ".docx", ".pptx", ".xlsx", ".hwp", ".hwpx", ".md", ".html", ".htm"} and meta["state"] not in {"failed", "unsupported"}:
        _require(meta["triage"] is not None, "Missing successful triage")
    if meta["ext"] in {".txt", ".csv", ".log", ".json", ".xml", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}:
        _require(meta["triage"] is None, "Unexpected triage on plain text/raster")
    _ocr(meta["ocr"], meta, directory, referenced)
    _llm(meta["llm"], meta, directory, referenced)
    _require((meta["error"] is not None) == (meta["state"] == "failed"), "Error/state mismatch")
    if meta["error"] is not None:
        _keys(meta["error"], "code message date")
        _string(meta["error"]["code"])
        _string(meta["error"]["message"])
        _date(meta["error"]["date"])
        _require(meta["reason"] == meta["error"]["code"], "Failure reason/error mismatch")
    return _orphans(directory, referenced, meta["id"])


def _corrupt(operation):
    try:
        return operation()
    except SbError as error:
        if error.code == ErrorCode.CORRUPT_META:
            raise
        raise SbError(ErrorCode.CORRUPT_META, 1, str(error)) from error
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError) as error:
        raise SbError(ErrorCode.CORRUPT_META, 1, str(error)) from error


def validate_meta(meta, directory):
    return _corrupt(lambda: _validate_meta(meta, Path(directory)))


def _read(directory, name):
    path = checked_path(directory, name)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def load_item(directory):
    directory = Path(directory)
    meta = _corrupt(lambda: _read(directory, "meta.json"))
    return Item(directory, meta, validate_meta(meta, directory))


def _validate_stage(stage, directory):
    _require(isinstance(stage, dict) and {"relpath", "filename", "charset", "claimed_at"} <= set(stage), "Invalid stage fields")
    _relative(stage["relpath"])
    _filename(stage["filename"])
    _require(Path(stage["relpath"]).name == stage["filename"], "Stage relpath/filename mismatch")
    _string(stage["charset"], nullable=True)
    _date(stage["claimed_at"])
    referenced = {"stage.json"}
    source = checked_path(directory, "src/" + stage["filename"])
    if source.exists():
        _require(source.is_file(), "Staged source must be a regular file")
        referenced.add("src/" + stage["filename"])
    if "identity" in stage:
        _keys(stage["identity"], "id sha256 size")
        _identity(stage["identity"])
        if source.exists():
            _require(source.stat().st_size == stage["identity"]["size"], "Staged source size mismatch")
    if "collision" in stage:
        _boolean(stage["collision"])
    _conversion(stage.get("conversion"), directory, referenced, pending=True)
    _triage(stage.get("triage"), Path(stage["filename"]).suffix.lower() == ".pdf")
    return _orphans(directory, referenced, stage.get("identity", {}).get("id"))


def validate_stage(stage, directory):
    return _corrupt(lambda: _validate_stage(stage, Path(directory)))


def load_stage(directory):
    directory = Path(directory)
    stage = _corrupt(lambda: _read(directory, "stage.json"))
    validate_stage(stage, directory)
    return stage
