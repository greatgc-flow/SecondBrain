"""Deterministic wiki tier (DESIGN section 7): wiki/ is a pure function of raws/."""
import json
import os
from pathlib import Path
import re
import unicodedata

from .errors import ErrorCode, SbError, WarningCode
from .fsutil import checked_path, esc, is_reparse_point, percent_encode, safe_delete, write_text
from .ledger import load_item
from .transcript import source_digest, view


def _exists(path):
    return os.path.lexists(path)


def _line(value):
    """One line of text: control characters become spaces."""
    return "".join(" " if unicodedata.category(c) == "Cc" else c for c in str(value))


def fence(body, info="text"):
    """Fenced block whose fence is longer than any backtick run in the body."""
    longest = max((len(run) for run in re.findall(r"`+", body)), default=0)
    mark = "`" * max(3, longest + 1)
    return f"{mark}{info}\n{body}\n{mark}\n"


def recover(root):
    """Build-start recovery: drop wiki.tmp; restore or drop wiki.old."""
    root = Path(root)
    for name in ("wiki", "wiki.tmp", "wiki.old"):
        if _exists(root / name):
            checked_path(root, name)  # refuses reparse points before any change
    if _exists(root / "wiki.tmp"):
        safe_delete(root, root / "wiki.tmp")
    if _exists(root / "wiki.old"):
        if _exists(root / "wiki"):
            safe_delete(root, root / "wiki.old")
        else:
            os.rename(root / "wiki.old", root / "wiki")


def _load(root):
    items, warnings, errors = [], [], []
    raws = Path(root) / "raws"
    names = sorted(p.name for p in raws.iterdir()) if raws.is_dir() else []
    for name in names:
        path = raws / name
        if name.startswith(".") or not path.is_dir():
            continue
        if is_reparse_point(path):
            warnings.append({"code": str(WarningCode.SKIPPED_REPARSE), "id": name, "path": f"raws/{name}",
                             "message": "Reparse point skipped"})
            continue
        try:
            item = load_item(path)
        except SbError as error:
            errors.append({"code": error.code, "id": name, "path": f"raws/{name}", "message": str(error)})
            continue
        warnings.extend(item.warnings)
        items.append(item)
    items.sort(key=lambda i: (i.meta["filename_nfc"].casefold(), i.meta["id"]))
    return items, warnings, errors


def _summary(meta):
    """Current summary revision, or None."""
    revisions = (meta.get("llm") or {}).get("summary")
    return revisions[-1] if revisions else None


def _counts(meta):
    units = meta["ocr"]["units"].values()
    total = len(units)
    approved = sum(u["status"] != "pending" for u in units)
    recorded = sum(u["status"] in ("recorded", "verified") for u in units)
    verified = sum(u["status"] == "verified" for u in units)
    return total, approved, recorded, verified


def _coverage(meta):
    return None if meta["triage"] is None else meta["triage"]["coverage"]["state"]


def _ocr_cell(meta):
    disposition = meta["ocr"]["disposition"]
    if disposition == "declined":
        return "declined"
    total, approved, recorded, verified = _counts(meta)
    if disposition == "approved":
        return f"{approved}/{total} approved, {recorded} recorded, {verified} verified"
    return "none"


def banner(meta):
    """Banner text per section 7 table; empty string means none."""
    cls, state, reason = meta["class"], meta["state"], meta["reason"]
    coverage = _coverage(meta)
    extra = f", coverage {coverage}" if coverage not in (None, "complete") else ""
    if state == "unsupported":
        return f"unsupported: {_line(reason)}"
    if state == "failed":
        error = meta.get("error") or {}
        return f"failed: {_line(error.get('code', reason or 'unknown'))}, {error.get('date', 'unknown')}"
    if cls == "unknown":
        text = f"not inspected: {_line(reason if reason else 'unknown')}"
        return text + (", declined" if state == "ready" else "")
    if cls == "text-only":
        return "" if meta["has_native_text"] else "empty document"
    total, approved, recorded, verified = _counts(meta)
    if state == "awaiting-approval":
        return f"OCR pending approval: {total} units, coverage {coverage if coverage else 'n/a'}"
    if state == "ocr-in-progress":
        return f"OCR in progress: {approved}/{total} approved, {recorded} recorded, {verified} verified"
    if meta["ocr"]["disposition"] == "declined":
        return "OCR declined" + extra
    return f"OCR verified: {total} units" + extra


def _json_subset(item):
    meta = item.meta
    ocr = {key: {"recorded": unit["attempts"][-1]["recorded"], "verified": unit["attempts"][-1]["verified"]}
           for key, unit in sorted(meta["ocr"]["units"].items()) if unit["status"] == "verified"}
    summary = _summary(meta)
    summary = summary["activity"] if summary else None
    subset = {
        "id": meta["id"], "sha256": meta["sha256"], "size": meta["size"],
        "filename": meta["filename"], "filename_nfc": meta["filename_nfc"], "aliases": meta["aliases"],
        "class": meta["class"], "state": meta["state"], "reason": meta["reason"], "triage": meta["triage"],
        "activities": {"convert": meta["conversion"]["activity"] if meta["conversion"] else None,
                       "ocr": ocr, "summary": summary},
        "source_digest": source_digest(item),
    }
    return json.dumps(subset, ensure_ascii=False, sort_keys=True, indent=1)


def source_page(item):
    meta = item.meta
    parts = [f"# {esc(meta['filename_nfc'])}\n\n", fence(_json_subset(item), "json"), "\n",
             f"[Original file](../../raws/{meta['id']}/src/{percent_encode(meta['filename'])})\n\n"]
    text = banner(meta)
    if text:
        parts += [fence(text), "\n"]
    revision = _summary(meta)
    if revision:
        body = (item.path / revision["file"]).read_bytes().decode("utf-8")
        parts += ["## Summary\n\n", fence(body), "\n"]
    if meta["state"] != "unsupported" and (meta["state"] != "failed" or _exists(item.path / "converted.md")):
        parts += ["## Transcript\n\n", fence(view(item))]
    return "".join(parts).rstrip("\n") + "\n"


def index_page(items):
    lines = ["# SecondBrain index", "",
             "| Source | Ext | Class | State | Ingested | OCR | Coverage | Summary |",
             "|---|---|---|---|---|---|---|---|"]
    for item in items:
        meta = item.meta
        label = f"[{esc(meta['filename_nfc'])}](sources/{meta['id']}.md)"
        cells = [label, esc(meta["ext"]), meta["class"] or "-", meta["state"], meta["ingested_at"][:10],
                 _ocr_cell(meta), _coverage(meta) or "-", "yes" if _summary(meta) else "no"]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def build(root):
    """Rebuild wiki/ from raws/. Returns {pages, items, warnings, errors}."""
    root = Path(root)
    try:
        recover(root)
        items, warnings, errors = _load(root)
        tmp = root / "wiki.tmp"
        write_text(tmp / "index.md", index_page(items))
        for item in items:
            write_text(tmp / "sources" / f"{item.meta['id']}.md", source_page(item))
        if _exists(root / "wiki"):
            os.rename(root / "wiki", root / "wiki.old")
        os.rename(tmp, root / "wiki")
        if _exists(root / "wiki.old"):
            safe_delete(root, root / "wiki.old")
    except OSError as error:
        raise SbError(ErrorCode.IO_ERROR, 1, str(error)) from error
    return {"pages": len(items) + 1, "items": items, "warnings": warnings, "errors": errors}
