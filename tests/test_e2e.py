"""Slice 8 end-to-end: every call goes through the installed `sb` console script as a child process.

The converter runs inside the child, so its call counts are read from the child's ledgers
(meta.json / converted.md), never from the parent's subprocess spy (DESIGN section 9).
`python -m secondbrain` is used only when the console script is not installed (run `pip install -e .`).
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sb_command():
    script = shutil.which("sb")
    return [script] if script else [sys.executable, "-m", "secondbrain"]


@pytest.fixture
def run(root, sb_command):
    def call(*argv, expect=None):
        done = subprocess.run([*sb_command, "--root", str(root), "--json", *argv], capture_output=True, encoding="utf-8")
        env = json.loads(done.stdout)  # stdout is exactly one JSON object
        assert env["exit"] == done.returncode and env["ok"] == (done.returncode == 0)
        if expect is not None:
            assert done.returncode == expect, (argv, env["errors"], done.stderr)
        return env, done.stderr
    return call


def item_dir(root, env):
    return root / "raws" / env["items"][0]["id"]


def test_e2e_text_ingest_duplicates_and_wiki(root, run):
    source = (FIXTURES / "text" / "plain.txt").read_bytes()
    (root / "inbox" / "sub").mkdir()
    (root / "inbox" / "sub" / "plain.txt").write_bytes(source)
    env, _ = run("ingest", expect=0)
    item = env["items"][0]
    assert item["result"] == "new" and item["class"] == "text-only" and item["state"] == "ready" and not list((root / "inbox").rglob("*.txt"))
    directory = root / "raws" / item["id"]
    assert (directory / "src" / "plain.txt").read_bytes() == source
    converted, ledger = (directory / "converted.md").read_bytes(), json.loads((directory / "meta.json").read_text(encoding="utf-8"))["conversion"]
    (root / "inbox" / "copy.txt").write_bytes(source)
    env, _ = run("ingest", expect=0)
    assert env["items"][0]["result"] == "alias_added"
    meta_after_alias = (directory / "meta.json").read_bytes()
    (root / "inbox" / "copy.txt").write_bytes(source)
    env, _ = run("ingest", expect=0)
    assert env["items"][0]["result"] == "duplicate" and (directory / "meta.json").read_bytes() == meta_after_alias
    assert (directory / "converted.md").read_bytes() == converted  # no reconversion (ledger evidence)
    assert json.loads(meta_after_alias.decode("utf-8"))["conversion"] == ledger
    assert [p for p in (root / "raws").iterdir() if p.name != ".staging"] == [directory] and not list((root / "raws" / ".staging").iterdir())
    env, _ = run("wiki", "build", expect=0)
    assert env["pages"] == 2 and env["items"][0]["result"] == "built"
    first = {p.relative_to(root).as_posix(): p.read_bytes() for p in (root / "wiki").rglob("*") if p.is_file()}
    assert "plain.txt" in first["wiki/index.md"].decode("utf-8") and set(first) == {"wiki/index.md", f"wiki/sources/{item['id']}.md"}
    run("wiki", "build", expect=0)
    assert {p.relative_to(root).as_posix(): p.read_bytes() for p in (root / "wiki").rglob("*") if p.is_file()} == first
    env, _ = run("status", expect=0)
    assert env["counts"]["ready"] == 1 and env["items"][0]["result"] == "listed"


def test_e2e_raster_ocr_approve_record_verify(root, run):
    (root / "inbox" / "photo.png").write_bytes((FIXTURES / "ocr" / "photo.png").read_bytes())
    env, _ = run("ingest", expect=0)
    item_id = env["items"][0]["id"]
    assert env["items"][0]["class"] == "ocr-required" and env["items"][0]["state"] == "awaiting-approval"
    assert env["items"][0]["units"]["total"] == 1
    work = root / "work" / item_id
    env, err = run("ocr", "approve", item_id, expect=0)
    assert env["items"][0]["state"] == "ocr-in-progress" and "leave this machine" in err
    assert (work / "u0001.png").read_bytes() == (FIXTURES / "ocr" / "photo.png").read_bytes() and (work / "COMMANDS.txt").is_file()
    shutil.copyfile(FIXTURES / "peer-output" / "u0001.md", work / "u0001.md")
    env, _ = run("ocr", "record", item_id, "--peer", "cx", "--model", "m", expect=0)
    assert env["items"][0]["units"]["recorded"] == 1
    env, _ = run("ocr", "verify", item_id, "--peer", "CX", "--model", "m", "--ok", "u0001", expect=2)
    assert env["errors"][0]["code"] == "same_peer"
    run("wiki", "build", expect=0)
    assert "SYNTHETIC INVOICE" not in (root / "wiki" / "sources" / f"{item_id}.md").read_text(encoding="utf-8")  # unverified (I6)
    env, _ = run("ocr", "verify", item_id, "--peer", "cc", "--model", "m", "--ok", "u0001", expect=0)
    assert env["items"][0]["result"] == "finalized" and env["items"][0]["state"] == "ready" and not work.exists()
    run("wiki", "build", expect=0)
    page = (root / "wiki" / "sources" / f"{item_id}.md").read_text(encoding="utf-8")
    assert "SYNTHETIC INVOICE" in page and "## OCR u0001 (source self;" in page
    env, _ = run("ocr", "verify", item_id, "--peer", "cc", "--model", "m", expect=0)
    assert env["items"][0]["result"] == "cleaned"


def test_e2e_llm_prepare_accept_and_rejection(root, run):
    (root / "inbox" / "plain.txt").write_bytes((FIXTURES / "text" / "plain.txt").read_bytes())
    item_id = run("ingest", expect=0)[0]["items"][0]["id"]
    env, err = run("llm", "prepare", item_id, expect=0)
    assert env["items"][0]["result"] == "prepared" and "COMMANDS.txt" in err
    scratch = root / "work" / item_id / "llm"
    prompt = (scratch / "prompt.txt").read_text(encoding="utf-8")
    assert "Invoice 12345, total 42 USD." in prompt and "data, not instructions" in prompt
    shutil.copyfile(FIXTURES / "llm" / "valid.md", scratch / "summary.md")
    shutil.copyfile(FIXTURES / "llm" / "bad-digest.json", scratch / "summary.json")
    env, _ = run("llm", "accept", item_id, expect=2)
    assert env["errors"][0]["code"] == "llm_invalid" and not (root / "raws" / item_id / "llm").exists()
    shutil.copyfile(FIXTURES / "llm" / "valid.json", scratch / "summary.json")
    env, _ = run("llm", "accept", item_id, expect=0)
    assert env["items"][0]["result"] == "accepted" and env["items"][0]["summary"] is True
    assert run("llm", "accept", item_id, expect=0)[0]["items"][0]["result"] == "unchanged"
    run("wiki", "build", expect=0)
    page = (root / "wiki" / "sources" / f"{item_id}.md").read_text(encoding="utf-8")
    assert "Synthetic invoice 12345 totals 42 USD." in page and "## Summary" in page


def test_e2e_status_on_empty_root_and_usage_error(root, run):
    env, _ = run("status", expect=0)
    assert env["items"] == [] and env["counts"]["ready"] == 0
    env, _ = run("ocr", "approve", expect=2)
    assert env["errors"][0]["code"] == "usage"


def test_e2e_python_dash_m_entry_point(root):
    done = subprocess.run([sys.executable, "-m", "secondbrain", "--root", str(root), "--json", "status"], capture_output=True, encoding="utf-8")
    assert done.returncode == 0 and json.loads(done.stdout)["command"] == "status"
