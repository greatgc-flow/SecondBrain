"""R8 S1 local single-writer *pre-commit* vault publication.

A published payload is NOT SEALED or COMMITTED. This module does not write a
canonical EvidenceObject, AcquisitionEvent, CustodyEvent, or commit receipt.
No cloud/distributed writer exclusion, notarization, or legal authenticity.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import secrets
import uuid
from typing import Any, Iterator

from .capture import (
    CaptureFailure, _copy_source, _encode, _ensure_parent, _fsync_dir,
    _write_exclusive, verify_capture,
)
from .verify import IntegrityFailure, _digest_fd, _safe_regular_file, _strict_json, _unsafe_windows_attributes
from .recovery import recovery_hold_present


class WriterFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _root(path: str | Path) -> Path:
    root = Path(path).expanduser().absolute()
    if (not root.is_dir() or root.is_symlink() or _unsafe_windows_attributes(root.lstat()) or
            (hasattr(root, 'is_junction') and root.is_junction())):
        raise WriterFailure('INVALID_ROOT')
    return root


def _authority_path(root: Path) -> Path:
    return root / '90_System' / 'writer' / 'authority.json'


def _read_doc(root: Path, file: Path, *, missing: str) -> dict[str, Any]:
    try:
        _safe_regular_file(root, file, missing_code=missing)
        return _strict_json(file)
    except IntegrityFailure as exc:
        if exc.code == 'UNSAFE_PATH':
            raise WriterFailure('UNSAFE_PATH') from exc
        if exc.code == 'JSON_DUPLICATE_KEY':
            raise WriterFailure('INTEGRITY_MISMATCH') from exc
        raise WriterFailure(missing if exc.code in (missing, 'INCOMPLETE_COMMIT') else 'INTEGRITY_MISMATCH') from exc


def _authority(root: Path) -> dict[str, Any]:
    auth = _read_doc(root, _authority_path(root), missing='WRITER_NOT_AUTHORIZED')
    if (set(auth) != {'schema_version', 'writer_id', 'writer_epoch'} or
        auth['schema_version'] != 1 or not isinstance(auth['writer_id'], str) or
        not auth['writer_id'] or not isinstance(auth['writer_epoch'], str) or
        not auth['writer_epoch']):
        raise WriterFailure('WRITER_NOT_AUTHORIZED')
    return auth


def configure_writer(root: str | Path, writer_id: str) -> dict[str, Any]:
    """Explicit one-time *policy* registration; the epoch is not a password.

    Operator MUST confirm no previous writer and no unsynced counterpart.
    Root filesystem O_EXCL is not a cross-device/cloud coordination service.
    """
    root = _root(root)
    if recovery_hold_present(root):
        raise WriterFailure('RECOVERY_HOLD')
    if not isinstance(writer_id, str) or not writer_id or len(writer_id) > 128 or '/' in writer_id or '\\' in writer_id:
        raise WriterFailure('INVALID_ARGUMENT')
    path = _authority_path(root)
    _mkdir_safe(root, path.parent)
    auth = {'schema_version': 1, 'writer_id': writer_id, 'writer_epoch': str(uuid.uuid4())}
    try:
        _create_new_bytes(path, _encode(auth))
        _fsync_dir(path.parent)
    except FileExistsError as exc:
        raise WriterFailure('WRITER_ALREADY_CONFIGURED') from exc
    except OSError as exc:
        raise WriterFailure('INCOMPLETE_PUBLISH') from exc
    return {'status': 'WRITER_CONFIGURED_POLICY_ONLY', 'writer_id': writer_id, 'writer_epoch': auth['writer_epoch']}


def _mkdir_safe(root: Path, directory: Path) -> None:
    try:
        _ensure_parent(root, directory)
    except CaptureFailure as exc:
        raise WriterFailure('UNSAFE_PATH') from exc


def _create_new_bytes(path: Path, data: bytes) -> None:
    _write_exclusive(path, data)


def _verify_small_existing(root: Path, path: Path, expected: bytes) -> None:
    _safe_existing(root, path)
    try:
        if path.read_bytes() != expected:
            raise WriterFailure('IDEMPOTENCY_CONFLICT')
    except OSError as exc:
        raise WriterFailure('INTEGRITY_MISMATCH') from exc


def _safe_existing(root: Path, file: Path) -> None:
    try:
        _safe_regular_file(root, file, missing_code='INCOMPLETE_PUBLISH')
    except IntegrityFailure as exc:
        raise WriterFailure('UNSAFE_PATH' if exc.code == 'UNSAFE_PATH' else 'INCOMPLETE_PUBLISH') from exc


def _publish_bytes_once(root: Path, path: Path, data: bytes) -> None:
    """Publish immutable small metadata with hardlink create-if-absent.

    The staging file is on the same filesystem. Never use replace() here.
    Filesystems without same-volume hardlinks cause fail-closed warning.
    """
    _mkdir_safe(root, path.parent)
    if path.exists() or path.is_symlink():
        _verify_small_existing(root, path, data)
        return
    staged = path.parent / ('.stage-' + secrets.token_hex(16))
    try:
        _create_new_bytes(staged, data)
        try:
            os.link(staged, path, follow_symlinks=False)
        except FileExistsError:
            pass  # Verify after disposing of our staging name.
        # An intentional temporary hardlink is not a valid *published*
        # two-name state. Unlink it before the new R13-D alias check.
        staged.unlink()
        _fsync_dir(path.parent)
        _verify_small_existing(root, path, data)
    finally:
        try: staged.unlink(missing_ok=True)
        except OSError: pass


def _vault_rel(sha256: str) -> str:
    return f'10_Evidence/Vault/objects/sha256/{sha256[:2]}/{sha256[2:4]}/{sha256}/payload'


def _vault_path(root: Path, digest: str) -> Path:
    return root.joinpath(*_vault_rel(digest).split('/'))


def _verify_vault(root: Path, target: Path, sha256: str, sha512: str, length: int) -> None:
    _safe_existing(root, target)
    try:
        a, b, sz = _digest_fd(target)
    except IntegrityFailure as exc:
        raise WriterFailure('INTEGRITY_MISMATCH') from exc
    if (a, b, sz) != (sha256, sha512, length):
        raise WriterFailure('INTEGRITY_MISMATCH')


def _copy_vault_once(root: Path, source: Path, sha256: str, sha512: str, length: int) -> None:
    target = _vault_path(root, sha256)
    _mkdir_safe(root, target.parent)
    if target.exists() or target.is_symlink():
        _verify_vault(root, target, sha256, sha512, length)
        return
    staged = target.parent / ('.stage-' + secrets.token_hex(16))
    try:
        a, b, sz = _copy_source(source, staged)
        if (a, b, sz) != (sha256, sha512, length):
            raise WriterFailure('INTEGRITY_MISMATCH')
        try:
            os.link(staged, target, follow_symlinks=False)
        except FileExistsError:
            pass  # A concurrent identical publisher is verified, never overwritten.
        # Drop our staging hardlink before verifying the final inode's
        # link count; do NOT bypass validation to permit permanent aliases.
        staged.unlink()
        _fsync_dir(target.parent)
        _verify_vault(root, target, sha256, sha512, length)
    finally:
        try: staged.unlink(missing_ok=True)
        except OSError: pass


@contextmanager
def _writer_lock(root: Path) -> Iterator[None]:
    if recovery_hold_present(root):
        raise WriterFailure('RECOVERY_HOLD')
    path = root / '90_System' / 'writer' / '.active'
    _mkdir_safe(root, path.parent)
    try:
        _create_new_bytes(path, b'LOCAL_LOCK_NOT_CLOUD_SAFE\n')
    except FileExistsError as exc:
        raise WriterFailure('WRITER_BUSY') from exc
    try:
        if recovery_hold_present(root):
            raise WriterFailure('RECOVERY_HOLD')
        yield
    finally:
        try:
            path.unlink()
            _fsync_dir(path.parent)
        except OSError:
            # Intentionally leave manual repair required instead of asserting unlocked.
            pass


def _paths(root: Path, device: str, capture_id: str) -> tuple[Path, Path]:
    # Device/capture arguments are already validated by verify_capture.
    base = root / '10_Evidence' / 'Records' / 'pending'
    return (base / 'observations' / device / f'{capture_id}.json',
            base / 'ingest' / device / f'{capture_id}.json')


def _observation(device: str, capture_id: str, writer: dict[str, Any], cap: dict[str, Any]) -> dict[str, Any]:
    digest = hashlib.sha256(('observation\x00' + device + '\x00' + capture_id).encode('utf-8')).hexdigest()
    return {'schema_version': 1, 'status': 'PENDING_CUSTODY', 'observation_id': 'obs-sha256-' + digest,
            'device_id': device, 'capture_id': capture_id, 'object_id': 'obj-sha256-' + cap['sha256'],
            'sha256': cap['sha256'], 'size_bytes': cap['size_bytes'],
            'writer_id': writer['writer_id'], 'writer_epoch': writer['writer_epoch']}


def _receipt(device: str, capture_id: str, writer: dict[str, Any], cap: dict[str, Any], obs: dict[str, Any]) -> dict[str, Any]:
    return {'schema_version': 1, 'status': 'VAULT_VERIFIED_UNCOMMITTED',
            'device_id': device, 'capture_id': capture_id, 'writer_id': writer['writer_id'],
            'writer_epoch': writer['writer_epoch'], 'object_id': obs['object_id'],
            'observation_id': obs['observation_id'], 'sha256': cap['sha256'],
            'size_bytes': cap['size_bytes'], 'vault_relpath': _vault_rel(cap['sha256']),
            'observation_sha256': hashlib.sha256(_encode(obs)).hexdigest()}


def _verified_capture(root: Path, device: str, capture_id: str) -> dict[str, Any]:
    try:
        return verify_capture(root, device, capture_id)
    except CaptureFailure as exc:
        raise WriterFailure('CAPTURE_NOT_READY' if exc.code == 'INCOMPLETE_CAPTURE' else exc.code) from exc


def _make(root: Path, device: str, capture_id: str, writer: dict[str, Any],
          cap: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    obs = _observation(device, capture_id, writer, cap)
    return obs, _receipt(device, capture_id, writer, cap, obs)


def verify_publication(root: str | Path, device_id: str, capture_id: str) -> dict[str, Any]:
    """Read-only verification. Does NOT attest custody, permanence, cloud sync or legal status."""
    root = _root(root)
    cap = _verified_capture(root, device_id, capture_id)
    obs_path, receipt_path = _paths(root, device_id, capture_id)
    receipt = _read_doc(root, receipt_path, missing='INCOMPLETE_PUBLISH')
    writer = _authority(root)
    obs, expected = _make(root, device_id, capture_id, writer, cap)
    if receipt != expected or receipt_path.read_bytes() != _encode(expected):
        raise WriterFailure('INTEGRITY_MISMATCH')
    actual_obs = _read_doc(root, obs_path, missing='INCOMPLETE_PUBLISH')
    if (actual_obs != obs or obs_path.read_bytes() != _encode(obs) or
        hashlib.sha256(_encode(actual_obs)).hexdigest() != receipt['observation_sha256']):
        raise WriterFailure('INTEGRITY_MISMATCH')
    _verify_vault(root, _vault_path(root, cap['sha256']), cap['sha256'], _capture_sha512(root, device_id, capture_id), cap['size_bytes'])
    return {**expected, 'receipt_sha256': hashlib.sha256(_encode(receipt)).hexdigest(),
            'scope': 'local_vault_bytes_unsealed_no_custody'}


def _capture_sha512(root: Path, device: str, cid: str) -> str:
    path = root/'00_Inbox'/'Drop'/device/cid/'capture.receipt.json'
    receipt = _read_doc(root, path, missing='CAPTURE_NOT_READY')
    return receipt['sha512']


def publish_capture(root: str | Path, device_id: str, capture_id: str,
                    writer_id: str, writer_epoch: str) -> dict[str, Any]:
    """Idempotent local writer publication; final *custody commit* deliberately excluded."""
    root = _root(root)
    cap = _verified_capture(root, device_id, capture_id)
    writer = _authority(root)
    if (writer_id, writer_epoch) != (writer['writer_id'], writer['writer_epoch']):
        raise WriterFailure('WRITER_NOT_AUTHORIZED')
    with _writer_lock(root):
        if _authority(root) != writer:
            raise WriterFailure('WRITER_NOT_AUTHORIZED')
        obs_path, receipt_path = _paths(root, device_id, capture_id)
        if receipt_path.exists() or receipt_path.is_symlink():
            return verify_publication(root, device_id, capture_id)
        src = root/'00_Inbox'/'Drop'/device_id/capture_id/'payload'
        try:
            _copy_vault_once(root, src, cap['sha256'], _capture_sha512(root, device_id, capture_id), cap['size_bytes'])
            if _verified_capture(root, device_id, capture_id)['sha256'] != cap['sha256']:
                raise WriterFailure('INTEGRITY_MISMATCH')
            obs, receipt = _make(root, device_id, capture_id, writer, cap)
            _publish_bytes_once(root, obs_path, _encode(obs))
            # The receipt is the last locally published file, but is NOT a custody commit.
            _publish_bytes_once(root, receipt_path, _encode(receipt))
        except (OSError, CaptureFailure) as exc:
            raise WriterFailure('INCOMPLETE_PUBLISH') from exc
        return verify_publication(root, device_id, capture_id)
