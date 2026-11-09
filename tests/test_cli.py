"""Slice 8: CLI envelope, exit precedence, command-by-state matrix, status (AT-15, AT-16, AT-34)."""
import json
from pathlib import Path
import shutil

import pytest

import helpers
from secondbrain import cli, ocr
from secondbrain.errors import ErrorCode, WarningCode
from secondbrain.ledger import load_item

FIXTURES = Path(__file__).parent / "fixtures"
SOURCE = (FIXTURES / "reports" / "text--plain.txt.converted.md").read_bytes().decode("utf-8")
CODES = {str(c) for c in ErrorCode} | {str(c) for c in WarningCode}
ENVELOPE = {"command", "ok", "exit", "root", "items", "warnings", "errors"}
ITEM = {"id", "filename", "filename_nfc", "ext", "class", "state", "reason", "disposition", "pages_total",
        "image_occurrences", "coverage", "units", "summary", "result"}
STATES = ["ready", "awaiting-approval", "ocr-in-progress", "unsupported", "failed"]


tree = helpers.tree


def check_envelope(env, code):
    assert ENVELOPE <= set(env) and env["exit"] == code and env["ok"] == (code == 0)
    assert [i["id"] for i in env["items"]] == sorted(i["id"] for i in env["items"])
    for item in env["items"]:
        assert set(item) == ITEM and set(item["coverage"]) == {"state", "scope"}
    for notes in (env["warnings"], env["errors"]):
        assert [(n["id"] or "", n["code"]) for n in notes] == sorted((n["id"] or "", n["code"]) for n in notes)
        for note in notes:
            assert set(note) == {"code", "id", "path", "message"} and note["code"] in CODES


def sb(capsys, root, *argv):
    code = cli.main(["--root", str(root), "--json", *argv])
    captured = capsys.readouterr()
    env = json.loads(captured.out)
    assert captured.out == json.dumps(env, ensure_ascii=False, sort_keys=True) + "\n"  # exactly one object
    check_envelope(env, code)
    return code, env, captured.err


@pytest.fixture
def fake_render(monkeypatch):
    monkeypatch.setattr(ocr, "_render", lambda item, key, unit, target, dpi: Path(target).write_bytes(b"png"))


def all_states(root):
    make = helpers.make_item
    return {
        "ready": make(root, filename="ready.txt", text=SOURCE),
        "awaiting-approval": make(root, state="awaiting-approval", classification="mixed", filename="a.pdf", statuses=["pending", "pending"]),
        "ocr-in-progress": make(root, state="ocr-in-progress", classification="mixed", filename="p.pdf", statuses=["approved", "recorded"]),
        "unsupported": make(root, state="unsupported", filename="u.xyz"),
        "failed": make(root, state="failed", filename="f.txt"),
    }


# ---------------------------------------------------------------- AT-16

def test_at16_status_json_fields_counts_errors_warnings_and_no_writes(root, capsys):
    items = all_states(root)
    (items["ready"].path / "stray.bin").write_bytes(b"orphan")
    corrupt = root / "raws" / "ffffffffffffffff"
    corrupt.mkdir()
    (corrupt / "meta.json").write_text("{", encoding="utf-8")
    before = tree(root)
    code, env, _ = sb(capsys, root, "status")
    assert tree(root) == before and not (root / "raws" / ".staging").exists()
    assert code == 1 and env["command"] == "status"
    assert [e["code"] for e in env["errors"]] == ["corrupt_meta"] and env["errors"][0]["id"] == "ffffffffffffffff"
    assert [(w["code"], w["id"], w["path"]) for w in env["warnings"]] == [("orphan", items["ready"].meta["id"], "stray.bin")]
    assert env["counts"] == dict.fromkeys(STATES, 1)
    rows = {i["id"]: i for i in env["items"]}
    assert rows["ffffffffffffffff"]["result"] == "corrupt" and rows["ffffffffffffffff"]["state"] is None
    awaiting = rows[items["awaiting-approval"].meta["id"]]
    assert awaiting["result"] == "listed" and awaiting["class"] == "mixed" and awaiting["state"] == "awaiting-approval"
    assert awaiting["pages_total"] == 2 and awaiting["image_occurrences"] == 2
    assert awaiting["coverage"] == {"state": "complete", "scope": "inspected"}
    assert awaiting["units"] == {"total": 2, "approved": 0, "recorded": 0, "verified": 0}
    progress = rows[items["ocr-in-progress"].meta["id"]]
    assert progress["units"] == {"total": 2, "approved": 2, "recorded": 1, "verified": 0} and progress["disposition"] == "approved"
    ready = rows[items["ready"].meta["id"]]
    assert ready["pages_total"] is None and ready["coverage"] == {"state": None, "scope": None} and ready["summary"] is False
    assert rows[items["unsupported"].meta["id"]]["reason"] == "extension_not_allowed"


