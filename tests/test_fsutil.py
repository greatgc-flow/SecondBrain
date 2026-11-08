from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import tempfile

import pytest

from secondbrain.errors import ErrorCode, SbError, WarningCode
from secondbrain import fsutil


def test_codes_and_error():
    assert ErrorCode.CORRUPT_META == "corrupt_meta"
    assert WarningCode.ORPHAN == "orphan"
    error = SbError(ErrorCode.INVALID_REQUEST, 2, "bad request")
    assert (error.code, error.exit, str(error)) == ("invalid_request", 2, "bad request")


def test_root_precedence(root, monkeypatch):
    monkeypatch.chdir(root)
    assert fsutil.resolve_root() == root
    monkeypatch.setenv("SB_ROOT", str(root / "env"))
    assert fsutil.resolve_root() == root / "env"
    assert fsutil.resolve_root(root / "explicit") == root / "explicit"


def test_utf8_lf_and_atomic_json(root, monkeypatch):
    target = root / "meta.json"
    fsutil.write_text(root / "text.md", "한글\r\nnext\rline")
    assert (root / "text.md").read_bytes() == "한글\nnext\nline".encode()
    fsutil.write_json_atomic(target, {"z": "한글", "a": 1})
    assert target.read_bytes() == '{\n "a": 1,\n "z": "한글"\n}\n'.encode()
    before = target.read_bytes()
    def fail(*args):
        raise OSError("injected before replace")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        fsutil.write_json_atomic(target, {"new": True})
    assert target.read_bytes() == before


def test_fault_after_committed_meta_is_once(root, fault_after):
    target = root / "meta.json"
    fault_after("meta.json")
    with pytest.raises(OSError, match="fault"):
        fsutil.write_json_atomic(target, {"committed": True})
    assert json.loads(target.read_text()) == {"committed": True}
    fsutil.write_json_atomic(target, {"committed": False})


@pytest.mark.parametrize("relative", ["work/0123456789abcdef", "raws/.staging/tmp-1", "wiki.tmp", "wiki.old"])
def test_at36_allowed_deletion(root, relative):
    path = root / relative
    path.mkdir(parents=True)
    (path / "keep-until-delete.txt").write_text("synthetic")
    fsutil.safe_delete(root, path)
    assert not path.exists()


@pytest.mark.parametrize("relative", [".", "raws", "raws/0123456789abcdef", "inbox", "wiki", "work", "../outside", "work/not-an-id"])
def test_at36_other_deletion_targets_refused(root, relative):
    with pytest.raises(SbError) as error:
        fsutil.safe_delete(root, root / relative)
    assert (error.value.code, error.value.exit) == ("io_error", 1)


def test_at36_reparse_ancestor_refused_before_delete(root, monkeypatch):
    target = root / "work" / "0123456789abcdef"
    target.mkdir(parents=True)
    original = fsutil.is_reparse_point
    monkeypatch.setattr(fsutil, "is_reparse_point", lambda p: Path(p) == root / "work" or original(p))
    with pytest.raises(SbError):
        fsutil.safe_delete(root, target)
    assert target.is_dir()


def test_at36_symlink_detection(root, monkeypatch):
    # DESIGN §2: simulate the OS reparse attribute without requiring Windows link privileges.
    class Reparse:
        st_file_attributes = 0x400
        st_mode = 0
    monkeypatch.setattr(Path, "lstat", lambda self: Reparse())
    assert fsutil.is_reparse_point(root / "junction")


def test_path_length_escaping_percent_and_fences(root):
    fsutil.check_path_length(Path("x" * 240))
    with pytest.raises(SbError, match="240") as error:
        fsutil.check_path_length(Path("x" * 241))
    assert error.value.code == "path_too_long"
    assert fsutil.esc("[x](y) <b>`z` #!\n한글|") == "\\[x\\]\\(y\\) &lt;b>'z' \\#\\! 한글\\|"
    assert fsutil.percent_encode("한 글#?.pdf") == "%ED%95%9C%20%EA%B8%80%23%3F.pdf"
    assert fsutil.fenced_block("<script>\n````\n") == "`````text\n<script>\n````\n`````"


