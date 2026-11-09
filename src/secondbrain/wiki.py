"""Deterministic wiki tier (DESIGN section 7): wiki/ is a pure function of raws/."""
import json
import os
from pathlib import Path
import re
import string
import unicodedata

from .errors import ErrorCode, SbError
from .fsutil import checked_path, esc, percent_encode, safe_delete, write_text
from .ledger import scan
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


_DEST = re.compile(r"https?://|[^:&\\/?#]*(?:[/?#]|$)", re.I)  # http(s), or relative: no scheme/entity/escape before the first "/?#"
_INLINE_LINK = re.compile(r"(\]\(\s*)([^\s)]*)")
_LINK_DEFINITION = re.compile(r"(\[(?:[^\]\\]|\\.)+\]:\s*)(\S+)")
_QUOTE = re.compile(r"[ ]{0,3}(?:> ?)*")


def _safe_dest(match):
    dest = match.group(2)
    return match.group(0) if _DEST.match(dest) else match.group(1) + "#"


def _quote_safe(line):
    """Escape ">" except in the leading blockquote marker."""
    head = _QUOTE.match(line).group()
    return head + line[len(head):].replace(">", "&gt;")


_FENCE = re.compile(r"(`{3,}|~{3,})(.*)")  # column 0 only: such a line is never inside a list item or blockquote
_BACKTICKS = re.compile(r"`+")


def _closes(line, mark):
    line = line.rstrip(" \t\r")
    body = line.lstrip(" ")
    return len(line) - len(body) <= 3 and len(body) >= len(mark) and set(body) == {mark[0]}


def _mask_block(text, keep):
    """One blank-line-delimited block: backtick runs are paired across all its lines (as the renderer does).

    Only a span whose two runs share a line (outside a table row) is masked. A run left unmatched means the
    renderer may pair differently, so then nothing in the block is masked.
    """
    spans, i = [], 0
    while i < len(text):
        if text[i] == "\\" and text[i + 1:i + 2] in tuple(string.punctuation):
            i += 2
        elif text[i] == "`":
            size = _BACKTICKS.match(text, i).end() - i
            closer = next((m.end() for m in _BACKTICKS.finditer(text, i + size) if m.end() - m.start() == size), None)
            if closer is None:
                return text
            spans.append((i, closer))
            i = closer
        else:
            i += 1
    out, last = [], 0
    for start, end in spans:
        line = text[text.rfind("\n", 0, start) + 1:(text.find("\n", end) % (len(text) + 1))]  # find()==-1 -> len(text)
        if "\n" not in text[start:end] and "|" not in line:
            out += [text[last:start], keep(text[start:end])]
            last = end
    return "".join(out) + text[last:]


def _mask_code(text):
    """Fenced blocks and code spans, which are inert, replaced by NUL placeholders; returns (text, kept).

    Conservative on purpose: only column-0 fences that are closed, and same-line spans, count as code.
    Everything else (indented or nested fences, an unclosed fence and all that follows) is escaped like prose,
    so the renderer can never see code where this pass saw prose.
    """
    kept, out, block, lines, i = [], [], [], text.split("\n"), 0

    def keep(chunk):
        kept.append(chunk)
        return f"\x00{len(kept) - 1}\x00"

    def flush():
        if block:
            out.append(_mask_block("\n".join(block), keep))
            block.clear()
    while i < len(lines):
        opening = _FENCE.fullmatch(lines[i])
        end = i + 1
        if opening and not (opening[1][0] == "`" and "`" in opening[2]):
            while end < len(lines) and not _closes(lines[end], opening[1]):
                end += 1
            if end == len(lines):  # unclosed: escape this line and everything after it
                flush()
                out.extend(lines[i:])
                break
            flush()
            out.append(keep("\n".join(lines[i:end + 1])))
            i = end + 1
        elif lines[i].strip(" \t") == "":
            flush()
            out.append(lines[i])
            i += 1
        else:
            block.append(lines[i])
            i += 1
    flush()
    return "\n".join(out), kept