def test_at16_status_zero_for_every_state_without_errors(root, capsys):
    helpers.add_summary(all_states(root)["ready"])
    before = tree(root)
    code, env, _ = sb(capsys, root, "status")
    assert code == 0 and not env["errors"] and tree(root) == before
    assert [i["summary"] for i in env["items"] if i["state"] == "ready"] == [True]


def test_status_warnings_stale_work_and_staged_collision(root, capsys):
    items = all_states(root)
    ready, failed = items["ready"], items["failed"]
    (root / "work" / ready.meta["id"] / "llm").mkdir(parents=True)  # llm scratch of a ready item is legitimate
    (root / "work" / failed.meta["id"]).mkdir(parents=True)
    (root / "work" / failed.meta["id"] / "u0001.png").write_bytes(b"x")
    staged = root / "raws" / ".staging" / "tmp-1"
    staged.mkdir(parents=True)
    (staged / "stage.json").write_text(json.dumps({"collision": True, "identity": {"id": "0123456789abcdef"}}), encoding="utf-8")
    code, env, _ = sb(capsys, root, "status")
    assert code == 0
    assert sorted((w["code"], w["id"]) for w in env["warnings"]) == sorted([("stale_work", failed.meta["id"]), ("staged_collision", "0123456789abcdef")])


def test_status_reuses_ledger_scan_and_shared_unit_counts(root, capsys):
    from secondbrain import wiki
    items = all_states(root)
    assert wiki.unit_counts(items["ocr-in-progress"].meta) == {"total": 2, "approved": 2, "recorded": 1, "verified": 0}
    code, env, _ = sb(capsys, root, "status")
    row = next(i for i in env["items"] if i["id"] == items["ocr-in-progress"].meta["id"])
    assert code == 0 and row["units"] == wiki.unit_counts(items["ocr-in-progress"].meta)


def test_status_human_output(root, capsys):
    make = helpers.make_item
    make(root, filename="ready.txt", text=SOURCE)
    big = make(root, state="awaiting-approval", classification="mixed", filename="big.pdf", statuses=["pending"] * 21)
    code = cli.main(["--root", str(root), "status"])
    out = capsys.readouterr().out.splitlines()
    assert code == 0
    assert f"{big.meta['id']} awaiting-approval mixed 21/21 0/0/0/21 complete big.pdf" in out
    assert any(l.startswith("OCR approval needed") for l in out)
    assert f"  {big.meta['id']} big.pdf units=21 LARGE" in out
    assert out[-1] == "counts: ready=1, awaiting-approval=1, ocr-in-progress=0, unsupported=0, failed=0"
    assert not any(l.startswith("{") for l in out)


def test_korean_names_are_printed_unescaped(root, capsys):
    helpers.make_item(root, filename="기획서.txt", text=SOURCE)
    cli.main(["--root", str(root), "--json", "status"])
    assert "기획서.txt" in capsys.readouterr().out


