"""R10 TDD: checkpoint comparison requires an operator-retained external copy."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brain_core.capture import capture_file
from brain_core.writer import configure_writer, publish_capture
from brain_core.custody import commit_capture, _event_path, _canon
from brain_core.checkpoint import CheckpointFailure, create_checkpoint, verify_checkpoint


def prepared(tmp_path):
    root = tmp_path / '한글 root with spaces'
    root.mkdir()
    src = tmp_path / 'synthetic.source'
    src.write_bytes(b'synthetic-only\x00')
    auth = configure_writer(root, 'local-1')
    def add_capture():
        cap = capture_file(root, src, 'dev1', 'synthetic')
        publish_capture(root, 'dev1', cap['capture_id'], 'local-1', auth['writer_epoch'])
        commit_capture(root, 'dev1', cap['capture_id'], 'local-1', auth['writer_epoch'])
        return cap
    add_capture()
    return root, src, add_capture


def test_red_export_is_read_only_and_exact_comparison(tmp_path):
    root, _, _ = prepared(tmp_path)
    checkpoint = create_checkpoint(root)
    outside = tmp_path / 'operator-independent-copy.json'
    outside.write_bytes(__import__('rfc8785').dumps(checkpoint))
    before = sorted(str(p) for p in root.rglob('*'))
    outcome = verify_checkpoint(root, outside)
    assert outcome['status'] == 'CHECKPOINT_EXACT_MATCH_EXTERNAL_CUSTODY_UNVERIFIED'
    assert outcome['verified_event_count'] == 2
    assert sorted(str(p) for p in root.rglob('*')) == before


def test_red_suffix_is_explicitly_not_anchored(tmp_path):
    root, _, add = prepared(tmp_path)
    outside = tmp_path/'checkpoint.json'
    outside.write_bytes(__import__('rfc8785').dumps(create_checkpoint(root)))
    add()
    result = verify_checkpoint(root, outside)
    assert result['status'] == 'CHECKPOINT_PREFIX_MATCH_UNANCHORED_SUFFIX'
    assert result['verified_event_count'] == 2
    assert result['current_event_count'] == 4


def test_red_total_rollback_detected(tmp_path):
    root, _, add = prepared(tmp_path)
    add()
    outside = tmp_path/'checkpoint.json'
    outside.write_bytes(__import__('rfc8785').dumps(create_checkpoint(root)))
    _event_path(root,4).unlink()
    _event_path(root,3).unlink()
    with pytest.raises(CheckpointFailure, match='CHECKPOINT_AHEAD_OR_ROLLBACK'):
        verify_checkpoint(root, outside)


def test_red_complete_chain_rewrite_detected(tmp_path):
    root, _, _ = prepared(tmp_path)
    outside = tmp_path/'checkpoint.json'
    outside.write_bytes(__import__('rfc8785').dumps(create_checkpoint(root)))
    # Consistent rewrite of both linked events, not just random corruption.
    from brain_core.custody import _canon, _event, ZERO
    for i in (1, 2):
        path = _event_path(root, i)
        original = json.loads(path.read_text())
        original.pop('event_hash')
        original['capture_id'] = 'CAP-altered'
        if i == 1:
            original['prev_hash'] = ZERO
        else:
            first = json.loads(_event_path(root, 1).read_text())
            original['prev_hash'] = first['event_hash']
        path.write_bytes(_canon(_event(original)))
    with pytest.raises(CheckpointFailure, match='CHECKPOINT_CHAIN_MISMATCH'):
        verify_checkpoint(root, outside)


def test_red_wrong_checkpoint_digest_fails(tmp_path):
    root, _, _ = prepared(tmp_path)
    outside = tmp_path/'checkpoint.json'
    checkpoint = create_checkpoint(root)
    checkpoint['tip_hash'] = 'f'*64
    outside.write_bytes(__import__('rfc8785').dumps(checkpoint))
    with pytest.raises(CheckpointFailure, match='CHECKPOINT_MISMATCH'):
        verify_checkpoint(root, outside)


def test_red_checkpoint_inside_vault_rejected(tmp_path):
    root, _, _ = prepared(tmp_path)
    path = root/'local-checkpoint.json'
    path.write_bytes(__import__('rfc8785').dumps(create_checkpoint(root)))
    with pytest.raises(CheckpointFailure, match='CHECKPOINT_INSIDE_ROOT'):
        verify_checkpoint(root, path)


def test_red_symlink_checkpoint_rejected(tmp_path):
    root, _, _ = prepared(tmp_path)
    outside = tmp_path/'checkpoint.json'
    outside.write_bytes(__import__('rfc8785').dumps(create_checkpoint(root)))
    alias = tmp_path/'alias.json'
    try: alias.symlink_to(outside)
    except (OSError, NotImplementedError): pytest.skip('symlinks unavailable')
    with pytest.raises(CheckpointFailure, match='UNSAFE_CHECKPOINT_PATH'):
        verify_checkpoint(root, alias)


def test_red_uncommitted_chain_not_exportable(tmp_path):
    root = tmp_path/'new-root'
    root.mkdir()
    with pytest.raises(CheckpointFailure, match='CHAIN_NOT_COMMIT_READY'):
        create_checkpoint(root)


def test_red_duplicate_key_rejected(tmp_path):
    root, _, _ = prepared(tmp_path)
    path = tmp_path/'dup.json'
    path.write_text('{"schema_version":1,"schema_version":1}',encoding='utf-8')
    with pytest.raises(CheckpointFailure, match='CHECKPOINT_MALFORMED'):
        verify_checkpoint(root,path)


def test_red_cli_export_verify_and_no_false_certificate(tmp_path):
    root, _, _ = prepared(tmp_path)
    base = [sys.executable, str(Path(__file__).resolve().parents[1]/'brain.py'), 'checkpoint']
    export = subprocess.run(base+['export','--root',str(root),'--json'],capture_output=True,text=True)
    assert export.returncode == 0, export.stderr
    assert json.loads(export.stdout)['event_count'] == 2
    outside = tmp_path/'manual.json'
    outside.write_text(export.stdout.strip(), encoding='utf-8')
    check = subprocess.run(base+['verify',str(outside),'--root',str(root),'--json'],capture_output=True,text=True)
    assert check.returncode == 0, check.stderr
    assert 'EXTERNAL_CUSTODY_UNVERIFIED' in check.stdout


def test_r13n_cli_export_redirect_is_verifiable_byte_for_byte(tmp_path):
    """Documented `checkpoint export --json > file` must round-trip (no trailing newline/CRLF)."""
    root, _, _ = prepared(tmp_path)
    brain = Path(__file__).resolve().parents[1] / 'brain.py'
    out = tmp_path / 'external-checkpoint.json'
    with out.open('wb') as handle:
        done = subprocess.run([sys.executable, str(brain), 'checkpoint', 'export', '--root', str(root), '--json'],
                              stdout=handle, check=False)
    assert done.returncode == 0
    assert not out.read_bytes().endswith((b'\n', b'\r'))
    verify = subprocess.run([sys.executable, str(brain), 'checkpoint', 'verify', str(out), '--root', str(root), '--json'],
                            capture_output=True, text=True, check=False)
    assert verify.returncode == 0, verify.stdout


@pytest.mark.parametrize('flags', [[], ['--json']])
def test_red_cli_export_stdout_is_canonical_bytes(tmp_path, flags):
    root, _, _ = prepared(tmp_path)
    brain = Path(__file__).resolve().parents[1] / 'brain.py'
    done = subprocess.run([sys.executable, str(brain), 'checkpoint', 'export', '--root', str(root)] + flags,
                          capture_output=True)
    assert done.returncode == 0, done.stderr
    assert done.stdout == _canon(create_checkpoint(root))


@pytest.mark.parametrize('flags', [[], ['--json']])
def test_red_cli_export_out_is_canonical_and_no_overwrite(tmp_path, flags):
    root, _, _ = prepared(tmp_path)
    brain = Path(__file__).resolve().parents[1] / 'brain.py'
    outside = tmp_path / '한글 external checkpoint.json'
    command = [sys.executable, str(brain), 'checkpoint', 'export', '--root', str(root), '--out', str(outside)] + flags
    done = subprocess.run(command, capture_output=True)
    assert done.returncode == 0, done.stderr
    assert outside.read_bytes() == _canon(create_checkpoint(root))
    assert done.stdout == b''
    outside.write_bytes(b'existing operator copy')
    refused = subprocess.run(command, capture_output=True)
    assert refused.returncode != 0
    assert outside.read_bytes() == b'existing operator copy'


def test_red_cli_export_out_inside_root_rejected(tmp_path):
    root, _, _ = prepared(tmp_path)
    brain = Path(__file__).resolve().parents[1] / 'brain.py'
    inside = root / 'checkpoint.json'
    done = subprocess.run([sys.executable, str(brain), 'checkpoint', 'export', '--root', str(root), '--out', str(inside)],
                          capture_output=True)
    assert done.returncode != 0
    assert b'CHECKPOINT_INSIDE_ROOT' in done.stderr
    assert not inside.exists()
