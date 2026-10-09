"""R9 local unanchored RFC8785 event chain; NOT legal authenticity or WORM.

Strictly one local writer; immutable per-sequence files and paired acquisition /
custody events. Rewriting *all* local history may evade detection without a trusted
external anchor; cross-device cloud writers are not synchronized by this code.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any

from .verify import IntegrityFailure, _safe_regular_file, _strict_json
from .writer import (WriterFailure, _root, _authority, _writer_lock,
                     _publish_bytes_once, verify_publication)

ZERO = '0' * 64
EVENT_NAME = re.compile(r'[0-9]{20}\.json\Z')
CORE_KEYS = frozenset({'schema_version','sequence','event_type','prev_hash',
                       'device_id','capture_id','writer_id','writer_epoch',
                       'object_id','sha256','observation_sha256'})


class CustodyFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _canon(value: Any) -> bytes:
    try:
        import rfc8785
    except ImportError as exc:
        raise CustodyFailure('RFC8785_NOT_INSTALLED') from exc
    try:
        return rfc8785.dumps(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise CustodyFailure('JCS_INVALID') from exc


def _events(root: Path) -> Path:
    return root / '10_Evidence' / 'Records' / 'custody' / 'events'


def _event_path(root: Path, sequence: int) -> Path:
    return _events(root) / f'{sequence:020d}.json'


def _receipt_path(root: Path, device: str, capture_id: str) -> Path:
    return root/'10_Evidence'/'Records'/'commits'/device/f'{capture_id}.json'


def _read(root: Path, path: Path, *, missing: str) -> dict[str, Any]:
    try:
        _safe_regular_file(root, path, missing_code=missing)
        return _strict_json(path)
    except IntegrityFailure as exc:
        raise CustodyFailure('UNSAFE_PATH' if exc.code == 'UNSAFE_PATH' else missing) from exc


def _scan(root: Path) -> list[dict[str, Any]]:
    folder = _events(root)
    if not folder.exists() and not folder.is_symlink():
        return []
    if folder.is_symlink() or not folder.is_dir():
        raise CustodyFailure('UNSAFE_PATH')
    try:
        names = sorted(p.name for p in folder.iterdir() if p.suffix == '.json')
    except OSError as exc:
        raise CustodyFailure('CHAIN_TAMPERED') from exc
    if not all(EVENT_NAME.fullmatch(n) for n in names):
        raise CustodyFailure('CHAIN_TAMPERED')
    chain: list[dict[str, Any]] = []
    prev = ZERO
    for idx, name in enumerate(names, start=1):
        if name != f'{idx:020d}.json':
            raise CustodyFailure('CHAIN_TAMPERED')
        path = folder/name
        try:
            event = _read(root, path, missing='CHAIN_TAMPERED')
            if set(event) != CORE_KEYS | {'event_hash'} or type(event['sequence']) is not int:
                raise CustodyFailure('CHAIN_TAMPERED')
            if (event['schema_version'] != 1 or event['sequence'] != idx or
                event['event_type'] != ('ACQUISITION' if idx % 2 else 'CUSTODY') or
                event['prev_hash'] != prev):
                raise CustodyFailure('CHAIN_TAMPERED')
            core = {k: event[k] for k in CORE_KEYS}
            digest = hashlib.sha256(_canon(core)).hexdigest()
            if (event['event_hash'] != digest or
                    path.read_bytes() != _canon(event)):
                raise CustodyFailure('CHAIN_TAMPERED')
            if idx % 2 == 0:
                earlier = chain[-1]
                for key in CORE_KEYS - {'event_type','sequence','prev_hash'}:
                    if event[key] != earlier[key]:
                        raise CustodyFailure('CHAIN_TAMPERED')
            prev = digest
            chain.append(event)
        except (CustodyFailure, OSError, KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, CustodyFailure) and exc.code == 'RFC8785_NOT_INSTALLED':
                raise
            raise CustodyFailure('CHAIN_TAMPERED') from exc
    return chain


def verify_chain(root: str | Path) -> dict[str, Any]:
    root = _root_checked(root)
    chain = _scan(root)
    return {'status': 'LOCAL_CHAIN_VALID_UNANCHORED',
            'event_count': len(chain),
            'tip_hash': chain[-1]['event_hash'] if chain else ZERO,
            'scope': 'local_hash_integrity_only_no_external_anchor'}


def _root_checked(path: str | Path) -> Path:
    try:
        return _root(path)
    except WriterFailure as exc:
        raise CustodyFailure(exc.code) from exc


def _publication(root: Path, device: str, capture_id: str) -> dict[str, Any]:
    try:
        return verify_publication(root, device, capture_id)
    except WriterFailure as exc:
        raise CustodyFailure('PUBLICATION_INVALID') from exc


def _core(sequence: int, event_type: str, prev: str,
          pub: dict[str, Any], writer: dict[str, Any]) -> dict[str, Any]:
    return {'schema_version': 1, 'sequence': sequence, 'event_type': event_type,
            'prev_hash': prev, 'device_id': pub['device_id'],
            'capture_id': pub['capture_id'], 'writer_id': writer['writer_id'],
            'writer_epoch': writer['writer_epoch'], 'object_id': pub['object_id'],
            'sha256': pub['sha256'], 'observation_sha256': pub['observation_sha256']}


def _event(core: dict[str, Any]) -> dict[str, Any]:
    return {**core, 'event_hash': hashlib.sha256(_canon(core)).hexdigest()}


def _publish_event(root: Path, path: Path, data: bytes) -> None:
    _publish_bytes_once(root, path, data)


def _publish_commit(root: Path, path: Path, data: bytes) -> None:
    _publish_bytes_once(root, path, data)


def _expected_receipt(pub: dict[str, Any], seq: int, event_hash: str) -> dict[str, Any]:
    return {'schema_version': 1, 'status': 'LOCAL_CHAIN_COMMITTED_UNANCHORED',
            'device_id': pub['device_id'], 'capture_id': pub['capture_id'],
            'writer_id': pub['writer_id'], 'writer_epoch': pub['writer_epoch'],
            'object_id': pub['object_id'], 'sha256': pub['sha256'],
            'observation_sha256': pub['observation_sha256'],
            'sequence': seq, 'custody_hash': event_hash}


def _with_scope(r: dict[str, Any]) -> dict[str, Any]:
    return {**r, 'scope': 'local_unanchored_no_legal_authenticity'}


def commit_capture(root: str | Path, device_id: str, capture_id: str,
                   writer_id: str, writer_epoch: str) -> dict[str, Any]:
    """Create a local, crash-recoverable pair of immutable linked events.

    The final receipt is a *local ledger record*, not a sealed EvidenceObject,
    trusted timestamp, forensic custody certification or legal endorsement.
    """
    root = _root_checked(root)
    pub = _publication(root, device_id, capture_id)
    try:
        writer = _authority(root)
    except WriterFailure as exc:
        raise CustodyFailure('WRITER_NOT_AUTHORIZED') from exc
    if (writer_id, writer_epoch) != (writer['writer_id'], writer['writer_epoch']):
        raise CustodyFailure('WRITER_NOT_AUTHORIZED')
    try:
        with _writer_lock(root):
            if _authority(root) != writer:
                raise CustodyFailure('WRITER_NOT_AUTHORIZED')
            chain = _scan(root)
            matches = [i for i, ev in enumerate(chain)
                       if (ev['device_id'], ev['capture_id']) == (device_id, capture_id)]
            if matches:
                first = matches[0]
                if first != len(chain)-1 and not (len(matches) == 2 and first == len(chain)-2):
                    # Already-complete earlier capture is checked through its receipt.
                    if len(matches) != 2:
                        raise CustodyFailure('CHAIN_TAMPERED')
                for i in matches:
                    ev = chain[i]
                    expected = _event(_core(i+1, ev['event_type'], ev['prev_hash'], pub, writer))
                    if ev != expected:
                        raise CustodyFailure('CHAIN_TAMPERED')
                if len(matches) == 2:
                    last = chain[matches[-1]]
                    receipt = _expected_receipt(pub, last['sequence'], last['event_hash'])
                    _publish_commit(root, _receipt_path(root, device_id, capture_id), _canon(receipt))
                    return verify_commit(root, device_id, capture_id)
                if first != len(chain)-1 or len(chain) % 2 != 1:
                    raise CustodyFailure('CHAIN_TAMPERED')
            else:
                if len(chain) % 2:
                    raise CustodyFailure('INCOMPLETE_CHAIN')
                core = _core(len(chain)+1, 'ACQUISITION',
                             chain[-1]['event_hash'] if chain else ZERO, pub, writer)
                event = _event(core)
                _publish_event(root, _event_path(root, core['sequence']), _canon(event))
                chain.append(event)
            core = _core(len(chain)+1, 'CUSTODY', chain[-1]['event_hash'], pub, writer)
            event = _event(core)
            _publish_event(root, _event_path(root, core['sequence']), _canon(event))
            receipt = _expected_receipt(pub, core['sequence'], event['event_hash'])
            _publish_commit(root, _receipt_path(root, device_id, capture_id), _canon(receipt))
            return verify_commit(root, device_id, capture_id)
    except CustodyFailure:
        raise
    except WriterFailure as exc:
        if exc.code in ('WRITER_BUSY', 'WRITER_NOT_AUTHORIZED', 'UNSAFE_PATH', 'RECOVERY_HOLD'):
            raise CustodyFailure(exc.code) from exc
        label = 'INCOMPLETE_COMMIT' if len(_scan(root)) % 2 == 0 else 'INCOMPLETE_CHAIN'
        raise CustodyFailure(label) from exc
    except OSError as exc:
        label = 'INCOMPLETE_COMMIT' if len(_scan(root)) % 2 == 0 else 'INCOMPLETE_CHAIN'
        raise CustodyFailure(label) from exc


def verify_commit(root: str | Path, device_id: str, capture_id: str) -> dict[str, Any]:
    root = _root_checked(root)
    pub = _publication(root, device_id, capture_id)
    chain = _scan(root)
    hits = [e for e in chain if (e['device_id'], e['capture_id']) == (device_id, capture_id)]
    if len(hits) != 2 or hits[0]['event_type'] != 'ACQUISITION' or hits[1]['event_type'] != 'CUSTODY':
        raise CustodyFailure('INCOMPLETE_COMMIT')
    expected = _expected_receipt(pub, hits[1]['sequence'], hits[1]['event_hash'])
    path = _receipt_path(root, device_id, capture_id)
    try:
        actual = _read(root, path, missing='INCOMPLETE_COMMIT')
        if actual != expected or path.read_bytes() != _canon(expected):
            raise CustodyFailure('COMMIT_TAMPERED')
    except OSError as exc:
        raise CustodyFailure('COMMIT_TAMPERED') from exc
    return _with_scope(expected)
