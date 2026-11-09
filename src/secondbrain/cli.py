"""`sb` command line (DESIGN section 8): argparse, JSON envelope, exit precedence, human output.

The command-by-state matrix (section 4) is enforced by the command modules themselves
(they reject with `state_not_allowed` before any write); this module only wires them up.
"""
import argparse
import json
from pathlib import Path
import sys

from . import ingest, llm, ocr, wiki
from .errors import ErrorCode, SbError, WarningCode
from .fsutil import resolve_root
from .ledger import load_item

STATES = ("ready", "awaiting-approval", "ocr-in-progress", "unsupported", "failed")


class UsageError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def build_parser():
    common = Parser(add_help=False)  # --root/--json also accepted after the command
    common.add_argument("--root", default=argparse.SUPPRESS, help="data root (default: $SB_ROOT, else the current folder)")
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="print exactly one JSON object")
    parser = Parser(prog="sb", description="SecondBrain: inbox -> raws -> wiki", parents=[common])
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")

    def leaf(group, name, help_text):
        return group.add_parser(name, parents=[common], help=help_text)

    ingest_p = leaf(commands, "ingest", "move files out of inbox/ and classify them")
    ingest_p.add_argument("--retry", action="store_true", help="retry failed items")
    ingest_p.add_argument("--charset", help="text encoding of plain-text files, e.g. cp949")
    leaf(commands, "status", "list every item (read-only)")

    ocr_p = leaf(commands, "ocr", "OCR approval workflow")
    ocr_actions = ocr_p.add_subparsers(dest="action", required=True, metavar="action")
    approve = leaf(ocr_actions, "approve", "approve the next units and prepare scratch")
    approve.add_argument("id")
    approve.add_argument("--yes-large", action="store_true", help="required once when an item has more than 20 units")
    approve.add_argument("--dpi", type=int, help="render resolution (default 200)")
    leaf(ocr_actions, "decline", "decline OCR for the whole item").add_argument("id")
    record = leaf(ocr_actions, "record", "record peer transcriptions")
    record.add_argument("id")
    record.add_argument("--peer", required=True)
    record.add_argument("--model", required=True)
    record.add_argument("--dpi", type=int, help="dpi of the images (default: the dpi used at approve, else 200)")
    verify = leaf(ocr_actions, "verify", "record the second peer's verification")
    verify.add_argument("id")
    verify.add_argument("--peer", required=True)
    verify.add_argument("--model", required=True)
    verify.add_argument("--ok", action="append", metavar="L", help="comma-separated units that match")
    verify.add_argument("--mismatch", action="append", metavar="L", help="comma-separated units that differ")

    wiki_p = leaf(commands, "wiki", "generated wiki")
    leaf(wiki_p.add_subparsers(dest="action", required=True, metavar="action"), "build", "rebuild wiki/ from raws/")

    llm_p = leaf(commands, "llm", "optional LLM summary tier")
    llm_actions = llm_p.add_subparsers(dest="action", required=True, metavar="action")
    leaf(llm_actions, "prepare", "write the summary prompt").add_argument("id")
    leaf(llm_actions, "accept", "validate and record a peer summary").add_argument("id")
    return parser


# ------------------------------------------------------------------ projections

def _note(note):
    code = str(note["code"])
    return {"code": code, "id": note.get("id"), "path": note.get("path"), "message": note.get("message") or code}


def row(meta, result):
    triage = meta["triage"]
    return {"id": meta["id"], "filename": meta["filename"], "filename_nfc": meta["filename_nfc"], "ext": meta["ext"],
            "class": meta["class"], "state": meta["state"], "reason": meta["reason"],
            "disposition": meta["ocr"]["disposition"],
            "pages_total": triage["coverage"]["pages_total"] if triage else None,
            "image_occurrences": triage["image_occurrences"] if triage else None,
            "coverage": {"state": triage["coverage"]["state"] if triage else None, "scope": triage["scope"] if triage else None},
            "units": wiki.unit_counts(meta), "summary": meta["llm"] is not None, "result": result}


