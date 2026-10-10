"""R10 manual external-checkpoint contract for an R9 local custody ledger.

The software can verify bytes against a *supplied* independently retained
checkpoint. It cannot prove the user actually preserved the checkpoint at an
independent/trusted location or timestamp. Never call this notarization.
"""
from __future__ import annotations

import hashlib
import re
import stat
from pathlib import Path
from typing import Any

from .custody import CustodyFailure, _canon, _root_checked, _scan
from .verify import IntegrityFailure, _strict_json, _unsafe_windows_attributes

HEX = re.compile(r'[0-9a-f]{64}\Z')
FIELDS = frozenset({'schema_version', 'kind', 'event_count', 'tip_hash', 'checkpoint_sha256'})


class CheckpointFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _body(event_count: int, tip_hash: str) -> dict[str, Any]:
    return {'schema_version': 1, 'kind': 'SECOND_BRAIN_CUSTODY_CHECKPOINT',
            'event_count': event_count, 'tip_hash': tip_hash}


def create_checkpoint(root: str | Path) -> dict[str, Any]:
    """Produce bytes for OUT-OF-ROOT copying; no silent local persistence."""
    try:
        chain = _scan(_root_checked(root))
        if not chain or len(chain) % 2:
            raise CheckpointFailure('CHAIN_NOT_COMMIT_READY')
        body = _body(len(chain), chain[-1]['event_hash'])
        return {**body, 'checkpoint_sha256': hashlib.sha256(_canon(body)).hexdigest()}
    except CustodyFailure as exc:
        raise CheckpointFailure(exc.code) from exc


def _external_leaf_identity(path: Path) -> tuple[int, ...]:
    """Read ONLY metadata; block external aliases and Windows recall paths.

    Before/after leaf stats guard ordinary replacement, not malicious
    parent-directory ABA races or proofs of external custody.
    """
    try:
        leaf = None
        for current in (path, *path.parents):
            info = current.lstat()  # do not traverse symlink/cloud targets
            if (_unsafe_windows_attributes(info) or
                    stat.S_ISLNK(info.st_mode) or
                    (hasattr(current, 'is_junction') and current.is_junction())):
                raise CheckpointFailure('UNSAFE_CHECKPOINT_PATH')
            if current == path:
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise CheckpointFailure('UNSAFE_CHECKPOINT_PATH')
                leaf = info
            elif not stat.S_ISDIR(info.st_mode):
                raise CheckpointFailure('UNSAFE_CHECKPOINT_PATH')
        assert leaf is not None
        return (leaf.st_dev, leaf.st_ino, leaf.st_size, leaf.st_mtime_ns,
                leaf.st_ctime_ns, leaf.st_nlink)
    except (OSError, RuntimeError, ValueError) as exc:
        raise CheckpointFailure('UNSAFE_CHECKPOINT_PATH') from exc


def _external_path(root: Path, file: str | Path) -> Path:
    """Reject aliases before resolving/reading; NOT custody independence."""
    path = Path(file).expanduser().absolute()
    if path == root or path.is_relative_to(root):
        raise CheckpointFailure('CHECKPOINT_INSIDE_ROOT')
    _external_leaf_identity(path)
    try:
        canonical_root = root.resolve(strict=True)
        canonical_path = path.resolve(strict=True)
        if canonical_path == canonical_root or canonical_path.is_relative_to(canonical_root):
            raise CheckpointFailure('CHECKPOINT_INSIDE_ROOT')
    except (OSError, RuntimeError) as exc:
        raise CheckpointFailure('UNSAFE_CHECKPOINT_PATH') from exc
    return path


def verify_checkpoint(root: str | Path, checkpoint_path: str | Path) -> dict[str, Any]:
    """Validate anchored PREFIX. Later unanchored suffix is explicitly reported."""
    try:
        checked_root = _root_checked(root)
        file = _external_path(checked_root, checkpoint_path)
        witness_before = _external_leaf_identity(file)
        try:
            record = _strict_json(file)
        except IntegrityFailure as exc:
            raise CheckpointFailure('CHECKPOINT_MALFORMED') from exc
        if (set(record) != FIELDS or type(record['schema_version']) is not int or
                record['schema_version'] != 1 or record['kind'] != 'SECOND_BRAIN_CUSTODY_CHECKPOINT' or
                type(record['event_count']) is not int or record['event_count'] <= 0 or
                record['event_count'] % 2 or not isinstance(record['tip_hash'], str) or
                not HEX.fullmatch(record['tip_hash']) or
                not isinstance(record['checkpoint_sha256'], str) or
                not HEX.fullmatch(record['checkpoint_sha256'])):
            raise CheckpointFailure('CHECKPOINT_MALFORMED')
        body = _body(record['event_count'], record['tip_hash'])
        if hashlib.sha256(_canon(body)).hexdigest() != record['checkpoint_sha256']:
            raise CheckpointFailure('CHECKPOINT_MISMATCH')
        canonical_bytes_match = file.read_bytes() == _canon(record)
        witness_after = _external_leaf_identity(file)
        if witness_after != witness_before:
            raise CheckpointFailure('UNSAFE_CHECKPOINT_PATH')
        if not canonical_bytes_match:
            raise CheckpointFailure('CHECKPOINT_MALFORMED')
        chain = _scan(checked_root)
        count = record['event_count']
        if len(chain) < count:
            raise CheckpointFailure('CHECKPOINT_AHEAD_OR_ROLLBACK')
        if chain[count - 1]['event_hash'] != record['tip_hash']:
            raise CheckpointFailure('CHECKPOINT_CHAIN_MISMATCH')
        return {'status': ('CHECKPOINT_PREFIX_MATCH_UNANCHORED_SUFFIX' if len(chain) > count
                           else 'CHECKPOINT_EXACT_MATCH_EXTERNAL_CUSTODY_UNVERIFIED'),
                'verified_event_count': count, 'current_event_count': len(chain),
                'checkpoint_sha256': record['checkpoint_sha256'],
                'scope': 'supplied_checkpoint_match_only_not_timestamp_or_external_custody_proof'}
    except CustodyFailure as exc:
        raise CheckpointFailure(exc.code) from exc
    except OSError as exc:
        raise CheckpointFailure('UNSAFE_CHECKPOINT_PATH') from exc