# ---------------------------------------------------------------- AT-15

# (command, state) -> allowed writes, DESIGN section 4 matrix; "-" = state_not_allowed
MATRIX = {
    "wiki": dict.fromkeys(STATES, "W"),
    "dup": dict.fromkeys(STATES, "A"),
    "retry": {"ready": "0", "awaiting-approval": "0", "ocr-in-progress": "0", "unsupported": "0", "failed": "M"},
    "approve": {"ready": "-", "awaiting-approval": "M", "ocr-in-progress": "M", "unsupported": "-", "failed": "-"},
    "decline": {"ready": "-", "awaiting-approval": "M", "ocr-in-progress": "-", "unsupported": "-", "failed": "-"},
    "record": {"ready": "-", "awaiting-approval": "-", "ocr-in-progress": "M", "unsupported": "-", "failed": "-"},
    "verify": {"ready": "S", "awaiting-approval": "-", "ocr-in-progress": "M", "unsupported": "-", "failed": "-"},
    "prepare": {"ready": "S", "awaiting-approval": "-", "ocr-in-progress": "-", "unsupported": "-", "failed": "-"},
    "accept": {"ready": "M", "awaiting-approval": "-", "ocr-in-progress": "-", "unsupported": "-", "failed": "-"},
}


def prepare_cell(root, command, state):
    make = helpers.make_item
    if state == "ready":
        item = make(root, filename="ready.txt", text=SOURCE)
    elif state == "awaiting-approval":
        item = make(root, state=state, classification="mixed", filename="a.pdf", statuses=["pending", "pending"])
    elif state == "ocr-in-progress":
        statuses = {"approve": ["approved", "pending"], "record": ["approved"]}.get(command, ["recorded"])
        item = make(root, state=state, classification="mixed", filename="p.pdf", statuses=statuses)
    elif state == "unsupported":
        item = make(root, state=state, filename="u.xyz")
    else:
        item = make(root, state=state, filename="f.txt")
    item_id, work = item.meta["id"], root / "work" / item.meta["id"]
    if command == "record" and state == "ocr-in-progress":
        work.mkdir(parents=True)
        (work / "u0001.md").write_text("recorded text", encoding="utf-8")
    if command == "verify" and state == "ready":
        work.mkdir(parents=True)
        (work / "u0001.png").write_bytes(b"stale scratch")
    if command == "accept" and state == "ready":
        (work / "llm").mkdir(parents=True)
        shutil.copyfile(FIXTURES / "llm" / "valid.md", work / "llm" / "summary.md")
        shutil.copyfile(FIXTURES / "llm" / "valid.json", work / "llm" / "summary.json")
    if command == "dup":
        (root / "inbox" / "copy.dup").write_bytes((root / "raws" / item_id / "src" / item.meta["filename"]).read_bytes())
    argv = {"wiki": ["wiki", "build"], "dup": ["ingest"], "retry": ["ingest", "--retry"],
            "approve": ["ocr", "approve", item_id], "decline": ["ocr", "decline", item_id],
            "record": ["ocr", "record", item_id, "--peer", "cx", "--model", "m"],
            "verify": ["ocr", "verify", item_id, "--peer", "cc", "--model", "m", "--ok", "u0001"],
            "prepare": ["llm", "prepare", item_id], "accept": ["llm", "accept", item_id]}[command]
    return item_id, argv


def allowed(letter, item_id):
    return {"0": (), "-": (), "A": ("inbox/", f"raws/{item_id}/meta.json"), "S": ("work/",), "W": ("wiki",),
            "M": (f"raws/{item_id}/", "work/")}[letter]


