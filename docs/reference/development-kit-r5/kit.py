#!/usr/bin/env python3
"""Very Simple package helper. Never touches external providers or product data.

Stdlib-only: help, feature inventory, structural offline checks, append-only local feedback.
It is *not* the Second Brain or GenericDev application implementation.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / ".kit_state"
FEEDBACK = STATE_DIR / "feedback.jsonl"
LOCK = STATE_DIR / "feedback.lock"
ZERO_HASH = "0" * 64

def canonical_bytes(record: dict) -> bytes:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def event_digest(event: dict) -> str:
    return hashlib.sha256(canonical_bytes({k:v for k,v in event.items() if k != "event_hash"})).hexdigest()

@contextmanager
def journal_lock():
    """Single local process writer. Stale lock needs manual inspection, never auto-steal."""
    STATE_DIR.mkdir(exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError("feedback locked; check existing writer before manually clearing stale lock") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"pid": os.getpid(), "at": utc_now()}))
            fh.flush(); os.fsync(fh.fileno())
        yield
    finally:
        LOCK.unlink(missing_ok=True)



def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_events() -> list[dict]:
    if not FEEDBACK.exists():
        return []
    result: list[dict] = []
    previous = ZERO_HASH
    with FEEDBACK.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            try:
                if not line.strip():
                    raise ValueError("blank line")
                event = json.loads(line)
                if not isinstance(event, dict) or not event.get("id") or not event.get("event"):
                    raise ValueError("required keys missing")
                if (event.get("seq") != i or event.get("prev_hash") != previous
                    or event.get("event_hash") != event_digest(event)):
                    raise ValueError("sequence/hash chain invalid")
                result.append(event)
                previous = event["event_hash"]
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Corrupted feedback log at line {i}: {exc}") from exc
    return result


def latest(events: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    transitions = {
        "CLOSE_PROPOSED": ({"OPEN", "CLOSE_REQUESTED"}, "CLOSE_REQUESTED"),
        "CLOSE_APPROVED": ({"CLOSE_REQUESTED"}, "CLOSED"),
        "REOPENED": ({"CLOSED"}, "OPEN"),
    }
    required_fields = {
        "CREATED": ("at", "kind", "title", "note", "creator"),
        "NOTED": ("at", "kind", "note"),
        "CLOSE_PROPOSED": ("at", "release", "regression", "observation", "lesson", "evidence"),
        "CLOSE_APPROVED": ("at", "reviewer", "evidence"),
        "REOPENED": ("at", "reason"),
    }
    for e in events:
        name, key = e["event"], e["id"]
        if name not in required_fields or any(
                not isinstance(e.get(field), str) or not e[field].strip()
                for field in required_fields[name]):
            raise ValueError(f"invalid/blank fields for {name}: {key}")
        if name == "CREATED":
            if key in out:
                raise ValueError(f"duplicate CREATED for id {key}")
            out[key] = dict(e, status="OPEN", creator=e.get("creator", "user"))
            out[key]["last_event"] = e
        else:
            if key not in out:
                raise ValueError(f"event without original CREATED: {key}")
            old = out[key]
            if name == "NOTED":
                # Notes update history, not closure state.
                if old["status"] == "CLOSED":
                    raise ValueError(f"cannot note CLOSED item: {key}; reopen first")
            else:
                if name not in transitions or old["status"] not in transitions[name][0]:
                    raise ValueError(f"invalid transition {old['status']} -> {name} ({key})")
                if name == "CLOSE_APPROVED" and e.get("reviewer") == old.get("creator"):
                    raise ValueError(f"creator cannot self-approve: {key}")
                old["status"] = transitions[name][1]
            old["last_event"] = e
    return out


def append_event(event: dict) -> None:
    """Write a locally verified, hash-linked JSONL event under O_EXCL lock.

    This is tamper *detection*, NOT authenticity: without external anchors an
    attacker with write access can rewrite all hashes. The cloud has no CAS.
    """
    with journal_lock():
        prior = read_events()
        latest(prior)
        if event["event"] == "CREATED" and event["id"] in latest(prior):
            raise ValueError("duplicate feedback ID")
        if event["event"] != "CREATED" and event["id"] not in latest(prior):
            raise ValueError("unknown feedback ID")
        event["seq"] = len(prior) + 1
        event["prev_hash"] = prior[-1]["event_hash"] if prior else ZERO_HASH
        event["event_hash"] = event_digest(event)
        # Validate transition before saving, otherwise an invalid event could
        # leave the only journal in an unusable state.
        latest(prior + [event])
        data = canonical_bytes(event) + b"\n"
        with FEEDBACK.open("ab") as f:
            f.write(data)
            f.flush(); os.fsync(f.fileno())


def feedback_command(a: argparse.Namespace) -> int:
    if a.fb_action == "add":
        id_ = "FB-" + str(uuid.uuid4())
        append_event({"id": id_, "event": "CREATED", "at": utc_now(), "kind": a.kind,
                      "title": a.title, "note": a.note, "creator": a.creator})
        print(f"CREATED {id_} | OPEN | {a.title}")
        return 0
    events = read_events()
    records = latest(events)
    if a.fb_action == "verify":
        print(json.dumps({"status": "PASS", "events": len(events), "records": len(records),
                          "last_hash": events[-1]["event_hash"] if events else None,
                          "scope": "LOCAL_APPEND_CHAIN_ONLY_NOT_AUTHENTICATION"}))
        return 0
    if a.fb_action == "list":
        selected = sorted(records.items())
        if a.json:
            print(json.dumps([{"id": ident, "status": x["status"], "kind": x.get("kind"),
                               "title": x.get("title")} for ident, x in selected], ensure_ascii=False))
        else:
            for ident, x in selected:
                print(f"{ident} | {x['status']} | {x.get('kind','')} | {x.get('title','')}")
            if not selected:
                print("EMPTY: feedback journal has no records")
        return 0
    if a.id not in records:
        print(f"ERROR: unknown feedback id: {a.id}", file=sys.stderr)
        return 3
    entry = records[a.id]
    if a.fb_action == "show":
        data = [e for e in events if e["id"] == a.id]
        print(json.dumps({"id": a.id, "status": entry["status"], "events": data},
                         ensure_ascii=False, indent=2))
        return 0
    if a.fb_action == "note":
        if entry["status"] == "CLOSED":
            print("ERROR: reopen a CLOSED item before updating", file=sys.stderr)
            return 3
        append_event({"id": a.id, "event": "NOTED", "at": utc_now(),
                      "kind": a.kind, "note": a.note, "ref": a.ref or ""})
        print(f"NOTED {a.id} | {a.kind}")
        return 0
    if a.fb_action == "propose-close":
        if entry["status"] not in {"OPEN", "CLOSE_REQUESTED"}:
            print("ERROR: only OPEN items may request closure", file=sys.stderr)
            return 3
        append_event({"id": a.id, "event": "CLOSE_PROPOSED", "at": utc_now(),
                      "release": a.release, "regression": a.regression, "observation": a.observation,
                      "lesson": a.lesson, "evidence": a.evidence})
        print(f"CLOSE_REQUESTED {a.id} — requires independent review")
        return 0
    if a.fb_action == "approve-close":
        if entry["status"] != "CLOSE_REQUESTED":
            print("ERROR: close proposal missing", file=sys.stderr)
            return 3
        if a.reviewer == entry.get("creator", "user"):
            print("ERROR: reviewer must be different from creator", file=sys.stderr)
            return 5
        append_event({"id": a.id, "event": "CLOSE_APPROVED", "at": utc_now(),
                      "reviewer": a.reviewer, "evidence": a.evidence})
        print(f"CLOSED {a.id} — reviewer attestation recorded, not independently authenticated")
        return 0
    if a.fb_action == "reopen":
        if entry["status"] != "CLOSED":
            print("ERROR: only CLOSED items may reopen", file=sys.stderr)
            return 3
        append_event({"id": a.id, "event": "REOPENED", "at": utc_now(), "reason": a.reason})
        print(f"REOPENED {a.id}")
        return 0
    return 2

def catalog_command(a: argparse.Namespace) -> int:
    rows = read_csv(ROOT / "catalog/FEATURE_INVENTORY.csv")
    if a.profile != "all":
        rows = [x for x in rows if x["profile"] == a.profile]
    if a.id:
        rows = [x for x in rows if x["feature_id"] == a.id]
    if a.find:
        needle = a.find.casefold()
        rows = [x for x in rows if needle in (x["feature_id"] + " " + x["description"] + " " + x["category"]).casefold()]
    if a.summary:
        counts: dict[str, int] = {}
        for x in rows:
            counts[x["profile"]] = counts.get(x["profile"], 0) + 1
        print(json.dumps({"profiles": counts, "total": len(rows), "product_implementation": "NOT_IMPLEMENTED", "product_tests": "NOT_RUN"}, ensure_ascii=False))
        return 0
    if a.limit is not None:
        if a.limit < 1:
            raise ValueError("--limit must be positive")
        rows = rows[:a.limit]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{r['feature_id']} | {r['profile']} | {r['description'][:95]} | {r['implementation']} | {r['test_execution']}")
    if not rows:
        print("No matching planned requirement", file=sys.stderr)
        return 3
    return 0

def verify_command(a: argparse.Namespace) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    checks = {}
    files = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
             if p.is_file() and not p.relative_to(ROOT).parts[0].startswith(".kit_state")
             and "__pycache__" not in p.relative_to(ROOT).parts and p.suffix != ".pyc"
             and p.relative_to(ROOT).as_posix() != "PACKAGE_MANIFEST.sha256"}
    expected = {}
    man = ROOT / "PACKAGE_MANIFEST.sha256"
    if not man.is_file():
        errors.append("root manifest absent")
    else:
        for lineno, line in enumerate(man.read_text(encoding="utf-8").splitlines(), start=1):
            try:
                digest, name = line.split("\t", 1)
                parts = Path(name).parts
                if (name in expected or len(digest) != 64 or not all(c in "0123456789abcdef" for c in digest)
                    or Path(name).is_absolute() or '..' in parts or '\\' in name or ':' in name):
                    raise ValueError("duplicate name, invalid path or digest")
                expected[name] = digest
            except ValueError:
                errors.append(f"manifest invalid line {lineno}")
        if set(expected) != files:
            errors.append(f"manifest paths differ (missing={len(files-set(expected))}, stale={len(set(expected)-files)})")
        for name, digest in expected.items():
            target = ROOT / name
            if not target.is_file() or target.is_symlink() or sha256_file(target) != digest:
                errors.append(f"manifest mismatch: {name}")
    checks["manifest_entries"] = len(expected)
    features = read_csv(ROOT / "catalog/FEATURE_INVENTORY.csv")
    ids = [(r.get("profile"), r.get("feature_id")) for r in features]
    if len(ids) != len(set(ids)):
        errors.append("duplicate profile/id")
    if not features:
        errors.append("empty feature inventory")
    for r in features:
        if not (ROOT / r["contract"]).is_file() or not (ROOT / r["test_catalog"]).is_file():
            errors.append(f"missing feature reference: {r['feature_id']}")
        if r["implementation"] != "NOT_IMPLEMENTED" or r["test_execution"] != "NOT_RUN":
            errors.append(f"unverified product completion claim: {r['feature_id']}")
    # Inventory must be a generated view of canonical source catalogs, not a second SSOT.
    g = read_csv(ROOT / 'profiles/generic/quality/requirements.csv')
    b = read_csv(ROOT / 'profiles/secondbrain/traceability/requirements_to_tests.csv')
    source_map = {("generic", r['id']): (r['statement'], r['test_id']) for r in g}
    source_map.update({("secondbrain", r['requirement_id']): (r['requirement_text'], r['planned_test_id']) for r in b})
    if len(source_map) != len(features):
        errors.append("canonical requirements and generated inventory count mismatch")
    for f in features:
        pair = (f['profile'], f['feature_id'])
        if source_map.get(pair) != (f['description'], f['test_id']):
            errors.append(f"canonical requirement drift: {f['feature_id']}")
    # Explicit one-to-one reference check (not merely file-exists).
    gtests = read_csv(ROOT / "profiles/generic/quality/test_catalog.csv")
    gtest_map = {r["requirement_id"]: r["id"] for r in gtests}
    if len(gtest_map) != len(gtests):
        errors.append("generic test catalog duplicate requirement IDs")
    for r in g:
        if gtest_map.get(r["id"]) != r["test_id"]:
            errors.append(f"missing/mismatched test mapping: {r['id']}")
    if any(not r["planned_test_id"] or not r["design_reference"] for r in b):
        errors.append("secondbrain requirement/test/design reference incomplete")
    scenarios = read_csv(ROOT / "catalog/SCENARIOS.csv")
    if not scenarios or any(s["execution_status"] != "NOT_RUN" for s in scenarios):
        errors.append("bad scenario/test plan state")
    scenario_ids = [s["scenario_id"] for s in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        errors.append("duplicate scenario ID")
    for sc in scenarios:
        if (sc["profile"] not in {"generic", "secondbrain"}
            or sc["test_tier"] not in {"T0", "T1", "T2", "T3", "T4"}
            or sc["gate"] not in {f"G{i}" for i in range(8)}
            or not sc["expected"].strip() or not sc["fault_or_scenario"].strip()):
            errors.append(f"invalid scenario row: {sc['scenario_id']}")
    checks.update(features=len(features), scenarios=len(scenarios), product_status="PRE_TDD")
    # Do not execute any bundled checker from an altered/unknown package.
    if not errors:
        for root_name, script in [('generic', 'tools/design_lint.py'), ('secondbrain', 'tools/static_design_audit.py'), ('secondbrain','tools/r4_independent_audit.py')]:
            path = ROOT / 'profiles' / root_name
            try:
                proc = subprocess.run([sys.executable, script], cwd=path, capture_output=True, text=True, timeout=60)
                label = f"{root_name}/{Path(script).stem}"
                checks[label] = "PASS" if proc.returncode == 0 else "FAIL"
                if proc.returncode != 0:
                    errors.append(f"{label} failed ({proc.stderr[-400:]})")
            except (subprocess.TimeoutExpired, OSError) as exc:
                errors.append(f"{root_name}/{script}: {exc}")
    if " " in str(ROOT) or any(ord(c) > 127 for c in str(ROOT)):
        warnings.append("external Node/Windows/CLI providers may have path limitations: require T3 probe, no auto rename")
    report = {"status": "PASS" if not errors else "FAIL", "scope": "DESIGN_STATIC_AND_KIT_ONLY",
              "checks": checks, "warnings": warnings, "errors": errors,
              "not_run": ["product TDD", "cloud restore", "live AI provider", "security pen test", "pip/winget release"]}
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status']} | {len(features)} planned features | {len(scenarios)} planned scenarios | product tests NOT_RUN")
        for item in errors:
            print("ERROR:", item)
        for item in warnings:
            print("WARN:", item)
    return 0 if not errors else 3


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Very Simple design kit (not product CLI)", prog="kit", epilog="Examples: kit help | kit catalog --summary | kit verify | kit feedback add --kind bug --title X --note Y")
    commands = p.add_subparsers(dest="command", required=True)
    h = commands.add_parser("help", help="Show quick commands or detailed command help")
    h.add_argument("topic", nargs="?", choices=["catalog", "verify", "feedback"])
    c = commands.add_parser("catalog", help="Read complete planned feature registry")
    c.add_argument("--summary", action="store_true", help="Show per-profile counts")
    c.add_argument("--id", help="Find exact requirement ID e.g. GD-001")
    c.add_argument("--find", help="Case-insensitive substring search")
    c.add_argument("--limit", type=int, help="Maximum matching items displayed")
    c.add_argument("--json", action="store_true", help="JSON records for AI tools")
    c.add_argument("--profile", choices=["all", "generic", "secondbrain"], default="all")
    v = commands.add_parser("verify", help="Offline static checks only, no product tests")
    v.add_argument("--json", action="store_true", help="Machine-readable result")
    fb = commands.add_parser("feedback", help="Local single-writer improvement log")
    actions = fb.add_subparsers(dest="fb_action", required=True)
    add = actions.add_parser("add", help="Record error, incident, idea, lesson, or question")
    add.add_argument("--kind", choices=["task", "bug", "error", "incident", "idea", "lesson", "question"], required=True)
    add.add_argument("--title", required=True)
    add.add_argument("--note", required=True)
    add.add_argument("--creator", default="user", help="Creator ID; reviewer must differ")
    list_cmd = actions.add_parser("list", help="List current statuses")
    list_cmd.add_argument("--json", action="store_true")
    show = actions.add_parser("show", help="Show all history events for one ID")
    show.add_argument("id")
    note = actions.add_parser("note", help="Record progress, error, evidence, lesson, or decision")
    note.add_argument("id")
    note.add_argument("--kind", choices=["progress", "error", "evidence", "lesson", "decision"], required=True)
    note.add_argument("--note", required=True)
    note.add_argument("--ref", help="Optional external issue/commit/test URL or ID")
    actions.add_parser("verify", help="Validate local JSONL chain and transitions")
    propose = actions.add_parser("propose-close", help="Provide release, regression, observation, lesson and evidence")
    propose.add_argument("id")
    for opt in ["release", "regression", "observation", "lesson", "evidence"]:
        propose.add_argument("--" + opt, required=True)
    close = actions.add_parser("approve-close", help="Independent review attestation; no cryptographic claim")
    close.add_argument("id"); close.add_argument("--reviewer", required=True); close.add_argument("--evidence", required=True)
    reopen = actions.add_parser("reopen", help="Reopen after recurrence")
    reopen.add_argument("id");reopen.add_argument("--reason", required=True)
    return p


def main() -> int:
    p = parser(); a = p.parse_args()
    if a.command == "help":
        if a.topic:
            # argparse owns authoritative recursive help, not a second hand-kept catalog.
            sub = parser(); sub.parse_args([a.topic, "--help"])
        else:
            p.print_help()
        return 0
    try:
        if a.command == "catalog": return catalog_command(a)
        if a.command == "verify": return verify_command(a)
        if a.command == "feedback": return feedback_command(a)
    except (ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
