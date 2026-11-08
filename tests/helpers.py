"""Synthetic committed items shared by later command tests."""
from hashlib import sha256
from pathlib import Path
import json
import unicodedata

DATE = "2026-11-09T00:00:00Z"
DEFAULT = object()


def provenance(method="convert", peer=None):
    convert = method == "convert"
    params = {"charset": None, "extract_media": False} if convert else {"prompt_rev": "verify-v1" if method == "ocr-verify" else "llm-v1" if method == "summary" else "ocr-v1"}
    if method == "ocr-vision":
        params.update(dpi=200, unit_file="u0001.png")
    return {"tool": "markitdown-gc" if convert else "peerhub", "version": "0.3.5" if convert else None,
            "method": method, "peer": None if convert else peer or "cx", "model": None if convert else "synthetic-model",
            "date": DATE, "params": params}


def save_meta(item):
    (item.path / "meta.json").write_text(json.dumps(item.meta, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def make_item(root, *, state="ready", classification=DEFAULT, filename=None, text=DEFAULT, statuses=None):
    from secondbrain.ledger import Item
    if classification is DEFAULT:
        classification = {"failed": None, "unsupported": "unsupported", "awaiting-approval": "mixed", "ocr-in-progress": "mixed"}.get(state, "text-only")
    if filename is None:
        filename = "source" + {"ocr-required": ".pdf", "mixed": ".pdf", "unknown": ".md", "unsupported": ".xyz", None: ".pdf"}.get(classification, ".txt")
    raster = Path(filename).suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
    if text is DEFAULT:
        text = None if raster or classification in {None, "unsupported"} else "" if classification == "ocr-required" else "Synthetic text 123."
    source = (filename + " synthetic original").encode("utf-8")
    digest = sha256(source).hexdigest()
    path = Path(root) / "raws" / digest[:16]
    (path / "src").mkdir(parents=True)
    (path / "src" / filename).write_bytes(source)
    conversion = None
    if text is not None:
        (path / "converted.md").write_bytes(text.encode("utf-8"))
        conversion = {"activity": provenance(), "sha256": sha256(text.encode("utf-8")).hexdigest(), "media": []}
    units = {}
    if classification in {"ocr-required", "mixed"}:
        statuses = statuses or (["verified"] if state == "ready" else ["approved"] if state == "ocr-in-progress" else ["pending"])
        for n, status in enumerate(statuses, 1):
            key = f"u{n:04}"
            attempts = []
            if status in {"recorded", "verified"}:
                body = f"Verified synthetic OCR {n}."
                file = f"ocr/{key}.a1.md"
                (path / "ocr").mkdir(exist_ok=True)
                (path / file).write_bytes(body.encode("utf-8"))
                attempts = [{"n": 1, "file": file, "sha256": sha256(body.encode("utf-8")).hexdigest(),
                             "recorded": provenance("ocr-vision", "cx"), "verified": provenance("ocr-verify", "cc") if status == "verified" else None,
                             "result": "ok" if status == "verified" else None}]
            if attempts:
                attempts[0]["recorded"]["params"]["unit_file"] = key + ".png"
            units[key] = {"source": "self" if raster else f"p{n}", "kind": "raster" if raster else "page", "status": status, "attempts": attempts}
    triage = None
    if Path(filename).suffix.lower() in {".pdf", ".docx", ".pptx", ".xlsx", ".hwp", ".hwpx", ".md", ".html", ".htm"} and classification not in {None, "unsupported"}:
        triage = {"decision": "review" if units else "unknown" if classification == "unknown" else "no_candidates",
                  "coverage": {"state": "complete" if classification != "unknown" else "none", "pages_total": len(units) or 1, "pages_inspected": len(units) or 1},
                  "scope": "inspected", "image_occurrences": len(units), "candidates": [
                      {"id": u["source"], "kind": "page", "page": n, "priority": "high"} for n, u in enumerate(units.values(), 1)],
                  "issues": ["media_not_inspected"] if classification == "unknown" else []}
    disposition = "approved" if any(u["status"] != "pending" for u in units.values()) else "declined" if state == "ready" and classification == "unknown" else "none"
    meta = {"schema": 1, "id": digest[:16], "sha256": digest, "size": len(source), "ext": Path(filename).suffix.lower(),
            "filename": filename, "filename_nfc": unicodedata.normalize("NFC", filename), "aliases": [], "ingested_at": DATE,
            "class": classification, "reason": "SyntheticError" if state == "failed" else "media_not_inspected" if classification == "unknown" else "extension_not_allowed" if classification == "unsupported" else "raster" if raster else None,
            "state": state, "conversion": conversion, "triage": triage, "has_native_text": None if text is None else bool(text),
            "ocr": {"disposition": disposition, "large_ack": len(units) > 20 and disposition == "approved", "units": units},
            "llm": None, "error": {"code": "SyntheticError", "message": "synthetic failure", "date": DATE} if state == "failed" else None}
    item = Item(path, meta)
    save_meta(item)
    return item


def add_summary(item, text="Synthetic summary."):
    file = "llm/summary.a1.md"
    (item.path / "llm").mkdir(exist_ok=True)
    (item.path / file).write_bytes(text.encode("utf-8"))
    from secondbrain.transcript import source_digest
    item.meta["llm"] = {"summary": [{"n": 1, "file": file, "sha256": sha256(text.encode("utf-8")).hexdigest(),
                                 "source_digest": source_digest(item), "activity": provenance("summary", "cx")}]}
    save_meta(item)
    return item