def corrupt_row(item_id, result):
    return {"id": item_id, "filename": None, "filename_nfc": None, "ext": None, "class": None, "state": None,
            "reason": None, "disposition": None, "pages_total": None, "image_occurrences": None,
            "coverage": {"state": None, "scope": None}, "units": None, "summary": None, "result": result}


def _row_for(root, item_id, result):
    try:
        return row(load_item(Path(root) / "raws" / item_id).meta, result)
    except SbError:
        return corrupt_row(item_id, "corrupt")


def _relative(root, path):
    return Path(path).relative_to(root).as_posix()


def _stale_work(root, item):
    work = root / "work" / item.meta["id"]
    if not work.is_dir() or item.meta["state"] == "ocr-in-progress":
        return None
    leftovers = [p.name for p in work.iterdir() if not (p.name == "llm" and item.meta["state"] == "ready")]
    if not leftovers:
        return None
    return {"code": str(WarningCode.STALE_WORK), "id": item.meta["id"], "path": _relative(root, work),
            "message": "Scratch left over; the next verify or approve cleans it"}


def _staged_collisions(root):
    warnings = []
    for directory in sorted((root / "raws" / ".staging").glob("tmp-*")):
        try:
            stage = json.loads((directory / "stage.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(stage, dict) and stage.get("collision") is True:
            identity = stage.get("identity") if isinstance(stage.get("identity"), dict) else {}
            warnings.append({"code": str(WarningCode.STAGED_COLLISION), "id": identity.get("id"),
                             "path": _relative(root, directory), "message": "Staged file kept for the operator to resolve"})
    return warnings


def run_status(root):
    loaded, warnings, errors = wiki.load_items(root)  # the one ledger scan, shared with `wiki build`
    items = [row(item.meta, "listed") for item in loaded] + [corrupt_row(error["id"], "corrupt") for error in errors]
    warnings = [*warnings, *filter(None, (_stale_work(root, item) for item in loaded)), *_staged_collisions(root)]
    counts = {state: sum(1 for i in items if i["state"] == state) for state in STATES}
    return {"items": items, "warnings": warnings, "errors": errors, "extra": {"counts": counts}, "messages": []}


# ------------------------------------------------------------------ dispatch

def _keys(values):
    return [key.strip() for value in values or [] for key in value.split(",") if key.strip()]


def run_command(args, root):
    command = args.command if args.command in ("ingest", "status") else f"{args.command} {args.action}"
    if command == "status":
        return run_status(root)
    if command == "ingest":
        result = ingest.ingest(root, retry=args.retry, charset=args.charset)
        items = [_row_for(root, entry["id"], entry["result"]) for entry in result["items"]]
        return {"items": items, "warnings": result["warnings"], "errors": result["errors"], "extra": {}, "messages": []}
    if command == "wiki build":
        result = wiki.build(root)
        return {"items": [row(item.meta, "built") for item in result["items"]], "warnings": result["warnings"],
                "errors": result["errors"], "extra": {"pages": result["pages"]}, "messages": []}
    messages = []
    if command == "ocr approve":
        done = ocr.approve(root, args.id, yes_large=args.yes_large, dpi=args.dpi)
        messages = [done["notice"], f"Next: follow {done['commands']}"]
    elif command == "ocr decline":
        done = ocr.decline(root, args.id)
    elif command == "ocr record":
        done = ocr.record(root, args.id, args.peer, args.model, dpi=args.dpi)
    elif command == "ocr verify":
        done = ocr.verify(root, args.id, args.peer, args.model, ok=_keys(args.ok), mismatch=_keys(args.mismatch))
    elif command == "llm prepare":
        done = llm.prepare(root, args.id)
        messages = ["The summary is the operator's judgment call: read it before you trust it.",
                    f"Next: follow {Path(done['prompt']).with_name('COMMANDS.txt')}"]
    else:  # llm accept
        done = llm.accept(root, args.id)
    return {"items": [_row_for(root, done["id"], done["result"])], "warnings": [], "errors": [], "extra": {}, "messages": messages}


# ------------------------------------------------------------------ output

def _sorted(notes):
    return sorted(map(_note, notes), key=lambda n: (n["id"] or "", n["code"], n["path"] or "", n["message"]))


def envelope(command, exit_code, root, items=(), warnings=(), errors=(), extra=None):
    value = {"command": command, "ok": exit_code == 0, "exit": exit_code, "root": str(root),
             "items": sorted(items, key=lambda i: i["id"] or ""), "warnings": _sorted(warnings), "errors": _sorted(errors)}
    value.update(extra or {})
    return value


def _status_lines(env):
    lines = []
    awaiting = []
    for item in env["items"]:
        if item["state"] is None:
            lines.append(f"{item['id']} corrupt")
            continue
        units, coverage = item["units"], item["coverage"]["state"]
        pages = "-" if item["pages_total"] is None else item["pages_total"]
        lines.append(f"{item['id']} {item['state']} {item['class'] or '-'} {pages}/{item['image_occurrences'] or 0} "
                     f"{units['approved']}/{units['recorded']}/{units['verified']}/{units['total']} {coverage or '-'} {item['filename']}")
        if item["state"] == "awaiting-approval":
            awaiting.append(item)
    if awaiting:
        lines += ["", "OCR approval needed:"]
        lines += [f"  {i['id']} {i['filename']} units={i['units']['total']}" + (" LARGE" if i["units"]["total"] > ocr.LARGE else "")
                  for i in awaiting]
    lines += ["", "counts: " + ", ".join(f"{state}={n}" for state, n in env["counts"].items())]
    return lines


def emit(env, as_json, messages=()):
    out, err = sys.stdout, sys.stderr
    if as_json:
        out.write(json.dumps(env, ensure_ascii=False, sort_keys=True) + "\n")
        for message in messages:
            err.write(message + "\n")
    else:
        if env["command"] == "status":
            lines = _status_lines(env)
        else:
            lines = [f"{i['id']} {i['result']} {i['filename']}" if i["filename"] else f"{i['id']} {i['result']}" for i in env["items"]]
            if "pages" in env:
                lines.append(f"pages: {env['pages']}")
        lines += list(messages)
        out.write("\n".join(lines) + ("\n" if lines else ""))
    for kind, notes in (("warning", env["warnings"]), ("error", env["errors"])):
        for note in notes:
            where = " ".join(part for part in (note["id"], note["path"]) if part)
            err.write(f"{kind}: {note['code']}{' ' + where if where else ''}: {note['message']}\n")
    out.flush()
    err.flush()


def _utf8():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass


def _guess(argv, option):
    for n, token in enumerate(argv):
        if token == option and n + 1 < len(argv):
            return argv[n + 1]
        if token.startswith(option + "="):
            return token.split("=", 1)[1]
    return None


def _command_guess(argv):
    """Best-effort command name for a parser failure ("usage" when none is recognizable)."""
    words = [t for t in argv if not t.startswith("-")]
    if words and words[0] in ("ingest", "status"):
        return words[0]
    if words and words[0] in ("wiki", "ocr", "llm"):
        return " ".join(words[:2])
    return "usage"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    _utf8()
    as_json = "--json" in argv
    try:
        args = build_parser().parse_args(argv)
    except UsageError as error:
        root = resolve_root(_guess(argv, "--root"))
        emit(envelope(_command_guess(argv), 2, root, errors=[{"code": str(ErrorCode.USAGE), "id": None, "path": None, "message": str(error)}]), as_json)
        return 2
    as_json = getattr(args, "json", False)  # defaults are SUPPRESSed so either position works
    root = resolve_root(getattr(args, "root", None))
    command = args.command if args.command in ("ingest", "status") else f"{args.command} {args.action}"
    item_id = getattr(args, "id", None)
    try:
        result = run_command(args, root)
    except SbError as error:
        env = envelope(command, error.exit, root, errors=[{"code": error.code, "id": item_id, "path": None, "message": str(error)}])
        emit(env, as_json)
        return env["exit"]
    except OSError as error:
        env = envelope(command, 1, root, errors=[{"code": str(ErrorCode.IO_ERROR), "id": item_id, "path": None, "message": str(error)}])
        emit(env, as_json)
        return 1
    exit_code = 1 if result["errors"] else 0
    env = envelope(command, exit_code, root, result["items"], result["warnings"], result["errors"], result["extra"])
    emit(env, as_json, result["messages"])
    return exit_code
