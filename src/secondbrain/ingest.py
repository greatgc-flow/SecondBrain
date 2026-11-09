"""DESIGN §4: inbox handoff, durable staging, commit and failed-item retry."""
import codecs
from datetime import datetime, timezone
import os
from pathlib import Path
import unicodedata

from . import convert
from .errors import ErrorCode, SbError, WarningCode
from .fsutil import check_path_length, checked_path, is_reparse_point, load_json_strict, safe_delete, sha256_file, write_json_atomic
from .ledger import load_item, load_stage, scan, validate_meta


def _note(code, root, path, identity=None, message=None):
    return {"code": str(code), "id": identity, "path": Path(path).relative_to(root).as_posix(),
            "message": str(code) if message is None else str(message)}


def _error(result, root, path, error, identity=None):
    code = error.code if isinstance(error, SbError) else ErrorCode.IO_ERROR
    result["errors"].append(_note(code, root, path, identity, error))


def _snapshot(root, result):
    paths = []
    def walk(directory):
        for path in sorted(directory.iterdir()):
            if is_reparse_point(path):
                result["warnings"].append(_note(WarningCode.SKIPPED_REPARSE, root, path))
            elif path.name.startswith("."):
                result["warnings"].append(_note(WarningCode.SKIPPED_HIDDEN, root, path))
            elif path.is_dir():
                walk(path)
            elif path.is_file():
                paths.append(path)
    walk(root / "inbox")
    return sorted(paths, key=lambda p: p.relative_to(root / "inbox").as_posix())


def _meta(stage):
    identity = stage["identity"]
    conversion = stage.get("conversion")
    if conversion is not None and conversion["sha256"] is None:
        conversion = None
    return {"schema": 1, **identity, "filename": stage["filename"],
            "filename_nfc": unicodedata.normalize("NFC", stage["filename"]),
            "ext": Path(stage["filename"]).suffix.lower(), "aliases": [], "ingested_at": stage["claimed_at"],
            **{key: stage[key] for key in ("class", "state", "reason", "error", "ocr")},
            "conversion": conversion, "triage": stage.get("triage"),
            "has_native_text": stage.get("has_native_text") if conversion is not None else None, "llm": None}


def _read_meta(path):
    try:
        return load_json_strict(path)
    except ValueError as error:
        raise SbError(ErrorCode.CORRUPT_META, 1, str(error)) from error


def _finished(root, directory, result, outcome):
    item = load_item(directory)
    result["items"].append({"id": item.meta["id"], "result": outcome})
    result["warnings"].extend(item.warnings)
    if item.meta["error"] is not None:
        error = item.meta["error"]
        result["errors"].append(_note(error["code"], root, directory, item.meta["id"], error["message"]))


def _resume(root, directory, stage, result):
    source = checked_path(directory, "src/" + stage["filename"])
    if not source.exists():
        safe_delete(root, directory)
        return
    if stage.get("collision"):
        if "identity" not in stage:
            raise SbError(ErrorCode.CORRUPT_META, 1, "Collision flag requires an identity")
        result["warnings"].append(_note(WarningCode.STAGED_COLLISION, root, directory, stage["identity"]["id"]))
        return
    if "identity" not in stage:
        digest = sha256_file(source)
        stage["identity"] = {"sha256": digest, "id": digest[:16], "size": source.stat().st_size}
        write_json_atomic(directory / "stage.json", stage)
    identity = stage["identity"]["id"]
    target = checked_path(root, "raws/" + identity)
    if target.exists():
        item = load_item(target)
        if item.meta["sha256"] != stage["identity"]["sha256"]:
            stage["collision"] = True
            write_json_atomic(directory / "stage.json", stage)
            result["warnings"].append(_note(WarningCode.STAGED_COLLISION, root, directory, identity))
            raise SbError(ErrorCode.ID_COLLISION, 1, "Different full digest for an occupied id")
        name = stage["filename"]
        outcome = "duplicate"
        if name != item.meta["filename"] and name not in item.meta["aliases"]:
            item.meta["aliases"] = sorted([*item.meta["aliases"], name])
            validate_meta(item.meta, target)
            write_json_atomic(target / "meta.json", item.meta)
            outcome = "alias_added"
        safe_delete(root, directory)
        result["items"].append({"id": identity, "result": outcome})
        return
    meta_path = checked_path(directory, "meta.json")
    if meta_path.exists():
        # Only committed meta gets full-schema validation. A staged commit must
        # agree with its governing stage ledger before rename 2 can proceed.
        try:
            expected = _meta(stage)
        except (KeyError, TypeError) as error:
            raise SbError(ErrorCode.CORRUPT_META, 1, "Staged meta has no completed ledger") from error
        if _read_meta(meta_path) != expected:
            raise SbError(ErrorCode.CORRUPT_META, 1, "Staged meta disagrees with stage ledger")
    else:
        convert.classify_item(directory, stage)
        write_json_atomic(meta_path, _meta(stage))
    os.rename(directory, target)
    _finished(root, target, result, "new")


