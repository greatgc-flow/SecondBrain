"""Worktree-local scratch, offline tests, subprocess spy, and named crash hooks."""
import importlib.util
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import warnings

import pytest

WORKTREE = Path(__file__).resolve().parents[1]
GUARD_SOURCE = '''import socket
def denied(*args, **kwargs):
    raise OSError("network disabled by the test guard")
socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.create_connection = denied
socket.getaddrinfo = denied
socket.gethostbyname = denied
socket.gethostbyname_ex = denied
'''


def pytest_configure(config):
    # Resolve stdlib Windows platform metadata before installing the per-test
    # subprocess spy: platform.uname() may invoke the OS's `ver` command once.
    platform.uname()
    platform.platform()
    base = config.option.basetemp
    if base is None or not Path(base).resolve().is_relative_to(WORKTREE):
        raise pytest.UsageError("Use --basetemp inside this worktree")
    if os.name == "nt":
        # Python 3.13+ gives mkdir(0700) a private DACL that restricted Windows
        # tokens cannot reuse. Preserve inherited workspace permissions in tests.
        original = os.mkdir
        def mkdir(path, mode=0o777, *args, **kwargs):
            if mode == 0o700 and Path(os.fsdecode(path)).resolve().is_relative_to(WORKTREE):
                mode = 0o777
            return original(path, mode, *args, **kwargs)
        config._sb_original_mkdir = original
        os.mkdir = mkdir
        try:
            if Path(base).exists():
                list(Path(base).iterdir())
        except PermissionError:
            config.option.basetemp = str(WORKTREE / "work" / "pytest-foundation")
            warnings.warn("Inaccessible .pytest-tmp; using work/pytest-foundation within this worktree", pytest.PytestWarning)


def pytest_unconfigure(config):
    if hasattr(config, "_sb_original_mkdir"):
        os.mkdir = config._sb_original_mkdir


@pytest.fixture(scope="session", autouse=True)
def network_guard():
    calls = []
    def denied(*args, **kwargs):
        calls.append((args, kwargs))
        raise OSError("network disabled by the test guard")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(socket.socket, "connect", denied)
        patch.setattr(socket.socket, "connect_ex", denied)
        for name in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex"):
            patch.setattr(socket, name, denied)
        yield calls


@pytest.fixture(scope="session", autouse=True)
def audio_extra_check():
    """CI installs the declared dependencies only; report shared local extras."""
    extras = [name for name in ("speech_recognition", "pydub") if importlib.util.find_spec(name) is not None]
    if os.environ.get("CI"):
        assert not extras, f"Audio extras must be absent in CI: {extras}"
    return extras


@pytest.fixture(autouse=True)
def local_temp(tmp_path, monkeypatch):
    assert tmp_path.resolve().is_relative_to(WORKTREE)
    path = tmp_path / "temp"
    path.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(path))
    for name in ("TMP", "TEMP", "TMPDIR"):
        monkeypatch.setenv(name, str(path))
    assert Path(tempfile.gettempdir()).resolve().is_relative_to(WORKTREE)


@pytest.fixture
def root(tmp_path):
    path = tmp_path / "root"
    (path / "inbox").mkdir(parents=True)
    return path


@pytest.fixture(autouse=True)
def subprocess_spy(monkeypatch, tmp_path):
    calls = []
    original = subprocess.Popen
    guard = tmp_path / "network-guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(GUARD_SOURCE, encoding="utf-8", newline="\n")

    def popen(args, *positional, **kwargs):
        calls.append(args)
        assert not isinstance(args, (str, bytes)) and args and not kwargs.get("shell"), "subprocess refused"
        executable = Path(args[0]).name.lower().removesuffix(".exe")
        allowed = executable in {"sb", "markitdown-gc"} or (
            (Path(args[0]).resolve() == Path(sys.executable).resolve() or executable in {"python", "python3"})
            and list(args[1:3]) == ["-m", "secondbrain"])
        assert allowed, f"subprocess refused: {args}"
        env = dict(os.environ if kwargs.get("env") is None else kwargs["env"])
        env["PYTHONPATH"] = os.pathsep.join((str(guard), str(WORKTREE / "src"), env.get("PYTHONPATH", "")))
        env["PYTHONUTF8"] = "1"
        kwargs["env"] = env
        return original(args, *positional, **kwargs)
    monkeypatch.setattr(subprocess, "Popen", popen)
    return calls


@pytest.fixture
def fault_after(monkeypatch):
    """Arm once after stage.json/claim/identity/conversion_pending/converted.md/
    conversion/triage/meta.json/commit. Accept any destination basename as well.
    The exception is raised AFTER the real rename/replace, like process death.
    """
    armed = None
    replace, rename = os.replace, os.rename

    def matches(step, source, destination):
        if step == destination.name:
            return True
        if step == "claim":
            return destination.parent.name == "src" and ".staging" in destination.parts
        if step == "commit":
            return destination.parent.name == "raws" and source.parent.name == ".staging"
        if destination.name == "stage.json":
            data = json.loads(destination.read_text(encoding="utf-8"))
            conversion = data.get("conversion")
            return (step == "identity" and "identity" in data
                    or step == "conversion_pending" and conversion is not None and conversion.get("sha256") is None
                    or step == "conversion" and conversion is not None and conversion.get("sha256") is not None
                    or step == "triage" and data.get("triage") is not None)
        return False

    def wrap(operation):
        def call(source, destination, *args, **kwargs):
            nonlocal armed
            result = operation(source, destination, *args, **kwargs)
            if armed is not None and matches(armed, Path(source), Path(destination)):
                step, armed = armed, None
                raise OSError(f"fault after {step}")
            return result
        return call

    monkeypatch.setattr(os, "replace", wrap(replace))
    monkeypatch.setattr(os, "rename", wrap(rename))
    def arm(step):
        nonlocal armed
        armed = step
    return arm
