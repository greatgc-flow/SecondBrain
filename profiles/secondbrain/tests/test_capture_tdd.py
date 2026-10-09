"""R7 RED cases: capture-only evidence intake, synthetic files and no internet."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))
from brain_core.capture import CaptureFailure, capture_file, verify_capture


def setup(tmp_path):
    root = tmp_path / "한글 root space #"
    root.mkdir()
    source = tmp_path / "원본 자료.txt"
    source.write_bytes(b"\x00hello capture\xff")
    return root, source


def test_captures_original_unmodified_and_publish_ready_last(tmp_path):
    root, source = setup(tmp_path)
    before = source.read_bytes()
    result = capture_file(root, source, "device_A", "tester")
    assert result["status"] == "READY"
    assert result["scope"] == "capture_only_uncommitted"
    assert source.read_bytes() == before
    assert verify_capture(root, "device_A", result["capture_id"])["status"] == "READY"
    assert result["sha256"] == hashlib.sha256(before).hexdigest()
    assert not (root / '10_Evidence').exists()


def test_same_capture_id_is_idempotent_and_different_bytes_conflict(tmp_path):
    root, source = setup(tmp_path)
    cid = "CAP-018f7a3e-9b4e-7c19-8e42-09abc1234567"
    a = capture_file(root, source, "device_A", "tester", capture_id=cid)
    b = capture_file(root, source, "device_A", "tester", capture_id=cid)
    assert b["already_exists"] is True
    assert a["sha256"] == b["sha256"]
    source.write_bytes(b"other bytes")
    with pytest.raises(CaptureFailure, match="CAPTURE_CONFLICT"):
        capture_file(root, source, "device_A", "tester", capture_id=cid)


def test_same_bytes_different_capture_ids_remain_distinct_observations(tmp_path):
    root, source = setup(tmp_path)
    a = capture_file(root, source, "device_A", "tester")
    b = capture_file(root, source, "device_A", "tester")
    assert a["capture_id"] != b["capture_id"]
    assert a["sha256"] == b["sha256"]
    assert len(list((root/"00_Inbox/Drop/device_A").iterdir())) == 2


def test_tampered_payload_and_receipt_rejected(tmp_path):
    root, source = setup(tmp_path)
    result = capture_file(root, source, "d1", "tester")
    location = root / "00_Inbox/Drop/d1" / result["capture_id"]
    (location/"payload").write_bytes(b"tamper")
    with pytest.raises(CaptureFailure, match="INTEGRITY_MISMATCH"):
        verify_capture(root, "d1", result["capture_id"])
    (location/"payload").write_bytes(source.read_bytes())
    receipt = json.loads((location/"capture.receipt.json").read_text())
    receipt["collector"] = "forged"
    (location/"capture.receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(CaptureFailure, match="RECEIPT_TAMPERED"):
        verify_capture(root, "d1", result["capture_id"])


def test_incomplete_directory_fails_closed(tmp_path):
    root, source = setup(tmp_path)
    cid="CAP-018f7a3e-9b4e-7c19-8e42-09abc1234567"
    pending=root/"00_Inbox/Drop/d1"/cid
    pending.mkdir(parents=True)
    (pending/"payload").write_bytes(b"unfinished")
    with pytest.raises(CaptureFailure, match="INCOMPLETE_CAPTURE"):
        verify_capture(root,"d1",cid)
    with pytest.raises(CaptureFailure, match="INCOMPLETE_CAPTURE"):
        capture_file(root,source,"d1","tester",capture_id=cid)


def test_rejects_source_symlink_and_directory(tmp_path):
    root, source = setup(tmp_path)
    symlink=tmp_path/'link';symlink.symlink_to(source)
    with pytest.raises(CaptureFailure,match="UNSAFE_SOURCE"):
        capture_file(root,symlink,'d1','tester')
    with pytest.raises(CaptureFailure,match="UNSAFE_SOURCE"):
        capture_file(root,tmp_path,'d1','tester')


@pytest.mark.parametrize('device,cid',[("../bad",None),("bad/name",None),("d1","../../other"),("d1","CAP-invalid")])
def test_rejects_unsafe_user_identifiers(tmp_path,device,cid):
    root, source=setup(tmp_path)
    with pytest.raises(CaptureFailure,match="INVALID_ARGUMENT"):
        capture_file(root,source,device,'tester',capture_id=cid)


def test_missing_root_refused(tmp_path):
    source=tmp_path/'source';source.write_bytes(b'a')
    with pytest.raises(CaptureFailure,match="INVALID_ROOT"):
        capture_file(tmp_path/'missing',source,'d1','tester')


def test_capture_can_relocate_root_and_empty_source(tmp_path):
    root, source=setup(tmp_path)
    source.write_bytes(b'')
    result=capture_file(root,source,'d1','tester')
    new=tmp_path/'옮긴 root [한글]';root.rename(new)
    assert verify_capture(new,'d1',result['capture_id'])['sha256']==hashlib.sha256(b'').hexdigest()


def test_cli_capture_json_and_verify(tmp_path):
    root, source=setup(tmp_path)
    cmd=[sys.executable,str(PROFILE/'brain.py'),'capture','file',str(source),'--root',str(root),'--device-id','d1','--collector','tester','--json']
    run=subprocess.run(cmd,capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    result=json.loads(run.stdout)
    assert result['status']=='READY'
    verify=subprocess.run([sys.executable,str(PROFILE/'brain.py'),'capture','verify',result['capture_id'],'--root',str(root),'--device-id','d1','--json'],capture_output=True,text=True)
    assert verify.returncode==0,verify.stderr
    assert json.loads(verify.stdout)['status']=='READY'


def test_no_network_calls(tmp_path,monkeypatch):
    root, source=setup(tmp_path)
    import socket
    def blocked(*args,**kwargs):raise AssertionError('network not allowed')
    monkeypatch.setattr(socket,'create_connection',blocked)
    assert capture_file(root,source,'d1','tester')['status']=='READY'


def test_truncated_or_missing_ready_marker_is_not_accepted(tmp_path):
    root, source=setup(tmp_path)
    result=capture_file(root,source,'d1','tester')
    marker=root/'00_Inbox/Drop/d1'/result['capture_id']/'.ready'
    marker.write_text('{',encoding='utf-8')
    with pytest.raises(CaptureFailure,match='INCOMPLETE_CAPTURE'):
        verify_capture(root,'d1',result['capture_id'])
    marker.unlink()
    with pytest.raises(CaptureFailure,match='INCOMPLETE_CAPTURE'):
        verify_capture(root,'d1',result['capture_id'])


def test_root_symlink_rejected(tmp_path):
    root, source=setup(tmp_path)
    alias=tmp_path/'alias';alias.symlink_to(root,target_is_directory=True)
    with pytest.raises(CaptureFailure, match='INVALID_ROOT'):
        capture_file(alias,source,'d1','tester')


def test_receipt_schema_fails_if_required_field_missing(tmp_path):
    root, source=setup(tmp_path)
    result=capture_file(root,source,'d1','tester')
    location=root/'00_Inbox/Drop/d1'/result['capture_id']
    rp=location/'capture.receipt.json'
    record=json.loads(rp.read_text());del record['sha256']
    rp.write_text(json.dumps(record),encoding='utf-8')
    with pytest.raises(CaptureFailure, match='RECEIPT_TAMPERED|SCHEMA_INVALID'):
        verify_capture(root,'d1',result['capture_id'])


def test_simulated_failure_before_marker_leaves_incomplete_not_success(tmp_path,monkeypatch):
    root, source=setup(tmp_path)
    from brain_core import capture as impl
    cid='CAP-018f7a3e-9b4e-7c19-8e42-09abc1234567'
    real=impl._write_exclusive
    def fail_marker(path, blob):
        if path.name=='.ready':
            raise OSError('injected disk failure')
        return real(path,blob)
    monkeypatch.setattr(impl,'_write_exclusive',fail_marker)
    with pytest.raises(CaptureFailure,match='INCOMPLETE_CAPTURE'):
        capture_file(root,source,'d1','tester',capture_id=cid)
    assert source.read_bytes()==b'\x00hello capture\xff'
    with pytest.raises(CaptureFailure,match='INCOMPLETE_CAPTURE'):
        verify_capture(root,'d1',cid)
    assert not (root/'00_Inbox/Drop/d1'/cid/'.ready').exists()


def test_source_parent_symlink_rejected(tmp_path):
    root, source=setup(tmp_path)
    folder=tmp_path/'linked-folder'
    folder.symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(CaptureFailure,match='UNSAFE_SOURCE'):
        capture_file(root,folder/source.name,'d1','tester')


def test_incorrect_device_even_with_valid_id_fails_closed(tmp_path):
    root, source=setup(tmp_path)
    result=capture_file(root,source,'d1','tester')
    with pytest.raises(CaptureFailure,match='INCOMPLETE_CAPTURE'):
        verify_capture(root,'d2',result['capture_id'])
