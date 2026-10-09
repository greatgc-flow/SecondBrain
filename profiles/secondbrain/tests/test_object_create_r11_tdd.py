"""R11 RED: synthetic, local-only EvidenceObject and per-capture lineage tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))
from brain_core.capture import capture_file
from brain_core.writer import configure_writer, publish_capture
from brain_core.custody import commit_capture, verify_chain
from brain_core.object import ObjectFailure, create_object, verify_object_link
from brain_core.verify import verify_object


def prepared(tmp_path, data=b"synthetic R11 bytes\x00"):
    root = tmp_path / "한글 공백 Second Brain"
    root.mkdir()
    source = tmp_path / "원본 테스트 1.txt"
    source.write_bytes(data)
    writer = configure_writer(root, "sole-writer")
    cap = capture_file(root, source, "pc_1", "synthetic-only")
    publish_capture(root, "pc_1", cap["capture_id"], "sole-writer", writer["writer_epoch"])
    return root, source, writer, cap


def commit(root, writer, cap):
    return commit_capture(root, "pc_1", cap["capture_id"], "sole-writer", writer["writer_epoch"])


def create(root, writer, cap):
    return create_object(root, "pc_1", cap["capture_id"], "sole-writer", writer["writer_epoch"])


def record_path(root, oid):
    return root / "10_Evidence/Records/objects" / (oid + ".json")


def link_path(root, cap):
    return root / "10_Evidence/Records/objects/links/pc_1" / (cap["capture_id"] + ".json")


def test_record_and_lineage_crosslinks_no_fake_seal(tmp_path):
    root, source, writer, cap = prepared(tmp_path)
    receipt = commit(root, writer, cap)
    out = create(root, writer, cap)
    oid = "obj-sha256-" + hashlib.sha256(source.read_bytes()).hexdigest()
    assert out["status"] == "LOCAL_OBJECT_LINK_VERIFIED_UNANCHORED"
    assert out["object_id"] == oid
    meta = json.loads(record_path(root, oid).read_text("utf-8"))
    assert meta["object_id"] == oid
    assert meta["record_scope"] == "LOCAL_UNSEALED_UNANCHORED"
    assert "recorded_at" in meta and "sealed_at" not in meta
    assert meta["sha512"] == hashlib.sha512(source.read_bytes()).hexdigest()
    assert meta["size_bytes"] == source.stat().st_size
    assert meta["vault_relpath"].startswith("10_Evidence/Vault/")
    link = json.loads(link_path(root, cap).read_text("utf-8"))
    assert link["observation_sha256"] and link["observation_id"]
    assert link["acquisition_sequence"] == 1
    assert link["custody_sequence"] == receipt["sequence"] == 2
    assert link["custody_hash"] == receipt["custody_hash"]
    assert link["commit_receipt_sha256"]
    assert verify_object(root, oid)["scope"] == "local_object_bytes_only"
    assert verify_object_link(root, "pc_1", cap["capture_id"]) == out
    assert source.read_bytes() == b"synthetic R11 bytes\x00"


def test_idempotent_replay_never_overwrites_metadata_or_link(tmp_path):
    root, _, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    first = create(root, writer, cap)
    op, lp = record_path(root, first["object_id"]), link_path(root, cap)
    saved = op.read_bytes(), lp.read_bytes()
    assert create(root, writer, cap) == first
    assert (op.read_bytes(), lp.read_bytes()) == saved
    assert verify_chain(root)["event_count"] == 2


def test_identical_bytes_have_one_record_but_distinct_capture_lineage(tmp_path):
    root, source, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    a = create(root, writer, cap)
    other = capture_file(root, source, "pc_1", "synthetic-only")
    publish_capture(root, "pc_1", other["capture_id"], "sole-writer", writer["writer_epoch"])
    commit(root, writer, other)
    b = create(root, writer, other)
    assert a["object_id"] == b["object_id"]
    assert a["custody_hash"] != b["custody_hash"]
    assert len(list((root / "10_Evidence/Records/objects").glob("obj-*.json"))) == 1
    assert len(list((root / "10_Evidence/Records/objects/links/pc_1").glob("*.json"))) == 2
    assert len(list((root / "10_Evidence/Vault/objects").rglob("payload"))) == 1


def test_requires_committed_capture_and_writer_authority(tmp_path):
    root, _, writer, cap = prepared(tmp_path)
    with pytest.raises(ObjectFailure, match="CUSTODY_INVALID"):
        create(root, writer, cap)
    assert not (root / "10_Evidence/Records/objects").exists()
    commit(root, writer, cap)
    for wid, epoch in [("other", writer["writer_epoch"]), ("sole-writer", "wrong")]:
        with pytest.raises(ObjectFailure, match="WRITER_NOT_AUTHORIZED"):
            create_object(root, "pc_1", cap["capture_id"], wid, epoch)
    assert not (root / "10_Evidence/Records/objects").exists()


@pytest.mark.parametrize("target", ["vault", "observation", "commit", "acquisition", "capture"])
def test_tamper_in_any_dependency_breaks_full_link_verification(tmp_path, target):
    root, _, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    out = create(root, writer, cap)
    oid = out["object_id"]
    targets = {
        "vault": root / "10_Evidence" / "Vault" / "objects" / "sha256" /
                 oid[-64:-62] / oid[-62:-60] / oid[-64:] / "payload",
        "observation": root / "10_Evidence/Records/pending/observations/pc_1" / (cap["capture_id"] + ".json"),
        "commit": root / "10_Evidence/Records/commits/pc_1" / (cap["capture_id"] + ".json"),
        "acquisition": root / "10_Evidence/Records/custody/events/00000000000000000001.json",
        "capture": root / "00_Inbox/Drop/pc_1" / cap["capture_id"] / "payload",
    }
    file = targets[target]
    file.write_bytes(b"changed!")
    with pytest.raises(ObjectFailure):
        verify_object_link(root, "pc_1", cap["capture_id"])


def test_duplicate_json_and_symlinked_link_rejected(tmp_path):
    root, _, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    create(root, writer, cap)
    path = link_path(root, cap)
    original = path.read_bytes()
    path.write_bytes(original[:-1] + b',"capture_id":"duplicate"}')
    with pytest.raises(ObjectFailure, match="LINK_TAMPERED"):
        verify_object_link(root, "pc_1", cap["capture_id"])
    path.unlink()
    external = tmp_path / "external.json"
    external.write_bytes(original)
    try:
        path.symlink_to(external)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(ObjectFailure, match="UNSAFE_PATH"):
        verify_object_link(root, "pc_1", cap["capture_id"])


def test_existing_object_conflict_never_overwritten(tmp_path):
    root, _, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    oid = "obj-sha256-" + cap["sha256"]
    path = record_path(root, oid)
    path.parent.mkdir(parents=True)
    path.write_bytes(b'{"forged":true}')
    with pytest.raises(ObjectFailure, match="OBJECT_RECORD_CONFLICT"):
        create(root, writer, cap)
    assert path.read_bytes() == b'{"forged":true}'
    assert not link_path(root, cap).exists()


def test_existing_link_conflict_never_overwritten(tmp_path):
    root, _, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    out = create(root, writer, cap)
    path = link_path(root, cap)
    path.write_bytes(b'{"forged":true}')
    with pytest.raises(ObjectFailure, match="LINK_TAMPERED"):
        create(root, writer, cap)
    assert path.read_bytes() == b'{"forged":true}'


@pytest.mark.parametrize("fault_at", ["object", "link"])
def test_publish_interruption_fails_closed_and_retry_recovers(tmp_path, monkeypatch, fault_at):
    from brain_core import object as mod
    root, _, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    real = mod._publish_record
    def injected(root_, path, data):
        if ("links" in path.parts) == (fault_at == "link"):
            raise OSError("disk full synthetic")
        return real(root_, path, data)
    monkeypatch.setattr(mod, "_publish_record", injected)
    with pytest.raises(ObjectFailure, match="INCOMPLETE_OBJECT"):
        create(root, writer, cap)
    with pytest.raises(ObjectFailure, match="INCOMPLETE_OBJECT_LINK"):
        verify_object_link(root, "pc_1", cap["capture_id"])
    monkeypatch.setattr(mod, "_publish_record", real)
    assert create(root, writer, cap)["status"] == "LOCAL_OBJECT_LINK_VERIFIED_UNANCHORED"


def test_relocated_root_keeps_relative_links(tmp_path):
    root, _, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    create(root, writer, cap)
    moved = tmp_path / "이름 변경 및 공백 #Brain"
    root.rename(moved)
    assert verify_object_link(moved, "pc_1", cap["capture_id"])["status"] == "LOCAL_OBJECT_LINK_VERIFIED_UNANCHORED"
    assert str(root).encode() not in link_path(moved, cap).read_bytes()


def test_cli_create_verify_link_help_and_error_codes(tmp_path):
    root, _, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    base = [sys.executable, str(PROFILE / "brain.py"), "object"]
    args = [cap["capture_id"], "--device-id", "pc_1", "--root", str(root), "--json"]
    create_cmd = base + ["create"] + args + ["--writer-id", "sole-writer", "--writer-epoch", writer["writer_epoch"]]
    ok = subprocess.run(create_cmd, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    assert json.loads(ok.stdout)["status"] == "LOCAL_OBJECT_LINK_VERIFIED_UNANCHORED"
    checked = subprocess.run(base + ["verify-link"] + args, capture_output=True, text=True)
    assert checked.returncode == 0
    assert json.loads(checked.stdout)["object_id"] == json.loads(ok.stdout)["object_id"]
    help_text = subprocess.run(base + ["--help"], capture_output=True, text=True)
    assert "verify-link" in help_text.stdout and "create" in help_text.stdout
    bad = subprocess.run(base + ["verify-link", "not-valid", "--device-id", "pc_1", "--root", str(root), "--json"], capture_output=True, text=True)
    assert bad.returncode == 3 and json.loads(bad.stdout)["error_code"] == "INVALID_ARGUMENT"


def test_no_network_for_create_and_verify(tmp_path, monkeypatch):
    import socket
    root, _, writer, cap = prepared(tmp_path)
    commit(root, writer, cap)
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    create(root, writer, cap)
    assert verify_object_link(root, "pc_1", cap["capture_id"])["status"] == "LOCAL_OBJECT_LINK_VERIFIED_UNANCHORED"
