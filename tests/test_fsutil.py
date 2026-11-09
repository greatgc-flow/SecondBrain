from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import pytest

from secondbrain.errors import ErrorCode, SbError, WarningCode
from secondbrain import fsutil
from conftest import WORKTREE


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


@pytest.mark.parametrize("form", ["path", "text", "bytes"])
def test_load_json_strict_reads_utf8_and_rejects_nested_duplicate_keys(root, form):
    valid = '{"name":"한글","nested":{"n":1}}'
    duplicate = '{"nested":{"n":1,"n":2}}'
    def source(text):
        if form == "path":
            path = root / "input.json"
            path.write_bytes(text.encode("utf-8"))
            return path
        return text.encode("utf-8") if form == "bytes" else text
    assert fsutil.load_json_strict(source(valid)) == {"name": "한글", "nested": {"n": 1}}
    with pytest.raises(ValueError, match="Duplicate"):
        fsutil.load_json_strict(source(duplicate))


def test_load_json_strict_rejects_invalid_utf8_and_syntax(root):
    source = root / "bad.json"
    source.write_bytes(b"\xff")
    with pytest.raises(UnicodeError):
        fsutil.load_json_strict(source)
    with pytest.raises(ValueError):
        fsutil.load_json_strict("{")


def test_write_bytes_atomic_preserves_bytes_and_fsync_order(root, monkeypatch):
    target = root / "nested/output.md"
    data = b"\xef\xbb\xbfExact\r\nbytes\r\n"
    events = []
    sync, replace = os.fsync, os.replace
    def synced(fd):
        assert target.with_name("output.md.tmp").read_bytes() == data
        events.append("fsync")
        return sync(fd)
    def replaced(source, destination):
        assert events == ["fsync"]
        events.append("replace")
        return replace(source, destination)
    monkeypatch.setattr(os, "fsync", synced)
    monkeypatch.setattr(os, "replace", replaced)
    fsutil.write_bytes_atomic(target, data)
    assert target.read_bytes() == data and events == ["fsync", "replace"]


def test_write_bytes_atomic_failed_fsync_keeps_previous_artifact(root, monkeypatch):
    target = root / "output.md"
    target.write_bytes(b"committed")
    def failed(fd):
        raise OSError("fsync failed")
    monkeypatch.setattr(os, "fsync", failed)
    with pytest.raises(OSError, match="fsync failed"):
        fsutil.write_bytes_atomic(target, b"new bytes")
    assert target.read_bytes() == b"committed"


def test_fault_after_committed_meta_is_once(root, fault_after):
    target = root / "meta.json"
    fault_after("meta.json")
    with pytest.raises(OSError, match="fault"):
        fsutil.write_json_atomic(target, {"committed": True})
    assert json.loads(target.read_text(encoding="utf-8")) == {"committed": True}
    fsutil.write_json_atomic(target, {"committed": False})


@pytest.mark.parametrize("relative", ["work/0123456789abcdef", "raws/.staging/tmp-1", "wiki.tmp", "wiki.old"])
def test_at36_allowed_deletion(root, relative):
    path = root / relative
    path.mkdir(parents=True)
    (path / "keep-until-delete.txt").write_text("synthetic", encoding="utf-8")
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


def test_path_length_boundary(root):
    fsutil.check_path_length(Path("x" * 240))
    with pytest.raises(SbError, match="240") as error:
        fsutil.check_path_length(Path("x" * 241))
    assert error.value.code == "path_too_long"


def test_esc_controls_and_markdown():
    assert fsutil.esc("[x](y) <b>`z` #!\n한글|") == "\\[x\\]\\(y\\) &lt;b>'z' \\#\\! 한글\\|"
    assert fsutil.esc("a\x00b\t*\\_") == "a b \\*\\\\\\_"


def test_percent_encode_filename():
    assert fsutil.percent_encode("한 글#?.pdf") == "%ED%95%9C%20%EA%B8%80%23%3F.pdf"
    assert fsutil.percent_encode("[x]/100%.md") == "%5Bx%5D%2F100%25.md"


def test_temporary_files_stay_in_worktree(root, monkeypatch):
    monkeypatch.chdir(root / "inbox")
    assert Path(tempfile.gettempdir()).resolve().is_relative_to(WORKTREE)


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
    assert process.returncode == 2  # slice 8: the real CLI rejects a missing command; the spy only needs to allow the launch
    assert "usage" in process.stderr


def test_at36_reparse_descendant_refused_before_any_delete(root, monkeypatch):
    target = root / "wiki.old"
    target.mkdir()
    (target / "ordinary.txt").write_text("keep", encoding="utf-8")
    (target / "linked").mkdir()
    original = fsutil.is_reparse_point
    monkeypatch.setattr(fsutil, "is_reparse_point", lambda p: Path(p) == target / "linked" or original(p))
    with pytest.raises(SbError):
        fsutil.safe_delete(root, target)
    assert (target / "ordinary.txt").read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("step", ["stage.json", "identity", "conversion_pending", "conversion", "triage"])
