"""R13 local recovery quarantine markers; never a distributed writer fence.

Two redundant local markers detect accidental deletion of one marker and
incomplete restore. Anyone who controls the whole writable root can delete
both; no trusted remote lease or independent operator confirmation exists.
"""
from __future__ import annotations

from pathlib import Path
import re
import stat

from .verify import IntegrityFailure, _safe_regular_file, _strict_json, _unsafe_windows_attributes

HOLD_REL = "90_System/writer/recovery-hold.json"
SENTINEL_REL = "90_System/writer/recovery-sentinel.json"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class RecoveryFailure(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _marker_state(root: Path, relpath: str) -> str:
    """Metadata-only presence check: present / missing / unsafe.

    Unlike Path.exists(), lstat does not follow the marker's link target.
    A denied read or unsafe ancestor is NEVER interpreted as absent. This is
    only a local guard on one mutable filesystem, not distributed fencing.
    """
    try:
        for parent in (root, root / "90_System", root / "90_System" / "writer"):
            try:
                info = parent.lstat()
            except FileNotFoundError:
                return "missing"  # no marker possible under absent directory
            if (_unsafe_windows_attributes(info) or
                    not stat.S_ISDIR(info.st_mode) or
                    (hasattr(parent, "is_junction") and parent.is_junction())):
                return "unsafe"
        marker = root / relpath
        try:
            info = marker.lstat()
        except FileNotFoundError:
            return "missing"
        if (_unsafe_windows_attributes(info) or
                not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
                (hasattr(marker, "is_junction") and marker.is_junction())):
            return "unsafe"
        return "present"
    except (OSError, RuntimeError, ValueError):
        # ACL denial, vanished provider, invalid path, broken parent, etc.
        return "unsafe"


def recovery_hold_present(root: Path) -> bool:
    """Fail closed when EITHER quarantine marker exists or cannot be ruled out."""
    return any(_marker_state(root, path) != "missing"
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


def _marker_file_identity(path: Path) -> tuple[int, ...]:
    try:
        info = path.lstat()
        if (_unsafe_windows_attributes(info) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
            raise RecoveryFailure("UNSAFE_PATH")
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)
    except OSError as exc:
        raise RecoveryFailure("UNSAFE_PATH") from exc


def validate_recovery_hold(root: Path, expected_manifest_sha256: str | None = None) -> dict:
    """Read only: inspect both canonical records and optional expected snapshot ID."""
    p = root / HOLD_REL
    second = root / SENTINEL_REL
    p_state = _marker_state(root, HOLD_REL)
    s_state = _marker_state(root, SENTINEL_REL)
    if "unsafe" in (p_state, s_state):
        raise RecoveryFailure("UNSAFE_PATH")
    if p_state != "present" or s_state != "present":
        raise RecoveryFailure("RECOVERY_HOLD_MISSING")
    try:
        _safe_regular_file(root, p, missing_code="RECOVERY_HOLD_MISSING")
        _safe_regular_file(root, second, missing_code="RECOVERY_HOLD_MISSING")
        identity_before = (_marker_file_identity(p), _marker_file_identity(second))
        value = _strict_json(p)
        other = _strict_json(second)
        from .custody import _canon  # lazy import: writer/custody import each other
        digest = value.get("manifest_sha256")
        pair = _payloads(digest)
        if (value != pair[0] or other != pair[1] or
            p.read_bytes() != _canon(value) or second.read_bytes() != _canon(other) or
            (expected_manifest_sha256 is not None and digest != expected_manifest_sha256)):
            raise RecoveryFailure("RECOVERY_HOLD_INVALID")
        if identity_before != (_marker_file_identity(p), _marker_file_identity(second)):
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
    if (not path.is_dir() or path.is_symlink() or _unsafe_windows_attributes(path.lstat()) or
        (hasattr(path, 'is_junction') and path.is_junction())):
        raise RecoveryFailure("INVALID_ROOT")
    if not recovery_hold_present(path):
        # This is a local policy observation, NOT verified exclusive authority.
        return {"status": "LOCAL_WRITER_POLICY_ONLY", "writer_active": None,
                "scope": "no_recovery_hold_observed_not_external_exclusivity"}
    return validate_recovery_hold(path)
