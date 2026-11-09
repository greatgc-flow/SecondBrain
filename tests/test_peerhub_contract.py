"""Check generated commands against the installed CLI without invoking a peer."""
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tomllib

import pytest

from conftest import GUARD_SOURCE
from helpers import make_item
from secondbrain import llm, ocr


@pytest.fixture
def subprocess_spy(monkeypatch, tmp_path):
    """This module permits only offline CLI help, never a peer request."""
    original = subprocess.Popen
    guard = tmp_path / "help-guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(GUARD_SOURCE, encoding="utf-8")
    def help_only(args, *positional, **kwargs):
        assert not kwargs.get("shell") and list(args[1:]) == ["ask", "--help"]
        assert Path(args[0]).name.lower().removesuffix(".exe") == "peerhub"
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join((str(guard), env.get("PYTHONPATH", "")))
        env["PYTHONUTF8"] = "1"
        kwargs["env"] = env
        return original(args, *positional, **kwargs)
    monkeypatch.setattr(subprocess, "Popen", help_only)


def test_dev_extra_installs_peerhub():
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    assert "peerhub==0.24.1" in project["project"]["optional-dependencies"]["dev"]


def test_generated_flags_exist_in_real_peerhub_ask_help(root, monkeypatch):
    executable = shutil.which("peerhub")
    if executable is None:
        if os.environ.get("CI"):
            pytest.fail("CI must install peerhub via .[dev]")
        pytest.skip("peerhub is not installed locally")
    process = subprocess.run([executable, "ask", "--help"], capture_output=True,
                             text=True, encoding="utf-8", check=True, timeout=30)
    available = set(re.findall(r"(?<![\w-])--?[a-z][a-z0-9-]*", process.stdout))
    assert available, process.stdout
    item = make_item(root, classification="mixed", state="awaiting-approval")
    monkeypatch.setattr(ocr, "_render", lambda item, key, unit, path, dpi: Path(path).write_bytes(b"image"))
    ocr.approve(root, item.meta["id"])
    text = (root / "work" / item.meta["id"] / "COMMANDS.txt").read_text(encoding="utf-8")
    ready = make_item(root, filename="summary.txt", text="Summary source 123")
    llm.prepare(root, ready.meta["id"])
    text += (root / "work" / ready.meta["id"] / "llm/COMMANDS.txt").read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("peerhub ask ")]
    assert len(lines) >= 3  # transcription, independent verification, summary
    for line in lines:
        flags = {token for token in shlex.split(line)[3:] if re.fullmatch(r"--?[a-z][a-z0-9-]*", token)}
        assert flags and flags <= available, f"Unsupported flags {flags - available}: {line}"