def test_named_stage_faults(root, fault_after, step):
    path = root / "raws/.staging/tmp-1/stage.json"
    data = {"identity": {"id": "synthetic"}, "conversion": {"sha256": None if step == "conversion_pending" else "synthetic"}, "triage": {"decision": "synthetic"}}
    fault_after(step)
    with pytest.raises(OSError, match="fault"):
        fsutil.write_json_atomic(path, data)
    assert json.loads(path.read_text(encoding="utf-8")) == data
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


def test_atomic_json_flushed_and_synced_before_replace(root, monkeypatch):
    target = root / "meta.json"
    fsutil.write_json_atomic(target, {"old": True})
    before = target.read_bytes()
    events = []
    sync, replace = os.fsync, os.replace
    def synced(descriptor):
        assert target.read_bytes() == before
        assert json.loads((root / "meta.json.tmp").read_text(encoding="utf-8")) == {"new": "한글"}
        events.append("sync")
        sync(descriptor)
    def replaced(source, destination):
        assert events == ["sync"]
        events.append("replace")
        replace(source, destination)
    monkeypatch.setattr(os, "fsync", synced)
    monkeypatch.setattr(os, "replace", replaced)
    fsutil.write_json_atomic(target, {"new": "한글"})
    assert events == ["sync", "replace"]


def test_failed_fsync_preserves_committed_json(root, monkeypatch):
    target = root / "meta.json"
    fsutil.write_json_atomic(target, {"old": True})
    before = target.read_bytes()
    def fail(descriptor):
        raise OSError("injected fsync failure")
    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError, match="fsync"):
        fsutil.write_json_atomic(target, {"new": True})
    assert target.read_bytes() == before


def test_safe_delete_readonly_file(root):
    import stat
    target = root / "wiki.old"
    target.mkdir()
    file = target / "readonly.txt"
    file.write_bytes(b"temporary derived content")
    file.chmod(stat.S_IREAD)
    fsutil.safe_delete(root, target)
    assert not target.exists()


def test_safe_delete_readonly_error_handler(root, monkeypatch):
    import stat
    target = root / "wiki.old"
    target.mkdir()
    file = target / "readonly.txt"
    file.write_bytes(b"derived")
    original_stat = Path.stat
    def file_stat(path, *args, **kwargs):
        info = original_stat(path, *args, **kwargs)
        if path == file:
            return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=stat.FILE_ATTRIBUTE_READONLY)
        return info
    def denied_once(path, *, onerror):
        error = PermissionError("simulated Windows read-only file")
        onerror(os.unlink, str(file), (type(error), error, None))
        target.rmdir()
    monkeypatch.setattr(Path, "stat", file_stat)
    monkeypatch.setattr(fsutil.shutil, "rmtree", denied_once)
    fsutil.safe_delete(root, target)
    assert not target.exists()


@pytest.mark.parametrize("scenario", ["default", "outside", "permission"])
def test_basetemp_configuration(tmp_path, monkeypatch, scenario):
    import conftest
    monkeypatch.setattr(conftest, "WORKTREE", tmp_path)
    base = tmp_path / ".pytest-tmp"
    selected = None if scenario == "default" else str(tmp_path.parent / "outside" if scenario == "outside" else base)
    factory = SimpleNamespace(_given_basetemp=base, _basetemp=tmp_path / "old")
    config = SimpleNamespace(option=SimpleNamespace(basetemp=selected), _tmp_path_factory=factory)
    expected = base
    if scenario == "outside":
        with pytest.raises(pytest.UsageError):
            conftest.configure_basetemp(config)
        return
    if scenario == "permission":
        monkeypatch.setattr(conftest, "os", SimpleNamespace(name="nt"))
        base.mkdir()
        original = Path.iterdir
        def denied(path):
            if path == base:
                raise PermissionError("private Windows ACL")
            return original(path)
        monkeypatch.setattr(Path, "iterdir", denied)
        expected = tmp_path / "work/pytest-foundation"
        with pytest.warns(pytest.PytestWarning, match="Inaccessible"):
            conftest.configure_basetemp(config)
    else:
        conftest.configure_basetemp(config)
    assert Path(config.option.basetemp) == factory._given_basetemp == expected
    assert factory._basetemp is None


def test_audio_extra_check_is_strict_in_ci(monkeypatch):
    import conftest
    monkeypatch.setenv("CI", "1")
    monkeypatch.setattr(conftest.importlib.util, "find_spec", lambda name: object())
    with pytest.raises(AssertionError, match="Audio extras"):
        conftest.check_audio_extras()
    monkeypatch.setattr(conftest.importlib.util, "find_spec", lambda name: None)
    assert conftest.check_audio_extras() == []


def test_safe_delete_does_not_retry_other_permission_failures(root, monkeypatch):
    target = root / "wiki.old"
    target.mkdir()
    file = target / "ordinary.txt"
    file.write_bytes(b"preserve after permission failure")
    def denied(path, *, onerror):
        error = PermissionError("not a read-only attribute")
        onerror(os.unlink, str(file), (type(error), error, None))
    monkeypatch.setattr(fsutil.shutil, "rmtree", denied)
    with pytest.raises(SbError) as error:
        fsutil.safe_delete(root, target)
    assert error.value.code == "io_error"
    assert file.read_bytes() == b"preserve after permission failure"
