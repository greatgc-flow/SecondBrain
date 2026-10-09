"""R13 local recovery quarantine markers; never a distributed writer fence.

Two redundant local markers detect accidental deletion of one marker and
incomplete restore. Anyone who controls the whole writable root can delete
both; no trusted remote lease or independent operator confirmation exists.
"""
from __future__ import annotations

from pathlib import Path
import re

from .verify import IntegrityFailure, _safe_regular_file, _strict_json

HOLD_REL = "90_System/writer/recovery-hold.json"
SENTINEL_REL = "90_System/writer/recovery-sentinel.json"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class RecoveryFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def recovery_hold_present(root: Path) -> bool:
    """Presence of EITHER marker blocks writers, regardless of its bytes."""
    return any((root / path).exists() or (root / path).is_symlink()
               for path in (HOLD_REL, SENTINEL_REL))


def _payloads(manifest_sha256: str) -> tuple[dict, dict]:
    if not isinstance(manifest_sha256, str) or not HEX64.fullmatch(manifest_sha256):
        raise RecoveryFailure("RECOVERY_HOLD_INVALID")
    return (
        {"schema_version": 1, "kind": "LOCAL_RECOVERY_HOLD",
         "status": "RECOVERED_READ_ONLY", "manifest_sha256": manifest_sha256},
        {"schema_version": 1, "kind": "LOCAL_RECOVERY_SENTINEL",
         "manifest_sha256": manifest_sha256},
    )


def validate_recovery_hold(root: Path, expected_manifest_sha256: str | None = None) -> dict:
    """Read only: inspect both canonical records and optional expected snapshot ID."""
    p = root / HOLD_REL
    second = root / SENTINEL_REL
    has_p = p.exists() or p.is_symlink()
    has_s = second.exists() or second.is_symlink()
    if not has_p and not has_s:
        raise RecoveryFailure("RECOVERY_HOLD_MISSING")
    if not has_p or not has_s:
        raise RecoveryFailure("RECOVERY_HOLD_MISSING")
    try:
        _safe_regular_file(root, p, missing_code="RECOVERY_HOLD_MISSING")
        _safe_regular_file(root, second, missing_code="RECOVERY_HOLD_MISSING")
        value = _strict_json(p)
        other = _strict_json(second)
        from .custody import _canon  # lazy import: writer/custody import each other
        digest = value.get("manifest_sha256")
        pair = _payloads(digest)
        if (value != pair[0] or other != pair[1] or
            p.read_bytes() != _canon(value) or second.read_bytes() != _canon(other) or
            (expected_manifest_sha256 is not None and digest != expected_manifest_sha256)):
            raise RecoveryFailure("RECOVERY_HOLD_INVALID")
        return {"status": "RECOVERED_READ_ONLY", "writer_active": False,
                "manifest_sha256": digest,
                "scope": "local_advisory_only_not_distributed_fencing"}
    except RecoveryFailure:
        raise
    except IntegrityFailure as exc:
        if exc.code == "UNSAFE_PATH":
            raise RecoveryFailure("UNSAFE_PATH") from exc
        raise RecoveryFailure("RECOVERY_HOLD_INVALID") from exc
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RecoveryFailure("RECOVERY_HOLD_INVALID") from exc


def recovery_status(root: str | Path) -> dict:
    path = Path(root).expanduser().absolute()
    if not path.is_dir() or path.is_symlink():
        raise RecoveryFailure("INVALID_ROOT")
    if not recovery_hold_present(path):
        # This is a local policy observation, NOT verified exclusive authority.
        return {"status": "LOCAL_WRITER_POLICY_ONLY", "writer_active": False,
                "scope": "no_recovery_hold_observed_not_external_exclusivity"}
    return validate_recovery_hold(path)