@pytest.mark.parametrize("command,state", [(c, s) for c, row in MATRIX.items() for s in row])
def test_at15_command_by_state_matrix(root, capsys, fake_render, command, state):
    item_id, argv = prepare_cell(root, command, state)
    letter = MATRIX[command][state]
    before = tree(root)
    code, env, _ = sb(capsys, root, *argv)
    after = tree(root)
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    if letter == "-":
        assert code == 2 and [e["code"] for e in env["errors"]] == ["state_not_allowed"] and not changed
    else:
        assert code == 0 and not env["errors"], env["errors"]
        assert all(p.startswith(allowed(letter, item_id)) for p in changed), changed
        if letter != "0":
            assert changed, "the cell's write must happen"


def test_matrix_covers_every_cell():
    assert all(set(row) == set(STATES) for row in MATRIX.values())


# ---------------------------------------------------------------- AT-34

def test_at34_parser_failures_are_one_json_object(root, capsys):
    for argv in (["--bogus"], [], ["ocr"], ["ocr", "approve"], ["ocr", "approve", "x", "--dpi", "abc"], ["ingest", "--bogus"],
                 ["status", "extra"], ["ocr", "record", "x"], ["wiki"], ["llm", "frobnicate", "x"], ["--root"]):
        code = cli.main(["--json", *argv])
        captured = capsys.readouterr()
        env = json.loads(captured.out)
        check_envelope(env, code)
        assert code == 2 and env["items"] == [] and [e["code"] for e in env["errors"]] == ["usage"], argv
    cli.main(["--json", "ocr", "approve"])
    assert json.loads(capsys.readouterr().out)["command"] == "ocr approve"


