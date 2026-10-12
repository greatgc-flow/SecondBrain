"""R9 local append-only custody ledger contracts; synthetic data only."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brain_core.capture import capture_file
from brain_core.writer import configure_writer, publish_capture
from brain_core.custody import CustodyFailure, commit_capture, verify_commit, verify_chain


def prepared(tmp_path):
    root = tmp_path / '한글 Root space'
    root.mkdir()
    original = tmp_path / 'source.bin'
    original.write_bytes(b'unchanged source\x00')
    cap = capture_file(root, original, 'pc_1', 'test-collector')
    policy = configure_writer(root, 'sole-writer')
    publish_capture(root, 'pc_1', cap['capture_id'], 'sole-writer', policy['writer_epoch'])
    return root, original, cap, policy


def commit(root, cap, policy):
    return commit_capture(root, 'pc_1', cap['capture_id'], 'sole-writer', policy['writer_epoch'])


def test_red_commit_two_chained_events_and_recheck(tmp_path):
    root, original, cap, policy = prepared(tmp_path)
    result = commit(root, cap, policy)
    assert result['status'] == 'LOCAL_CHAIN_COMMITTED_UNANCHORED'
    assert result['scope'] == 'local_unanchored_no_legal_authenticity'
    assert result['sequence'] == 2
    assert verify_chain(root)['event_count'] == 2
    assert verify_commit(root, 'pc_1', cap['capture_id'])['sha256'] == cap['sha256']
    assert original.read_bytes() == b'unchanged source\x00'


def test_red_same_receipt_on_retry(tmp_path):
    root, _, cap, policy = prepared(tmp_path)
    first = commit(root, cap, policy)
    second = commit(root, cap, policy)
    assert first == second
    assert verify_chain(root)['event_count'] == 2


def test_red_different_capture_same_bytes_has_independent_events(tmp_path):
    root, original, cap, policy = prepared(tmp_path)
    a = commit(root, cap, policy)
    cap2 = capture_file(root, original, 'pc_1', 'test-collector')
    publish_capture(root, 'pc_1', cap2['capture_id'], 'sole-writer', policy['writer_epoch'])
    b = commit(root, cap2, policy)
    assert a['sha256'] == b['sha256']
    assert a['custody_hash'] != b['custody_hash']
    assert verify_chain(root)['event_count'] == 4


def test_red_wrong_authority_no_mutation(tmp_path):
    root, _, cap, policy = prepared(tmp_path)
    with pytest.raises(CustodyFailure, match='WRITER_NOT_AUTHORIZED'):
        commit_capture(root, 'pc_1', cap['capture_id'], 'other', policy['writer_epoch'])
    assert verify_chain(root)['event_count'] == 0


def test_red_event_tamper_detected(tmp_path):
    root, _, cap, policy = prepared(tmp_path)
    commit(root, cap, policy)
    event = root/'10_Evidence/Records/custody/events/00000000000000000001.json'
    event.write_bytes(event.read_bytes().replace(b'ACQUISITION', b'ALTERED_EVENT'))
    with pytest.raises(CustodyFailure, match='CHAIN_TAMPERED'):
        verify_chain(root)
    with pytest.raises(CustodyFailure, match='CHAIN_TAMPERED'):
        verify_commit(root, 'pc_1', cap['capture_id'])


def test_red_missing_earlier_event_detected(tmp_path):
    root, _, cap, policy = prepared(tmp_path)
    commit(root, cap, policy)
    (root/'10_Evidence/Records/custody/events/00000000000000000001.json').unlink()
    with pytest.raises(CustodyFailure, match='CHAIN_TAMPERED'):
        verify_chain(root)


def test_red_append_fail_recovers_only_same_capture(tmp_path, monkeypatch):
    from brain_core import custody as mod
    root, _, cap, policy = prepared(tmp_path)
    real = mod._publish_event
    def injected(root_, path, data):
        if '00000000000000000002.json' in str(path):
            raise OSError('simulated disk-full')
        return real(root_, path, data)
    monkeypatch.setattr(mod, '_publish_event', injected)
    with pytest.raises(CustodyFailure, match='INCOMPLETE_CHAIN'):
        commit(root, cap, policy)
    assert verify_chain(root)['event_count'] == 1
    with pytest.raises(CustodyFailure, match='INCOMPLETE_COMMIT'):
        verify_commit(root, 'pc_1', cap['capture_id'])
    monkeypatch.setattr(mod, '_publish_event', real)
    result = commit(root, cap, policy)
    assert result['sequence'] == 2
    assert verify_chain(root)['event_count'] == 2


def test_red_committed_receipt_tamper_detected(tmp_path):
    root, _, cap, policy = prepared(tmp_path)
    commit(root, cap, policy)
    path = root/'10_Evidence/Records/commits/pc_1'/f"{cap['capture_id']}.json"
    payload=json.loads(path.read_text(encoding='utf-8'))
    payload['sha256']='0'*64
    path.write_text(json.dumps(payload), encoding='utf-8')
    with pytest.raises(CustodyFailure, match='COMMIT_TAMPERED'):
        verify_commit(root, 'pc_1', cap['capture_id'])


def test_red_crash_before_receipt_is_idempotent(tmp_path, monkeypatch):
    from brain_core import custody as mod
    root, _, cap, policy = prepared(tmp_path)
    real=mod._publish_commit
    def fail(*_): raise OSError('disk full')
    monkeypatch.setattr(mod, '_publish_commit', fail)
    with pytest.raises(CustodyFailure, match='INCOMPLETE_COMMIT'):
        commit(root, cap, policy)
    assert verify_chain(root)['event_count']==2
    monkeypatch.setattr(mod, '_publish_commit', real)
    assert commit(root, cap, policy)['sequence']==2
    assert verify_chain(root)['event_count']==2


def test_red_relocation_and_bad_event_shape(tmp_path):
    root, _, cap, policy = prepared(tmp_path)
    commit(root, cap, policy)
    new = tmp_path/'새 이름 (moved)'
    root.rename(new)
    assert verify_commit(new,'pc_1',cap['capture_id'])['sequence']==2
    event = new/'10_Evidence/Records/custody/events/00000000000000000002.json'
    blob = event.read_text(encoding='utf-8')
    event.write_text(blob.replace('"sequence":2', '"sequence":3'), encoding='utf-8')
    with pytest.raises(CustodyFailure, match='CHAIN_TAMPERED'):
        verify_chain(new)


def test_red_no_unverified_object_or_final_erl(tmp_path):
    root, _, cap, policy = prepared(tmp_path)
    result = commit(root, cap, policy)
    assert result['status'] != 'SEALED'
    assert not (root/'10_Evidence/Records/objects').exists()


def test_cli_commit_verify_chain(tmp_path):
    import subprocess
    root, _, cap, policy = prepared(tmp_path)
    base = [sys.executable, str(Path(__file__).resolve().parents[1]/'brain.py'), 'custody']
    for args in [
        ['commit', cap['capture_id'], '--device-id', 'pc_1', '--writer-id', 'sole-writer',
         '--writer-epoch', policy['writer_epoch']],
        ['verify', cap['capture_id'], '--device-id', 'pc_1'],
        ['chain'],
    ]:
        result = subprocess.run(base+args+['--root',str(root),'--json'],capture_output=True,text=True)
        assert result.returncode == 0, result.stderr
        assert 'status' in json.loads(result.stdout)


def test_rfc8785_utf16_key_order():
    import rfc8785
    # UTF-16 code unit ordering differs from Python Unicode codepoint ordering.
    encoded = rfc8785.dumps({'\uE000': 1, '\U00010000': 2})
    assert encoded == b'{"\xf0\x90\x80\x80":2,"\xee\x80\x80":1}'


def test_partial_chain_blocks_unrelated_capture(tmp_path, monkeypatch):
    from brain_core import custody as mod
    root, original, cap, policy = prepared(tmp_path)
    real = mod._publish_event
    def fail_second(root_, path, data):
        if path.name == '00000000000000000002.json':
            raise OSError('fault')
        return real(root_, path, data)
    monkeypatch.setattr(mod, '_publish_event', fail_second)
    with pytest.raises(CustodyFailure, match='INCOMPLETE_CHAIN'):
        commit(root, cap, policy)
    cap2 = capture_file(root, original, 'pc_1', 'tester')
    publish_capture(root, 'pc_1', cap2['capture_id'], 'sole-writer', policy['writer_epoch'])
    with pytest.raises(CustodyFailure, match='INCOMPLETE_CHAIN'):
        commit(root, cap2, policy)
    monkeypatch.setattr(mod, '_publish_event', real)
    assert commit(root, cap, policy)['sequence'] == 2
    assert commit(root, cap2, policy)['sequence'] == 4


def test_unexpected_event_filename_is_rejected(tmp_path):
    root, _, cap, policy = prepared(tmp_path)
    commit(root, cap, policy)
    directory = root/'10_Evidence/Records/custody/events'
    (directory/'invalid.json').write_text('{}', encoding='utf-8')
    with pytest.raises(CustodyFailure, match='CHAIN_TAMPERED'):
        verify_chain(root)


def test_custody_missing_package_fails_closed(tmp_path, monkeypatch):
    from brain_core import custody as mod
    root, _, cap, policy = prepared(tmp_path)
    def missing(_):
        raise CustodyFailure('RFC8785_NOT_INSTALLED')
    monkeypatch.setattr(mod, '_canon', missing)
    with pytest.raises(CustodyFailure, match='RFC8785_NOT_INSTALLED'):
        commit(root, cap, policy)
    assert not (root/'10_Evidence/Records/commits').exists()


def test_writer_lock_blocks_ledger_append(tmp_path):
    root, _, cap, policy = prepared(tmp_path)
    (root/'90_System/writer/.active').write_text('busy\n', encoding='utf-8')
    with pytest.raises(CustodyFailure, match='WRITER_BUSY'):
        commit(root, cap, policy)
    assert verify_chain(root)['event_count'] == 0