def test_temporary_files_stay_in_worktree(root):
    assert Path(tempfile.gettempdir()).resolve().is_relative_to(Path.cwd().resolve())


def test_at37_socket_creation_and_loopback_bind_allowed():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))


@pytest.mark.parametrize("operation", ["connect", "connect_ex", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "create_connection"])
def test_at37_network_and_dns_blocked(operation):
    with pytest.raises(OSError, match="network"):
        if operation in {"connect", "connect_ex"}:
            with socket.socket() as sock:
                getattr(sock, operation)(("192.0.2.1", 80))
        elif operation == "getaddrinfo":
            socket.getaddrinfo("example.invalid", 80)
        elif operation == "create_connection":
            socket.create_connection(("192.0.2.1", 80))
        else:
            getattr(socket, operation)("example.invalid")


def test_at37_real_converter_import_and_http_control(network_guard):
    before = len(network_guard)
    from markitdown import MarkItDown
    converter = MarkItDown(enable_plugins=False)
    assert len(network_guard) == before
    with pytest.raises(Exception):
        converter.convert("http://x")
    assert len(network_guard) > before


def test_subprocess_spy_rejects_shell_and_other_python(subprocess_spy):
    for args in ([sys.executable, "-c", "print('not allowed')"], ["peerhub", "ask"], "sb status"):
        with pytest.raises(AssertionError, match="subprocess"):
            subprocess.run(args, capture_output=True)
    assert len(subprocess_spy) == 3


def test_at37_converter_child_is_guarded(root, subprocess_spy):
    process = subprocess.run(["markitdown-gc", "http://x"], capture_output=True, text=True)
    assert process.returncode != 0
    assert "network" in process.stderr.lower()
    assert subprocess_spy[-1][0].endswith("markitdown-gc")


def test_subprocess_spy_allows_module_entrypoint(subprocess_spy):
    process = subprocess.run([sys.executable, "-m", "secondbrain"], capture_output=True, text=True)
    assert process.returncode == 1  # Slice 0 placeholder; no CLI behavior asserted here.
    assert "not implemented" in process.stderr


def test_at36_reparse_descendant_refused_before_any_delete(root, monkeypatch):
    target = root / "wiki.old"
    target.mkdir()
    (target / "ordinary.txt").write_text("keep")
    (target / "linked").mkdir()
    original = fsutil.is_reparse_point
    monkeypatch.setattr(fsutil, "is_reparse_point", lambda p: Path(p) == target / "linked" or original(p))
    with pytest.raises(SbError):
        fsutil.safe_delete(root, target)
    assert (target / "ordinary.txt").read_text() == "keep"


@pytest.mark.parametrize("step", ["stage.json", "identity", "conversion_pending", "conversion", "triage"])
def test_named_stage_faults(root, fault_after, step):
    path = root / "raws/.staging/tmp-1/stage.json"
    data = {"identity": {"id": "synthetic"}, "conversion": {"sha256": None if step == "conversion_pending" else "synthetic"}, "triage": {"decision": "synthetic"}}
    fault_after(step)
    with pytest.raises(OSError, match="fault"):
        fsutil.write_json_atomic(path, data)
    assert json.loads(path.read_text()) == data
    fsutil.write_json_atomic(path, data)


def test_named_claim_and_commit_faults(root, fault_after):
    staging = root / "raws/.staging/tmp-1"
    (staging / "src").mkdir(parents=True)
    source = root / "inbox/file.txt"
    source.write_bytes(b"original")
    fault_after("claim")
    with pytest.raises(OSError):
        os.replace(source, staging / "src/file.txt")
    assert (staging / "src/file.txt").read_bytes() == b"original"
    fault_after("commit")
    target = root / "raws/0123456789abcdef"
    with pytest.raises(OSError):
        os.rename(staging, target)
    assert (target / "src/file.txt").read_bytes() == b"original"
