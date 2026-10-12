"""S1/T2 read-only byte verifier: SEM-01..03, real payload and fail-closed cases."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT_OF_SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_OF_SOURCE))

from brain_core.verify import IntegrityFailure, verify_object  # RED: package not yet implemented


def fixture(tmp_path: Path, contents: bytes = b"Evidence bytes\x00\xff"):
    root = tmp_path / "내 자료 Main Brain"
    root.mkdir()
    digest = hashlib.sha256(contents).hexdigest()
    object_id = f"obj-sha256-{digest}"
    rel = f"10_Evidence/Vault/objects/sha256/{digest[:2]}/{digest[2:4]}/{digest}/payload"
    payload = root / rel
    payload.parent.mkdir(parents=True)
    payload.write_bytes(contents)
    record = {
        "schema_version": 2,
        "object_id": object_id,
        "sha256": digest,
        "sha512": hashlib.sha512(contents).hexdigest(),
        "size_bytes": len(contents),
        "media_type": "application/octet-stream",
        "sealed_at": "2026-10-10T10:00:00+09:00",
        "vault_relpath": rel,
        "source_fidelity": "unknown",
    }
    rp = root / "10_Evidence/Records/objects" / (object_id + ".json")
    rp.parent.mkdir(parents=True)
    rp.write_text(json.dumps(record), encoding="utf-8")
    return root, object_id, rp, payload, record


def change(rp, data):
    rp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_valid_real_bytes_and_original_untouched(tmp_path):
    root, oid, rp, payload, _ = fixture(tmp_path)
    before = payload.read_bytes()
    result = verify_object(root, oid)
    assert result["status"] == "PASS"
    assert result["object_id"] == oid
    assert payload.read_bytes() == before


def test_sem01_object_id_digest_conflict(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    r["sha256"] = "b" * 64
    change(rp, r)
    with pytest.raises(IntegrityFailure, match="INTEGRITY_MISMATCH"):
        verify_object(root, oid)


def test_sem02_path_digest_conflict(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    r["vault_relpath"] = "10_Evidence/Vault/objects/sha256/bb/bb/" + "b"*64 + "/payload"
    change(rp, r)
    with pytest.raises(IntegrityFailure, match="UNSAFE_PATH"):
        verify_object(root, oid)


def test_sem03_sha512_payload_conflict(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    r["sha512"] = "c" * 128
    change(rp, r)
    with pytest.raises(IntegrityFailure, match="INTEGRITY_MISMATCH"):
        verify_object(root, oid)


def test_payload_bit_flip_detected(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    payload.write_bytes(b"modified bytes")
    with pytest.raises(IntegrityFailure, match="INTEGRITY_MISMATCH"):
        verify_object(root, oid)


def test_missing_payload_detected(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    payload.unlink()
    with pytest.raises(IntegrityFailure, match="NOT_HYDRATED"):
        verify_object(root, oid)


def test_vault_symlink_to_external_is_denied(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    external = tmp_path / "external"; external.write_bytes(payload.read_bytes())
    payload.unlink()
    try: payload.symlink_to(external)
    except (OSError, NotImplementedError): pytest.skip("symlink creation blocked by OS")
    with pytest.raises(IntegrityFailure, match="UNSAFE_PATH"):
        verify_object(root, oid)


def test_duplicate_json_key_is_denied(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    raw = json.dumps(r)
    rp.write_text(raw[:-1] + ',"size_bytes": 999}', encoding='utf-8')
    with pytest.raises(IntegrityFailure, match="JSON_DUPLICATE_KEY"):
        verify_object(root, oid)


def test_missing_schema_required_field_fails(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    r.pop("source_fidelity")
    change(rp, r)
    with pytest.raises(IntegrityFailure, match="SCHEMA_INVALID"):
        verify_object(root, oid)


def test_works_after_root_renamed_and_with_unicode(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    root2 = tmp_path / "새 루트 한글 # second brain"
    root.rename(root2)
    assert verify_object(root2, oid)["status"] == "PASS"


def test_cli_json_success_and_nonzero_fail(tmp_path):
    root, oid, rp, payload, r = fixture(tmp_path)
    cmd = [sys.executable, str(ROOT_OF_SOURCE / "brain.py"), "object", "verify", oid, "--root", str(root), "--json"]
    ok = subprocess.run(cmd, text=True, capture_output=True, check=False)
    assert ok.returncode == 0, ok.stderr
    assert json.loads(ok.stdout)["status"] == "PASS"
    payload.write_bytes(b"broken")
    bad = subprocess.run(cmd, text=True, capture_output=True, check=False)
    assert bad.returncode != 0
    assert json.loads(bad.stdout)["error_code"] == "INTEGRITY_MISMATCH"


def test_no_network_or_runtime_ai_dependency(tmp_path, monkeypatch):
    root, oid, *_ = fixture(tmp_path)
    import socket
    def no_network(*args, **kwargs): raise AssertionError("Network access attempted")
    monkeypatch.setattr(socket, "create_connection", no_network)
    assert verify_object(root, oid)["status"] == "PASS"


def test_empty_bytes_allowed_and_verified(tmp_path):
    root, oid, _, _, _ = fixture(tmp_path, b"")
    result = verify_object(root, oid)
    assert result["size_bytes"] == 0
    assert result["sha256"] == hashlib.sha256(b"").hexdigest()


def test_missing_metadata_is_incomplete_commit(tmp_path):
    root, oid, record, *_ = fixture(tmp_path)
    record.unlink()
    with pytest.raises(IntegrityFailure, match="INCOMPLETE_COMMIT"):
        verify_object(root, oid)


def test_unknown_object_id_rejected_without_path_access(tmp_path):
    root = tmp_path / "new brain"
    root.mkdir()
    with pytest.raises(IntegrityFailure, match="SCHEMA_INVALID"):
        verify_object(root, "../../etc/passwd")


def test_record_symlink_denied(tmp_path):
    root, oid, record, payload, _ = fixture(tmp_path)
    backup = tmp_path / "record.json"; backup.write_bytes(record.read_bytes()); record.unlink()
    try: record.symlink_to(backup)
    except (OSError, NotImplementedError): pytest.skip("symlink creation blocked")
    with pytest.raises(IntegrityFailure, match="UNSAFE_PATH"):
        verify_object(root, oid)


def test_invalid_time_rejected(tmp_path):
    root, oid, record, payload, obj = fixture(tmp_path)
    obj["sealed_at"] = "2026-13-45T33:99:00+09:00"
    change(record, obj)
    with pytest.raises(IntegrityFailure, match="SCHEMA_INVALID"):
        verify_object(root, oid)


def test_unknown_claim_in_canonical_record_rejected(tmp_path):
    root, oid, record, payload, obj = fixture(tmp_path)
    obj["erl"] = "ERL-5"
    change(record, obj)
    with pytest.raises(IntegrityFailure, match="SCHEMA_INVALID"):
        verify_object(root, oid)


def test_multimegabyte_stream_verified(tmp_path):
    contents = bytes(range(256)) * 16385
    root, oid, record, payload, obj = fixture(tmp_path, contents)
    assert verify_object(root, oid)["status"] == "PASS"


def test_old_version_schema_rejected(tmp_path):
    root, oid, record, payload, obj = fixture(tmp_path)
    obj["schema_version"] = 1
    change(record, obj)
    with pytest.raises(IntegrityFailure, match="SCHEMA_INVALID"):
        verify_object(root, oid)