def safe_markdown(text):
    """Untrusted Markdown made inert: no raw HTML, no image embeds, only http(s)/relative link targets.

    Nothing is fetched. Entities are used (not backslashes) so a hostile backslash cannot undo them.
    Fenced code blocks and code spans are left byte-identical (they are inert and entities would show).
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "�")  # CR is a line ending for the renderer
    text, kept = _mask_code(text)
    text = text.replace("<", "&lt;").replace("![", "&#33;[")
    text = "\n".join(_quote_safe(line) for line in text.split("\n"))
    text = _LINK_DEFINITION.sub(_safe_dest, _INLINE_LINK.sub(_safe_dest, text))
    return re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m[1])], text)


def tags(meta):
    """Deterministic tags: class, extension, collected year-month (all derived from meta)."""
    found = [f"collected-{meta['ingested_at'][:7]}"]
    if meta["class"]:
        found.append(f"class-{meta['class']}")
    found.append("ext-" + (meta["ext"][1:] if re.fullmatch(r"\.[a-z0-9]{1,16}", meta["ext"]) else "other"))
    return sorted(found)


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


def _summary(meta):
    """Current summary revision, or None (the validator guarantees a non-empty history when llm is set)."""
    return meta["llm"]["summary"][-1] if meta["llm"] else None


def unit_counts(meta):
    """Cumulative unit counts: approved = not pending, recorded = recorded or verified."""
    units = list(meta["ocr"]["units"].values())
    return {"total": len(units), "approved": sum(u["status"] != "pending" for u in units),
            "recorded": sum(u["status"] in ("recorded", "verified") for u in units),
            "verified": sum(u["status"] == "verified" for u in units)}


def _coverage(meta):
    return None if meta["triage"] is None else meta["triage"]["coverage"]["state"]


def _ocr_cell(meta):
    disposition = meta["ocr"]["disposition"]
    if disposition == "declined":
        return "declined"
    counts = unit_counts(meta)
    if disposition == "approved":
        return f"{counts['approved']}/{counts['total']} approved, {counts['recorded']} recorded, {counts['verified']} verified"
    return "none"


def banner(meta):
    """Banner text per section 7 table; empty string means none."""
    cls, state, reason = meta["class"], meta["state"], meta["reason"]
    coverage = _coverage(meta)
    extra = f", coverage {coverage}" if coverage not in (None, "complete") else ""
    if state == "unsupported":
        return f"unsupported: {_line(reason)}"
    if state == "failed":
        return f"failed: {_line(meta['error']['code'])}, {meta['error']['date']}"
    if cls == "unknown":
        return f"not inspected: {_line(reason)}" + (", declined" if state == "ready" else "")
    if cls == "text-only":
        return "" if meta["has_native_text"] else "empty document"
    counts = unit_counts(meta)
    if state == "awaiting-approval":
        return f"OCR pending approval: {counts['total']} units, coverage {coverage if coverage else 'n/a'}"
    if state == "ocr-in-progress":
        return (f"OCR in progress: {counts['approved']}/{counts['total']} approved, "
                f"{counts['recorded']} recorded, {counts['verified']} verified")
    if meta["ocr"]["disposition"] == "declined":
        return "OCR declined" + extra
    return f"OCR verified: {counts['total']} units" + extra


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
             f"[Original file](../../raws/{meta['id']}/src/{percent_encode(meta['filename'])})\n\n",
             "Tags: " + ", ".join(f"[{t}](../tags/{t}.md)" for t in tags(meta)) + " · [Index](../index.md)\n\n"]
    text = banner(meta)
    if text:
        parts += [fence(text), "\n"]
    revision = _summary(meta)
    if revision:
        body = (item.path / revision["file"]).read_bytes().decode("utf-8")
        parts += ["## Summary\n\n", fence(body), "\n"]
    if meta["state"] != "unsupported" and (meta["state"] != "failed" or meta["conversion"] is not None):
        parts += ["## Transcript\n\n", safe_markdown(view(item))]  # last section: an unclosed fence cannot swallow more
    return "".join(parts).rstrip("\n") + "\n"


def tag_members(items):
    """{tag: [meta, ...]} in item order."""
    members = {}
    for item in items:
        for tag in tags(item.meta):
            members.setdefault(tag, []).append(item.meta)
    return members


def tag_page(tag, metas):
    """Links back to the index and to every source page that carries the tag."""
    return "\n".join([f"# Tag: {tag}", "", "[Index](../index.md)", "",
                      *(f"- [{esc(m['filename_nfc'])}](../sources/{m['id']}.md)" for m in metas)]) + "\n"


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
    members = tag_members(items)
    if members:
        lines += ["", "## Tags", "", *(f"- [{tag}](tags/{tag}.md) ({len(members[tag])})" for tag in sorted(members))]
    return "\n".join(lines) + "\n"


def build(root):
    """Rebuild wiki/ from raws/. Returns {pages, items, warnings, errors}."""
    root = Path(root)
    try:
        recover(root)
        items, warnings, errors = scan(root)
        items.sort(key=lambda i: (i.meta["filename_nfc"].casefold(), i.meta["id"]))
        tmp = root / "wiki.tmp"
        write_text(tmp / "index.md", index_page(items))
        for item in items:
            write_text(tmp / "sources" / f"{item.meta['id']}.md", source_page(item))
        members = tag_members(items)
        for tag, metas in members.items():
            write_text(tmp / "tags" / f"{tag}.md", tag_page(tag, metas))
        if _exists(root / "wiki"):
            os.rename(root / "wiki", root / "wiki.old")
        os.rename(tmp, root / "wiki")
        if _exists(root / "wiki.old"):
            safe_delete(root, root / "wiki.old")
    except OSError as error:
        raise SbError(ErrorCode.IO_ERROR, 1, str(error)) from error
    return {"pages": len(items) + len(members) + 1, "items": items, "warnings": warnings, "errors": errors}