def _recover(root, result):
    staging = checked_path(root, "raws/.staging")
    if not staging.exists():
        return
    for directory in sorted(staging.glob("tmp-*")):
        stage = {}
        try:
            checked_path(root, directory)
            if not (directory / "stage.json").exists():
                safe_delete(root, directory)
                continue
            stage = load_stage(directory)
            _resume(root, directory, stage, result)
        except (SbError, OSError) as error:
            _error(result, root, directory, error, stage.get("identity", {}).get("id"))


def _claim(root, source, charset):
    source = checked_path(root, source)
    check_path_length(root / "raws" / ("0" * 16) / "src" / source.name)
    staging = checked_path(root, "raws/.staging")
    staging.mkdir(parents=True, exist_ok=True)
    number = 1
    while os.path.lexists(staging / f"tmp-{number}"):
        number += 1
    directory = staging / f"tmp-{number}"
    (directory / "src").mkdir(parents=True)
    stage = {"filename": source.name, "relpath": source.relative_to(root / "inbox").as_posix(), "charset": charset,
             "claimed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    write_json_atomic(directory / "stage.json", stage)
    os.replace(source, directory / "src" / source.name)
    return directory, stage


def _retry(root, item, charset, result):
    directory, meta = item.path, item.meta
    if meta["state"] != "failed":
        result["items"].append({"id": meta["id"], "result": "skipped"})
        return
    if checked_path(directory, "stage.json").exists():
        stage = load_stage(directory)
        if stage.get("identity") != {key: meta[key] for key in ("id", "sha256", "size")} or stage["filename"] != meta["filename"]:
            raise SbError(ErrorCode.CORRUPT_META, 1, "Retry identity differs from committed meta")
    else:
        stage = {"filename": meta["filename"], "relpath": meta["filename"], "claimed_at": meta["ingested_at"],
                 "identity": {key: meta[key] for key in ("id", "sha256", "size")},
                 "charset": meta["conversion"]["activity"]["params"]["charset"] if meta["conversion"] else None}
        for key in ("conversion", "triage", "has_native_text"):
            if meta[key] is not None:
                stage[key] = meta[key]
    # A new charset can affect an uncompleted attempt, never a completed output.
    if charset is not None and not checked_path(directory, "converted.md").exists():
        stage["charset"] = charset
        stage.pop("conversion", None)
    write_json_atomic(directory / "stage.json", stage)
    outcome = convert.classify_item(directory, stage)
    merged = {**meta, **outcome}
    validate_meta(merged, directory)
    write_json_atomic(directory / "meta.json", merged)
    _finished(root, directory, result, "retried")


def ingest(root, *, retry=False, charset=None):
    """Return item result ids and notes; the CLI owns projection and exit codes.

    Recover staging first, retry pre-existing failed items on request, then claim
    one fixed inbox snapshot. Persisted claim options win during recovery.
    """
    if charset is not None:
        try:
            codecs.lookup(charset)
        except (LookupError, TypeError) as error:
            raise SbError(ErrorCode.INVALID_REQUEST, 2, "Unknown charset") from error
    convert.check_version()
    root = Path(os.path.abspath(root))
    inbox = checked_path(root, "inbox")
    if not inbox.is_dir():
        raise SbError(ErrorCode.IO_ERROR, 1, "ingest requires an existing inbox directory")
    result = {"items": [], "warnings": [], "errors": []}
    try:
        items, warnings, errors = scan(root) if retry else ([], [], [])
        result["warnings"].extend(warnings)
        result["errors"].extend(errors)
        _recover(root, result)
        if retry:
            for item in items:
                try:
                    _retry(root, load_item(item.path), charset, result)
                except (SbError, OSError) as error:
                    _error(result, root, item.path, error, item.meta["id"])
        for source in _snapshot(root, result):
            stage = {}
            try:
                directory, stage = _claim(root, source, charset)
                _resume(root, directory, stage, result)
            except (SbError, OSError) as error:
                _error(result, root, source, error, stage.get("identity", {}).get("id"))
    except (SbError, OSError) as error:
        _error(result, root, root, error)
    result["items"].sort(key=lambda entry: entry["id"])
    for key in ("warnings", "errors"):
        unique = {(note["id"], note["code"], note["path"]): note for note in result[key]}
        result[key] = sorted(unique.values(), key=lambda note: (note["id"] or "", note["code"], note["path"]))
    return result