def test_parser_failure_without_json_goes_to_stderr(root, capsys):
    assert cli.main(["--root", str(root), "ocr", "approve"]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "error: usage" in captured.err


def test_json_flag_accepted_before_or_after_command(root, capsys):
    for argv in (["--json", "status"], ["status", "--json"]):
        code = cli.main(["--root", str(root), *argv])
        env = json.loads(capsys.readouterr().out)
        assert code == 0 and env["command"] == "status"


def test_at34_every_command_returns_a_valid_envelope(root, capsys, fake_render):
    items = all_states(root)
    ready = items["ready"].meta["id"]
    ghost = "0123456789abcdef"
    cases = [(["ingest"], 0), (["ingest", "--retry"], 0), (["ingest", "--charset", "nope-codec"], 2), (["status"], 0),
             (["wiki", "build"], 0), (["ocr", "approve", ghost], 2), (["ocr", "decline", ghost], 2),
             (["ocr", "record", ghost, "--peer", "cx", "--model", "m"], 2),
             (["ocr", "verify", ghost, "--peer", "cc", "--model", "m", "--ok", "u0001"], 2),
             (["llm", "prepare", ghost], 2), (["llm", "accept", ghost], 2), (["llm", "accept", ready], 2),
             (["ocr", "verify", items["ocr-in-progress"].meta["id"], "--peer", "cx", "--model", "m", "--ok", "u0002"], 2)]
    for argv, expected in cases:
        code, env, _ = sb(capsys, root, *argv)
        assert code == expected, (argv, env["errors"])
    code, env, _ = sb(capsys, root, "ocr", "verify", items["ocr-in-progress"].meta["id"], "--peer", "cx", "--model", "m", "--ok", "u0002")
    assert env["errors"][0]["code"] == "same_peer"
    code, env, _ = sb(capsys, root, "llm", "accept", ready)
    assert env["errors"][0]["code"] == "llm_invalid"


def test_at34_warnings_and_exit_precedence(root, capsys):
    (root / "inbox" / ".hidden").write_text("x", encoding="utf-8")
    code, env, _ = sb(capsys, root, "ingest")
    assert code == 0 and [w["code"] for w in env["warnings"]] == ["skipped_hidden"]
    helpers.make_item(root, filename="ok.txt", text=SOURCE)
    bad = root / "raws" / "ffffffffffffffff"
    bad.mkdir()
    (bad / "meta.json").write_text("{", encoding="utf-8")
    code, env, _ = sb(capsys, root, "wiki", "build")
    assert code == 1 and env["pages"] == 2 and [e["code"] for e in env["errors"]] == ["corrupt_meta"]
    assert [i["result"] for i in env["items"]] == ["built"]
    code, env, _ = sb(capsys, root, "ocr", "approve", "ffffffffffffffff")
    assert code == 1 and env["errors"][0]["code"] == "corrupt_meta" and env["items"] == []


def test_verify_lists_tolerate_spaces_around_keys(root, capsys):
    item = helpers.make_item(root, state="ocr-in-progress", classification="mixed", filename="p.pdf",
                             statuses=["recorded", "recorded", "recorded", "recorded"])
    code, env, _ = sb(capsys, root, "ocr", "verify", item.meta["id"], "--peer", "cc", "--model", "m",
                      "--ok", "u0001, u0002", "--ok", " u0003", "--mismatch", " u0004 ,")
    assert code == 0 and env["items"][0]["units"] == {"total": 4, "approved": 4, "recorded": 3, "verified": 3}
    units = load_item(item.path).meta["ocr"]["units"]
    assert [u["status"] for u in units.values()] == ["verified", "verified", "verified", "approved"]


def test_wiki_build_envelope_and_pages(root, capsys):
    helpers.make_item(root, filename="a.txt")
    code, env, _ = sb(capsys, root, "wiki", "build")
    assert code == 0 and env["command"] == "wiki build" and env["pages"] == 2 and (root / "wiki" / "index.md").is_file()


def test_ingest_exit_one_when_inbox_is_missing(tmp_path, capsys):
    code, env, _ = sb(capsys, tmp_path / "empty-root", "ingest")
    assert code == 1 and [e["code"] for e in env["errors"]] == ["io_error"]


def test_root_precedence_flag_then_env_then_cwd(root, tmp_path, capsys, monkeypatch):
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("SB_ROOT", str(other))
    monkeypatch.chdir(root)
    cli.main(["--json", "status"])
    assert json.loads(capsys.readouterr().out)["root"] == str(other.resolve())
    cli.main(["--json", "--root", str(root), "status"])
    assert json.loads(capsys.readouterr().out)["root"] == str(root.resolve())
    monkeypatch.delenv("SB_ROOT")
    cli.main(["--json", "status"])
    assert json.loads(capsys.readouterr().out)["root"] == str(root.resolve())


# ---------------------------------------------------------------- notices

def test_approve_prints_notice_and_next_step(root, capsys, fake_render):
    item = helpers.make_item(root, state="awaiting-approval", classification="mixed", filename="a.pdf", statuses=["pending"])
    assert cli.main(["--root", str(root), "ocr", "approve", item.meta["id"]]) == 0
    out = capsys.readouterr().out
    assert "leave this machine" in out and "COMMANDS.txt" in out and f"{item.meta['id']} approved a.pdf" in out
    other = helpers.make_item(root, state="awaiting-approval", classification="mixed", filename="b.pdf", statuses=["pending"])
    code, env, err = sb(capsys, root, "ocr", "approve", other.meta["id"])
    assert "leave this machine" in err and env["items"][0]["result"] == "approved"  # stdout stays one JSON object


def test_llm_prepare_prints_next_step(root, capsys):
    item = helpers.make_item(root, filename="a.txt", text=SOURCE)
    assert cli.main(["--root", str(root), "llm", "prepare", item.meta["id"]]) == 0
    out = capsys.readouterr().out
    assert "COMMANDS.txt" in out and f"{item.meta['id']} prepared a.txt" in out


def test_rejection_in_human_mode_prints_error_to_stderr(root, capsys):
    item = helpers.make_item(root, filename="a.txt")
    assert cli.main(["--root", str(root), "ocr", "approve", item.meta["id"]]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "error: state_not_allowed" in captured.err
    assert load_item(item.path).meta["state"] == "ready"
