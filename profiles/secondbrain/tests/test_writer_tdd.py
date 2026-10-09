"""R8 S1 writer pre-commit RED contracts; only synthetic temporary roots."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

PROFILE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROFILE))
from brain_core.capture import capture_file
from brain_core.writer import WriterFailure, configure_writer, publish_capture, verify_publication


def prepared(tmp_path, *, data=b'synthetic\x00 bytes'):
    root = tmp_path / '한글 root space'
    root.mkdir()
    src = tmp_path / 'example.txt'
    src.write_bytes(data)
    capture = capture_file(root, src, 'device_1', 'synthetic-tester')
    writer = configure_writer(root, 'central-writer')
    return root, src, capture, writer


def publish(root, cap, w):
    return publish_capture(root, 'device_1', cap['capture_id'], 'central-writer', w['writer_epoch'])


def test_red_writer_publish_and_reverify(tmp_path):
    root, src, cap, w = prepared(tmp_path)
    output = publish(root, cap, w)
    assert output['status'] == 'VAULT_VERIFIED_UNCOMMITTED'
    assert output['object_id'] == 'obj-sha256-' + hashlib.sha256(src.read_bytes()).hexdigest()
    assert verify_publication(root, 'device_1', cap['capture_id'])['status'] == output['status']
    assert src.read_bytes() == b'synthetic\x00 bytes'
    assert not (root/'10_Evidence/Records/objects').exists()
    assert not (root/'10_Evidence/Records/commits').exists()


def test_requires_explicit_authority_and_correct_epoch(tmp_path):
    root, src, cap, w = prepared(tmp_path)
    for who, epoch in [('other-writer', w['writer_epoch']), ('central-writer', 'wrong')]:
        with pytest.raises(WriterFailure, match='WRITER_NOT_AUTHORIZED'):
            publish_capture(root, 'device_1', cap['capture_id'], who, epoch)
    assert not (root/'10_Evidence').exists()


def test_authority_is_single_creation_no_rotation_without_review(tmp_path):
    root, src, cap, w = prepared(tmp_path)
    with pytest.raises(WriterFailure, match='WRITER_ALREADY_CONFIGURED'):
        configure_writer(root, 'replacement')
    assert w['writer_epoch']


def test_authority_is_required_for_publish(tmp_path):
    root = tmp_path/'brain';root.mkdir()
    src=tmp_path/'sample';src.write_bytes(b'x')
    cap=capture_file(root,src,'device_1','actor')
    with pytest.raises(WriterFailure, match='WRITER_NOT_AUTHORIZED'):
        publish_capture(root,'device_1',cap['capture_id'],'central','epoch')


def test_retry_returns_same_receipt_and_does_not_duplicate_observation(tmp_path):
    root, src, cap, w = prepared(tmp_path)
    a=publish(root,cap,w)
    rp=root/'10_Evidence/Records/pending/ingest/device_1'/f"{cap['capture_id']}.json"
    initial=rp.read_bytes()
    b=publish(root,cap,w)
    assert a['receipt_sha256']==b['receipt_sha256']
    assert rp.read_bytes()==initial
    obs=list((root/'10_Evidence/Records/pending/observations/device_1').glob('*.json'))
    assert len(obs)==1


def test_same_bytes_different_captures_make_independent_observations(tmp_path):
    root, src, cap, w = prepared(tmp_path)
    other=capture_file(root,src,'device_1','synthetic-tester')
    a=publish(root,cap,w);b=publish(root,other,w)
    assert a['object_id']==b['object_id']
    assert a['observation_id']!=b['observation_id']
    assert len(list((root/'10_Evidence/Records/pending/observations/device_1').glob('*.json')))==2
    assert len(list((root/'10_Evidence/Vault/objects').rglob('payload')))==1


def test_tampering_with_receipt_or_observation_never_verifies(tmp_path):
    root, src, cap, w = prepared(tmp_path)
    out=publish(root,cap,w)
    rp=root/'10_Evidence/Records/pending/ingest/device_1'/f"{cap['capture_id']}.json"
    op=root/'10_Evidence/Records/pending/observations/device_1'/f"{cap['capture_id']}.json"
    before=op.read_bytes()
    op.write_bytes(before.replace(b'PENDING_CUSTODY',b'FAKE_CUSTODY_OK'))
    with pytest.raises(WriterFailure, match='INTEGRITY_MISMATCH'):
        verify_publication(root,'device_1',cap['capture_id'])
    op.write_bytes(before)
    r=json.loads(rp.read_text());r['status']='COMMITTED'
    rp.write_text(json.dumps(r),encoding='utf-8')
    with pytest.raises(WriterFailure, match='INTEGRITY_MISMATCH|SCHEMA_INVALID'):
        verify_publication(root,'device_1',cap['capture_id'])


def test_corrupt_existing_vault_must_never_be_overwritten(tmp_path):
    root,src,cap,w=prepared(tmp_path)
    published=publish(root,cap,w)
    rel=published['vault_relpath']
    target=root.joinpath(*rel.split('/'))
    target.write_bytes(b'forged bytes')
    with pytest.raises(WriterFailure, match='INTEGRITY_MISMATCH'):
        publish(root,cap,w)
    assert target.read_bytes()==b'forged bytes'


def test_crash_before_receipt_must_not_claim_publication_and_can_retry(tmp_path,monkeypatch):
    from brain_core import writer as impl
    root,src,cap,w=prepared(tmp_path)
    real=impl._publish_bytes_once
    def fault(root,path,data):
        if '/pending/ingest/' in path.as_posix():
            raise OSError('simulated disk full')
        return real(root,path,data)
    monkeypatch.setattr(impl,'_publish_bytes_once',fault)
    with pytest.raises(WriterFailure, match='INCOMPLETE_PUBLISH'):
        publish(root,cap,w)
    with pytest.raises(WriterFailure, match='INCOMPLETE_PUBLISH'):
        verify_publication(root,'device_1',cap['capture_id'])
    monkeypatch.setattr(impl,'_publish_bytes_once',real)
    assert publish(root,cap,w)['status']=='VAULT_VERIFIED_UNCOMMITTED'


def test_existing_writer_lock_blocks_publication(tmp_path):
    root,src,cap,w=prepared(tmp_path)
    lock=root/'90_System/writer/.active'
    lock.write_text('another local process',encoding='utf-8')
    with pytest.raises(WriterFailure,match='WRITER_BUSY'):
        publish(root,cap,w)
    assert not (root/'10_Evidence').exists()


def test_symlink_vault_branch_refused(tmp_path):
    root,src,cap,w=prepared(tmp_path)
    outside=tmp_path/'outside';outside.mkdir()
    evidence=root/'10_Evidence';evidence.symlink_to(outside,target_is_directory=True)
    with pytest.raises(WriterFailure,match='UNSAFE_PATH'):
        publish(root,cap,w)
    assert not list(outside.rglob('payload'))


def test_root_relocation_does_not_break_receipt(tmp_path):
    root,src,cap,w=prepared(tmp_path)
    publish(root,cap,w)
    new=tmp_path/'moved [한글]';root.rename(new)
    assert verify_publication(new,'device_1',cap['capture_id'])['status']=='VAULT_VERIFIED_UNCOMMITTED'


def test_cli_writer_configure_publish_verify(tmp_path):
    root=tmp_path/'my root';root.mkdir()
    src=tmp_path/'dummy.txt';src.write_bytes(b'dummy')
    cap=capture_file(root,src,'pc1','tester')
    base=[sys.executable,str(PROFILE/'brain.py'),'writer']
    def run(args):
        result=subprocess.run(base+args,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        return json.loads(result.stdout)
    w=run(['init','--root',str(root),'--writer-id','lead','--json'])
    a=run(['publish',cap['capture_id'],'--device-id','pc1','--writer-id','lead','--writer-epoch',w['writer_epoch'],'--root',str(root),'--json'])
    assert a['status']=='VAULT_VERIFIED_UNCOMMITTED'
    b=run(['verify',cap['capture_id'],'--device-id','pc1','--root',str(root),'--json'])
    assert b['sha256']==cap['sha256']


def test_semantically_same_rewritten_receipt_bytes_are_detected(tmp_path):
    root, src, cap, w = prepared(tmp_path)
    publish(root, cap, w)
    path=root/'10_Evidence/Records/pending/ingest/device_1'/f"{cap['capture_id']}.json"
    original=json.loads(path.read_text(encoding='utf-8'))
    path.write_text(json.dumps(original, indent=2, ensure_ascii=False), encoding='utf-8')
    with pytest.raises(WriterFailure, match='INTEGRITY_MISMATCH'):
        verify_publication(root,'device_1',cap['capture_id'])


def test_object_verifier_does_not_pretend_candidate_is_sealed(tmp_path):
    from brain_core.verify import IntegrityFailure, verify_object
    root, src, cap, w = prepared(tmp_path)
    result=publish(root,cap,w)
    with pytest.raises(IntegrityFailure, match='INCOMPLETE_COMMIT'):
        verify_object(root,result['object_id'])


def test_capture_tamper_after_publish_blocks_retry(tmp_path):
    root, src, cap, w = prepared(tmp_path)
    publish(root,cap,w)
    captured=root/'00_Inbox/Drop/device_1'/cap['capture_id']/'payload'
    captured.write_bytes(b'different')
    with pytest.raises(WriterFailure,match='INTEGRITY_MISMATCH'):
        publish(root,cap,w)


def test_no_network_or_provider_use_in_writer(tmp_path,monkeypatch):
    import socket
    root,src,cap,w=prepared(tmp_path)
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k: (_ for _ in ()).throw(AssertionError('network')))
    assert publish(root,cap,w)['status']=='VAULT_VERIFIED_UNCOMMITTED'
